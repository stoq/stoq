# -*- coding: utf-8 -*-
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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s):       Evandro Vale Miquelito      <evandro@async.com.br>
##
##
""" Routines for database schema migration"""

from kiwi.component import get_utility
from kiwi.environ import environ

import stoqlib
from stoqlib.database.database import finish_transaction, execute_sql
from stoqlib.database.admin import create_base_schema
from stoqlib.database.runtime import new_transaction
from stoqlib.domain.profile import update_profile_applications
from stoqlib.domain.system import SystemTable
from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.lib.interfaces import IDatabaseSettings
from stoqlib.lib.parameters import (check_parameter_presence,
                                    ensure_system_parameters)

class SchemaMigration:
    """Schema migration management"""

    def __init__(self):
        self.current_db_version = None
        self.db_version = stoqlib.db_version

    def _get_migration_files(self, current_db_version, db_version):
        """Returns a list of all the migration sql files for a certain
        db schema version
        """
        rdbms_name = get_utility(IDatabaseSettings).rdbms
        migration_files = []
        for version in range(current_db_version + 1, self.db_version +1):
            filename = '%s-schema-migration-%s.sql' % (rdbms_name, version)
            sql_file = environ.find_resource('sql', filename)
            migration_files.append(sql_file)
        return migration_files

    def _check_up_to_date(self, conn):
        """Checks if the current database schema is up to date"""
        if not conn.tableExists(SystemTable.sqlmeta.table):
            SystemTable.createTable(connection=conn)
            self.current_db_version = stoqlib.FIRST_DB_VERSION
            SystemTable.update(conn, check_new_db=True,
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

    def check_updated(self, conn):
        if not self._check_up_to_date(conn):
            return True

        if check_parameter_presence(conn):
            return True

        return False

    def update_schema(self):
        """Check the current version of database and update the schema if
        it's needed
        """
        trans = new_transaction()

        if not self._check_up_to_date(trans):
            finish_transaction(trans, 1)
            return

        # Updating the schema for all the versions from the current database
        # version to the last schema version.
        sql_files = self._get_migration_files(self.current_db_version,
                                              self.db_version)
        for sql_file in sql_files:
            execute_sql(sql_file, trans)
            parts = sql_file.replace('.sql', '').split('-')
            version = parts[-1]
            try:
                version = int(version)
            except ValueError:
                raise ValueError("Bad sql file name, got %s" % sql_file)
            SystemTable.update(trans, version=version)
        # checks if there is new applications and update all the user
        # profiles on the system
        update_profile_applications(trans)
        # Updating the parameter list
        ensure_system_parameters(update=True)
        # Update the base schema
        create_base_schema()
        finish_transaction(trans, 1)

schema_migration = SchemaMigration()
