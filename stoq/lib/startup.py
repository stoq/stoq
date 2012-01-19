# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source <http://www.async.com.br>
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
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
""" Database startup routines"""

import gettext
import os
import socket
import sys

from kiwi.component import provide_utility
from kiwi.log import Logger
from stoqlib.database.admin import ensure_admin_user, initialize_system
from stoqlib.database.database import check_version
from stoqlib.database.migration import StoqlibSchemaMigration
from stoqlib.database.orm import orm_enable_debugging, orm_startup
from stoqlib.database.runtime import (get_connection,
                                      set_current_branch_station,
                                      new_transaction)
from stoqlib.domain.profile import UserProfile
from stoqlib.domain.profile import ProfileSettings
from stoqlib.exceptions import (DatabaseError, StoqlibError,
                                DatabaseInconsistency)
from stoqlib.lib.configparser import register_config, StoqConfig
from stoqlib.lib.crashreport import collect_traceback
from stoqlib.lib.interfaces import  IApplicationDescriptions
from stoqlib.lib.message import error
from stoqlib.lib.osutils import read_registry_key

from stoq.lib.options import get_option_parser

_ = gettext.gettext
log = Logger('startup')


def _check_tables():
    # Check so SystemTable is present
    conn = get_connection()
    if not conn.tableExists('system_table'):
        error(
            _("Database schema error"),
            _("Table 'system_table' does not exist.\n"
              "Consult your database administrator to solve this problem."))


def setup_path():
    import platform
    if platform.system() != 'Windows':
        return

    paths = []

    # PostgreSQL, we're only working with 8.4 for now
    key = r'Software\PostgreSQL\Installations\postgresql-8.4'
    base_dir = read_registry_key('HKLM', key, 'Base Directory')
    if base_dir is not None:
        paths.append(os.path.join(base_dir, 'bin'))

    # Stoq, for stoqdbadmin and restarting Stoq itself
    key = r'Software\Stoq'
    stoq_dir = read_registry_key('HKCC', r'Software\Stoq', 'Path')
    if stoq_dir is not None:
        paths.append(stoq_dir)

    for path in paths:
        if path not in os.environ['PATH']:
            os.environ['PATH'] += ';' + path


def setup(config=None, options=None, register_station=True, check_schema=True,
          load_plugins=True):
    """
    Loads the configuration from arguments and configuration file.

    @param config: a StoqConfig instance
    @param options: a Optionparser instance
    @param register_station: if we should register the branch station.
    @param check_schema: if we should check the schema
    @param load_plugins: if we should load plugins for the system
    """

    # NOTE: No GUI calls are allowed in here
    #       If you change anything here, you need to verify that all
    #       callsites are still working properly.
    #       bin/stoq
    #       bin/stoqdbadmin
    #       python stoq/tests/runtest.py

    if options is None:
        parser = get_option_parser()
        options, args = parser.parse_args(sys.argv)

    if options.verbose:
        from kiwi.log import set_log_level
        set_log_level('stoq*', 0)

    setup_path()

    if config is None:
        config = StoqConfig()
        if options.filename:
            config.load(options.filename)
        else:
            config.load_default()
    config.set_from_options(options)

    register_config(config)

    from stoq.lib.applist import ApplicationDescriptions
    provide_utility(IApplicationDescriptions, ApplicationDescriptions())

    if register_station:
        try:
            conn = get_connection()
        except DatabaseError, e:
            error(e.short, str(e.msg))

        check_version(conn)
        orm_startup()
        # For LTSP systems we cannot use the hostname as stoq is run
        # on a shared serve system. Instead the ip of the client system
        # is available in the LTSP_CLIENT environment variable
        station_name = os.environ.get('LTSP_CLIENT_HOSTNAME', None)
        if station_name is None:
            station_name = socket.gethostname()
        set_current_branch_station(conn, station_name)

    if load_plugins:
        from stoqlib.lib.pluginmanager import get_plugin_manager
        manager = get_plugin_manager()
        manager.activate_installed_plugins()

    if check_schema:
        _check_tables()

        migration = StoqlibSchemaMigration()
        if (not migration.check_uptodate() or
            (load_plugins and not migration.check_plugins())):
            error(_("Database schema error"),
                  _("The database schema has changed, but the database has "
                    "not been updated. Run 'stoqdbadmin updateschema` to "
                    "update the schema  to the latest available version."))

        orm_startup()

    if options:
        if options.debug:
            from gtk import keysyms
            from stoqlib.gui.keyboardhandler import install_global_keyhandler
            from stoqlib.gui.introspection import introspect_slaves
            install_global_keyhandler(keysyms.F12, introspect_slaves)

        if options.sqldebug:
            orm_enable_debugging()

    from stoqlib.gui.keybindings import load_user_keybindings
    load_user_keybindings()


def needs_schema_update():
    try:
        migration = StoqlibSchemaMigration()
    except StoqlibError:
        error(_("Update Error"),
             _("You need to call setup() before checking the database "
               "schema."))

    try:
        update = not (migration.check_uptodate() and migration.check_plugins())
    except DatabaseInconsistency, e:
        error(str(e))
    return update


def clean_database(config, options=None):
    """Clean the database
    @param config: a StoqConfig instance
    @param options: a Optionparser instance
    """
    if not options:
        password = ''
    else:
        password = options.password

    try:
        password = password or config.get_password()
        initialize_system()
        set_default_profile_settings()
        ensure_admin_user(password)
    except Exception:
        collect_traceback(sys.exc_info(), submit=True)


def set_default_profile_settings():
    trans = new_transaction()
    profile = UserProfile.selectOneBy(name=_('Salesperson'), connection=trans)
    # Not sure what is happening. If it doesnt exist, check if it was not
    # created in english. workaround for crash report 207 (bug 4587)
    if not profile:
        profile = UserProfile.selectOneBy(name='Salesperson', connection=trans)
    assert profile
    ProfileSettings.set_permission(trans, profile, 'pos', True)
    ProfileSettings.set_permission(trans, profile, 'sales', True)
    ProfileSettings.set_permission(trans, profile, 'till', True)
    trans.commit(close=True)
