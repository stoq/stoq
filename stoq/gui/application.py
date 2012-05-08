# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2012 Async Open Source <http://www.async.com.br>
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
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Base classes for application's GUI """

import datetime
import gettext
import locale
import os
import platform
import sys

import gobject
import gtk
from kiwi.component import get_utility
from kiwi.enums import SearchFilterPosition
from kiwi.environ import environ
from kiwi.log import Logger
from kiwi.ui.delegates import GladeDelegate
from stoqlib.api import api
from stoqlib.database.orm import ORMObjectQueryExecuter
from stoqlib.exceptions import StoqlibError
from stoqlib.lib.crashreport import has_tracebacks
from stoqlib.lib.interfaces import IAppInfo
from stoqlib.lib.message import yesno
from stoqlib.lib.webservice import WebService
from stoqlib.gui.base.dialogs import get_dialog, run_dialog
from stoqlib.gui.base.infobar import InfoBar
from stoqlib.gui.base.search import StoqlibSearchSlaveDelegate
from stoqlib.gui.dialogs.crashreportdialog import show_dialog
from stoqlib.gui.dialogs.feedbackdialog import FeedbackDialog
from stoqlib.gui.dialogs.spreadsheetexporterdialog import SpreadSheetExporterDialog
from stoqlib.gui.editors.preferenceseditor import PreferencesEditor
from stoqlib.gui.events import StopApplicationEvent
from stoqlib.gui.help import show_contents, show_section
from stoqlib.gui.introspection import introspect_slaves
from stoqlib.gui.keybindings import get_accel, get_accels
from stoqlib.gui.logo import render_logo_pixbuf
from stoqlib.gui.openbrowser import open_browser
from stoqlib.gui.printing import print_report
from stoqlib.gui.splash import hide_splash
from stoqlib.gui.toolmenuaction import ToolMenuAction
from stoqlib.domain.inventory import Inventory
from twisted.internet import reactor
from twisted.internet.defer import succeed

import stoq

log = Logger('stoq.application')
_ = gettext.gettext


class Statusbar(gtk.Statusbar):
    def __init__(self, app):
        gtk.Statusbar.__init__(self)
        self._disable_border()
        self.message_area = self._create_message_area()
        self._create_default_widgets()
        self.app = app

    def _disable_border(self):
        # Disable border on statusbar
        children = self.get_children()
        if children and isinstance(children[0], gtk.Frame):
            frame = children[0]
            frame.set_shadow_type(gtk.SHADOW_NONE)

    def _create_message_area(self):
        for child in self.get_children():
            child.hide()
        area = gtk.HBox(False, 4)
        self.add(area)
        area.show()
        return area

    def _create_default_widgets(self):
        alignment = gtk.Alignment(0.0, 0.0, 1.0, 1.0)
        # FIXME: These looks good on Mac, might need to tweak
        # on Linux to look good
        alignment.set_padding(2, 3, 5, 5)
        self.message_area.pack_start(alignment, True, True)
        alignment.show()

        widget_area = gtk.HBox(False, 0)
        alignment.add(widget_area)
        widget_area.show()

        self._text_label = gtk.Label()
        self._text_label.set_alignment(0.0, 0.5)
        widget_area.pack_start(self._text_label, True, True)
        self._text_label.show()

        vsep = gtk.VSeparator()
        widget_area.pack_start(vsep, False, False, 0)
        vsep.show()
        from stoqlib.gui.stockicons import STOQ_FEEDBACK
        self._feedback_button = gtk.Button(_('Feedback'))
        image = gtk.Image()
        image.set_from_stock(STOQ_FEEDBACK, gtk.ICON_SIZE_MENU)
        self._feedback_button.set_image(image)
        image.show()
        self._feedback_button.set_can_focus(False)
        self._feedback_button.connect('clicked',
          self._on_feedback__clicked)
        self._feedback_button.set_relief(gtk.RELIEF_NONE)
        widget_area.pack_start(self._feedback_button, False, False, 0)
        self._feedback_button.show()

        vsep = gtk.VSeparator()
        widget_area.pack_start(vsep, False, False, 0)
        vsep.show()

    def do_text_popped(self, ctx, text):
        self._text_label.set_label(text)

    def do_text_pushed(self, ctx, text):
        self._text_label.set_label(text)

    #
    # Callbacks
    #

    def _on_feedback__clicked(self, button):
        if self.app.current_app:
            screen = self.app.current_app.app.name + ' application'
        else:
            screen = 'launcher'
        run_dialog(FeedbackDialog, self.get_toplevel(), screen)

gobject.type_register(Statusbar)


class App(object):
    """Class for application control. """

    def __init__(self, window_class, config, options, shell, embedded,
                 launcher, name):
        """
        Create a new object App.
        @param main_window_class: A eAppWindow subclass
        """
        if not issubclass(window_class, AppWindow):
            raise TypeError
        self.config = config
        self.options = options
        self.shell = shell
        self.window_class = window_class
        self.embedded = embedded
        self.launcher = launcher
        self.name = name

        # The self should be passed to main_window to let it access
        # shutdown and do_sync methods.
        self.main_window = window_class(self)

    def show(self, params=None):
        if self.embedded:
            win = self.main_window.get_toplevel()
            self.launcher.show_app(self.main_window, win.get_child(), params)
            win.hide()
        else:
            self.main_window.show()

    def run(self, params=None):
        self.show(params)

    def hide(self):
        self.main_window.hide()


class AppWindow(GladeDelegate):
    """ Class for the main window of applications.

    @cvar app_name: This attribute is used when generating titles for
                    applications.  It's also useful if we get a list of
                    available applications with the application names
                    translated. This list is going to be used when
                    creating new user profiles.

    """

    app_windows = []
    app_name = None
    search = None
    gladefile = toplevel_name = ''
    title = ''
    size = ()

    def __init__(self, app, keyactions=None):
        self._action_groups = {}
        self._osx_app = None
        self._sensitive_group = dict()
        self._tool_items = []
        self.app = app
        self.conn = api.get_connection()
        self.current_app = None
        self.current_app_widget = None
        self.uimanager = None
        self.accel_group = None

        self._pre_init()
        GladeDelegate.__init__(self,
                               keyactions=keyactions,
                               gladefile=self.gladefile,
                               toplevel_name=self.toplevel_name)
        self._post_init()

    def _pre_init(self):
        if platform.system() == 'Darwin':
            import gtk_osxapplication
            self._osx_app = gtk_osxapplication.OSXApplication()
            self._osx_app.connect(
                'NSApplicationBlockTermination',
                self._on_osx__block_termination)
            self._osx_app.set_use_quartz_accelerators(True)
        api.user_settings.migrate()
        self.uimanager = self._create_ui_manager()
        self.accel_group = self.uimanager.get_accel_group()
        self._app_settings = api.user_settings.get('app-ui', {})
        self._create_ui_manager_ui()

    def _post_init(self):
        self._configure_toplevel()
        self._create_shared_ui()
        self.create_ui()
        self._ui_bootstrap()
        if self._osx_app:
            self._osx_setup_menus()

    def _osx_setup_menus(self):
        if self.app.name != 'launcher':
            return
        self.Quit.set_visible(False)
        self.HelpAbout.set_visible(False)
        self.HelpAbout.set_label(_('About Stoq'))
        self._osx_app.set_help_menu(
             self.HelpMenu.get_proxies()[0])
        self._osx_app.insert_app_menu_item(
             self.HelpAbout.get_proxies()[0], 0)
        self._osx_app.insert_app_menu_item(
             gtk.SeparatorMenuItem(), 1)
        self.Preferences.set_visible(False)
        self._osx_app.insert_app_menu_item(
             self.Preferences.get_proxies()[0], 2)
        self._osx_app.ready()

    def _create_ui_manager(self):
        if self.app.embedded:
            uimanager = self.app.launcher.uimanager
        else:
            uimanager = gtk.UIManager()
        return uimanager

    def _create_ui_manager_ui(self):
        # Create actions, this must be done before the constructor
        # is called, eg when signals are autoconnected
        self._create_shared_actions()
        self.create_actions()
        if self.app.options.debug:
            self.add_debug_ui()

    def _configure_toplevel(self):
        toplevel = self.get_toplevel()
        toplevel.connect('delete-event', self._on_toplevel__delete_event)
        toplevel.connect('configure-event', self._on_toplevel__configure)
        if self.size:
            toplevel.set_size_request(*self.size)
        toplevel.set_title(self.get_title())

        if not self.app.embedded:
            toplevel.add_accel_group(self.uimanager.get_accel_group())

    def _ui_bootstrap(self):
        if self.app.name != 'launcher':
            return

        hide_splash()
        AppWindow.app_windows.append(self)
        self._restore_window_size()
        self.hide_app()

        self._check_demo_mode()
        self._check_version()
        self._update_toolbar_style()

        if not stoq.stable and not api.is_developer_mode():
            self._display_unstable_version_message()

        # Initial fullscreen state for launcher must be handled
        # separate since the window is not realized when the state loading
        # is run in hide_app() the first time.
        window = self.get_toplevel()
        window.realize()
        self.ToggleFullscreen.set_active(
            self._app_settings.get('show-fullscreen', False))
        self.ToggleFullscreen.notify('active')

    def _create_shared_actions(self):
        if self.app.name != 'launcher':
            return
        group = get_accels('app.common')
        actions = [
            ('menubar', ),
            ('toolbar', ),

            # Menus
            ('FileMenu', None, _("_File")),
            ('FileMenuNew', None),
            ("NewMenu", None, _("New")),

            ('NewWindow', None, _("_Window"),
             group.get('new_window'),
            _('Opens up a new window')),
            ('Close', None, _('Close'),
             group.get('close_window'),
            _('Close the current view and go back to the initial screen')),
            ('ChangePassword', None, _('Change password...'),
             group.get('change_password'),
            _('Change the password for the currently logged in user')),
            ('SignOut', None, _('Sign out...'),
             group.get('sign_out'),
            _('Sign out the currently logged in user and login as another')),
            ('Print', gtk.STOCK_PRINT, _("Print..."),
             group.get('print')),
            ('ExportSpreadSheet', gtk.STOCK_SAVE_AS, _('Export to spreadsheet...')),
            ("Quit", gtk.STOCK_QUIT, _('Quit'),
             group.get('quit'),
             _('Exit the application')),

            # Edit
            ('EditMenu', None, _("_Edit")),
            ('Preferences', None, _("_Preferences"),
             group.get('preferences'),
             _('Show preferences')),

            # View
            ('ViewMenu', None, _("_View")),

            # Search
            ('SearchMenu', None, _("_Search")),

            # Help
            ("HelpMenu", None, _("_Help")),
            ("HelpContents", gtk.STOCK_HELP, _("Contents"),
             group.get('help_contents')),
            ("HelpTranslate", None, _("Translate Stoq..."), None,
             _("Translate this application online")),
            ("HelpSupport", None, _("Get support online..."), None,
             _("Get support for Stoq online")),
            ("HelpChat", None, _("Online chat..."), None,
             _("Talk about Stoq online")),
            ("HelpAbout", gtk.STOCK_ABOUT),

            # Toolbar
            ("NewToolMenu", None, _("New")),
            ("SearchToolMenu", None, _("Search")),
            ]
        self.add_ui_actions(None, actions, filename='launcher.xml')
        self.Close.set_sensitive(False)
        toggle_actions = [
            ('ToggleToolbar', None, _("_Toolbar"),
             group.get('toggle_toolbar'),
             _('Show or hide the toolbar')),
            ('ToggleStatusbar', None, _("_Statusbar"),
             group.get('toggle_statusbar'),
             _('Show or hide the statusbar')),
            ('ToggleFullscreen', None, _("_Fullscreen"),
             group.get('toggle_fullscreen'),
             _('Enter or leave fullscreen mode')),
            ]
        self.add_ui_actions('', toggle_actions, 'ToggleActions',
                            'toggle')

        self.Print.set_short_label(_("Print"))
        self.add_tool_menu_actions([
            ("NewToolItem", _("New"), '', gtk.STOCK_NEW),
            ("SearchToolItem", _("Search"), None, gtk.STOCK_FIND),
            ])
        self.NewToolItem.props.is_important = True
        self.SearchToolItem.props.is_important = True

    def _create_shared_ui(self):
        if self.app.name != 'launcher':
            return
        self.uimanager.connect('connect-proxy',
            self._on_uimanager__connect_proxy)
        self.uimanager.connect('disconnect-proxy',
            self._on_uimanager__disconnect_proxy)

        self.ToggleToolbar.connect(
            'notify::active', self._on_ToggleToolbar__notify_active)
        self.ToggleStatusbar.connect(
            'notify::active', self._on_ToggleStatusbar__notify_active)
        self.ToggleFullscreen.connect(
            'notify::active', self._on_ToggleFullscreen__notify_active)

        self.NewToolItem.connect(
            'activate', self._on_NewToolItem__activate)
        self.SearchToolItem.connect(
            'activate', self._on_SearchToolItem__activate)
        self.NewWindow.connect(
            'activate', self._on_NewWindow__activate)
        self.Close.connect(
            'activate', self._on_Close__activate)
        self.ChangePassword.connect(
            'activate', self._on_ChangePassword__activate)
        self.SignOut.connect(
            'activate', self._on_SignOut__activate)
        self.Print.connect(
            'activate', self._on_Print__activate)
        self.ExportSpreadSheet.connect(
            'activate', self._on_ExportSpreadSheet__activate)
        self.Quit.connect(
            'activate', self._on_Quit__activate)

        self.Preferences.connect(
            'activate', self._on_Preferences__activate)
        self.HelpContents.connect(
            'activate', self._on_HelpContents__activate)
        self.HelpTranslate.connect(
            'activate', self._on_HelpTranslate__activate)
        self.HelpSupport.connect(
            'activate', self._on_HelpSupport__activate)
        self.HelpChat.connect(
            'activate', self._on_HelpChat__activate)
        self.HelpAbout.connect(
            'activate', self._on_HelpAbout__activate)

        menubar = self.uimanager.get_widget('/menubar')
        if self._osx_app:
            self._osx_app.set_menu_bar(menubar)
        else:
            self.main_vbox.pack_start(menubar, False, False)
            self.main_vbox.reorder_child(menubar, 0)

        toolbar = self.uimanager.get_widget('/toolbar')
        self.main_vbox.pack_start(toolbar, False, False)
        self.main_vbox.reorder_child(toolbar, len(self.main_vbox) - 3)

        self.statusbar = self._create_statusbar()
        self.main_vbox.pack_start(self.statusbar, False, False)
        self.main_vbox.reorder_child(self.statusbar, len(self.main_vbox) - 1)

        menu_tool_button = self.SearchToolItem.get_proxies()[0]
        # This happens when we couldn't set the GType of ToolMenuAction
        # properly
        if not hasattr(menu_tool_button, 'get_menu'):
            return
        search_tool_menu = menu_tool_button.get_menu()
        # FIXME: For some reason, without this hack, some apps like Stock and
        #        Purchase shows an extra search tool menu labeled 'empty'
        for child in search_tool_menu.get_children():
            search_tool_menu.remove(child)

    def _get_action_group(self, name):
        action_group = self.app.launcher._action_groups.get(name)
        if action_group is None:
            action_group = gtk.ActionGroup(name)
            self.uimanager.insert_action_group(action_group, 0)
            self.app.launcher._action_groups[name] = action_group
        return action_group

    def _display_unstable_version_message(self):
        msg = _(
            'You are currently using an <b>unstable version</b> of Stoq that '
            'is under development,\nbe aware that it may behave incorrectly, '
            'crash or even loose your data.\n<b>Do not use in production.</b>')
        self.add_info_bar(gtk.MESSAGE_WARNING, msg)

    def _display_open_inventory_message(self):
        msg = _(u'There is an inventory process open at the moment.\n'
                'While that inventory is open, you will be unable to do '
                'operations that modify your stock.')
        self.inventory_bar = self.add_info_bar(gtk.MESSAGE_WARNING, msg)

    def _check_demo_mode(self):
        if not api.sysparam(self.conn).DEMO_MODE:
            return

        if api.user_settings.get('hide-demo-warning'):
            return

        button_label = _('Enable production mode')
        title = _('You are using Stoq in demonstration mode.')
        desc = (_("Some features are limited due to fiscal reasons. "
                  "Click on '%s' to remove the limitations and finish the demonstration.")
                % button_label)
        msg = '<b>%s</b>\n%s' % (title, desc)

        button = gtk.Button(button_label)
        button.connect('clicked', self._on_enable_production__clicked)
        self.add_info_bar(gtk.MESSAGE_WARNING, msg, action_widget=button)

    def _check_version(self):
        if not api.sysparam(self.conn).ONLINE_SERVICES:
            return
        self._version_checker = VersionChecker(self.conn, self)
        self._version_checker.check_new_version()

    def _read_resource(self, domain, name):
        try:
            data = environ.get_resource_string('stoq', domain, name)
            if data:
                return data
        except EnvironmentError:
            pass

        import gzip
        license = environ.find_resource(domain, name + '.gz')
        return gzip.GzipFile(license).read()

    def _run_about(self):
        info = get_utility(IAppInfo)
        about = gtk.AboutDialog()
        about.set_name(info.get("name"))
        about.set_version(info.get("version"))
        about.set_website(stoq.website)
        release_date = stoq.release_date
        about.set_comments(_('Release date: %s') %
                           datetime.datetime(*release_date).strftime('%x'))
        about.set_copyright('Copyright (C) 2005-2012 Async Open Source')

        about.set_logo(render_logo_pixbuf('about'))

        # License

        if locale.getlocale()[0] == 'pt_BR':
            filename = 'COPYING.pt_BR'
        else:
            filename = 'COPYING'
        data = self._read_resource('docs', filename)
        about.set_license(data)

        # Authors & Contributors
        data = self._read_resource('docs', 'AUTHORS')
        lines = data.split('\n')
        lines.append('') # separate authors from contributors
        data = self._read_resource('docs', 'CONTRIBUTORS')
        lines.extend([c.strip() for c in data.split('\n')])
        about.set_authors(lines)

        about.run()
        about.destroy()

    def _show_uri(self, uri):
        toplevel = self.get_toplevel()
        open_browser(uri, toplevel.get_screen())

    def _new_window(self):
        self.app.shell.run()

    def _restore_window_size(self):
        d = api.user_settings.get('launcher-geometry', {})
        try:
            width = int(d.get('width', -1))
            height = int(d.get('height', -1))
            x = int(d.get('x', -1))
            y = int(d.get('y', -1))
        except ValueError:
            pass
        toplevel = self.get_toplevel()
        toplevel.set_default_size(width, height)
        if x != -1 and y != -1:
            toplevel.move(x, y)

    def _save_launcher_window_size(self):
        if not hasattr(self, '_width'):
            return
        # Do not save the size of the window when we are in fullscreen
        window = self.get_toplevel()
        window = window.get_window()
        if window.get_state() & gtk.gdk.WINDOW_STATE_FULLSCREEN:
            return
        d = api.user_settings.get('launcher-geometry', {})
        d['width'] = str(self._width)
        d['height'] = str(self._height)
        d['x'] = str(self._x)
        d['y'] = str(self._y)

    def _create_statusbar(self):
        statusbar = Statusbar(self)

        # Set the initial text, the currently logged in user and the actual
        # branch and station.
        user = api.get_current_user(self.conn)
        station = api.get_current_station(self.conn)
        status_str = '   |   '.join([
            _("User: %s") % (user.get_description(),),
            _("Computer: %s") % (station.name,)
            ])
        statusbar.push(0, status_str)
        return statusbar

    def _empty_message_area(self):
        area = self.get_statusbar_message_area()
        for child in area.get_children()[1:]:
            child.destroy()

    def _update_toggle_actions(self, app_name):
        self._current_app_settings = d = self._app_settings.setdefault(app_name, {})
        self.ToggleToolbar.set_active(d.get('show-toolbar', True))
        self.ToggleStatusbar.set_active(d.get('show-statusbar', True))
        self.ToggleToolbar.notify('active')
        self.ToggleStatusbar.notify('active')

    def _update_toolbar_style(self):
        toolbar = self.uimanager.get_widget('/toolbar')
        if not toolbar:
            return

        style_map = {'icons': gtk.TOOLBAR_ICONS,
                     'text': gtk.TOOLBAR_TEXT,
                     'both': gtk.TOOLBAR_BOTH,
                     'both-horizontal': gtk.TOOLBAR_BOTH_HORIZ}
        # We set both horizontal as default to improve usability,
        # it's easier for the user to know what some of the buttons
        # in the toolbar does by having a label next to it
        toolbar_style = api.user_settings.get('toolbar-style',
                                              'both-horizontal')
        value = style_map.get(toolbar_style)
        if value:
            toolbar.set_style(value)

    def _hide_current_application(self):
        if not self.current_app:
            return False

        if self.current_app.shutdown_application():
            self.hide_app()
        return True

    @api.async
    def _terminate(self, restart=False):
        log.info("Terminating Stoq")

        log.debug('Logging out the current user')
        try:
            user = api.get_current_user(api.get_connection())
            if user:
                user.logout()
        except StoqlibError:
            pass

        self._save_launcher_window_size()

        # Write user settings to disk, this obviously only happens on successful
        # terminations which is the right place to do
        log.debug("Flushing user settings")
        api.user_settings.flush()

        # This removes all temporary files created when calling
        # get_resource_filename() that extract files to the file system
        import pkg_resources
        pkg_resources.cleanup_resources()

        log.debug('Stopping deamon')
        from stoqlib.lib.daemonutils import stop_daemon
        stop_daemon()

        # Finally, go out of the reactor and show possible crash reports
        yield self._quit_reactor_and_maybe_show_crashreports()

        if restart:
            from stoqlib.lib.process import Process
            log.info('Restarting Stoq')
            Process([sys.argv[0]], shell=True)

        # os._exit() forces a quit without running atexit handlers
        # and does not block on any running threads
        # FIXME: This is the wrong solution, we should figure out why there
        #        are any running threads/processes at this point
        log.debug("Terminating by calling os._exit()")
        os._exit(0)

        raise AssertionError("Should never happen")

    def _show_crash_reports(self):
        if not has_tracebacks():
            return succeed(None)
        if 'STOQ_DISABLE_CRASHREPORT' in os.environ:
            return succeed(None)
        return show_dialog()

    @api.async
    def _quit_reactor_and_maybe_show_crashreports(self):
        log.debug("Show some crash reports")
        yield self._show_crash_reports()
        log.debug("Shutdown reactor")
        reactor.stop()

    #
    # Overridables
    #

    def create_actions(self):
        """This is called before the BaseWindow constructor, so we
        can create actions that can be autoconnected.
        The widgets and actions loaded from builder files are not set
        yet"""

    def create_ui(self):
        """This is called when the UI such as GtkWidgets should be
        created. Glade widgets are now created and can be accessed
        in the instance.
        """

    def activate(self, params):
        """This is when you switch to an application.
        You should setup widget sensitivity here and refresh lists etc
        @params: an dictionary with optional parameters.
        """

    def setup_focus(self):
        """Define this method on child when it's needed.
        This is for calling grab_focus(), it's called after the window
        is shown. focus chains should be created in create_ui()"""

    def get_title(self):
        # This method must be redefined in child when it's needed
        branch = api.get_current_branch(self.conn)
        return _('[%s] - %s') % (branch.get_description(), self.app_name)

    def can_change_application(self):
        """Define if we can change the current application or not.

        @returns: True if we can change the application, False otherwise.
        """
        return True

    def can_close_application(self):
        """Define if we can close the current application or not.

        @returns: True if we can close the application, False otherwise.
        """
        return True

    def set_open_inventory(self):
        """ Subclasses should overide this if they call
        check_open_inventory.

        This method will be called it there is an open inventory, so the
        application can disable some funcionalities
        """
        raise NotImplementedError

    def new_activate(self):
        """Called when the New toolbar item is activated"""
        raise NotImplementedError

    def search_activate(self):
        """Called when the Search toolbar item is activated"""
        raise NotImplementedError

    def print_activate(self):
        """Called when the Print toolbar item is activated"""
        raise NotImplementedError

    def export_spreadsheet_activate(self):
        """Called when the Export menu item is activated"""
        raise NotImplementedError

    #
    # Public API
    #

    def get_statusbar_message_area(self):
        return self.app.launcher.statusbar.message_area

    def print_report(self, report_class, *args, **kwargs):
        filters = self.search.get_search_filters()
        if filters:
            kwargs['filters'] = filters

        print_report(report_class, *args, **kwargs)

    def set_sensitive(self, widgets, value):
        """Set the C{widgets} sensitivity based on C{value}

        @note: if a sensitive group was registered for any widget,
            it's validation function will be tested and, if C{False}
            is returned, it will be set insensitive, ignoring C{value}

        @param widgets: a :class:`list` of widgets
        @param value: either C{True} or C{False}
        """
        # FIXME: Maybe this should ne done on kiwi?
        for widget in widgets:
            sensitive = value

            for validator in self._sensitive_group.get(widget, []):
                if not validator[0](*validator[1]):
                    sensitive = False
                    break

            widget.set_sensitive(sensitive)

    def register_sensitive_group(self, widgets, validation_func, *args):
        """Register widgets on a sensitive group.

        Everytime self.set_sensitive() is called, if there is any
        validation function for a given widget on sensitive group,
        then that will be used to decide if it gets sensitive or
        insensitive.

        @param widgets: a :class:`list` of widgets
        @param validation_func: a function for validation. It should
            return either C{True} or C{False}.
        @param args: args that will be passed to C{validation_func}
        """
        assert callable(validation_func)

        for widget in widgets:
            validators = self._sensitive_group.setdefault(widget, set())
            validators.add((validation_func, args))

    def get_dialog(self, dialog_class, *args, **kwargs):
        """ Encapsuled method for getting dialogs. """
        return get_dialog(self, dialog_class, *args, **kwargs)

    def run_dialog(self, dialog_class, *args, **kwargs):
        """ Encapsuled method for running dialogs. """
        return run_dialog(dialog_class, self, *args, **kwargs)

    def add_ui_actions(self, ui_string, actions, name='Actions',
                       action_type='normal', filename=None):
        ag = self._get_action_group(name)

        to_add = [entry[0] for entry in actions]
        for action in ag.list_actions():
            if action.get_name() in to_add:
                ag.remove_action(action)

        if action_type == 'normal':
            ag.add_actions(actions)
        elif action_type == 'toggle':
            ag.add_toggle_actions(actions)
        elif action_type == 'radio':
            ag.add_radio_actions(actions)
        else:
            raise ValueError(action_type)
        if filename is not None:
            ui_string = environ.get_resource_string('stoq', 'uixml', filename)
        ui_id = self.uimanager.add_ui_from_string(ui_string)
        for action in ag.list_actions():
            setattr(self, action.get_name(), action)
        return ui_id

    def add_tool_menu_actions(self, actions):
        group = self._get_action_group("ToolMenuGroup")
        for name, label, tooltip, stock_id in actions:
            action = ToolMenuAction(name=name,
                                    label=label,
                                    tooltip=tooltip,
                                    stock_id=stock_id)
            group.add_action(action)
            setattr(self, action.get_name(), action)

    def set_help_section(self, label, section):
        def on_HelpHelp__activate(action):
            show_section(section)

        ui_string = """<ui>
        <menubar action="menubar">
          <menu action="HelpMenu">
            <placeholder name="HelpPH">
              <menuitem action="HelpHelp"/>
            </placeholder>
          </menu>
        </menubar>
        </ui>"""
        help_help_actions = [
            ("HelpHelp", None, label,
             get_accel('app.common.help'),
             _("Show help for this application"),
             on_HelpHelp__activate),
            ]
        self.help_ui = self.add_ui_actions(
            ui_string,
            help_help_actions, 'HelpHelpActions')

    def add_debug_ui(self):
        ui_string = """<ui>
          <menubar name="menubar">
            <menu action="DebugMenu">
              <menuitem action="Introspect"/>
              <menuitem action="RemoveSettingsCache"/>
            </menu>
          </menubar>
        </ui>"""
        actions = [
            ('DebugMenu', None, _('Debug')),
            ('Introspect', None, _('Introspect slaves'),
             None, None, self._on_Introspect_activate),
            ('RemoveSettingsCache', None, _('Remove settings cache'),
             None, None, self._on_RemoveSettingsCache_activate),
            ]

        self.add_ui_actions(ui_string, actions, 'DebugActions')

    def has_open_inventory(self, from_cache=True):
        return Inventory.has_open(self.conn,
                                  api.get_current_branch(self.conn))

    def check_open_inventory(self):
        """Checks if there is an open inventory.

        In the case there is one, will call set_open_inventory (subclasses
        should implement it).

        Returns True if there is an open inventory. False otherwise
        """
        inventory_bar = getattr(self, 'inventory_bar', None)

        if self.has_open_inventory():
            if inventory_bar:
                inventory_bar.show()
            else:
                self._display_open_inventory_message()
            self.set_open_inventory()
            return True
        elif inventory_bar:
            inventory_bar.hide()
            return False

    def add_info_bar(self, message_type, label, action_widget=None):
        """Show an information bar to the user.
        @param message_type: message type, a gtk.MessageType
        @param label: label to display
        @param action_widget: optional, most likely a button
        @returns: the infobar
        """
        label = gtk.Label(label)
        label.set_use_markup(True)
        label.set_line_wrap(True)
        label.set_width_chars(100)
        label.set_alignment(0, 0)
        label.set_padding(12, 0)
        label.show()

        bar = InfoBar()
        bar.get_content_area().add(label)
        if action_widget:
            bar.add_action_widget(action_widget, 0)
            action_widget.show()
        bar.set_message_type(message_type)
        bar.show()

        self.main_vbox.pack_start(bar, False, False, 0)
        # 0 = menubar, 1 = toolbar, 2 is above iconview
        self.main_vbox.reorder_child(bar, 2)

        return bar

    def add_new_items(self, actions):
        self._tool_items.extend(
            self.NewToolItem.add_actions(self.uimanager, actions))

    def add_search_items(self, actions):
        self._tool_items.extend(
            self.SearchToolItem.add_actions(self.uimanager, actions))

    def set_new_menu_sensitive(self, sensitive):
        new_item = self.NewToolItem.get_proxies()[0]
        button = new_item.get_children()[0].get_children()[0]
        button.set_sensitive(sensitive)

    def show_app(self, app, app_window, params=None):
        app_window.reparent(self.application_box)
        self.application_box.set_child_packing(app_window, True, True, 0,
                                               gtk.PACK_START)
        self.Close.set_sensitive(True)
        self.ChangePassword.set_visible(False)
        self.SignOut.set_visible(False)
        self.Print.set_visible(True)
        self.Print.set_sensitive(False)
        self.ExportSpreadSheet.set_visible(True)
        self.ExportSpreadSheet.set_sensitive(False)
        self.Quit.set_visible(False)
        self.NewToolItem.set_tooltip("")
        self.NewToolItem.set_sensitive(True)
        self.SearchToolItem.set_tooltip("")
        self.SearchToolItem.set_sensitive(True)

        self._update_toggle_actions(app.app.name)

        self.get_toplevel().set_title(app.get_title())
        self.application_box.show()
        app.activate(params or {})

        self.uimanager.ensure_update()
        while gtk.events_pending():
            gtk.main_iteration()
        app_window.show()
        app.toplevel = self.get_toplevel()
        app.setup_focus()

        self.current_app = app
        self.current_widget = app_window

    def hide_app(self):
        self.application_box.hide()
        if self.current_app:
            if self.current_app.search:
                self.current_app.search.save_columns()
            self.current_app.deactivate()
            if self.current_app.help_ui:
                self.uimanager.remove_ui(self.current_app.help_ui)
                self.current_app.help_ui = None
            self.current_widget.destroy()

            app = self.current_app.app
            StopApplicationEvent.emit(app.name, app)
            self.current_app = None

        self.get_toplevel().set_title(self.get_title())
        self._empty_message_area()
        for item in self._tool_items:
            item.destroy()
        self._tool_items = []
        self.Close.set_sensitive(False)
        self.ChangePassword.set_visible(True)
        self.SignOut.set_visible(True)
        if not self._osx_app:
            self.Quit.set_visible(True)
        self.Print.set_sensitive(False)
        self.Print.set_visible(False)
        self.ExportSpreadSheet.set_visible(False)
        self.ExportSpreadSheet.set_sensitive(False)
        self.set_new_menu_sensitive(True)
        self.NewToolItem.set_tooltip(_("Open a new window"))
        self.SearchToolItem.set_tooltip("")
        self.SearchToolItem.set_sensitive(False)
        self._update_toggle_actions('launcher')

    #
    # AppWindow
    #

    def shutdown_application(self, restart=False):
        """Shutdown the application:
        There are 3 possible outcomes of calling this function, depending
        on how many windows and applications are open:
          - Hide application, save state, show launcher
          - Close window, save state, show launcher
          - Close window, save global state, terminate application

        This function is called in the following situations:
          - When closing a window (delete-event)
          - When clicking File->Close in an application
          - When clicking File->Quit in the launcher
          - When clicking enable production mode (restart=True)
          - Pressing Ctrl-w/F5 in an application
          - Pressing Ctrl-q in the launcher
          - Pressing Alt-F4 on Win32
          - Pressing Cmd-q on Mac

        :returns: True if shutdown was successful, False if not
        """

        if self.app.name == 'launcher':
            log.debug("Shutting down launcher")
        else:
            log.debug("Shutting down application %s" % (self.app.name, ))

        # Ask the application if we can close, currently this only happens
        # when trying to close the POS app if there's a sale in progress
        if not self.can_close_application():
            return False

        # Here we save app specific state such as object list
        # column position/ordering
        if self.current_app and self.current_app.search:
            self.current_app.search.save_columns()

        # If there are other windows open, do not terminate the application, just
        # close the current window and leave the others alone
        if AppWindow.app_windows:
            return True

        # The rest of the code only applies when closing down the launcher,
        # eg terminating the application.
        if self.app.name != 'launcher':
            return True

        self._terminate(restart=restart)

    #
    # Callbacks
    #

    def key_F5(self):
        # Backwards-compatibility
        if self.current_app and self.current_app.can_change_application():
            self.hide_app()
        return True

    def _on_toplevel__configure(self, widget, event):
        window = widget.get_window()
        rect = window.get_frame_extents()
        self._x = rect.x
        self._y = rect.y
        self._width = event.width
        self._height = event.height

    def _on_toplevel__delete_event(self, *args):
        if self._hide_current_application():
            return True

        AppWindow.app_windows.remove(self)
        self.shutdown_application()

    def _on_menu_item__select(self, menuitem, tooltip):
        self.statusbar.push(0xff, tooltip)

    def _on_menu_item__deselect(self, menuitem):
        self.statusbar.pop(0xff)

    def _on_tool_item__enter_notify_event(self, toolitem, event, tooltip):
        self.statusbar.push(0xff, tooltip)

    def _on_tool_item__leave_notify_event(self, toolitem, event):
        self.statusbar.pop(0xff)

    def _on_uimanager__connect_proxy(self, uimgr, action, widget):
        tooltip = action.get_tooltip()
        if not tooltip:
            return
        if isinstance(widget, gtk.MenuItem):
            widget.connect('select', self._on_menu_item__select, tooltip)
            widget.connect('deselect', self._on_menu_item__deselect)
        elif isinstance(widget, gtk.ToolItem):
            child = widget.get_child()
            if child is None:
                return
            child.connect('enter-notify-event',
                          self._on_tool_item__enter_notify_event, tooltip)
            child.connect('leave-notify-event',
                          self._on_tool_item__leave_notify_event)

    def _on_uimanager__disconnect_proxy(self, uimgr, action, widget):
        tooltip = action.get_tooltip()
        if not tooltip:
            return
        if isinstance(widget, gtk.MenuItem):
            try:
                widget.disconnect_by_func(self._on_menu_item__select)
                widget.disconnect_by_func(self._on_menu_item__deselect)
            except TypeError:
                # Maybe it was already disconnected
                pass
        elif isinstance(widget, gtk.ToolItem):
            child = widget.get_child()
            try:
                child.disconnect_by_func(
                    self._on_tool_item__enter_notify_event)
                child.disconnect_by_func(
                    self._on_tool_item__leave_notify_event)
            except TypeError:
                pass

    def _on_osx__block_termination(self, app):
        return not self.shutdown_application()

    # File

    def _on_NewToolItem__activate(self, action):
        if self.current_app:
            self.current_app.new_activate()
        else:
            self._new_window()

    def _on_SearchToolItem__activate(self, action):
        if self.current_app:
            self.current_app.search_activate()
        else:
            print 'FIXME'

    def _on_NewWindow__activate(self, action):
        self._new_window()

    def _on_Print__activate(self, action):
        if self.current_app:
            self.current_app.print_activate()

    def _on_ExportSpreadSheet__activate(self, action):
        if self.current_app:
            self.current_app.export_spreadsheet_activate()

    def _on_Close__activate(self, action):
        self._hide_current_application()

    def _on_ChangePassword__activate(self, action):
        from stoqlib.gui.slaves.userslave import PasswordEditor
        trans = api.new_transaction()
        user = api.get_current_user(trans)
        retval = self.run_dialog(PasswordEditor, trans, user)
        api.finish_transaction(trans, retval)

    def _on_SignOut__activate(self, action):
        from stoqlib.lib.interfaces import ICookieFile
        get_utility(ICookieFile).clear()
        self.get_toplevel().hide()
        self.app.shell.relogin()

    def _on_Quit__activate(self, action):
        if self._hide_current_application():
            return

        AppWindow.app_windows.remove(self)
        self.shutdown_application()
        self.get_toplevel().destroy()

    # View

    def _on_Preferences__activate(self, action):
        with api.trans() as trans:
            self.run_dialog(PreferencesEditor, trans)
        self._update_toolbar_style()

    # Edit

    def _on_ToggleToolbar__notify_active(self, action, pspec):
        toolbar = self.uimanager.get_widget('/toolbar')
        toolbar.set_visible(action.get_active())
        self._current_app_settings['show-toolbar'] = action.get_active()

    def _on_ToggleStatusbar__notify_active(self, action, pspec):
        self.statusbar.set_visible(action.get_active())
        self._current_app_settings['show-statusbar'] = action.get_active()

    def _on_ToggleFullscreen__notify_active(self, action, spec):
        window = self.get_toplevel()
        if not window.get_realized():
            return
        is_active = action.get_active()
        window = window.get_window()
        is_fullscreen = window.get_state() & gtk.gdk.WINDOW_STATE_FULLSCREEN
        if is_active != is_fullscreen:
            if is_active:
                window.fullscreen()
            else:
                window.unfullscreen()

        # This is shared between apps, since it's weird to change fullscreen
        # between applications
        self._app_settings['show-fullscreen'] = is_active

    # Help

    def _on_HelpContents__activate(self, action):
        show_contents()

    def _on_HelpTranslate__activate(self, action):
        self._show_uri("https://translations.launchpad.net/stoq")

    def _on_HelpChat__activate(self, action):
        self._show_uri("http://chat.stoq.com.br/")

    def _on_HelpSupport__activate(self, action):
        self._show_uri("http://www.stoq.com.br/suporte")

    def _on_HelpAbout__activate(self, action):
        self._run_about()

    # Debug

    def _on_Introspect_activate(self, action):
        window = self.get_toplevel()
        introspect_slaves(window)

    def _on_RemoveSettingsCache_activate(self, action):
        keys = ['app-ui', 'launcher-geometry']
        keys.append('search-columns-%s' % (
            api.get_current_user(api.get_connection()).username, ))

        for key in keys:
            try:
                api.user_settings.remove(key)
            except KeyError:
                pass

    def _on_enable_production__clicked(self, button):
        if not self.can_close_application():
            return
        if yesno(_("This will enable production mode and finish the demonstration. "
                   "Are you sure?"),
                 gtk.RESPONSE_NO,
                 _("Continue testing"),
                 _("Enable production mode")):
            return

        api.config.set('Database', 'enable_production', 'True')
        api.config.flush()
        AppWindow.app_windows.remove(self)
        self.shutdown_application(restart=True)


class SearchableAppWindow(AppWindow):
    """
    Base class for applications which main interface consists of a list

    @cvar search_table: The we will query on to perform the search
    @cvar search_label: Label left of the search entry
    @cvar report_table: the report class for printing the object list
        embedded on app.
    """

    search_table = None
    search_label = _('Search:')
    report_table = None

    def __init__(self, app):
        if self.search_table is None:
            raise TypeError("%r must define a search_table attribute" % self)

        self._loading_filters = False

        self.executer = ORMObjectQueryExecuter(api.get_connection())
        self.executer.set_table(self.search_table)

        self.search = StoqlibSearchSlaveDelegate(self.get_columns(),
                                     restore_name=self.__class__.__name__)
        self.search.enable_advanced_search()
        self.search.set_query_executer(self.executer)
        self.search.search.connect("search-completed",
                                   self._on_search__search_completed)
        self.results = self.search.search.results
        self.set_text_field_label(self.search_label)

        AppWindow.__init__(self, app)
        self.attach_slave('search_holder', self.search)

        self.create_filters()
        self._restore_filter_settings()

        self.search.focus_search_entry()

    def _save_filter_settings(self):
        if self._loading_filters:
            return
        filter_states = self.search.search.get_filter_states()
        settings = self._app_settings.setdefault(self.app.name, {})
        settings['filter-states'] = filter_states

    def _restore_filter_settings(self):
        self._loading_filters = True
        settings = self._app_settings.setdefault(self.app.name, {})
        filter_states = settings.get('filter-states')
        if filter_states is not None:
            self.search.search.set_filter_states(filter_states)
        self._loading_filters = False

    #
    # AppWindow hooks
    #

    def print_activate(self):
        if self.results.get_selection_mode() == gtk.SELECTION_MULTIPLE:
            results = self.results.get_selected_rows()
        else:
            result = self.results.get_selected()
            results = [result] if result else None
        results = results or list(self.results)

        self.print_report(self.report_table, self.results, results,
                          do_footer=False)

    def export_spreadsheet_activate(self):
        self.export_spread_sheet()

    #
    # Public API
    #

    def set_searchtable(self, search_table):
        """
        @param search_table:
        """
        self.executer.set_table(search_table)
        self.search_table = search_table

    def add_filter(self, search_filter, position=SearchFilterPosition.BOTTOM,
                   columns=None, callback=None):
        """
        See :class:`SearchSlaveDelegate.add_filter`
        """
        self.search.add_filter(search_filter, position, columns, callback)

    def set_text_field_columns(self, columns):
        """
        See :class:`SearchSlaveDelegate.set_text_field_columns`
        """
        self.search.set_text_field_columns(columns)

    def set_text_field_label(self, label):
        """
        @param label:
        """
        search_filter = self.search.get_primary_filter()
        search_filter.set_label(label)

    def disable_search_entry(self):
        self.search.disable_search_entry()

    def refresh(self):
        """
        See :class:`kiwi.ui.search.SearchSlaveDelegate.refresh`
        """
        self.search.refresh()

    def clear(self):
        """
        See :class:`kiwi.ui.search.SearchSlaveDelegate.clear`
        """
        self.search.clear()

    def export_spread_sheet(self):
        """Runs a dialog to export the current search results to a CSV file.
        """
        self.run_dialog(SpreadSheetExporterDialog,
                        object_list=self.results,
                        name=self.app_name,
                        filename_prefix=self.app.name)

    def select_result(self, result):
        """Select the object in the result list

        If the object is not in the list (filtered out, for instance), no error
        is thrown and nothing is selected
        """
        try:
            self.results.select(result)
        except ValueError:
            pass

    def create_filters(self):
        pass

    def search_completed(self, results, states):
        pass

    #
    # Callbacks
    #

    def _on_search__search_completed(self, search, results, states):
        self.search_completed(results, states)

        has_results = len(results)
        for widget in [self.app.launcher.Print,
                       self.app.launcher.ExportSpreadSheet]:
            widget.set_sensitive(has_results)
        self._save_filter_settings()


class VersionChecker(object):
    DAYS_BETWEEN_CHECKS = 7

    #
    #   Private API
    #

    def __init__(self, conn, app):
        self.conn = conn
        self.app = app

    def _display_new_version_message(self, latest_version):
        # Only display version message in admin app
        if 'AdminApp' not in self.app.__class__.__name__:
            return
        button = gtk.LinkButton(
            'http://www.stoq.com.br/novidades',
            _(u'Learn More...'))
        msg = _('<b>There is a new Stoq version available (%s)</b>') % (
            latest_version, )
        self.app.add_info_bar(gtk.MESSAGE_INFO, msg, action_widget=button)

    def _check_details(self, latest_version):
        current_version = tuple(stoq.version.split('.'))
        if tuple(latest_version.split('.')) > current_version:
            self._display_new_version_message(latest_version)
        else:
            log.debug('Using latest version %r, not showing message' % (
                stoq.version, ))

    def _download_details(self):
        log.debug('Downloading new version information')
        api = WebService()
        response = api.version(self.conn, stoq.version)
        response.addCallback(self._on_response_done)

    def _on_response_done(self, details):
        self._check_details(details['version'])
        api.user_settings.set('last-version-check',
                              datetime.date.today().strftime('%Y-%m-%d'))
        api.user_settings.set('latest-version', details['version'])

    #
    #   Public API
    #

    def check_new_version(self):
        if api.is_developer_mode():
            return
        log.debug('Checking version')
        date = api.user_settings.get('last-version-check')
        if date:
            check_date = datetime.datetime.strptime(date, '%Y-%m-%d')
            diff = datetime.date.today() - check_date.date()
            if diff.days >= self.DAYS_BETWEEN_CHECKS:
                return self._download_details()
        else:
            return self._download_details()

        latest_version = api.user_settings.get('latest-version')
        if latest_version:
            self._check_details(latest_version)
