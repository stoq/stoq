# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2009 Async Open Source <http://www.async.com.br>
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
import logging
import optparse
import os
import sys

from stoq.lib.applist import get_application_names
from stoq.lib.options import get_option_parser

PYGTK_REQUIRED = (2, 8, 1)
KIWI_REQUIRED = (1, 9, 24)
STOQLIB_REQUIRED = (0, 9, 9)
GAZPACHO_REQUIRED = (0, 6, 6)
REPORTLAB_REQUIRED = (1, 20)

_ = gettext.gettext
_stream = None

# To avoid kiwi dependency at startup
log = logging.getLogger('stoq.main')

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
    from stoqlib.lib.message import error
    log.debug('checking dependencies')

    def _missing_module_error(module, fancy=None):
        error(
            _("%s not found") % (fancy or module),
            _("Could not find the required python module %s on your system") %
            module)

    # PyGTK
    try:
        import gtk
        gtk # stuid pyflakes
    except ImportError:
        try:
            import pygtk
            # This modifies sys.path
            pygtk.require('2.0')
            # Try again now when pygtk is imported
            import gtk
        except ImportError:
            _missing_module_error("gtk", "PyGTK")

    gtk.rc_parse_string("""style "tree-style" {
        GtkTreeView::vertical-separator = 0
        GtkTreeView::horizontal-separator = 0
        GtkTreeView::grid-line-width = 0
    }
    class "GtkTreeView" style "tree-style" """)
    _setup_ui_dialogs()

    if gtk.pygtk_version < PYGTK_REQUIRED:
        error(_("PyGTK too old"),
              _("PyGTK version too old, needs %s but found %s") % (
            '.'.join(map(str, PYGTK_REQUIRED)),
            '.'.join(map(str, gtk.pygtk_version))))
    log.debug('pygtk %s found, okay' % ('.'.join(map(str, gtk.pygtk_version))))

    # Kiwi
    try:
        import kiwi
    except ImportError:
        _missing_module_error("kiwi")

    kiwi_version = kiwi.__version__.version
    if kiwi_version < KIWI_REQUIRED:
        error(_("Kiwi too old"),
              _("kiwi version too old, needs %s but found %s") % (
            '.'.join(map(str, KIWI_REQUIRED)),
            '.'.join(map(str, kiwi_version))))
    log.debug('kiwi %s found, okay' % ('.'.join(map(str, kiwi_version))))

    # Stoqlib
    try:
        import stoqlib
    except ImportError:
        _missing_module_error("stoqlib")

    stoqlib_version = tuple(stoqlib.version.split('.'))
    if stoqlib_version < STOQLIB_REQUIRED:
        error(_("Stoqlib too old"),
              _("stoqlib version too old, needs %s but found %s") % (
            '.'.join(map(str, STOQLIB_REQUIRED)),
            '.'.join(map(str, stoqlib_version))))
    log.debug('stoqlib %s found, okay' % ('.'.join(map(str, stoqlib_version))))

    # Gazpacho
    try:
        import gazpacho
    except ImportError:
        _missing_module_error("gazpacho")

    if map(int, gazpacho.__version__.split('.')) < list(GAZPACHO_REQUIRED):
        error(_("Gazpacho too old"),
              _("Gazpacho %s is required but %s found") % (
            '.'.join(map(str, GAZPACHO_REQUIRED)),
            gazpacho.__version__))
    log.debug('gazpacho %s found, okay' % (gazpacho.__version__,))

    # Reportlab
    try:
        import reportlab
    except ImportError:
        _missing_module_error("reportlab")

    if map(int, reportlab.Version.split('.')) < list(REPORTLAB_REQUIRED):
        error(_("Reportlab too old"),
              _("reportlab %s is required but %s found") % (
            '.'.join(map(str, REPORTLAB_REQUIRED)),
            reportlab.Version))
    log.debug('reportlab okay')

def _run_first_time_wizard(options):
    from stoqlib.gui.base.dialogs import run_dialog
    from stoq.gui.config import FirstTimeConfigWizard
    model = run_dialog(FirstTimeConfigWizard, None, options)
    if model is None:
        raise SystemExit("No configuration data provided")
    # We have a successfull installation, but the user want to close the
    # the application now.
    if model is False:
        raise SystemExit()

def _setup_ui_dialogs():
    # This needs to be here otherwise we can't install the dialog
    if 'STOQ_TEST_MODE' in os.environ:
        return
    log.debug('providing graphical notification dialogs')
    from stoqlib.gui.base.dialogs import DialogSystemNotifier
    from stoqlib.lib.message import ISystemNotifier
    from kiwi.component import provide_utility

    provide_utility(ISystemNotifier, DialogSystemNotifier(), replace=True)

def _setup_cookiefile(config_dir):
    log.debug('setting up cookie file')
    from kiwi.component import provide_utility
    from stoqlib.lib.cookie import Base64CookieFile
    from stoqlib.lib.interfaces import ICookieFile
    cookiefile = os.path.join(config_dir, "cookie")
    provide_utility(ICookieFile, Base64CookieFile(cookiefile))

def _initialize(options):
    global _stream

    # Do this as early as possible to get as much as possible into the
    # log file itself, which means we cannot depend on the config or
    # anything else
    stoqdir = os.path.join(os.environ['HOME'], '.stoq')
    if not os.path.exists(stoqdir):
        os.mkdir(stoqdir)

    from kiwi.log import set_log_file
    _stream = set_log_file(os.path.join(stoqdir, 'stoq.log'), 'stoq*')
    if options.debug:
        hook = _debug_hook
    else:
        hook = _write_exception_hook
    sys.excepthook = hook

    from stoqlib.lib.message import error
    from stoq.lib.configparser import StoqConfig
    log.debug('reading configuration')
    config = StoqConfig()
    config.load(options.filename)
    config_dir = config.get_config_directory()
    columns_dir = os.path.join(config_dir, 'columns')
    if not os.path.exists(columns_dir):
        os.mkdir(columns_dir)

    wizard = False
    if (options.wizard or
        not os.path.exists(os.path.join(config_dir, 'stoq.conf'))):
        _run_first_time_wizard(options)
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

    from stoqlib.exceptions import StoqlibError
    from stoqlib.database.exceptions import PostgreSQLError
    from stoq.lib.startup import setup
    log.debug('calling setup()')
    # XXX: progress dialog for connecting (if it takes more than
    # 2 seconds) or creating the database
    try:
        setup(config, options)
    except (StoqlibError, PostgreSQLError), e:
        error(_('Could not connect to database'),
              'error=%s uri=%s' % (str(e), config.get_connection_uri()))
        raise SystemExit("Error: bad connection settings provided")

def _run_app(options, appname):
    from stoqlib.gui.base.gtkadds import register_iconsets
    from stoqlib.exceptions import LoginError
    from stoqlib.lib.message import error

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

    # Do this as soon as possible, before we attempt to use the
    # external libraries/resources
    _check_dependencies()

    _initialize(options)
    _run_app(options, appname)
