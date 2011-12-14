# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2007 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

"""Synchronization, Distributed database replication.
"""

import sets
import socket

from dateutil.parser import parse
from kiwi.component import get_utility, provide_utility
from kiwi.log import Logger

from stoqlib.database.admin import create_base_schema
from stoqlib.database.database import dump_table
from stoqlib.database.interfaces import (ICurrentBranchStation, ICurrentBranch,
                                         IDatabaseSettings)
from stoqlib.database.orm import ORMObject, ORMObjectNotFound, const
from stoqlib.database.runtime import (get_connection, new_transaction,
                                      get_current_branch)
from stoqlib.database.policy import get_policy_by_name
from stoqlib.database.tables import get_table_type_by_name
from stoqlib.domain.base import AdaptableORMObject
from stoqlib.domain.person import PersonAdaptToUser
from stoqlib.domain.station import BranchStation
from stoqlib.domain.synchronization import BranchSynchronization
from stoqlib.domain.system import TransactionEntry
from stoqlib.enums import SyncPolicy
from stoqlib.lib.process import Process, PIPE
from stoqlib.net.xmlrpcservice import ServerProxy, XMLRPCService

log = Logger('stoqlib.synchronization')

CHUNKSIZE = 40960

# SERIAL in PostgreSQL is 64-bits
# 50-bits for object ids
# 14-bits for branch in other words
# 16384 branches
# 1 quadrillion (1000 million millions) objects per branch
# 10^15 is not exactly 50 bits, but it helps debugging
BRANCH_ID_OFFSET = 1000000000000000
#BRANCH_ID_OFFSET = 1 << 50


def _collect_table(tables, table):
    if table in tables:
        return

    parent = table.sqlmeta.parentClass
    while parent:
        _collect_table(tables, parent)
        parent = parent.sqlmeta.parentClass

   ##for column in table.sqlmeta.columnList:
   ##    if isinstance(column, SOForeignKey):
   ##        foreign_table = findClass(column.foreignKey)
   ##        _collect_table(tables, foreign_table)

    tables.append(table)

    if issubclass(table, AdaptableORMObject):
        # FIXME: Remove this and put the adapter tables in
        #        the policy list directly instead
        for facet_type in table.getFacetTypes():
            if issubclass(facet_type, ORMObject):
                _collect_table(tables, facet_type)


def get_tables(policy, pfilter=None):
    """Fetches a list of tables given a specific policy.
    A pfilter can optionally be specified to filter out tables
    which does not match a specific state.

    @param policy: a SynchronizationPolicy
    @param pfilter: a sequence of states to skip or None to fetch all
    @returns: a list of tables
    @rtype: list of sqlobject tables
    """
    tables = []
    for table_name, table_policy in policy.tables:
        if pfilter and table_policy in pfilter:
            continue
        table = get_table_type_by_name(table_name)
        _collect_table(tables, table)

    return tables


class TableSerializer:
    def __init__(self, conn, tables, station):
        self._conn = conn
        self._tables = tables
        self._branch = station.branch

    def _serialize_update(self, obj):
        values = []
        for column in obj.sqlmeta.columnList:
            value = getattr(obj, column.name)
            values.append("%s = %s" % (column.dbName,
                                       self._conn.sqlrepr(value)))

        cmd = ("UPDATE %s SET %s WHERE %s = %s;" %
               (obj.sqlmeta.table, ", ".join(values),
                obj.sqlmeta.idName, self._conn.sqlrepr(obj.id)))
        log.info(cmd)
        return cmd

    def _serialize_insert(self, obj):
        names = [obj.sqlmeta.idName]
        values = [str(obj.id)]
        for column in obj.sqlmeta.columnList:
            value = getattr(obj, column.name)
            names.append(column.dbName)
            values.append(self._conn.sqlrepr(value))

        cmd = ("INSERT INTO %s (%s) VALUES (%s);" %
               (obj.sqlmeta.table, ", ".join(names), ", ".join(values)))
        log.info(cmd)
        return cmd

    def _serialize_inserts(self, table, timestamp):
        results = self._branch.fetchTIDsForOtherStations(
            table, timestamp, TransactionEntry.CREATED, self._conn)

        data = ""
        if results:
            log.info("Serializing %d insert(s) to table %s" % (
                results.count(), table.sqlmeta.table))

            for so in results:
                tec = TransactionEntry.get(so.te_createdID,
                                           connection=self._conn)
                data += self._serialize_insert(tec)
                tem = TransactionEntry.get(so.te_modifiedID,
                                           connection=self._conn)
                data += self._serialize_insert(tem)
                data += self._serialize_insert(so)

        return data

    def _serialize_updates(self, table, timestamp):
        results = self._branch.fetchTIDsForOtherStations(
            table, timestamp, TransactionEntry.MODIFIED, self._conn)

        data = ""
        if results:
            log.info("Serializing %d update(s) to table %s" % (
                results.count(), table.sqlmeta.table))

            for so in results:
                te = TransactionEntry.get(so.te_modifiedID,
                                          connection=self._conn)
                data += self._serialize_update(te)
                data += self._serialize_update(so)

        return data

    def get_chunks(self, timestamp):
        data = ""

        for table in self._tables:
            data += self._serialize_inserts(table, timestamp)
            data += self._serialize_updates(table, timestamp)

            if len(data) >= CHUNKSIZE:
                yield data[:CHUNKSIZE]
                data = data[CHUNKSIZE:]

        if data:
            yield data


class SynchronizationService(XMLRPCService):
    def __init__(self, hostname, port):
        XMLRPCService.__init__(self, hostname, port)
        self._processes = {}

        self.conn = get_connection()
        if self.conn.tableExists('branch_station'):
            self.set_station_by_name(self.get_station_name())

    #
    # Protocol / Public Methods
    #

    def clean(self):
        """Cleans the database.
        """
        log.info('service.clean()')
        create_base_schema()

        # If we're going to copy the transaction_entry, drop the
        # user_id/station_id constraints before copying it, so we
        # can copy the whole table before copying anything else
        log.info('removing transaction entry constraints ')
        conn = get_connection()
        conn.query(
            '''ALTER TABLE %(t)s
            DROP CONSTRAINT %(t)s_station_id_fkey,
            DROP CONSTRAINT %(t)s_user_id_fkey;
            COMMIT;''' % dict(t='transaction_entry'))

    def get_station_name(self):
        """
        Gets the name of the station.
        @returns: the name of the station.
        """
        return socket.gethostname()

    def set_station_by_name(self, name):
        """
        Set the currently station by given name.
        @param name: name of the station
        """
        station = BranchStation.selectOneBy(name=name, connection=self.conn)

        # We can't use set_current_branch_station because we want to
        # replace the current utilities in some cases
        if station:
            log.info("Setting BranchStation to %s" % (station.name, ))
            provide_utility(ICurrentBranchStation, station, replace=True)
            provide_utility(ICurrentBranch, station.branch, replace=True)

    def bump_sequences(self, sequences, strlow, strhigh):
        low, high = long(strlow), long(strhigh)
        log.info("Bumping shared sequence ids (%d-%d)" % (low, high))
        for sequence in sequences:
            self.conn.bumpSequence(sequence, low + 1, low, high)

    def sql_prepare(self):
        """
        Gets an integer that represents the database insert.
        @returns: an integer representing the insert
        """
        log.info('service.sql_prepare()')
        settings = get_utility(IDatabaseSettings)

        CMD = ("psql -n -h %(address)s -U %(username)s "
               "-p %(port)s %(dbname)s --variable ON_ERROR_STOP=")

        cmd = CMD % dict(
            address=settings.address,
            username=settings.username,
            port=settings.port,
            dbname=settings.dbname)

        noisy = False
        if noisy:
            cmd += '-a'
            stdout = None
        else:
            cmd += '-q'
            stdout = PIPE

        log.info('sql_prepare: executing %s' % cmd)
        proc = Process(cmd, shell=True,
                       stdin=PIPE,
                       stdout=stdout)

        self._processes[proc.pid] = proc
        log.info('sql_prepare: PID is %d' % (proc.pid, ))

        return proc.pid

    def sql_insert(self, sid, data):
        """
        Insert sid and date.
        @param sid:
        @param data:
        """
        # XXX: rewrite the docstring
        # XMLRPC sends us unicode, postgres/subprocess expects utf-8
        data = data.encode('utf-8')

        log.info('service.sql_insert(%d, %d bytes)' % (sid, len(data)))
        proc = self._processes[sid]

        proc.stdin.write(data)

    def sql_finish(self, sid):
        """
        Finish an sql process.
        @param sid:
        @returns: None if successful, otherwise a string
        """
        # XXX: rewrite the docstring
        log.info('service.sql_finish(%d)' % (sid, ))

        proc = self._processes.pop(sid)

        proc.stdin.close()
        log.info('sql_finish: waiting for process %d to finish' % (proc.pid, ))
        returncode = proc.wait()
        log.info('sql_finish: psql process returned %d' % (returncode, ))

        if returncode == 3:
            return "psql returned an error: see the error log"

        return None

    def changes(self, policy_name, timestr):
        policy = get_policy_by_name(policy_name)
        timestamp = parse(timestr)
        conn = get_connection()
        branch = get_current_branch(conn)
        tables = get_tables(policy, (SyncPolicy.FROM_SOURCE,
                                     SyncPolicy.INITIAL))
        log.info("Fetching all changes since %s" % (timestamp, ))
        data = []
        for table in tables:
            if table == TransactionEntry:
                continue
            objs = []
            for te_type in [TransactionEntry.CREATED, TransactionEntry.MODIFIED]:
                for so in branch.fetchTIDs(
                    table, timestamp, te_type, conn):
                    if te_type == TransactionEntry.CREATED:
                        f = so.te_createdID
                    elif te_type == TransactionEntry.MODIFIED:
                        f = so.te_modifiedID
                    else:
                        raise AssertionError
                    te = TransactionEntry.get(f, connection=conn)

                    # XML-RPC does not handle:
                    #   - numbers using more than 32 bits
                    #   - datetime objects
                    # Convert these objects to string and convert them
                    # back on the other side
                    #
                    attrs = [(column.dbName,
                              conn.sqlrepr(getattr(so, column.name)))
                             for column in so.sqlmeta.columnList]
                    objs.append((conn.sqlrepr(so.id),
                                 attrs,
                                 conn.sqlrepr(so.te_createdID),
                                 conn.sqlrepr(so.te_modifiedID),
                                 conn.sqlrepr(te.te_time),
                                 conn.sqlrepr(te.user_id),
                                 conn.sqlrepr(te.station_id)))
            if objs:
                data.append((table.__name__, objs))

        log.info("changes: returning %d objects" % (
            sum([len(objs) for objs in data])))
        return data

    def quit(self):
        self.stop()

    # Twisted
    xmlrpc_clean = clean
    xmlrpc_get_station_name = get_station_name
    xmlrpc_set_station_by_name = set_station_by_name
    xmlrpc_bump_sequences = bump_sequences
    xmlrpc_changes = changes
    xmlrpc_sql_prepare = sql_prepare
    xmlrpc_sql_insert = sql_insert
    xmlrpc_sql_finish = sql_finish
    xmlrpc_quit = quit


class SynchronizationClient(object):
    def __init__(self, hostname, port):
        self._commit = True
        log.info('Connecting to %s:%d' % (hostname, port))
        self.proxy = ServerProxy("http://%s:%d" % (hostname, port))

    def _dump_tables(self, tables):
        combined = ''
        for table in tables:
            proc = dump_table(table.sqlmeta.table)
            # This is kind of tricky, only send data when we reached CHUNKSIZE,
            # it saves resources since rpc calls can be expensive
            while True:
                data = proc.stdout.read(CHUNKSIZE)
                if not data:
                    break
                combined += data
                if len(combined) >= CHUNKSIZE:
                    yield combined[:CHUNKSIZE]
                    combined = combined[CHUNKSIZE:]

        # Finally send leftovers
        if combined:
            yield combined

        # PersonAdaptToUser and BranchStation are now copied, add back the
        # constraints on the TransactionEntry table.
        if TransactionEntry in tables:
            assert PersonAdaptToUser in tables
            assert BranchStation in tables
            yield '''ALTER TABLE %(t)s
              ADD CONSTRAINT %(t)s_user_id_fkey FOREIGN KEY(user_id)
                REFERENCES person_adapt_to_user (id),
              ADD CONSTRAINT %(t)s_station_id_fkey FOREIGN KEY(station_id)
                REFERENCES branch_station (id);''' % dict(t='transaction_entry')

    def _get_policy(self, policy):
        log.info('Fetching policy %s' % (policy, ))
        try:
            configuration = get_policy_by_name(policy)
        except LookupError:
            raise Exception("Unknown policy name: %s" % (policy, ))
        return configuration

    def _get_station(self, conn, name):
        # Note: This assumes that names of the stations are unique
        station = BranchStation.selectOneBy(name=name, connection=conn)
        if station is None:
            raise Exception("There is no station for %s" % (name, ))
        return station

    def _get_synchronization(self, trans, branch):
        return BranchSynchronization.selectOneBy(
            branchID=branch.id, connection=trans)

    def _update_synchronization(self, trans, station, timestamp, policy):
        sync = self._get_synchronization(trans, station.branch)
        if not sync:
            log.info("Created BranchSynchronization object")
            BranchSynchronization(
                sync_time=timestamp, branch=station.branch, policy=policy,
                connection=trans)
        else:
            log.info("Updating BranchSynchronization object")
            sync.sync_time = timestamp

    def _sql_send(self, iterator):
        if not self._commit:
            import pprint
            pprint.pprint(list(iterator))
            return

        proxy = self.proxy
        sid = proxy.sql_prepare()
        for item in iterator:
            proxy.sql_insert(sid, item)

        error = proxy.sql_finish(sid)
        if error:
            raise SystemExit('sql_finish returned an error:\n %s' % error)

    def _get_last_timestamp(self, trans, station_name):
        station = self._get_station(trans, station_name)
        sync = self._get_synchronization(trans, station.branch)
        if not sync:
            raise SystemExit(
                "Tried to synchronize against for station %s which does "
                "not have an entry in the BranchSynchronization table" % (
                station_name, ))
        return sync.sync_time

    def _insert_one(self, trans, table, obj_id, attrs):
        attrs = attrs[:]
        attrs.insert(0, ('id', str(obj_id)))
        names, values = zip(*attrs)
        cmd = ("INSERT INTO %s (%s) VALUES (%s);" %
               (table.sqlmeta.table,
                ", ".join(names),
                ", ".join(values)))
        log.info("Executing SQL: %s" % (cmd, ))
        trans.query(cmd)

    def _update_one(self, trans, table, obj_id, attrs):
        cmd = ("UPDATE %s SET %s WHERE id = %s;" %
                (table.sqlmeta.table,
                 ", ".join('%s = %s' % (name, value) for name, value in attrs),
                 trans.sqlrepr(obj_id)))
        log.info("Executing SQL: %s" % (cmd, ))
        trans.query(cmd)

    def _bump_id_sequences(self, station, policy):
        table_names = [t.sqlmeta.table + '_id_seq' for t in get_tables(policy)]

        branch = station.branch
        # The main branch is assumed to be 1, so out must be at least 2
        if branch.id < 2:
            raise AssertionError
        # The main branch has ids allocated in the range 1..BRANCH_OFFSET,
        # The second branch in the range BRANCH_OFFSET..2*BRANCH_OFFSET etc
        branch_offset = (branch.id - 1) * BRANCH_ID_OFFSET
        self.proxy.bump_sequences(table_names, str(branch_offset),
                                  str(branch_offset + BRANCH_ID_OFFSET))

    def _has_update_conflict(self, trans, obj, station, last_sync, attrs):
        # At this point we need to check if the target has
        # modified an object which has been modified locally
        # as well, in that case we're just going to ignore it
        # and write an entry in a conflict log

        if (obj.te_modified.station == station and
            obj.te_modified.te_time <= last_sync):
            # FIXME: Write a conflict log entry
            return False

        current = [(column.dbName,
                    trans.sqlrepr(getattr(obj, column.name)))
                   for column in obj.sqlmeta.columnList]

        # xmlrpc converts the list of tuples to a list of lists,
        # convert it back so set won't barf at us.
        attrs = [tuple(pair) for pair in attrs]
        modified = sets.Set(current).difference(sets.Set(attrs))

        log.info("Change Conflict on %d in %s %s" % (
            obj.id, obj.sqlmeta.table,
            ', '.join(['%s=%s' % part for part in modified])))

        # FIXME: Delete the transaction entry on the client side
        return True

    def clean(self):
        self.proxy.clean()

    def get_station_name(self):
        return self.proxy.get_station_name()

    def update(self, station_name):
        """
        Update client.
        @param station_name:
        """
        # XXX: Rewrite docstring
        policy = self._get_policy('shop')
        trans = new_transaction()
        timestamp = const.NOW()
        station = self._get_station(trans, station_name)
        last_sync = self._get_last_timestamp(trans, station_name)
        # We're synchronizing in two steps;
        # First copy over all the changes from the target
        # Secondly copy over all the changes to the target

        # First step;
        # Ask the client for all the modifications (according to a certain policy)
        # since a specific timestamp and send it over.
        # We'll get them back in special format because we're not committing
        # all of them with certainty
        changes = self.proxy.changes(policy.name, str(last_sync))
        for table_name, objs in changes:
            table = get_table_type_by_name(table_name)
            for (obj_ids, attrs, tem_ids, tec_ids,
                 timestamp_, user_id, station_id) in objs:
                obj_id = long(obj_ids)
                tec_id = long(tec_ids)
                tem_id = long(tem_ids)
                try:
                    obj = table.get(obj_id, connection=trans)
                except ORMObjectNotFound:
                    obj = None

                entry_attrs = [('te_time', timestamp_),
                               ('user_id', user_id),
                               ('station_id', station_id)]

                if obj is None:
                    self._insert_one(trans, TransactionEntry, tec_id, entry_attrs)
                    self._insert_one(trans, TransactionEntry, tem_id, entry_attrs)
                    self._insert_one(trans, table, obj_id, attrs)
                else:
                    if self._has_update_conflict(trans, obj, station,
                                                 last_sync, attrs):
                        continue

                    self._update_one(trans, TransactionEntry, tem_id, entry_attrs)
                    self._update_one(trans, table, obj_id, attrs)

        # Second step
        # Send over all the changes from the source to the target
        tables = get_tables(policy, (SyncPolicy.FROM_TARGET,
                                     SyncPolicy.INITIAL))
        ts = TableSerializer(trans, tables, station)

        self._sql_send(ts.get_chunks(last_sync))

        if self._commit:
            self._update_synchronization(trans, station, timestamp,
                                         policy.name)
            trans.commit()

    def clone(self, station_name, transaction=None):
        """Clones the database of the current machine and sends over the complete
        state to the client as raw SQL commands.

        @param station_name:
        """
        policy = self._get_policy('shop')
        if not transaction:
            trans = new_transaction()
        else:
            trans = transaction
        timestamp = const.NOW()
        station = self._get_station(trans, station_name)
        tables = get_tables(policy, pfilter=(SyncPolicy.FROM_TARGET, ))
        self._sql_send(self._dump_tables(tables))
        if not self._commit:
            return
        self._update_synchronization(trans, station, timestamp, policy.name)
        trans.commit()

        # All objects are now transferred, we need to set the active station
        # and branch now because updating the database depends on it
        self.proxy.set_station_by_name(station.name)

        # Finally bump the sequence ids for all the tables which are
        # synchronized in both directions to avoid conflicts
        self._bump_id_sequences(station, policy)

    def quit(self):
        self.proxy.quit()

    def disable_commit(self):
        """Disables committing and sending data to the server
        """
        self._commit = False
