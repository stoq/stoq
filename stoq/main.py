# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2011 Async Open Source <http://www.async.com.br>
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

_ = gettext.gettext
_log_filename = None
_stream = None
_ran_wizard = False
_restart = False
_cur_exit_func = None
# To avoid kiwi dependency at startup
log = logging.getLogger('stoq.main')


def _write_exception_hook(exctype, value, tb):
    global _stream
    import traceback
    from stoq.gui.shell import get_shell
    from stoqlib.gui.base.dialogs import get_current_toplevel

    shell = get_shell()
    if shell:
        appname = shell.get_current_app_name()
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

    from stoqlib.lib.crashreport import collect_traceback
    collect_traceback((exctype, value, tb))


def _debug_hook(exctype, value, tb):
    import traceback
    _write_exception_hook(exctype, value, tb)
    traceback.print_exception(exctype, value, tb)
    print
    print '-- Starting debugger --'
    print
    import pdb
    pdb.pm()


# FIXME: this logic should be inside stoqlib.
def _exit_func():
    from stoqlib.lib.daemonutils import stop_daemon
    stop_daemon()

    from stoqlib.lib.crashreport import has_tracebacks
    if has_tracebacks() and not 'STOQ_DISABLE_CRASHREPORT' in os.environ:
        from stoqlib.gui.dialogs.crashreportdialog import show_dialog
        show_dialog()
        raise SystemExit

    from stoqlib.database.runtime import get_current_user, get_connection
    from stoqlib.exceptions import StoqlibError
    from stoqlib.lib.process import Process
    try:
        user = get_current_user(get_connection())
        if user:
            user.logout()
    except StoqlibError:
        pass

    if _cur_exit_func:
        _cur_exit_func()

    if _restart:
        Process([sys.argv[0]], shell=True)


def restart_stoq_atexit():
    global _restart
    _restart = True


def _set_app_info():
    from kiwi.component import provide_utility
    from stoqlib.lib.interfaces import IAppInfo
    from stoqlib.lib.appinfo import AppInfo
    import stoq
    stoq_version = stoq.version
    if hasattr(stoq.library, 'get_revision'):
        rev = stoq.library.get_revision()
        if rev is not None:
            stoq_version += ' r' + rev
    info = AppInfo()
    info.set("name", "Stoq")
    info.set("version", stoq_version)
    info.set("log", _log_filename)
    provide_utility(IAppInfo, info)


def _check_dependencies():
    from stoq.lib.dependencies import check_dependencies
    check_dependencies()


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


def _run_first_time_wizard(options, config=None):
    from stoqlib.gui.base.dialogs import run_dialog
    from stoq.gui.config import FirstTimeConfigWizard
    from stoqlib.gui.splash import hide_splash
    global _ran_wizard
    _ran_wizard = True
    hide_splash()
    # This may run Stoq
    run_dialog(FirstTimeConfigWizard, None, options, config)
    raise SystemExit()


def _run_update_wizard():
    from stoqlib.gui.base.dialogs import run_dialog
    from stoq.gui.update import SchemaUpdateWizard
    from stoqlib.gui.splash import hide_splash
    hide_splash()
    retval = run_dialog(SchemaUpdateWizard, None)
    if not retval:
        raise SystemExit()


def _show_splash():
    from stoqlib.gui.splash import show_splash
    show_splash()


def _setup_gtk():
    import gtk
    from kiwi.environ import environ

    # Total madness to make sure we can draw treeview lines,
    # this affects the GtkTreeView::grid-line-pattern style property
    #
    # Two bytes are sent in, see gtk_tree_view_set_grid_lines in gtktreeview.c
    # Byte 1 should be as high as possible, gtk+ 0x7F appears to be
    #        the highest allowed for Gtk+ 2.22 while 0xFF worked in
    #        earlier versions
    # Byte 2 should ideally be allowed to be 0, but neither C nor Python
    #        allows that.
    #
    stoq_rc = environ.find_resource("misc", "stoq.gtkrc")
    data = open(stoq_rc).read()
    data = data.replace('\\x7f\\x01', '\x7f\x01')

    gtk.rc_parse_string(data)

    # Creating a button as a temporary workaround for bug
    # https://bugzilla.gnome.org/show_bug.cgi?id=632538, until gtk 3.0
    gtk.Button()
    settings = gtk.settings_get_default()
    settings.props.gtk_button_images = True


def _setup_twisted():
    from twisted.internet import gtk2reactor
    gtk2reactor.install()


def _setup_ui_dialogs():
    # This needs to be here otherwise we can't install the dialog
    if 'STOQ_TEST_MODE' in os.environ:
        return
    log.debug('providing graphical notification dialogs')
    from stoqlib.gui.base.dialogs import DialogSystemNotifier
    from stoqlib.lib.interfaces import ISystemNotifier
    from kiwi.component import provide_utility
    provide_utility(ISystemNotifier, DialogSystemNotifier(), replace=True)

    import gtk
    from kiwi.environ import environ
    stock_app = environ.find_resource('pixmaps', 'stoq-stock-app-24x24.png')
    gtk.window_set_default_icon_from_file(stock_app)


def _setup_cookiefile():
    log.debug('setting up cookie file')
    from kiwi.component import provide_utility
    from stoqlib.lib.cookie import Base64CookieFile
    from stoqlib.lib.interfaces import ICookieFile
    from stoqlib.lib.osutils import get_application_dir
    app_dir = get_application_dir()
    cookiefile = os.path.join(app_dir, "cookie")
    provide_utility(ICookieFile, Base64CookieFile(cookiefile))


def _prepare_logfiles():
    global _log_filename, _stream

    from stoq.lib.logging import setup_logging
    _log_filename, _stream = setup_logging("stoq")


def _initialize(options):
    # Do this as early as possible to get as much as possible into the
    # log file itself, which means we cannot depend on the config or
    # anything else

    if options.debug:
        hook = _debug_hook
    else:
        hook = _write_exception_hook
    sys.excepthook = hook

    # Save any exiting exitfunc already set.
    if hasattr(sys, 'exitfunc'):
        global _cur_exit_func
        _cur_exit_func = sys.exitfunc
    sys.exitfunc = _exit_func

    from stoqlib.lib.configparser import StoqConfig
    from stoqlib.lib.message import error
    log.debug('reading configuration')
    config = StoqConfig()
    if options.filename:
        config.load(options.filename)
    else:
        config.load_default()
    config_file = config.get_filename()

    if options.wizard or not os.path.exists(config_file):
        _run_first_time_wizard(options)

    if config.get('Database', 'enable_production') == 'True':
        _run_first_time_wizard(options, config)

    settings = config.get_settings()

    try:
        conn_uri = settings.get_connection_uri()
    except:
        type, value, trace = sys.exc_info()
        error(_("Could not open the database config file"),
              _("Invalid config file settings, got error '%s', "
                "of type '%s'") % (value, type))

    from stoqlib.exceptions import StoqlibError
    from stoqlib.database.exceptions import PostgreSQLError
    from stoq.lib.startup import setup, needs_schema_update
    log.debug('calling setup()')

    # XXX: progress dialog for connecting (if it takes more than
    # 2 seconds) or creating the database
    try:
        setup(config, options, register_station=True,
              check_schema=False)
        if needs_schema_update():
            _run_update_wizard()
    except (StoqlibError, PostgreSQLError), e:
        error(_('Could not connect to the database'),
              'error=%s uri=%s' % (str(e), conn_uri))
        raise SystemExit("Error: bad connection settings provided")


def run_app(options, appname):
    global _ran_wizard
    from stoqlib.gui.stockicons import register

    log.debug('register stock icons')
    register()

    from stoq.gui.shell import Shell

    shell = Shell(options, appname)
    shell.ran_wizard = _ran_wizard
    shell.run_loop()


def _parse_command_line(args):
    from stoqlib.lib.uptime import set_initial
    set_initial()

    log.info('parsing command line arguments: %s ' % (args, ))
    from stoq.lib.options import get_option_parser
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

    from stoq.lib.applist import get_application_names
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
    try:
        options, appname = _parse_command_line(args)
    except ImportError:
        _check_dependencies()
        raise

    # Do this as soon as possible, before we attempt to use the
    # external libraries/resources
    _prepare_logfiles()
    _set_app_info()
    _check_dependencies()
    _show_splash()
    _setup_gtk()
    _setup_twisted()
    _check_version_policy()
    _setup_ui_dialogs()
    _setup_cookiefile()

    _initialize(options)
    run_app(options, appname)
