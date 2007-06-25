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
"""
Schema migration
"""

import glob
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


class Patch(object):
    """
    A Database Patch

    @ivar filename: patch filename
    @ivar level: database level
    @ivar generation: generation
    """
    def __init__(self, filename):
        """
        @param filename:
        """
        self.filename = filename
        self.level = int(os.path.basename(filename)[:-4].split('-', 1)[1])
        self.generation = 0

    def __cmp__(self, other):
        return cmp(self.level, other.level)

    def apply(self, conn):
        """
        Apply the patch
        @param conn: A database connection
        """
        log.info('Applying: %s' % (self.filename,))

        temporary = tempfile.mktemp(prefix="patch-%d-" % self.level)
        shutil.copy(self.filename, temporary)
        open(temporary, 'a').write(
            """INSERT INTO system_table (updated, patchlevel, generation) VALUES
            (NOW(), %s, %s)""" % (conn.sqlrepr(self.level),
                                  conn.sqlrepr(self.generation)))
        retcode = execute_sql(temporary)
        if retcode != 0:
            error('Failed to apply %s, psql returned error code: %d' % (
                os.path.basename(self.filename), retcode))

        os.unlink(temporary)


class SchemaMigration(object):
    """
    Schema migration management

    Is currently doing the following things:
      - Applies database patches
      - Makes sure that all parameters are present
      - Makes sure that all applications are present
    """

    def __init__(self):
        self.conn = get_connection()

    def _get_patches(self):
        patches = []
        for directory in environ.get_resource_paths('sql'):
            for filename in glob.glob(os.path.join(directory, 'patch-*.sql')):
                patches.append(Patch(filename))
        return sorted(patches)

    def _update_schema(self):
        """
        Check the current version of database and update the schema if
        it's needed
        """
        log.info("Updating schema")

        if self.check_uptodate():
            log.info("Schema is already up to date")
            return

        patches = self._get_patches()
        latest_available = patches[-1].level
        current_version = self._get_current_version()

        last_level = None
        if current_version != latest_available:
            applied = []
            for patch in patches:
                if patch.level <= current_version:
                    continue
                patch.apply(self.conn)
                applied.append(patch.level)

            assert applied
            log.info("All patches (%s) applied." % (
                ''.join(str(p) for p in applied)))
            last_level = applied[-1]

        # checks if there is new applications and update all the user
        # profiles on the system
        trans = new_transaction()
        update_profile_applications(trans)
        trans.commit(close=True)

        # Updating the parameter list
        ensure_system_parameters(update=True)

        return current_version, last_level

    def _get_current_version(self):
        assert self.conn.tableExists('system_table')

        if self.conn.tableHasColumn('system_table', 'generation'):
            results = SystemTable.select(connection=self.conn)
            current_version = results.max('patchlevel')
        elif self.conn.tableHasColumn('asellable', 'code'):
            raise SystemExit(
                _("Unsupported database version, you need to reinstall"))
        else:
            current_version = 0

        return current_version

    # Public API

    def check_uptodate(self):
        """
        @returns: True if the schema is up to date, otherwise false
        """
        # Fetch the latest, eg the last in the list
        patches = self._get_patches()
        latest_available = patches[-1].level

        current_version = self._get_current_version()
        if current_version == latest_available:
            return True
        elif current_version > latest_available:
            raise DatabaseInconsistency(
                'The current version of database (%d) is greater than the '
                'latest available version (%d)'
                % (current_version, latest_available))

        if not check_parameter_presence(self.conn):
            return False

        return False

    def apply_all_patches(self):
        """
        Apply all available patches
        """
        log.info("Applying all patches")
        for patch in self._get_patches():
            patch.apply(self.conn)

    def update(self):
        """
        Updates the database schema
        """
        if self.check_uptodate():
            print 'Database is already at revision %d' % (
                self._get_current_version())
        else:
            from_, to = self._update_schema()
            if to is None:
                print 'Database schema updated'
            else:
                print 'Database schema updated from %d to %d' % (from_, to)

