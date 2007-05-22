# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2007 Async Open Source <http://www.async.com.br>
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
from stoqlib.exceptions import LoginError, StoqlibError
from stoqlib.lib.message import error

from stoq.lib.applist import get_application_names
from stoq.lib.options import get_option_parser

_ = gettext.gettext
_stream = None

log = Logger('stoq.main')

def _write_exception_hook(exctype, value, tb):
    global _stream
    import traceback
    from stoq.gui.runner import get_runner
    from stoqlib.gui.base.dialogs import get_current_toplevel

    runner = get_runner()
    if runner:
        appname = runner.get_current_app_name()
    else:
        appname = 'unknown'

    window = get_current_toplevel()
    if window:
        window_name = window.name
    else:
        window_name = 'unknown'

    log.info('An error occurred in application "%s", toplevel window=%s:' % (
        appname, window_name))

    traceback.print_exception(exctype, value, tb, file=_stream)
    traceback.print_exception(exctype, value, tb)

def _debug_hook(exctype, value, tb):
    import traceback
    _write_exception_hook(exctype, value, tb)
    traceback.print_exception(exctype, value, tb)
    print
    print '-- Starting debugger --'
    print
    import pdb
    pdb.pm()

def _check_dependencies():
    if 0:
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
    from stoqlib.drivers.fiscalprinter import (
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
    from stoqlib.database.runtime import get_connection

    log.debug('checking tables')

    # Check so SystemTable is present
    conn = get_connection()
    if not conn.tableExists('system_table'):
        error(
            _("Database schema error"),
            _("Table `system_table' does not exist.\n"
              "Consult your database administrator to solve this problem."))

    # FIXME: Check so SystemTable is up-to-date

def _initialize(options):
    global _stream
    # Do this as early as possible to get as much as possible into the
    # log file itself, which means we cannot depend on the config or
    # anything else
    stoqdir = os.path.join(os.environ['HOME'], '.stoq')
    if not os.path.exists(stoqdir):
        os.mkdir(stoqdir)
    _stream = set_log_file(os.path.join(stoqdir, 'stoq.log'), 'stoq*')
    if options.debug:
        hook = _debug_hook
    else:
        hook = _write_exception_hook
    sys.excepthook = hook

    _check_dependencies()
    _setup_dialogs()

    from stoq.lib.configparser import StoqConfig
    log.debug('reading configuration')
    config = StoqConfig()
    config.load(options.filename)
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

    from stoq.lib.startup import setup
    from stoqlib.database.exceptions import PostgreSQLError
    log.debug('calling setup()')
    # XXX: progress dialog for connecting (if it takes more than
    # 2 seconds) or creating the database
    try:
        setup(config, options)
    except (StoqlibError, PostgreSQLError), e:
        error(_('Could not connect to database'),
              'error=%s uri=%s' % (str(e), config.get_connection_uri()))
        raise SystemExit("Error: bad connection settings provided")

    _check_tables()

def _run_app(options, appname):
    from stoqlib.gui.base.gtkadds import register_iconsets

    log.debug('register stock icons')
    register_iconsets()

    from stoq.gui.runner import ApplicationRunner
    runner = ApplicationRunner(options)

    try:
        if not runner.login():
            return
    except LoginError, e:
        error(e)

    if appname:
        app = runner.get_app_by_name(appname)
    else:
        app = runner.choose()
        if not app:
            return

    runner.run(app)

    _setup_printers()

    import gtk
    log.debug("Entering main loop")
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
    _run_app(options, appname)
