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

import locale
import logging
import os
import platform
import sys
import traceback

from stoqlib.lib.translation import stoqlib_gettext as _

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
        self._check_version_policy()
        self._setup_ui_dialogs()
        self._setup_cookiefile()
        self._register_stock_icons()
        self._setup_domain_slave_mapper()
        self._load_key_bindings()
        self._setup_debug_options()
        self._check_locale()

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

    def _prepare_logfiles(self):
        from stoq.lib.logging import setup_logging
        self._log_filename, self.stream = setup_logging("stoq")

        from stoqlib.lib.environment import is_developer_mode
        # We want developers to see deprecation warnings.
        if is_developer_mode():
            import warnings
            warnings.filterwarnings(
                "default", category=DeprecationWarning,
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
                stoq_version += ' r' + rev
                stoq_ver += ('r' + rev,)
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

        gtk.gdk.threads_init()
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

    def _setup_kiwi(self):
        from kiwi.ui.views import set_glade_loader_func
        set_glade_loader_func(self._glade_loader_func)

        from kiwi.datatypes import get_localeconv
        from kiwi.ui.widgets.label import ProxyLabel
        ProxyLabel.replace('$CURRENCY', get_localeconv()['currency_symbol'])

    def _show_splash(self):
        if not self._options.splashscreen:
            return
        from stoqlib.gui.splash import show_splash
        show_splash()

    def _setup_twisted(self, raise_=True):
        # FIXME: figure out why twisted is already loaded
        #assert not 'twisted' in sys.modules
        from stoqlib.net import gtk2reactor
        from twisted.internet.error import ReactorAlreadyInstalledError
        try:
            gtk2reactor.install()
        except ReactorAlreadyInstalledError:
            if self._initial and raise_:
                raise

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
        FIRST_UNSTABLE_EXTRA_VERSION = 90

        # Stable series of Stoq must:
        # 1) have extra_version set to < 90
        # 2) Depend on a stoqlib version with extra_version < 90
        #
        if stoq.stable:
            if (stoq.extra_version >= FIRST_UNSTABLE_EXTRA_VERSION and
                not 'rc' in stoq.extra_version):
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
        from stoqlib.gui.domainslavemapper import DefaultDomainSlaveMapper
        provide_utility(IDomainSlaveMapper, DefaultDomainSlaveMapper(),
                        replace=True)

    def _load_key_bindings(self):
        from stoqlib.gui.keybindings import load_user_keybindings
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
        from stoqlib.gui.keyboardhandler import install_global_keyhandler
        from stoqlib.gui.introspection import introspect_slaves
        install_global_keyhandler(keysyms.F12, introspect_slaves)

    #
    # Global functions
    #

    def _debug_hook(self, exctype, value, tb):
        self._write_exception_hook(exctype, value, tb)
        traceback.print_exception(exctype, value, tb)
        print
        print '-- Starting debugger --'
        print
        import pdb
        pdb.pm()

    def _glade_loader_func(self, view, filename, domain):
        from kiwi.environ import environ
        from kiwi.ui.builderloader import BuilderWidgetTree
        if not filename.endswith('ui'):
            filename += '.ui'
        ui_string = environ.get_resource_string('stoq', 'glade', filename)

        return BuilderWidgetTree(view, None, domain, ui_string)

    def _write_exception_hook(self, exctype, value, tb):
        # NOTE: This exception hook depends on gtk, kiwi, twisted being present
        #       In the future we might want it to run without some of these
        #       dependencies, so we can crash reports that happens really
        #       really early on for users with weird environments.
        if not self.entered_main:
            self._setup_twisted(raise_=False)

        appname = 'unknown'
        try:
            from stoq.gui.shell import get_shell
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

        log.info('An error occurred in application "%s", toplevel window=%s:' % (
            appname, window_name))

        traceback.print_exception(exctype, value, tb, file=self.stream)

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
