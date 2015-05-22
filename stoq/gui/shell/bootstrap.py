# -*- coding: utf-8 *-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2013 Async Open Source <http://www.async.com.br>
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

# NOTE: We need to be careful about imports at this point, we cannot yet
#       depend that all libraries are present, nor that all external
#       dependencies are properly configured, so only import the standard
#       library here.
import locale
import logging
import os
import platform
import sys
import time
import traceback

log = logging.getLogger(__name__)


class ShellBootstrap(object):
    """Bootstraps the Stoq application, it's responsible for:
    - Setting up log files
    - Checking dependencies
    - Setting up libraries (gobject, gtk, kiwi, twisted)
    - Checking version
    - Locale
    - User settings and keybindings

    When this is completed Stoq is ready to connect to a database.
    """

    def __init__(self, options, initial):
        self._initial = initial
        self._log_filename = None
        self._options = options
        self.entered_main = False
        self.stream = None

    def bootstrap(self):
        self._setup_gobject()
        self._set_uptime()
        # Do this as soon as possible, before we attempt to use the
        # external libraries/resources
        self._set_user_locale()
        # Do this as early as possible to get as much as possible into the
        # log file itself, which means we cannot depend on the config or
        # anything else
        self._prepare_logfiles()
        self._set_app_info()
        self._check_dependencies()
        self._setup_exception_hook()
        self._setup_gtk()
        self._setup_kiwi()
        self._show_splash()
        self._setup_twisted()
        self._setup_psycopg()
        self._check_version_policy()
        self._setup_ui_dialogs()
        self._setup_cookiefile()
        self._register_stock_icons()
        self._setup_domain_slave_mapper()
        self._load_key_bindings()
        self._setup_debug_options()
        self._check_locale()
        self._setup_autoreload()

    def _setup_gobject(self):
        if not self._initial:
            return
        assert not 'gobject' in sys.modules
        assert not 'gtk' in sys.modules

        if 'STOQ_USE_GI' in os.environ:
            from stoq.lib import gicompat
            gicompat.enable()

        import gobject
        gobject.threads_init()

    def _set_uptime(self):
        from stoqlib.lib.uptime import set_initial
        set_initial()

    def _set_user_locale(self):
        from stoqlib.lib.settings import get_settings
        from stoqlib.lib.translation import stoqlib_gettext as _

        self._locale_error = None
        settings = get_settings()
        lang = settings.get('user-locale', None)
        if not lang:
            return

        lang += '.UTF-8'
        try:
            locale.setlocale(locale.LC_ALL, lang)
        except locale.Error as err:
            msg = _("Could not set locale to %s. Make sure that you have "
                    "the packages for this locale installed.") % lang[:-6]
            self._locale_error = (msg, err)
            log.warning(msg)
        else:
            os.environ['LC_ALL'] = lang
            os.environ['LANGUAGE'] = lang

    def _setup_autoreload(self):
        if not self._options.autoreload:
            return

        from stoqlib.lib.autoreload import install_autoreload
        install_autoreload()

    def _prepare_logfiles(self):
        from stoqlib.lib.osutils import get_application_dir

        stoqdir = get_application_dir("stoq")
        log_dir = os.path.join(stoqdir, 'logs', time.strftime('%Y'),
                               time.strftime('%m'))
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        filename = 'stoq_%s.%s.log' % (time.strftime('%Y-%m-%d_%H-%M-%S'), os.getpid())
        self._log_filename = os.path.join(log_dir, filename)

        from kiwi.log import set_log_file
        self._stream = set_log_file(self._log_filename, 'stoq*')

        if hasattr(os, 'symlink'):
            link_file = os.path.join(stoqdir, 'stoq.log')
            if os.path.exists(link_file):
                os.unlink(link_file)
            os.symlink(self._log_filename, link_file)

        # We want developers to see deprecation warnings.
        from stoqlib.lib.environment import is_developer_mode
        if is_developer_mode():
            import warnings
            if self._options.non_fatal_warnings:
                action = "default"
            else:
                action = "error"
            warnings.filterwarnings(
                action, category=DeprecationWarning,
                module="^(stoq|kiwi)")

    def _set_app_info(self):
        from kiwi.component import provide_utility
        from stoqlib.lib.appinfo import AppInfo
        from stoqlib.lib.kiwilibrary import library
        from stoqlib.lib.interfaces import IAppInfo
        import stoq
        # FIXME: use only stoq.stoq_version here and all other callsites of
        # IAppInfo
        stoq_version = stoq.version
        stoq_ver = stoq.stoq_version
        if hasattr(library, 'get_revision'):
            rev = library.get_revision()
            if rev is not None:
                stoq_version += ' ' + rev
                stoq_ver += (rev,)
        info = AppInfo()
        info.set("name", "Stoq")
        info.set("version", stoq_version)
        info.set("ver", stoq_ver)
        info.set("log", self._log_filename)
        provide_utility(IAppInfo, info)

    def _check_dependencies(self):
        from stoq.lib.dependencies import check_dependencies
        check_dependencies()

    def _setup_exception_hook(self):
        if self._options.debug:
            hook = self._debug_hook
        else:
            hook = self._write_exception_hook
        sys.excepthook = hook

    def _setup_gtk(self):
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
        data = environ.get_resource_string("stoq", "misc", "stoq.gtkrc")
        data = data.replace('\\x7f\\x01', '\x7f\x01')

        gtk.rc_parse_string(data)

        # Creating a button as a temporary workaround for bug
        # https://bugzilla.gnome.org/show_bug.cgi?id=632538, until gtk 3.0
        gtk.Button()
        settings = gtk.settings_get_default()
        settings.props.gtk_button_images = True

        from stoqlib.lib.environment import is_developer_mode
        if is_developer_mode() and gtk.gtk_version[0] == 2:
            from gtk import gdk

            # Install a Control-Q handler that forcefully exits
            # the program without saving any kind of state
            def event_handler(event):
                if (event.type == gdk.KEY_PRESS and
                        event.state & gdk.CONTROL_MASK and
                        event.keyval == gtk.keysyms.q):
                    os._exit(0)
                gtk.main_do_event(event)
            gdk.event_handler_set(event_handler)

    def _setup_kiwi(self):
        from kiwi.datatypes import get_localeconv
        from kiwi.ui.widgets.label import ProxyLabel
        ProxyLabel.replace('$CURRENCY', get_localeconv()['currency_symbol'])

    def _show_splash(self):
        if not self._options.splashscreen:
            return
        from stoqlib.gui.widgets.splash import show_splash
        show_splash()

    def _setup_twisted(self, raise_=True):
        # FIXME: figure out why twisted is already loaded
        # assert not 'twisted' in sys.modules
        from stoqlib.net import gtk2reactor
        from twisted.internet.error import ReactorAlreadyInstalledError
        try:
            gtk2reactor.install()
        except ReactorAlreadyInstalledError:
            if self._initial and raise_:
                raise

    def _setup_psycopg(self):
        # This will only be required when we use uuid.UUID instances
        # for UUIDCol
        #from psycopg2.extras import register_uuid
        #register_uuid()
        return

    def _check_version_policy(self):
        # No need to bother version checking when not running in developer mode
        from stoqlib.lib.environment import is_developer_mode
        if not is_developer_mode():
            return

        import stoq

        #
        # Policies for stoq/stoqlib versions,
        # All these policies here are made so that stoqlib version is tightly
        # tied to the stoq versioning
        #

        # We reserve the first 89 for the stable series.
        FIRST_UNSTABLE_MICRO_VERSION = 90

        # Stable series of Stoq must:
        # 1) have extra_version set to < 90
        # 2) Depend on a stoqlib version with extra_version < 90
        #
        if stoq.stable:
            if (stoq.micro_version >= FIRST_UNSTABLE_MICRO_VERSION and
                    not 'rc' in stoq.extra_version):
                raise SystemExit(
                    "Stable stoq release should set micro_version to "
                    "%d or lower" % (FIRST_UNSTABLE_MICRO_VERSION, ))
        # Unstable series of Stoq must have:
        # 1) have extra_version set to >= 90
        # 2) Must depend stoqlib version with extra_version >= 90
        #
        else:
            if stoq.micro_version < FIRST_UNSTABLE_MICRO_VERSION:
                raise SystemExit(
                    "Unstable stoq (%s) must set micro_version to %d or higher, "
                    "or did you forget to set stoq.stable to True?" % (
                        stoq.version, FIRST_UNSTABLE_MICRO_VERSION))

    def _setup_ui_dialogs(self):
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
        from kiwi.ui.pixbufutils import pixbuf_from_string
        data = environ.get_resource_string(
            'stoq', 'pixmaps', 'stoq-stock-app-24x24.png')
        gtk.window_set_default_icon(pixbuf_from_string(data))

        if platform.system() == 'Darwin':
            from AppKit import NSApplication, NSData, NSImage
            bytes = environ.get_resource_string(
                'stoq', 'pixmaps', 'stoq-stock-app-48x48.png')
            data = NSData.alloc().initWithBytes_length_(bytes, len(bytes))
            icon = NSImage.alloc().initWithData_(data)
            app = NSApplication.sharedApplication()
            app.setApplicationIconImage_(icon)

    def _setup_cookiefile(self):
        log.debug('setting up cookie file')
        from kiwi.component import provide_utility
        from stoqlib.lib.cookie import Base64CookieFile
        from stoqlib.lib.interfaces import ICookieFile
        from stoqlib.lib.osutils import get_application_dir
        app_dir = get_application_dir()
        cookiefile = os.path.join(app_dir, "cookie")
        provide_utility(ICookieFile, Base64CookieFile(cookiefile))

    def _register_stock_icons(self):
        from stoqlib.gui.stockicons import register

        log.debug('register stock icons')
        register()

    def _setup_domain_slave_mapper(self):
        from kiwi.component import provide_utility
        from stoqlib.gui.interfaces import IDomainSlaveMapper
        from stoqlib.gui.slaves.domainslavemapper import DefaultDomainSlaveMapper
        provide_utility(IDomainSlaveMapper, DefaultDomainSlaveMapper(),
                        replace=True)

    def _load_key_bindings(self):
        from stoqlib.gui.utils.keybindings import load_user_keybindings
        load_user_keybindings()

    def _check_locale(self):
        if not self._locale_error:
            return

        from stoqlib.lib.message import warning
        warning(self._locale_error[0], str(self._locale_error[1]))

    def _setup_debug_options(self):
        if not self._options.debug:
            return
        from gtk import keysyms
        from stoqlib.gui.utils.introspection import introspect_slaves
        from stoqlib.gui.utils.keyboardhandler import install_global_keyhandler
        install_global_keyhandler(keysyms.F12, introspect_slaves)

    #
    # Global functions
    #

    def _debug_hook(self, exctype, value, tb):
        self._write_exception_hook(exctype, value, tb)
        traceback.print_exception(exctype, value, tb)
        print()
        print('-- Starting debugger --')
        print()
        import pdb
        pdb.pm()

    def _write_exception_hook(self, exctype, value, tb):
        # NOTE: This exception hook depends on gtk, kiwi, twisted being present
        #       In the future we might want it to run without some of these
        #       dependencies, so we can crash reports that happens really
        #       really early on for users with weird environments.
        if not self.entered_main:
            self._setup_twisted(raise_=False)

        try:
            from psycopg2 import OperationalError
            if exctype == OperationalError:
                from stoqlib.lib.message import error
                from stoqlib.lib.translation import stoqlib_gettext as _
                return error(_('There was an error quering the database'),
                             str(value))
        except ImportError:
            pass

        appname = 'unknown'
        try:
            from stoq.gui.shell.shell import get_shell
            shell = get_shell()
            if shell:
                appname = shell.get_current_app_name()
        except ImportError:
            pass

        window_name = 'unknown'
        try:
            from stoqlib.gui.base.dialogs import get_current_toplevel
            window = get_current_toplevel()
            if window:
                window_name = window.get_name()
        except ImportError:
            pass

        log.info('An error occurred in application "%s", toplevel window=%s' % (
            appname, window_name))

        exc_lines = traceback.format_exception(exctype, value, tb)
        for line in ''.join(exc_lines).split('\n')[:-1]:
            log.error(line)

        from stoqlib.lib.crashreport import collect_traceback
        collect_traceback((exctype, value, tb))

        if self.entered_main:
            return

        from stoqlib.gui.dialogs.crashreportdialog import show_dialog
        d = show_dialog()
        from twisted.internet import reactor
        d.addCallback(lambda *x: reactor.stop())
        reactor.run()
        raise SystemExit


def boot_shell(options, initial=True):
    bootstrap = ShellBootstrap(options=options, initial=initial)
    bootstrap.bootstrap()

    # We can now import Shell which can import any dependencies it like,
    # as all should be configured properly at this point
    from stoq.gui.shell.shell import Shell
    shell = Shell(bootstrap, options)
    return shell
