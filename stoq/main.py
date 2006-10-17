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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##              Johan Dahlin                <jdahlin@async.com.br>
##
##
""" Stoq startup routines"""


import gettext
import optparse
import os
import sys

from kiwi.component import provide_utility
from kiwi.log import Logger, set_log_file
from stoqlib.database.database import db_table_name
from stoqlib.database.exceptions import PostgreSQLError
from stoqlib.exceptions import StoqlibError
from stoqlib.lib.message import error

from stoq.lib.applist import get_application_names
from stoq.lib.configparser import StoqConfig
from stoq.lib.startup import setup, get_option_parser

_ = gettext.gettext
log = Logger('stoq.main')

def _check_dependencies():
    log.debug('checking dependencies')
    try:
        import reportlab
    except ImportError:
        raise SystemExit("Reportlab 1.20 is required but could not be found.")

    if map(int, reportlab.Version.split('.')) < [1, 20]:
        raise SystemExit("Reportlab 1.20 is required but %s found" %
                         reportlab.Version)
    log.debug('reportlab okay')

    try:
        import gazpacho
    except ImportError:
        raise SystemExit(
           "Gazpacho 0.6.6 or higher is required but could not be found.")

    if map(int, gazpacho.__version__.split('.')) < [0, 6, 6]:
        raise SystemExit("Gazpacho 0.6.6 is required but %s found" %
                         gazpacho.__version__)
    log.debug('gazpacho okay')

def _run_first_time_wizard(config):
    from stoqlib.gui.base.dialogs import run_dialog
    from stoq.gui.config import FirstTimeConfigWizard
    model = run_dialog(FirstTimeConfigWizard, None, config)
    if not model:
        raise SystemExit("No configuration data provided")

def _setup_dialogs():
    # This needs to be here otherwise we can't install the dialog
    if 'STOQ_TEST_MODE' in os.environ:
        return
    log.debug('providing graphical notification dialogs')
    from stoqlib.gui.base.dialogs import DialogSystemNotifier
    from stoqlib.lib.message import ISystemNotifier
    provide_utility(ISystemNotifier, DialogSystemNotifier(), replace=True)

def _setup_printers():
    log.debug('setting up printers')
    from stoqlib.database.runtime import get_connection, get_current_station
    from stoqlib.lib.drivers import (
        get_fiscal_printer_settings_by_station,
        create_virtual_printer_for_current_station)

    conn = get_connection()

    if not get_fiscal_printer_settings_by_station(conn,
                                                  get_current_station(conn)):
        create_virtual_printer_for_current_station()

def _setup_cookiefile(config_dir):
    log.debug('setting up cookie file')
    from stoqlib.lib.cookie import Base64CookieFile
    from stoqlib.lib.interfaces import ICookieFile
    cookiefile = os.path.join(config_dir, "cookie")
    provide_utility(ICookieFile, Base64CookieFile(cookiefile))

def _check_tables():
    from stoqlib.database.tables import get_table_types
    from stoqlib.database.runtime import get_connection

    log.debug('checking tables')

    # We must check if all the tables are already in the database.
    conn = get_connection()

    for table_type in get_table_types():
        classname = db_table_name(table_type)
        if not conn.tableExists(classname):
            error(
                _("Database schema error"),
                _("Table `%s' does not exist.\n"
                  "Consult your database administrator to solve this problem.")
                % classname)

def _initialize(options):
    # Do this as early as possible to get as much as possible into the
    # log file itself, which means we cannot depend on the config or
    # anything else
    stoqdir = os.path.join(os.environ['HOME'], '.stoq')
    if not os.path.exists(stoqdir):
        os.mkdir(stoqdir)
    set_log_file(os.path.join(stoqdir, 'stoq.log'), 'stoq*')

    _check_dependencies()
    _setup_dialogs()
    log.debug('reading configuration')
    config = StoqConfig(filename=options.filename)
    config_dir = config.get_config_directory()

    wizard = False
    if (options.wizard or
        not os.path.exists(os.path.join(config_dir, 'stoq.conf'))):
        _run_first_time_wizard(config)
        wizard = True

    # There must be ICookieFile registration now, regardless if we
    # ran the wizard or not
    _setup_cookiefile(config_dir)

    # The rest is only necessary when we're not running the first-time
    # configuration wizard, so we can safely skip out
    if wizard:
        return

    try:
        config.check_connection()
    except:
        type, value, trace = sys.exc_info()
        error(_('Could not open database config file'),
              _("Invalid config file settings, got error '%s', "
                "of type '%s'" % (value, type)))

    log.debug('calling setup()')
    # XXX: progress dialog for connecting (if it takes more than
    # 2 seconds) or creating the database
    try:
        setup(config, options)
    except (StoqlibError, PostgreSQLError), e:
        error(_('Could not connect to database'),
              'error=%s uri=%s' % (str(e), config.get_connection_uri()))
        raise SystemExit("Error: bad connection settings provided")

    _setup_printers()
    _check_tables()

def _show_splash():
    from stoqlib.gui.splash import SplashScreen
    from kiwi.environ import environ

    log.debug('displaying splash screen')
    splash = SplashScreen(environ.find_resource("pixmaps", "splash.jpg"))
    splash.show()

    return splash

def _run_app(appname):
    from stoqlib.gui.base.gtkadds import register_iconsets
    from stoq.gui.login import LoginHelper

    log.debug('register stock icons')
    register_iconsets()

    log.debug('loading application')
    appconf = LoginHelper(appname)
    # Get the selected application if nothing was selected
    if not appname:
        appname = appconf.appname

    splash = _show_splash()

    module = __import__("stoq.gui.%s.app" % appname, globals(), locals(), [''])
    if not hasattr(module, "main"):
        raise RuntimeError(
            "Application %s must have a app.main() function")

    log.info('Starting %s application' % appname)
    module.main(appconf)

    splash.hide()

    log.debug("Entering main loop")
    import gtk
    gtk.main()

    log.info("Shutting down %s application" % appname)

def _parse_command_line(args):
    log.info('parsing command line arguments: %s ' % (args,))
    parser = get_option_parser()

    group = optparse.OptionGroup(parser, 'Stoq')
    group.add_option('', '--wizard',
                      action="store_true",
                      dest="wizard",
                      default=None,
                      help='Run the wizard')
    parser.add_option_group(group)

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

    return options, appname

def main(args):
    options, appname = _parse_command_line(args)

    _initialize(options)
    _run_app(appname)
