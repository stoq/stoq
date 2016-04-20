# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007-2012 Async Open Source <http://www.async.com.br>
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

import fnmatch
import logging
import os
import re
import shutil
import sys
import tempfile
import traceback

from kiwi.environ import environ

from stoqlib.api import api
from stoqlib.database.runtime import (get_default_store,
                                      new_store)
from stoqlib.database.settings import db_settings, check_extensions
from stoqlib.domain.plugin import InstalledPlugin
from stoqlib.domain.profile import update_profile_applications
from stoqlib.exceptions import (DatabaseInconsistency, StoqlibError,
                                DatabaseError)
from stoqlib.lib.crashreport import collect_traceback
from stoqlib.lib.defaults import stoqlib_gettext
from stoqlib.lib.message import error, info
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.pluginmanager import get_plugin_manager

_ = stoqlib_gettext
log = logging.getLogger(__name__)
# Used by the wizard
create_log = logging.getLogger('stoqlib.database.create')


class Patch(object):
    """A Database Patch

    :attribute filename: patch filename
    :attribute level: database level
    """

    def __init__(self, filename, migration):
        """
        Create a new Patch object.
        :param filename:
        :param migration
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

    def apply(self, store):
        """Apply the patch
        :param store: a store
        """

        # Dont lock the database here, since StoqlibSchemaMigration.update has
        # already did that before starting to apply the patches

        # SQL statement to update the system_table
        sql = self._migration.generate_sql_for_patch(self)

        if self.filename.endswith('.sql'):
            # Create a temporary file used for writing SQL statements
            temporary = tempfile.mktemp(prefix="patch-%d-%d-" % self.get_version())

            # Overwrite the temporary file with the sql patch we want to apply
            shutil.copy(self.filename, temporary)

            # After successfully executing the SQL statements, we need to
            # make sure that the system_table is updated with the correct
            # schema generation and patchlevel
            open(temporary, 'a').write(sql)

            retcode = db_settings.execute_sql(temporary)
            if retcode != 0:
                error('Failed to apply %s, psql returned error code: %d' % (
                    os.path.basename(self.filename), retcode))

            os.unlink(temporary)
        elif self.filename.endswith('.py'):
            # Execute the patch, we cannot use __import__() since there are
            # hyphens in the filename and data/sql lacks an __init__.py
            ns = {}
            execfile(self.filename, ns, ns)
            function = ns['apply_patch']

            # Create a new store that will be used to apply the patch and
            # to update the system tables after the patch has been successfully
            # applied
            patch_store = new_store()

            # Apply the patch itself
            function(patch_store)

            # After applying the patch, update the system_table within the same
            # transaction
            patch_store.execute(sql)
            patch_store.commit(close=True)
        else:
            raise AssertionError("Unknown filename: %s" % (self.filename, ))

    def get_version(self):
        """Returns the patch version
        :returns: a tuple with the patch generation and level
        """
        return self.generation, self.level


class SchemaMigration(object):
    """Schema migration management

    Is currently doing the following things:
      - Applies database patches
      - Makes sure that all parameters are present
      - Makes sure that all applications are present
    """

    patch_resource_domain = None
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
        self.default_store = get_default_store()

        try:
            check_extensions(store=self.default_store)
        except ValueError:
            error("Missing PostgreSQL extension on the server, "
                  "please install postgresql-contrib")

    def _patchname_is_valid(self, filename):
        # simple checking of the patch naming convention
        valid_patterns = [r"patch-\d\d-\d\d.sql",
                          r"patch-\d\d-\d\d.py"]
        for valid_pattern in valid_patterns:
            if re.match(valid_pattern, filename) is not None:
                return True
        return False

    def _get_patches(self):
        patches = []
        for filename in environ.get_resource_names(self.patch_resource_domain,
                                                   self.patch_resource):
            for pattern in self.patch_patterns:
                if not fnmatch.fnmatch(filename, pattern):
                    continue
                if not self._patchname_is_valid(filename):
                    print("Invalid patch name: %s" % filename)
                    continue
                filename = environ.get_resource_filename(
                    self.patch_resource_domain, self.patch_resource, filename)
                patches.append(Patch(filename, self))

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

            from stoqlib.database.admin import create_database_functions
            create_database_functions()

            log.info("Applying %d patches" % (len(patches_to_apply), ))
            create_log.info("PATCHES:%d" % (len(patches_to_apply), ))

            for patch in patches_to_apply:
                create_log.info("PATCH:%d.%d" % (patch.generation,
                                                 patch.level))
                patch.apply(self.default_store)

            assert patches_to_apply
            log.info("All patches (%s) applied." % (
                ', '.join(str(p.level) for p in patches_to_apply)))
            last_level = patches_to_apply[-1].get_version()

        self.after_update()

        return current_version, last_level

    # Public API

    def check(self, check_plugins=True):
        if self.check_uptodate():
            return True

        if not check_plugins:
            return True

        if self.check_plugins():
            return True

        error(_("Database schema error"),
              _("The database schema has changed, but the database has "
                "not been updated. Run 'stoqdbadmin updateschema` to "
                "update the schema  to the latest available version."))
        return False

    def check_uptodate(self):
        """
        Verify if the schema is up to date.
        :returns: True or False.
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
                  'latest available version %s. Try upgrading your '
                  'installation.') % (current, latest))

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
            patch.apply(self.default_store)

        self._log("PATCHES APPLIED")

    def update(self):
        """Updates the database schema
        """
        if self.check_uptodate():
            print('Database is already at the latest version %d.%d' % (
                self.get_current_version()))
        else:
            from_, to = self._update_schema()
            if to is None:
                print('Database schema is already up to date')
            else:
                f = "(%d.%d)" % from_
                t = "(%d.%d)" % to
                print('Database schema updated from %s to %s' % (f, t))

    def get_current_version(self):
        """This method is revision for returning the database schema version
        for a migration subclass

        This must be implemented in a subclass
        :returns: the current database patch version
        """
        raise NotImplementedError

    def generate_sql_for_patch(self, patch):
        """This method is responsible for creating an SQL
        statement which is used to update the migration versioning
        information

        This must be implemented in a subclass
        :param patch: the patch that was applied
        :returns: an SQL string
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
    patch_resource_domain = 'stoq'
    patch_resource = 'sql'

    def __init__(self):
        super(StoqlibSchemaMigration, self).__init__()
        self._backup = None

    def _check_database(self):
        try:
            log.info("Locking database")
            self.default_store.lock_database()
        except DatabaseError:
            msg = _('Could not lock database. This means there are other clients '
                    'connected. Make sure to close every Stoq client '
                    'before updating the database')
            error(msg)

        # Database migration is actually run in subprocesses, We need to unlock
        # the tables again and let the upgrade continue
        log.info("Releasing database lock")
        self.default_store.unlock_database()

        sucess = db_settings.test_connection()
        if not sucess:
            # FIXME: Improve this message after 1.5 is released
            msg = _(u'Could not connect to the database using command line '
                    'tool! Aborting.') + ' '
            msg += _(u'Please, check if you can connect to the database '
                     'using:') + ' '
            msg += _(u'psql -l -h <server> -p <port> -U <username>')
            error(msg)
            return

        return True

    def _backup_database(self):
        temporary = tempfile.mktemp(prefix="stoq-dump-")
        log.info("Making a backup to %s" % (temporary, ))
        create_log.info("BACKUP-START:")
        success = db_settings.dump_database(temporary)
        if not success:
            info(_(u'Could not create backup! Aborting.'))
            info(_(u'Please contact stoq team to inform this problem.\n'))
            return

        self._backup = temporary
        return True

    def _restore_backup(self):
        if not self._backup:
            return

        log.info("Restoring backup %s" % (self._backup, ))
        create_log.info("RESTORE-START:")
        new_name = db_settings.restore_database(self._backup)
        create_log.info("RESTORE-DONE:%s" % (new_name, ))

    def _remove_backup(self):
        if not self._backup:
            return

        os.unlink(self._backup)

    @api.async
    def update_async(self, plugins=True, backup=True):
        log.info("Upgrading database (plugins=%r, backup=%r)" % (
            plugins, backup))

        if not self._check_database():
            api.asyncReturn(False)

        if backup:
            self._backup_database()

        # Don't try to update the plugins if the database doesn't
        # have the plugin_egg table, which was included in patch-05-15
        if self.get_current_version() >= (5, 15):
            manager = get_plugin_manager()
            for egg_plugin in manager.egg_plugins_names:
                try:
                    yield manager.download_plugin(egg_plugin)
                except Exception:
                    pass

        api.asyncReturn(
            self.update(plugins=plugins, backup=False, check_database=False))

    def update(self, plugins=True, backup=True, check_database=True):
        log.info("Upgrading database (plugins=%r, backup=%r)" % (
            plugins, backup))

        if check_database and not self._check_database():
            return False

        if backup:
            self._backup_database()

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
                self._restore_backup()
                return False
        finally:
            self._remove_backup()

        log.info("Migration done")
        return True

    def _get_plugins(self):
        manager = get_plugin_manager()
        for plugin_name in manager.installed_plugins_names:
            if plugin_name in manager.available_plugins_names:
                yield manager.get_plugin(plugin_name)

    def update_plugins(self):
        for plugin in self._get_plugins():
            migration = plugin.get_migration()
            if migration:
                migration.update()

    def check_plugins(self):
        # This cannot be done in check_uptodate since the plugin domain
        # classes were introduced as a patch and the way the callsites
        # works in stoq/lib/startup.py
        for plugin in self._get_plugins():
            migration = plugin.get_migration()
            if not migration:
                continue
            if not migration.check_uptodate():
                return False
        return True

    def get_current_version(self):
        result = self.default_store.execute(
            """SELECT generation, patchlevel
                 FROM system_table
             ORDER BY updated DESC
                LIMIT 1;""")
        value = result.get_one()
        result.close()
        return value

    def after_update(self):
        # checks if there is new applications and update all the user
        # profiles on the system
        store = new_store()
        update_profile_applications(store)

        # Updating the parameter list
        sysparam.ensure_system_parameters(store, update=True)
        store.commit(close=True)

    def generate_sql_for_patch(self, patch):
        return self.default_store.quote_query(
            "INSERT INTO system_table (updated, patchlevel, generation)"
            "VALUES (NOW(), %s, %s);", (patch.level,
                                        patch.generation))


class PluginSchemaMigration(SchemaMigration):
    """This is a SchemaMigration class which is suitable for use within
    a plugin
    """

    def __init__(self, plugin_name, resource_domain, resource, patterns):
        """
        Create a new PluginSchemaMigration object.
        :param plugin_name: name of the plugin
        :param resource: resource to load sql patches from
        :param patterns: sql patch pattern
        """
        self.plugin_name = plugin_name
        self.patch_resource_domain = resource_domain
        self.patch_resource = resource
        self.patch_patterns = patterns
        SchemaMigration.__init__(self)

        self._plugin = self.default_store.find(
            InstalledPlugin, plugin_name=self.plugin_name).one()

    def _log(self, msg):
        create_log.info('PLUGIN ' + msg)

    def generate_sql_for_patch(self, patch):
        assert self._plugin
        return self.default_store.quote_query(
            "UPDATE installed_plugin "
            "SET plugin_version = %s "
            "WHERE id = %s;",
            (patch.level, self._plugin.id))

    def get_current_version(self):
        if self._plugin:
            return (0, self._plugin.plugin_version)
        return (0, 0)


def needs_schema_update():
    try:
        migration = StoqlibSchemaMigration()
    except StoqlibError:
        error(_("Update Error"),
              _("You need to call setup() before checking the database "
                "schema."))

    try:
        update = not (migration.check_uptodate() and migration.check_plugins())
    except DatabaseInconsistency as e:
        error(str(e))

    # If we need to update the database, we need to close the connection,
    # otherwise the locking of the database will fail, since this connection has
    # already queried a few tables
    if update:
        migration.default_store.commit()
    return update
