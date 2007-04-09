# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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
##                  Johan Dahlin                <jdahlin@async.com.br>
##
##
""" Routines for database schema migration"""

import glob
import operator
import os
import shutil
import tempfile

from kiwi.environ import environ
from kiwi.log import Logger

from stoqlib.database.database import execute_sql
from stoqlib.database.runtime import new_transaction, get_connection
from stoqlib.domain.profile import update_profile_applications
from stoqlib.domain.system import SystemTable
from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.lib.defaults import stoqlib_gettext
from stoqlib.lib.message import error
from stoqlib.lib.parameters import (check_parameter_presence,
                                    ensure_system_parameters)

_ = stoqlib_gettext
log = Logger('stoqlib.database.migration')

def _extract_version(patch_filename):
    return int(patch_filename[:-4].split('-', 1)[1])

class SchemaMigration:
    """Schema migration management"""

    def _get_patches(self):
        patches = []
        for directory in environ.get_resource_paths('sql'):
            for patch in glob.glob(os.path.join(directory, 'patch-*.sql')):
                patches.append((patch, _extract_version(os.path.basename(patch))))
        return sorted(patches, key=operator.itemgetter(1))

    def _get_generation(self, conn, current_version):
        if current_version > 0:
            generation = SystemTable.select(connection=conn).max('generation')
        else:
            generation = 0

        return generation

    def _check_up_to_date(self, conn):
        # Fetch the latest, eg the last in the list
        patches = self._get_patches()
        unused, latest_available = patches[-1]

        current_version = self.get_current_version(conn)
        if current_version == latest_available:
            return True
        elif current_version > latest_available:
            raise DatabaseInconsistency(
                'The current version of database (%d) is greater than the '
                'latest available version (%d)'
                % (current_version, latest_available))

        return False

    def check_updated(self, conn):
        if not self._check_up_to_date(conn):
            return False

        if not check_parameter_presence(conn):
            return False

        return True

    def update_schema(self):
        """Check the current version of database and update the schema if
        it's needed
        """
        conn = get_connection()
        log.info("Updating schema")

        if self.check_updated(conn):
            log.info("Schema is already up to date")
            return

        patches = self._get_patches()
        current_version = self.get_current_version(conn)
        generation = self._get_generation(conn, current_version)

        initializing = current_version == 0

        for patch, patchlevel in patches:
            if patchlevel <= current_version:
                continue

            log.info('Applying: %s' % (patch,))

            temporary = tempfile.mktemp(prefix="patch-%d" % patchlevel)
            shutil.copy(patch, temporary)
            open(temporary, 'a').write(
                """INSERT INTO system_table (updated, patchlevel, generation) VALUES
                (NOW(), %s, %s)""" % (conn.sqlrepr(patchlevel),
                                      conn.sqlrepr(generation)))
            retcode = execute_sql(temporary)
            if retcode != 0:
                error('Failed to apply %s, psql returned error code: %d' % (
                    os.path.basename(patch), retcode))

            os.unlink(temporary)

        if not initializing:
            # checks if there is new applications and update all the user
            # profiles on the system
            trans = new_transaction()
            update_profile_applications(trans)
            trans.commit(close=True)

            # Updating the parameter list
            ensure_system_parameters(update=True)

        log.info("All patches applied")

        return current_version, patchlevel

    def get_current_version(self, conn):
        assert conn.tableExists('system_table')

        if conn.tableHasColumn('system_table', 'generation'):
            results = SystemTable.select(connection=conn)
            current_version = results.max('patchlevel')
        elif conn.tableHasColumn('asellable', 'code'):
            raise SystemExit(_("Unsupported database version, you need to reinstall"))
        else:
            current_version = 0

        return current_version

schema_migration = SchemaMigration()
