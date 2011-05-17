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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
""" Stoq startup routines"""

import gettext
import logging
import optparse
import os
import sys
import time

from stoqlib.lib.osutils import get_application_dir

from stoq.lib.applist import get_application_names
from stoq.lib.options import get_option_parser

PYGTK_REQUIRED = (2, 16, 0)
KIWI_REQUIRED = (1, 9, 27)
STOQLIB_REQUIRED = (0, 9, 15, 99)
GAZPACHO_REQUIRED = (0, 6, 6)
REPORTLAB_REQUIRED = (1, 20)

_ = gettext.gettext
_log_filename = None
_start_time = time.time()
_stream = None
_ran_wizard = False
_restart = False

# To avoid kiwi dependency at startup
log = logging.getLogger('stoq.main')

_tracebacks = []

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

    _tracebacks.append((exctype, value, tb))

def _debug_hook(exctype, value, tb):
    import traceback
    _write_exception_hook(exctype, value, tb)
    traceback.print_exception(exctype, value, tb)
    print
    print '-- Starting debugger --'
    print
    import pdb
    pdb.pm()

def _exit_func():
    #from stoqlib.lib.parameters import is_developer_mode
    # Disable dialog in developer mode eventually, but we
    # first need to test it properly.
    #if _tracebacks and not is_developer_mode():
    if _tracebacks:
        import stoq
        from stoqlib.gui.dialogs.crashreportdialog import show_dialog
        uptime = int(time.time() - _start_time)
        params = {
            'app-name': 'Stoq',
            'app-version': stoq.version,
            'app-uptime': uptime,
            'log-filename': _log_filename,
            }
        show_dialog(params, _tracebacks)

    if _restart:
        import subprocess
        subprocess.Popen([sys.argv[0]], shell=True)

def restart_stoq_atexit():
    global _restart
    _restart = True

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
    settings = gtk.settings_get_default()
    # Creating a button as a temporary workaround for bug
    # https://bugzilla.gnome.org/show_bug.cgi?id=632538, until gtk 3.0
    gtk.Button()
    settings.props.gtk_button_images = True
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

def _check_version_policy():
    # No need to bother version checking when not running in developer mode
    from stoqlib.lib.parameters import is_developer_mode
    if not is_developer_mode():
        return

    import stoq

    #
    # Policies for stoq/stoqlib versions,
    # All these policies here are made so that stoqlib version is tightly
    # tied to the stoq versioning
    #
    # All series of Stoq must:
    # 1) Depend on the same major/micro/minor version of stoqlib
    #
    if (stoq.major_version,
        stoq.minor_version,
        stoq.micro_version) != tuple(STOQLIB_REQUIRED[:3]):
        versions = ((stoq.major_version, stoq.minor_version,
                     stoq.micro_version) + STOQLIB_REQUIRED[:3])
        raise SystemExit(
            "stoq series (%d.%d.%d) need to require at least the same "
            "series (major/minor/micro) of stoqlib (%d.%d.%d)" % versions)

    # We reserve the first 89 for the stable series.
    FIRST_UNSTABLE_EXTRA_VERSION = 90

    # Stable series of Stoq must:
    # 1) have extra_version set to < 90
    # 2) Depend on a stoqlib version with extra_version < 90
    #
    if stoq.stable:
        if stoq.extra_version >= FIRST_UNSTABLE_EXTRA_VERSION:
           raise SystemExit(
               "Stable stoq release should set extra_version to %d or lower" % (
               FIRST_UNSTABLE_EXTRA_VERSION, ))

        if (len(STOQLIB_REQUIRED) >= 4 and
            STOQLIB_REQUIRED[3] >= FIRST_UNSTABLE_EXTRA_VERSION):
            raise SystemExit(
                "Stable stoq (%s) cannot depend on "
                "unstable stoqlib (%s)" % (
                stoq.version, '.'.join(map(str, STOQLIB_REQUIRED))))

    # Unstable series of Stoq must have:
    # 1) have extra_version set to >= 90
    # 2) Must depend stoqlib version with extra_version >= 90
    #
    else:
        if stoq.extra_version < FIRST_UNSTABLE_EXTRA_VERSION:
           raise SystemExit(
              "Unstable stoq (%s) must set extra_version to %d or higher, "
              "or did you forget to set stoq.stable to True?" % (
              stoq.version, FIRST_UNSTABLE_EXTRA_VERSION))

        if (len(STOQLIB_REQUIRED) < 4 or
            STOQLIB_REQUIRED[3] < FIRST_UNSTABLE_EXTRA_VERSION):
           raise SystemExit("Unstable stoq needs to depend on unstable stoqlib")


def _run_first_time_wizard(options, config=None):
    from stoqlib.gui.base.dialogs import run_dialog
    from stoq.gui.config import FirstTimeConfigWizard
    global _ran_wizard
    _ran_wizard = True
    # This may run Stoq
    run_dialog(FirstTimeConfigWizard, None, options, config)
    raise SystemExit()

def _run_update_wizard():
    from stoqlib.gui.base.dialogs import run_dialog
    from stoq.gui.update import SchemaUpdateWizard

    retval = run_dialog(SchemaUpdateWizard, None)
    if not retval:
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

def _setup_cookiefile():
    log.debug('setting up cookie file')
    from kiwi.component import provide_utility
    from stoqlib.lib.cookie import Base64CookieFile
    from stoqlib.lib.interfaces import ICookieFile
    app_dir = get_application_dir()
    cookiefile = os.path.join(app_dir, "cookie")
    provide_utility(ICookieFile, Base64CookieFile(cookiefile))

def _check_main_branch():
    from stoqlib.database.runtime import get_connection, new_transaction
    from stoqlib.domain.person import Person
    from stoqlib.domain.interfaces import IBranch, ICompany
    from stoqlib.lib.parameters import sysparam
    conn = get_connection()
    compaines = Person.iselect(ICompany, connection=conn)
    if (compaines.count() == 0 or
        not sysparam(conn).MAIN_COMPANY):
        from stoqlib.gui.base.dialogs import run_dialog
        from stoqlib.gui.dialogs.branchdialog import BranchDialog
        from stoqlib.lib.message import info
        if _ran_wizard:
            info(_("You need to register a company before using Stoq"))
        else:
            info(_("Couldn't find a company, You'll need to register one before using Stoq"))
        trans = new_transaction()
        person = run_dialog(BranchDialog, None, trans)
        if not person:
            raise SystemExit
        sysparam(trans).MAIN_COMPANY = IBranch(person).id
        trans.commit()

    return

def _prepare_logfiles():
    global _log_filename, _stream

    stoqdir = get_application_dir()

    import time
    log_dir = os.path.join(stoqdir, 'logs', time.strftime('%Y'),
                            time.strftime('%m'))
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    from kiwi.log import set_log_file
    _log_filename = os.path.join(log_dir, 'stoq_%s.log' %
                                time.strftime('%Y-%m-%d_%H-%M-%S'))
    _stream = set_log_file(_log_filename, 'stoq*')

    if hasattr(os, 'symlink'):
        link_file = os.path.join(stoqdir, 'stoq.log')
        if os.path.exists(link_file):
            os.unlink(link_file)
        os.symlink(_log_filename, link_file)

def _initialize(options):
    # Do this as early as possible to get as much as possible into the
    # log file itself, which means we cannot depend on the config or
    # anything else
    _prepare_logfiles()

    if options.debug:
        hook = _debug_hook
    else:
        hook = _write_exception_hook
    sys.excepthook = hook

    sys.exitfunc = _exit_func

    from stoqlib.lib.message import error
    from stoq.lib.configparser import StoqConfig
    log.debug('reading configuration')
    config = StoqConfig()
    config.load(options.filename)
    config_dir = config.get_config_directory()

    config_file = os.path.join(config_dir, 'stoq.conf')

    wizard = False
    if options.wizard or not os.path.exists(config_file):
        _run_first_time_wizard(options)

    if config.get('Database', 'remove_examples') == 'True':
        _run_first_time_wizard(options, config)

    try:
        config.check_connection()
    except:
        type, value, trace = sys.exc_info()
        error(_('Could not open database config file'),
              _("Invalid config file settings, got error '%s', "
                "of type '%s'" % (value, type)))

    from stoqlib.exceptions import StoqlibError
    from stoqlib.database.exceptions import PostgreSQLError
    from stoq.lib.startup import setup, needs_schema_update
    log.debug('calling setup()')

    # XXX: progress dialog for connecting (if it takes more than
    # 2 seconds) or creating the database
    try:
        setup(config, options, register_station=False,
              check_schema=False)
        if needs_schema_update():
            _run_update_wizard()
    except (StoqlibError, PostgreSQLError), e:
        error(_('Could not connect to database'),
              'error=%s uri=%s' % (str(e), config.get_connection_uri()))
        raise SystemExit("Error: bad connection settings provided")

def run_app(options, appname):
    from stoqlib.gui.base.gtkadds import register_iconsets
    from stoqlib.exceptions import LoginError
    from stoqlib.lib.message import error

    log.debug('register stock icons')
    register_iconsets()

    _setup_cookiefile()

    from stoq.gui.runner import ApplicationRunner
    runner = ApplicationRunner(options)

    try:
        if not runner.login():
            return
    except LoginError, e:
        error(e)

    _check_main_branch()

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
    group.add_option('', '--login-username',
                     action="store",
                     dest="login_username",
                     default=None,
                     help='Username to login to stoq with')
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
    _check_version_policy()

    _initialize(options)
    run_app(options, appname)
