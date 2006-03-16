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
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##              Johan Dahlin                <jdahlin@async.com.br>
##
##
""" Stoq startup routines"""


import sys
import optparse
import gettext

from stoqlib.database import check_database_connection

from stoq.lib.applist import get_application_names
from stoq.lib.configparser import (StoqConfigParser, register_config,
                                   get_config)

_ = gettext.gettext


def get_parser():
    parser = optparse.OptionParser()
    parser.add_option('-a', '--address',
                      action="store",
                      dest="address",
                      help='Database address to connect to')
    parser.add_option('-p', '--port',
                      action="store",
                      dest="port",
                      help='Database port')
    parser.add_option('-d', '--dbname',
                      action="store",
                      dest="dbname",
                      help='Database name to use')
    parser.add_option('-u', '--username',
                      action="store",
                      dest="username",
                      help='Database username')
    parser.add_option('-w', '--password',
                      action="store",
                      dest="password",
                      help='user password')
    parser.add_option('-c', '--clean',
                      action="store_true",
                      dest="clean",
                      help='Clean database before running')
    return parser


def _run_app(options, config, appname):
    from stoq.lib.stoqconfig import AppConfig

    appconf = AppConfig()
    appname = appconf.setup_app(appname, splash=True)
    module = __import__("stoq.gui.%s.app" % appname, globals(), locals(), [''])
    if not hasattr(module, "main"):
        raise RuntimeError(
            "Application %s must have a app.main() function")

    module.main(appconf)
    import gtk
    gtk.main()
    appconf.log("Shutting down application")


#
# Public routines
#


def setup_stoqlib_settings(apps=None, config=None):
    """A useful function that can be called on the system startup and also
    when running tests.
    """
    from stoqlib.database import register_db_settings, DatabaseSettings
    from stoqlib.lib.runtime import register_application_names
    config = config or get_config()
    if not config:
        raise ValueError("You should have a valid config instance "
                         "defined at this point")
    db_settings = DatabaseSettings(config.get_rdbms_name(),
                                   config.get_address(),
                                   config.get_port(),
                                   config.get_dbname(),
                                   config.get_username(),
                                   config.get_password())
    register_db_settings(db_settings)
    apps = apps or get_application_names()
    register_application_names(apps)


def setup_environment(options=None, verbose=False, force_init_db=False,
                      test_mode=False):
    config = StoqConfigParser(test_mode)
    has_been_installed = config.has_installed_config_data()
    if has_been_installed:
        try:
            config.load_config()
            config.raise_invalid_rdbms_settings()
        except:
            type, value, trace = sys.exc_info()
            msg = _("Invalid config file settings, got error '%s', "
                    "of type '%s'" % (value, type))
            from kiwi.ui.dialogs import error
            error(_('Could not open database config file'), long=msg)
            raise SystemExit("Error: bad config file")

        if options:
            force_init_db = force_init_db or options.clean
            if options.address:
                config.set_hostname(options.address)
            if options.port:
                config.set_port(options.port)
            if options.dbname:
                config.set_database(options.dbname)
            if options.username:
                config.set_username(options.username)
            if options.password:
                config.set_password(options.password)
    else:
        from stoqlib.gui.base.dialogs import run_dialog
        from stoq.gui.config import FirstTimeConfigWizard
        model = run_dialog(FirstTimeConfigWizard, None)
        if not model:
            raise SystemExit("No configuration data provided")
        config.install_default(model.db_settings)
        config.load_config()
    register_config(config)

    setup_stoqlib_settings(config=config)
    if has_been_installed:
        conn_uri = config.get_connection_uri()
        conn_ok, error_msg = check_database_connection(conn_uri)
        if not conn_ok:
            from kiwi.ui.dialogs import error
            error(_('Could not connect to database'), long=error_msg)
            raise SystemExit("Error: bad connection settings provided")

    if not has_been_installed or force_init_db:
        if force_init_db:
            password = ""
        else:
            password = model.stoq_user_data.password
        from stoqlib.lib.admin import initialize_system
        initialize_system(password=password, verbose=verbose)

    from stoqlib.lib.migration import schema_migration
    schema_migration.update_schema()

    if has_been_installed:
        from stoqlib.lib.parameters import ensure_system_parameters
        ensure_system_parameters()
    else:
        from stoqlib.lib.drivers import \
                            create_virtual_printer_for_current_host
        create_virtual_printer_for_current_host()


def main(args):
    parser = get_parser()
    options, args = parser.parse_args(args)

    apps = get_application_names()
    if len(args) < 2:
        appname = None
    else:
        appname = args[1].strip()
        if appname.endswith('/'):
            appname = appname[:-1]

        if not appname in apps:
            raise SystemExit("'%s' is not an application. "
                                 "Valid applications are: %s" % (appname, apps))

    setup_environment(options)
    _run_app(options, get_config(), appname)
