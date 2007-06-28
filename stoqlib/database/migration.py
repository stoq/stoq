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
from kiwi.component import get_utility
from kiwi.log import Logger

from stoqlib.database.database import execute_sql
from stoqlib.database.runtime import new_transaction, get_connection
from stoqlib.domain.plugin import InstalledPlugin
from stoqlib.domain.profile import update_profile_applications
from stoqlib.domain.system import SystemTable
from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.lib.defaults import stoqlib_gettext
from stoqlib.lib.interfaces import IPluginManager
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
    """
    def __init__(self, filename, migration):
        """
        @param filename:
        @param migration
        """
        self.filename = filename
        self.level = int(os.path.basename(filename)[:-4].split('-', 1)[1])
        self._migration = migration

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
        sql = self._migration.generate_sql_for_patch(self.level)
        open(temporary, 'a').write(sql)
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

    patch_resource = None
    patch_pattern = None

    def __init__(self):
        if self.patch_resource is None:
            raise ValueError(
                "%s needs to have the patch_resource class variable set" % (
                self.__class__.__name__))
        if self.patch_pattern is None:
            raise ValueError(
                "%s needs to have the patch_pattern class variable set" % (
                self.__class__.__name__))
        self.conn = get_connection()

    def _get_patches(self):
        patches = []
        for directory in environ.get_resource_paths(self.patch_resource):
            for filename in glob.glob(os.path.join(directory,
                                                   self.patch_pattern)):
                patches.append(Patch(filename, self))
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
        current_version = self.get_current_version()

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

        self.after_update()

        return current_version, last_level

    # Public API

    def check_uptodate(self):
        """
        @returns: True if the schema is up to date, otherwise false
        """
        # Fetch the latest, eg the last in the list
        patches = self._get_patches()
        latest_available = patches[-1].level

        current_version = self.get_current_version()
        if current_version == latest_available:
            return True
        elif current_version > latest_available:
            raise DatabaseInconsistency(
                'The current version of database (%d) is greater than the '
                'latest available version (%d)'
                % (current_version, latest_available))

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
                self.get_current_version())
        else:
            from_, to = self._update_schema()
            if to is None:
                print 'Database schema updated'
            else:
                print 'Database schema updated from %d to %d' % (from_, to)


    def get_current_version(self):
        """
        This method is revision for returning the database schema version
        for a migration subclass

        This must be implemented in a subclass
        @returns: the current database patch version
        """
        raise NotImplementedError

    def generate_sql_for_patch(self, level):
        """
        This method is responsible for creating an SQL
        statement which is used to update the migration versioning
        information

        This must be implemented in a subclass
        @param level: database level to upgrade to
        @returns: an SQL string
        """
        raise NotImplementedError

    def after_update(self):
        """
        This can be implemented in a subclass, but it is not mandatory.
        It'll be called after applying all patches
        """


class StoqlibSchemaMigration(SchemaMigration):
    """
    This is a SchemaMigration subclass used by Stoqlib.
    It's responsible for migrating the data for stoqlib itself
    and all its plugins
    """
    patch_resource = 'sql'
    patch_pattern = 'patch-*.sql'

    def check_uptodate(self):
        retval = super(StoqlibSchemaMigration, self).check_uptodate()

        if not check_parameter_presence(self.conn):
            return False

        return retval

    def update(self, plugins=True):
        super(StoqlibSchemaMigration, self).update()

        if plugins:
            self.update_plugins()

    def update_plugins(self):
        for plugin in get_utility(IPluginManager).get_active_plugins():
            migration = plugin.get_migration()
            migration.update()

    def check_plugins(self):
        # This cannot be done in check_uptodate since the plugin domain
        # classes were introduced as a patch and the way the callsites
        # works in stoq/lib/startup.py
        for plugin in get_utility(IPluginManager).get_active_plugins():
            migration = plugin.get_migration()
            if not migration.check_uptodate():
                return False
        return True

    def get_current_version(self):
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

    def after_update(self):
        # checks if there is new applications and update all the user
        # profiles on the system
        trans = new_transaction()
        update_profile_applications(trans)
        trans.commit(close=True)

        # Updating the parameter list
        ensure_system_parameters(update=True)

    def generate_sql_for_patch(self, level):
        return ("INSERT INTO system_table (updated, patchlevel, generation)"
                "VALUES (NOW(), %s, %s)" % (
            self.conn.sqlrepr(level),
            self.conn.sqlrepr(0)))


class PluginSchemaMigration(SchemaMigration):
    """
    This is a SchemaMigration class which is suitable for use within
    a plugin
    """
    def __init__(self, plugin_name, resource, pattern):
        """
        @param plugin_name: name of the plugin
        @param resource: resource to load sql patches from
        @param pattern: sql patch pattern
        """
        self.plugin_name = plugin_name
        self.patch_resource = resource
        self.patch_pattern = pattern
        SchemaMigration.__init__(self)

        self._plugin = InstalledPlugin.selectOneBy(
            plugin_name=self.plugin_name,
            connection=self.conn)

    def generate_sql_for_patch(self, level):
        assert self._plugin
        return ("UPDATE installed_plugin "
                "SET plugin_version = %s"
                "WHERE id = %s") % (self.conn.sqlrepr(level),
                                    self.conn.sqlrepr(self._plugin.id))

    def get_current_version(self):
        if self._plugin:
            return self._plugin.plugin_version
        return 0
