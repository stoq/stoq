# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s):       Evandro Vale Miquelito      <evandro@async.com.br>
##
##
""" Routines for database schema migration"""

import sys
import datetime

from kiwi.environ import environ
from sqlobject import SQLObject
from sqlobject import DateTimeCol, IntCol

import stoqlib
from stoqlib.exceptions import SQLError, DatabaseInconsistency
from stoqlib.lib.runtime import new_transaction
from stoqlib.lib.configparser import config
from stoqlib.database import finish_transaction
from stoqlib.domain.profile import update_profile_applications
from stoqlib.domain.system import SystemTable
from stoqlib.domain.base import AbstractModel
from stoqlib.domain.tables import get_table_types


class SchemaMigration:
    """Schema migration management"""

    def __init__(self):
        self.current_db_version = None
        self.db_version = stoqlib.__db_version__

    def _get_migration_files(self, current_db_version, db_version):
        """Returns a list of all the migration sql files for a certain
        db schema version
        """
        rdbms_name = config.get_rdbms_name()
        migration_files = []
        for version in range(current_db_version + 1, self.db_version +1):
            filename = '%s-schema-migration-%s.sql' % (rdbms_name, version)
            sql_file = environ.find_resource('sql', filename)
            migration_files.append(sql_file)
        return migration_files

    def _check_up_to_date(self, conn):
        """Checks if the current database schema is up to date"""
        if not conn.tableExists(SystemTable.get_db_table_name()):
            SystemTable.createTable(connection=conn)
            self.current_db_version = stoqlib.FIRST_DB_VERSION
            add_system_table_reference(conn, check_new_db=True,
                                        version=self.current_db_version)
            return True
        results = SystemTable.select(connection=conn)
        self.current_db_version = results.max('version')
        if self.current_db_version == self.db_version:
            return False
        if self.current_db_version > self.db_version:
            raise DatabaseInconsistency('The current version of database '
                                        '(%s) is greater than the system '
                                        'version (%s)'
                                        % (self.current_db_version,
                                           self.db_version))
        return True

    def _create_tables(self, conn):
        table_types = get_table_types()
        for table in table_types:
            if not conn.tableExists(table.get_db_table_name()):
                table.createTable(connection=conn)
        conn.commit()

    def update_schema(self):
        """Check the current version of database and update the schema if
        it's needed
        """
        conn = new_transaction()
        if not self._check_up_to_date(conn):
            finish_transaction(conn, 1)
            return
        self._create_tables(conn)

        # Updating the schema for all the versions from the current database
        # version to the last schema version.
        sql_files = self._get_migration_files(self.current_db_version,
                                              self.db_version)
        for sql_file in sql_files:
            file_data = open(sql_file).read()
            try:
                conn.query(file_data)
            except:
                type, value, trace = sys.exc_info()
                raise SQLError("Bad sql script, got error %s, of type %s"
                               % (value, type))
            conn.commit()
            add_system_table_reference(conn)
        # checks if there is new applications and update all the user
        # profiles on the system
        update_profile_applications(conn)
        finish_transaction(conn, 1)


def add_system_table_reference(conn, check_new_db=False, version=None):
    """Add a new entry on SystemTable with the current schema version"""
    result = SystemTable.select(connection=conn).count()
    if result and check_new_db:
        raise ValueError('SystemTable should be empty at this point '
                         'got %d results' % result)
    elif not result and not check_new_db:
        raise ValueError('SystemTable should have at least one '
                         'item at this point, got nothing')
    version = version or stoqlib.__db_version__
    SystemTable(version=version,
                update_date=datetime.datetime.now(),
                connection=conn)


schema_migration = SchemaMigration()
