# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
## Author(s):   Johan Dahlin      <jdahlin@async.com.br>
##

import datetime
import socket
import subprocess

from kiwi.component import get_utility
from kiwi.log import Logger

from stoqlib.database.admin import create_base_schema
from stoqlib.database.policy import get_policy_by_name
from stoqlib.database.runtime import get_connection, new_transaction
from stoqlib.database.tables import get_table_type_by_name
from stoqlib.domain.base import AdaptableSQLObject
from stoqlib.domain.station import BranchStation
from stoqlib.domain.synchronization import BranchSynchronization
from stoqlib.domain.transaction import TransactionEntry
from stoqlib.enums import SyncPolicy
from stoqlib.lib.interfaces import IDatabaseSettings
from stoqlib.lib.xmlrpc import ServerProxy, XMLRPCService
from sqlobject.sqlbuilder import AND

log = Logger('stoqlib.synchronization')

CHUNKSIZE = 40960

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

    if issubclass(table, AdaptableSQLObject):
        for facet_type in table.getFacetTypes():
            _collect_table(tables, facet_type)

def _get_tables(policy, filter):
    tables = []
    for table_name, table_policy in policy.tables:
        if table_policy in filter:
            continue
        table = get_table_type_by_name(table_name)
        _collect_table(tables, table)

    return tables

class TableSerializer:
    def __init__(self, conn, tables):
        self._conn = conn
        self._tables = tables

    def _serialize_update(self, obj):
        values = []
        for column in obj.sqlmeta.columnList:
            value = getattr(obj, column.name)
            values.append("%s = %s" % (column.dbName,
                                       self._conn.sqlrepr(value)))

        return ("UPDATE %s SET %s WHERE %s = %s;" %
                (obj.sqlmeta.table,
                 ", ".join(values),
                 obj.sqlmeta.idName,
                 self._conn.sqlrepr(obj.id)))

    def _serialize_updates(self, results):
        data = ""
        for so in results:
            te = TransactionEntry.get(so.te_modifiedID, connection=self._conn)
            data += self._serialize_update(te)
            data += self._serialize_update(so)

        return data

    def _serialize_insert(self, obj):
        names = [obj.sqlmeta.idName]
        values = [str(obj.id)]
        for column in obj.sqlmeta.columnList:
            value = getattr(obj, column.name)
            names.append(column.dbName)
            values.append(self._conn.sqlrepr(value))

        return ("INSERT INTO %s (%s) VALUES (%s);" %
                (obj.sqlmeta.table,
                 ", ".join(names),
                 ", ".join(values)))

    def _serialize_inserts(self, results):
        data = ""
        for so in results:
            te = TransactionEntry.get(so.te_createdID, connection=self._conn)
            data += self._serialize_insert(te)
            data += self._serialize_insert(so)

        return data

    def get_chunks(self, timestamp):

        data = ""
        for table in self._tables:
            # Created
            results = table.select(
                AND(TransactionEntry.q.id == table.q.te_createdID,
                    TransactionEntry.q.timestamp > timestamp),
                connection=self._conn)
            if results.count():
                log.info("Serializing %d inserts() to table %s" % (
                    results.count(), table.sqlmeta.table))
                data += self._serialize_inserts(results)

            # Modified
            results = table.select(
                AND(TransactionEntry.q.id == table.q.te_modifiedID,
                    TransactionEntry.q.timestamp > timestamp),
                connection=self._conn)

            if results.count():
                log.info("Serializing %d update(s) to table %s" % (
                    results.count(), table.sqlmeta.table))
                data += self._serialize_updates(results)

            if len(data) >= CHUNKSIZE:
                yield data[:CHUNKSIZE]
                data = data[CHUNKSIZE:]

        if data:
            yield data

class SynchronizationService(XMLRPCService):
    def __init__(self, hostname, port):
        XMLRPCService.__init__(self, hostname, port)
        self._processes = {}

    #
    # Protocol / Public Methods
    #

    def clean(self):
        """
        Cleans the database
        """
        log.info('service.clean()')
        create_base_schema()

    def get_station_name(self):
        """
        @returns: the name of the station
        """
        return socket.gethostname()

    def sql_prepare(self):
        """
        @returns: an integer representing the insert
        """
        log.info('service.sql_prepare()')
        settings = get_utility(IDatabaseSettings)

        CMD = ("psql -n -h %(address)s -p %(port)s %(dbname)s -q "
               "--variable ON_ERROR_STOP=")
        cmd = CMD % dict(
            address=settings.address,
            port=settings.port,
            dbname=settings.dbname)

        log.info('sql_prepare: executing %s' % cmd)
        proc = subprocess.Popen(cmd, shell=True,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE)

        self._processes[proc.pid] = proc
        log.info('sql_prepare: return %d' % (proc.pid, ))

        return proc.pid

    def sql_insert(self, sid, data):
        """
        @param sid:
        @param data:
        """
        log.info('service.sql_insert(%d, %d bytes)' % (sid, len(data)))
        proc = self._processes[sid]

        # XMLRPC sends us unicode, postgres expects utf-8
        proc.stdin.write(data.encode('utf-8'))

    def sql_finish(self, sid):
        """
        @param sid:
        @returns: None if successful, otherwise a string
        """
        log.info('service.sql_finish(%d)' % (sid,))

        proc = self._processes.pop(sid)

        log.info('sql_finish: closing stdin for pg_dump process %d' % (sid,))
        proc.stdin.close()
        returncode = proc.wait()
        log.info('sql_finish: psql process returned %d' % (returncode,))

        if returncode == 3:
            return "psql returned an error: see the error log"

        return None

    def sql_changes(self, tables, timestamp):
        conn = get_connection()
        s = TableSerializer(conn, tables)
        data = ""
        for chunk in s.get_chunks(timestamp):
            data += chunk

        return data

    # Twisted
    xmlrpc_clean = clean
    xmlrpc_get_station_name = get_station_name
    xmlrpc_sql_prepare = sql_prepare
    xmlrpc_sql_insert = sql_insert
    xmlrpc_sql_finish = sql_finish

DUMP = "pg_dump -E UTF-8 -a -d -h %(address)s -p %(port)s -t %%s %(dbname)s"

class SynchronizationClient(object):
    def __init__(self, hostname, port):
        self._commit = True
        log.info('Connecting to %s:%d' % (hostname, port))
        self.proxy = ServerProxy("http://%s:%d" % (hostname, port))

        settings = get_utility(IDatabaseSettings)
        self._pgdump_cmd = DUMP % dict(address=settings.address,
                                       port=settings.port,
                                       dbname=settings.dbname)

    def _pg_dump_table(self, table):
        cmd = self._pgdump_cmd % table.sqlmeta.table
        log.info('executing %s' % cmd)
        return subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                                env=dict(LANG='C'))

    def _dump_tables(self, tables):
        combined = ''
        for table in tables:
            proc = self._pg_dump_table(table)

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

    def _get_policy(self, policy):
        log.info('Fetching policy %s' % (policy,))
        try:
            configuration = get_policy_by_name(policy)
        except LookupError:
            raise Exception("Unknown policy name: %s" % (policy, ))

        return configuration

    def _get_station(self, conn, name):
        log.info("Fetching station %s" % (name, ))

        # Note: This assumes that names of the stations are unique
        stations = BranchStation.select(BranchStation.q.name == name,
                                        connection=conn)
        if stations.count() != 1:
            raise Exception(
                "There is no station for %s" % (name,))

        return stations[0]

    def _get_synchronization(self, trans, branch):
        results = BranchSynchronization.select(
            BranchSynchronization.q.branchID == branch.id,
            connection=trans)

        if results.count() == 0:
            return None
        return results[0]

    def _update_synchronization(self, trans, station_name, timestamp, policy):
        station = self._get_station(trans, station_name)

        sync = self._get_synchronization(trans, station.branch)
        if not sync:
            log.info("Created BranchSynchronization object")
            sync = BranchSynchronization(timestamp=timestamp,
                                         branch=station.branch,
                                         policy=policy,
                                         connection=trans)
        else:
            log.info("Updating BranchSynchronization object")
            sync.timestamp = timestamp

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
                "not have an entry in the BranchSynchronization table")

        return sync.timestamp

    # Public API

    def clean(self):
        self.proxy.clean()

    def get_station_name(self):
        return self.proxy.get_station_name()

    def update(self, station_name):
        """
        @param station_name:
        """
        policy = self._get_policy('shop')

        trans = new_transaction()

        last_sync = self._get_last_timestamp(trans, station_name)
        timestamp = datetime.datetime.now()

        tables = _get_tables(policy, (SyncPolicy.FROM_TARGET,
                                      SyncPolicy.INITIAL))
        ts = TableSerializer(trans, tables)

        self._sql_send(ts.get_chunks(last_sync))

        self._update_synchronization(trans, station_name, timestamp,
                                     policy.name)

        if self._commit:
            trans.commit()

    def clone(self, station_name):
        """
        Clones the database of the current machine and sends over the complete
        state to the client as raw SQL commands.

        @param station_name:
        """
        policy = self._get_policy('shop')

        trans = new_transaction()

        timestamp = datetime.datetime.now()

        tables = _get_tables(policy, filter=(SyncPolicy.FROM_TARGET,))
        self._sql_send(self._dump_tables(tables))

        self._update_synchronization(trans, station_name, timestamp,
                                     policy.name)

        if self._commit:
            trans.commit()

    def disable_commit(self):
        """
        Disables committing and sending data to the server
        """
        self._commit = False
