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

import logging
import os
import sys

from kiwi.component import provide_utility
from stoqlib.database.migration import StoqlibSchemaMigration
from stoqlib.database.debug import enable as enable_debugging
from stoqlib.database.runtime import (get_default_store,
                                      set_current_branch_station)
from stoqlib.exceptions import DatabaseError
from stoqlib.lib.configparser import register_config, StoqConfig
from stoqlib.lib.interfaces import IApplicationDescriptions
from stoqlib.lib.message import error
from stoqlib.lib.osutils import read_registry_key
from stoqlib.lib.translation import stoqlib_gettext as _

from stoq.lib.options import get_option_parser

log = logging.getLogger(__name__)


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

    if options and options.sqldebug:
        enable_debugging()

    from stoq.lib.applist import ApplicationDescriptions
    provide_utility(IApplicationDescriptions, ApplicationDescriptions(),
                    replace=True)

    if register_station:
        try:
            default_store = get_default_store()
        except DatabaseError as e:
            error(e.short, str(e.msg))

        config.get_settings().check_version(default_store)

        if check_schema:
            migration = StoqlibSchemaMigration()
            migration.check()

        if options and options.sqldebug:
            enable_debugging()

        set_current_branch_station(default_store, station_name=None)

    if load_plugins:
        from stoqlib.lib.pluginmanager import get_plugin_manager
        manager = get_plugin_manager()
        manager.activate_installed_plugins()

    if check_schema:
        default_store = get_default_store()
        if not default_store.table_exists('system_table'):
            error(
                _("Database schema error"),
                _("Table 'system_table' does not exist.\n"
                  "Consult your database administrator to solve this problem."))

        if check_schema:
            migration = StoqlibSchemaMigration()
            migration.check()
