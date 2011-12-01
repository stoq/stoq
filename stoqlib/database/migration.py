# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007-2011 Async Open Source <http://www.async.com.br>
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
"""Schema migration
"""

import glob
import os
import re
import shutil
import sys
import tempfile
import traceback

from kiwi.environ import environ
from kiwi.log import Logger

from stoqlib.database.database import (execute_sql, dump_database,
                                       restore_database, test_connection)
from stoqlib.database.runtime import new_transaction, get_connection
from stoqlib.domain.plugin import InstalledPlugin
from stoqlib.domain.profile import update_profile_applications
from stoqlib.domain.system import SystemTable
from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.lib.crashreport import collect_traceback
from stoqlib.lib.defaults import stoqlib_gettext
from stoqlib.lib.message import error, info
from stoqlib.lib.parameters import (check_parameter_presence,
                                    ensure_system_parameters)
from stoqlib.lib.pluginmanager import get_plugin_manager, PluginError

_ = stoqlib_gettext
log = Logger('stoqlib.database.migration')
# Used by the wizard
create_log = Logger('stoqlib.database.create')


class Patch(object):
    """A Database Patch

    @ivar filename: patch filename
    @ivar level: database level
    """
    def __init__(self, filename, migration):
        """
        Create a new Patch object.
        @param filename:
        @param migration
        """
        self.filename = filename

        # Base is the part of the filename minus the extension
        base = os.path.basename(filename).split('.')[0]

        # "patch-00-20" -> (00, 20): (generation, level)
        base_parts = base.split('-', 2)
        self.generation = int(base_parts[1])
        self.level = int(base_parts[2])
        self._migration = migration

    def __cmp__(self, other):
        return cmp(self.get_version(), other.get_version())

    def apply(self, conn):
        """Apply the patch
        @param conn: A database connection
        """

        temporary = tempfile.mktemp(prefix="patch-%d-%d-" % self.get_version())

        if self.filename.endswith('.sql'):
            shutil.copy(self.filename, temporary)
        elif self.filename.endswith('.py'):
            ns = {}
            execfile(self.filename, ns, ns)
            function = ns['apply_patch']
            trans = new_transaction()
            function(trans)
            trans.commit(close=True)
        else:
            raise AssertionError("Unknown filename: %s" % (self.filename, ))

        sql = self._migration.generate_sql_for_patch(self)
        open(temporary, 'a').write(sql)
        retcode = execute_sql(temporary)
        if retcode != 0:
            error('Failed to apply %s, psql returned error code: %d' % (
                os.path.basename(self.filename), retcode))

        os.unlink(temporary)

    def get_version(self):
        """Returns the patch version
        @returns: a tuple with the patch generation and level
        """
        return self.generation, self.level


class SchemaMigration(object):
    """Schema migration management

    Is currently doing the following things:
      - Applies database patches
      - Makes sure that all parameters are present
      - Makes sure that all applications are present
    """

    patch_resource = None
    patch_patterns = ["patch*.sql", "patch*.py"]

    def __init__(self):
        if self.patch_resource is None:
            raise ValueError(
                _("%s needs to have the patch_resource class variable set") % (
                self.__class__.__name__))
        if self.patch_patterns is None:
            raise ValueError(
                _("%s needs to have the patch_patterns class variable set") % (
                self.__class__.__name__))
        self.conn = get_connection()

    def _patchname_is_valid(self, filename):
        # simple checking of the patch naming convention
        valid_patterns = ["patch-\d\d-\d\d.sql", "patch-\d\d-\d\d.py"]
        for valid_pattern in valid_patterns:
            if re.match(valid_pattern, os.path.basename(filename)) is not None:
                return True
        return False

    def _get_patches(self):
        patches = []
        for directory in environ.get_resource_paths(self.patch_resource):
            for pattern in self.patch_patterns:
                for filename in glob.glob(os.path.join(directory, pattern)):
                    if self._patchname_is_valid(filename):
                        patches.append(Patch(filename, self))
                    else:
                        print "Invalid patch name: %s" % filename
        return sorted(patches)

    def _update_schema(self):
        """Check the current version of database and update the schema if
        it's needed
        """
        log.info("Updating schema")

        if self.check_uptodate():
            log.info("Schema is already up to date")
            return

        patches = self._get_patches()
        latest_available = patches[-1].get_version()
        current_version = self.get_current_version()

        last_level = None
        if current_version != latest_available:
            patches_to_apply = []
            for patch in patches:
                if patch.get_version() <= current_version:
                    continue
                patches_to_apply.append(patch)

            log.info("Applying %d patches" % (len(patches_to_apply), ))
            create_log.info("PATCHES:%d" % (len(patches_to_apply), ))

            for patch in patches_to_apply:
                create_log.info("PATCH:%d.%d" % (patch.generation,
                                                 patch.level))
                patch.apply(self.conn)

            assert patches_to_apply
            log.info("All patches (%s) applied." % (
                ''.join(str(p.level) for p in patches_to_apply)))
            last_level = patches_to_apply[-1]

        self.after_update()

        return current_version, last_level.get_version()

    # Public API

    def check_uptodate(self):
        """
        Verify if the schema is up to date.
        @returns: True or False.
        """
        # Fetch the latest, eg the last in the list
        patches = self._get_patches()
        latest_available = patches[-1].get_version()

        current_version = self.get_current_version()
        if current_version == latest_available:
            return True
        elif current_version > latest_available:
            current = "(%d.%d)" % current_version
            latest = "(%d.%d)" % latest_available
            raise DatabaseInconsistency(
                _('The current version of database %s is greater than the '
                  'latest available version %s') % (current, latest))

        return False

    def _log(self, msg):
        create_log.info(msg)

    def apply_all_patches(self):
        """Apply all available patches
        """
        log.info("Applying all patches")
        current_version = self.get_current_version()
        to_apply = []
        for patch in self._get_patches():
            if patch.get_version() > current_version:
                to_apply.append(patch)

        self._log("PATCHES:%d" % (len(to_apply), ))
        for i, patch in enumerate(to_apply):
            self._log("PATCH:%d" % (i, ))
            patch.apply(self.conn)
        self._log("PATCHES APPLIED")

    def update(self):
        """Updates the database schema
        """
        if self.check_uptodate():
            print 'Database is already at the latest version %d.%d' % (
                self.get_current_version())
        else:
            from_, to = self._update_schema()
            if to is None:
                print 'Database schema is already up to date'
            else:
                f = "(%d.%d)" % from_
                t = "(%d.%d)" % to
                print 'Database schema updated from %s to %s' % (f, t)

    def get_current_version(self):
        """This method is revision for returning the database schema version
        for a migration subclass

        This must be implemented in a subclass
        @returns: the current database patch version
        """
        raise NotImplementedError

    def generate_sql_for_patch(self, patch):
        """This method is responsible for creating an SQL
        statement which is used to update the migration versioning
        information

        This must be implemented in a subclass
        @param patch: the patch that was applied
        @returns: an SQL string
        """
        raise NotImplementedError

    def after_update(self):
        """This can be implemented in a subclass, but it is not mandatory.
        It'll be called after applying all patches
        """


class StoqlibSchemaMigration(SchemaMigration):
    """This is a SchemaMigration subclass used by Stoqlib.
    It's responsible for migrating the data for stoqlib itself
    and all its plugins
    """
    patch_resource = 'sql'

    def check_uptodate(self):
        retval = super(StoqlibSchemaMigration, self).check_uptodate()

        if not check_parameter_presence(self.conn):
            return False

        return retval

    def update(self, plugins=True, backup=True):
        log.info("Upgrading database (plugins=%r, backup=%r)" % (
            plugins, backup))

        sucess = test_connection()
        if not sucess:
            info(_(u'Could not connect to the database using command line '
                    'tool! Aborting.'))
            info(_(u'Please, check if you can connect to the database '
                    'using:'))
            info(_(u'psql -l -h <server> -p <port> -U <username>'))
            return

        if backup:
            temporary = tempfile.mktemp(prefix="stoq-dump-")
            log.info("Making a backup to %s" % (temporary, ))
            create_log.info("BACKUP-START:")
            success = dump_database(temporary)
            if not success:
                info(_(u'Could not create backup! Aborting.'))
                info(_(u'Please contact stoq team to inform this problem.\n'))
                return

        # We have to wrap a try/except statement inside a try/finally to
        # support python previous to 2.5 version.
        try:
            try:
                super(StoqlibSchemaMigration, self).update()
                if plugins:
                    self.update_plugins()
            except Exception:
                exc = sys.exc_info()
                tb_str = ''.join(traceback.format_exception(*exc))
                collect_traceback(exc, submit=True)
                create_log.info("ERROR:%s" % (tb_str, ))

                if backup:
                    log.info("Restoring backup %s" % (temporary, ))
                    create_log.info("RESTORE-START:")
                    new_name = restore_database(temporary)
                    create_log.info("RESTORE-DONE:%s" % (new_name, ))
                return False
        finally:
            if backup is True:
                os.unlink(temporary)
        log.info("Migration done")
        return True

    def update_plugins(self):
        manager = get_plugin_manager()
        for plugin_name in manager.installed_plugins_names:
            plugin = manager.get_plugin(plugin_name)
            migration = plugin.get_migration()
            if migration:
                migration.update()

    def check_plugins(self):
        # This cannot be done in check_uptodate since the plugin domain
        # classes were introduced as a patch and the way the callsites
        # works in stoq/lib/startup.py
        manager = get_plugin_manager()
        for plugin_name in manager.installed_plugins_names:
            try:
                plugin = manager.get_plugin(plugin_name)
            except PluginError:
                # tef is installed on the livecd, but we remove it when
                # instaling to HDD. This workaround will ignore if the plugin is
                # enabled but not installed. Figure out how to handle this
                # properly.
                if plugin_name == 'tef':
                    continue
                raise
            migration = plugin.get_migration()
            if not migration:
                continue
            if not migration.check_uptodate():
                return False
        return True

    def get_current_version(self):
        assert self.conn.tableExists('system_table')

        if self.conn.tableHasColumn('system_table', 'generation'):
            results = SystemTable.select(connection=self.conn)
            current_generation = results.max('generation')
            results = SystemTable.selectBy(generation=current_generation,
                                           connection=self.conn)
            current_patchlevel = results.max('patchlevel')
        elif self.conn.tableHasColumn('asellable', 'code'):
            raise SystemExit(
                _("Unsupported database version, you need to reinstall"))
        else:
            current_generation, current_patchlevel = 0

        return current_generation, current_patchlevel

    def after_update(self):
        # checks if there is new applications and update all the user
        # profiles on the system
        trans = new_transaction()
        update_profile_applications(trans)
        trans.commit(close=True)

        # Updating the parameter list
        ensure_system_parameters(update=True)

    def generate_sql_for_patch(self, patch):
        return ("INSERT INTO system_table (updated, patchlevel, generation)"
                "VALUES (NOW(), %s, %s)" % (
            self.conn.sqlrepr(patch.level),
            self.conn.sqlrepr(patch.generation)))


class PluginSchemaMigration(SchemaMigration):
    """This is a SchemaMigration class which is suitable for use within
    a plugin
    """
    def __init__(self, plugin_name, resource, patterns):
        """
        Create a new PluginSchemaMigration object.
        @param plugin_name: name of the plugin
        @param resource: resource to load sql patches from
        @param patterns: sql patch pattern
        """
        self.plugin_name = plugin_name
        self.patch_resource = resource
        self.patch_patterns = patterns
        SchemaMigration.__init__(self)

        self._plugin = InstalledPlugin.selectOneBy(
            plugin_name=self.plugin_name,
            connection=self.conn)

    def _log(self, msg):
        create_log.info('PLUGIN ' + msg)

    def generate_sql_for_patch(self, patch):
        assert self._plugin
        return ("UPDATE installed_plugin "
                "SET plugin_version = %s "
                "WHERE id = %s") % (self.conn.sqlrepr(patch.level),
                                    self.conn.sqlrepr(self._plugin.id))

    def get_current_version(self):
        if self._plugin:
            return (0, self._plugin.plugin_version)
        return (0, 0)
