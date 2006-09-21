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

import select
import subprocess

from kiwi.component import get_utility
from kiwi.log import Logger

from stoqlib.database.admin import create_base_schema, ensure_sellable_units
from stoqlib.database.database import db_table_name
from stoqlib.database.policy import get_policy_by_name
from stoqlib.database.runtime import new_transaction
from stoqlib.database.tables import create_tables, get_table_type_by_name
from stoqlib.domain.system import SystemTable
from stoqlib.enums import SyncPolicy
from stoqlib.exceptions import DatabaseError
from stoqlib.lib.component import AdaptableSQLObject
from stoqlib.lib.interfaces import IDatabaseSettings
from stoqlib.lib.xmlrpc import ServerProxy, XMLRPCService

log = Logger('stoqlib.synchronization')

CHUNKSIZE = 40960

class SynchronizationService(XMLRPCService):
    def __init__(self, hostname, port):
        XMLRPCService.__init__(self, hostname, port)
        self._processes = {}

    def _add_remaning_schema(self):
        log.info('adding remaining schema')
        trans = new_transaction()
        ensure_sellable_units()

        SystemTable.update(trans, check_new_db=True)
        trans.commit()

    def _check_error(self, proc):
        fds =  select.select([proc.stderr], [], [], .500)[0]
        if not fds:
            return
        data = (proc.stderr.readline() +
                proc.stderr.readline()[:-1])
        if data:
            raise DatabaseError(data)

    #
    # Protocol / Public Methods
    #

    def clean(self):
        log.info('service.clean()')
        create_tables()
        create_base_schema()

    def sql_prepare(self):
        log.info('service.sql_prepare()')
        settings = get_utility(IDatabaseSettings)

        CMD = "psql -n -h %(address)s -p %(port)s %(dbname)s -q"
        cmd = CMD % dict(
            address=settings.address,
            port=settings.port,
            dbname=settings.dbname)

        log.info('sql_prepare: executing %s' % cmd)
        proc = subprocess.Popen(cmd, shell=True,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE
                                )

        self._processes[proc.pid] = proc
        log.info('sql_prepare: return %d' % (proc.pid, ))
        return proc.pid

    def sql_insert(self, pid, dump):
        log.info('service.sql_insert(%d, %d bytes)' % (pid, len(dump)))
        proc = self._processes[pid]

        proc.stdin.write(dump.encode('utf-8'))
        self._check_error(proc)

    def sql_finish(self, pid):
        log.info('service.sql_finish(%d)' % (pid,))

        proc = self._processes.pop(pid)

        log.info('sql_finish: closing stdin for pg_dump process %d' % (pid,))
        proc.stdin.close()
        self._check_error(proc)

        returncode = proc.wait()
        log.info('sql_finish: psql process returned %d' % (returncode,))

        self._add_remaning_schema()

    # Twisted
    xmlrpc_clean = clean
    xmlrpc_sql_prepare = sql_prepare
    xmlrpc_sql_insert = sql_insert
    xmlrpc_sql_finish = sql_finish

class SynchronizationClient(object):
    def __init__(self, hostname, port):
        log.info('Connecting to %s:%d' % (hostname, port))
        self.proxy = ServerProxy("http://%s:%d" % (hostname, port))

        settings = get_utility(IDatabaseSettings)
        self._pgdump_cmd = (
            "pg_dump -E UTF-8 -a -d -h %(address)s -p %(port)s -t %%s %(dbname)s"
            % dict(address=settings.address,
                   port=settings.port,
                   dbname=settings.dbname))

    def _pg_dump_table(self, table):
        cmd = self._pgdump_cmd % db_table_name(table)
        log.info('executing %s' % cmd)
        return subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                                env=dict(LANG='C'))

    def _get_policy(self, policy):
        log.info('Fetching policy %s' % (policy,))
        try:
            configuration = get_policy_by_name(policy)
        except LookupError:
            raise Exception("Unknown policy name: %s" % (policy, ))

        return configuration

    # Public API

    def clean(self):
        self.proxy.clean()

    def _collect_table(self, tables, table):
        if table in tables:
            return

        parent = table.sqlmeta.parentClass
        while parent:
            self._collect_table(tables, parent)
            parent = parent.sqlmeta.parentClass

       ##for column in table.sqlmeta.columnList:
       ##    if isinstance(column, SOForeignKey):
       ##        foreign_table = findClass(column.foreignKey)
       ##        self._collect_table(tables, foreign_table)

        log.info('Adding table %s' % table)
        tables.append(table)

        if issubclass(table, AdaptableSQLObject):
            for facet_type in table.getFacetTypes():
                self._collect_table(tables, facet_type)

    def clone(self):
        tables = ('transaction_entry', 'person',)

        policy = self._get_policy('shop')

        sid = self.proxy.sql_prepare()

        combined = ""
        tables = []
        for table_name, table_policy in policy.tables:
            if table_policy == SyncPolicy.FROM_TARGET:
                continue
            table = get_table_type_by_name(table_name)
            self._collect_table(tables, table)

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
                    self.proxy.sql_insert(sid, combined[:CHUNKSIZE])
                    combined = combined[CHUNKSIZE:]

        # Also send left overs
        if combined:
            self.proxy.sql_insert(sid, combined)

        self.proxy.sql_finish(sid)
