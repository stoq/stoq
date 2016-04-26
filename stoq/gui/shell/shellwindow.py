# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011-2013 Async Open Source <http://www.async.com.br>
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import datetime
import locale
import logging
import platform
import os
import operator

import gtk
import glib
from kiwi.component import get_utility
from kiwi.environ import environ
from kiwi.ui.delegates import GladeDelegate
from stoqlib.api import api
from stoqlib.domain.views import ClientWithSalesView
from stoqlib.gui.base.dialogs import (add_current_toplevel,
                                      get_current_toplevel,
                                      run_dialog)
from stoqlib.gui.base.messagebar import MessageBar
from stoqlib.gui.editors.preferenceseditor import PreferencesEditor
from stoqlib.gui.events import StartApplicationEvent, StopApplicationEvent
from stoqlib.gui.utils.help import show_contents, show_section
from stoqlib.gui.utils.introspection import introspect_slaves
from stoqlib.gui.utils.keybindings import get_accel, get_accels
from stoqlib.gui.utils.logo import render_logo_pixbuf
from stoqlib.gui.utils.openbrowser import open_browser
from stoqlib.lib.interfaces import IAppInfo, IApplicationDescriptions
from stoqlib.lib.message import error, yesno
from stoqlib.lib.permissions import PermissionManager
from stoqlib.lib.translation import (stoqlib_gettext, stoqlib_ngettext,
                                     locale_sorted)
from stoqlib.lib.webservice import WebService
from stoqlib.gui.widgets.toolmenuaction import ToolMenuAction
from stoq.gui.shell.statusbar import ShellStatusbar
from stoq.lib.applist import get_application_icon, Application
import stoq

_ = stoqlib_gettext
log = logging.getLogger(__name__)


class ShellWindow(GladeDelegate):
    """
    A Shell window is a

    - Window
    - Menubar
    - Toolbar
    - Application box
    - Statusbar w/ Feedback button

    It contain common menu items for:
      - Opening a new Window
      - Signing out
      - Changing password
      - Closing the application
      - Printing
      - Editing user preferences
      - Spreedshet
      - Toggle toolbar and statusbar visibility
      - View Fullscreen
      - Help menu (Chat, Content, Translation, Support, About)

    The main function is to create the common ui and switch between different
    applications.
    """
    app_title = _('Stoq')

    action_permissions = {}

    # FIXME: we should have a common structure for all information regarding
    # Actions
    common_action_permissions = {
        'HelpChat': ('app.common.help_chat', PermissionManager.PERM_ACCESS),
        'HelpTranslate': ('app.common.help_translate', PermissionManager.PERM_ACCESS),
        'HelpContents': ('app.common.help_contents', PermissionManager.PERM_ACCESS),
        'HelpSupport': ('app.common.help_support', PermissionManager.PERM_ACCESS),
        'HelpHelp': ('app.common.help', PermissionManager.PERM_ACCESS),
    }

    def __init__(self, options, shell, store):
        """Creates a new window

        :param options: optparse options
        :param shell: the shell
        :param store: a store
        """
        self._action_groups = {}
        self._help_ui = None
        self._osx_app = None
        self.current_app = None
        self.current_app_widget = None
        self.shell = shell
        self.uimanager = gtk.UIManager()
        self.in_ui_test = False
        self.tool_items = []
        self.options = options
        self.store = store
        self._pre_launcher_init()
        GladeDelegate.__init__(self,
                               gladefile=self.gladefile)
        self._create_ui()
        self._launcher_ui_bootstrap()

    def _pre_launcher_init(self):
        if platform.system() == 'Darwin':
            import gtk_osxapplication
            self._osx_app = gtk_osxapplication.OSXApplication()
            self._osx_app.connect(
                'NSApplicationBlockTermination',
                self._on_osx__block_termination)
            self._osx_app.set_use_quartz_accelerators(True)
        api.user_settings.migrate()
        self._app_settings = api.user_settings.get('app-ui', {})
        self._create_shared_actions()
        if self.options.debug:
            self.add_debug_ui()

        self.main_vbox = gtk.VBox()

    #
    # Private
    #

    def _create_shared_actions(self):
        group = get_accels('app.common')
        actions = [
            ('menubar', ),
            ('toolbar', ),

            # Menus
            ('FileMenu', None, _("_File")),
            ('FileMenuNew', None),
            ("NewMenu", None, _("New")),
            ("HomeMenu", gtk.STOCK_HOME, _("Home"), None, _("Go back to launcher")),

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
        self.add_ui_actions(None, actions, filename='shellwindow.xml')
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
            ("HomeToolItem", _("Home"), None, gtk.STOCK_HOME),
        ])
        self.NewToolItem.props.is_important = True
        self.SearchToolItem.props.is_important = True

    def _create_application_actions(self):
        def callback(action, name):
            self.switch_application(name)

        self.application_actions = {}
        actions = []
        for app in self.get_available_applications():
            action = gtk.Action(app.name, app.fullname, app.description, app.icon)
            action.connect('activate', callback, app.name)
            actions.append(action)
            self.application_actions[app.name] = action

        # By default, the menu comes with an 'Empty' item that we must hide
        self.HomeToolItem.get_proxies()[0].get_menu().get_children()[-1].hide()
        self.HomeToolItem.add_actions(self.uimanager, actions,
                                      add_separator=False)

    def _create_shared_ui(self):
        self.ToggleToolbar.connect(
            'notify::active', self._on_ToggleToolbar__notify_active)
        self.ToggleStatusbar.connect(
            'notify::active', self._on_ToggleStatusbar__notify_active)
        self.ToggleFullscreen.connect(
            'notify::active', self._on_ToggleFullscreen__notify_active)

        self.toplevel.add(self.main_vbox)
        self.main_vbox.show()

        self.application_box = gtk.VBox()
        self.main_vbox.pack_start(self.application_box)
        self.application_box.show()

        menubar = self.uimanager.get_widget('/menubar')
        if self._osx_app:
            self._osx_app.set_menu_bar(menubar)
        else:
            self.main_vbox.pack_start(menubar, False, False)
            self.main_vbox.reorder_child(menubar, 0)

        toolbar = self.uimanager.get_widget('/toolbar')
        self.main_vbox.pack_start(toolbar, False, False)
        self.main_vbox.reorder_child(toolbar, len(self.main_vbox) - 2)

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

        self._create_application_actions()

    def _create_statusbar(self):
        statusbar = ShellStatusbar(self)

        # Set the initial text, the currently logged in user and the actual
        # branch and station.
        user = api.get_current_user(self.store)
        station = api.get_current_station(self.store)
        status_str = '   |   '.join([
            _("User: %s") % (user.get_description(),),
            _("Computer: %s") % (station.name,),
            "PID: %s" % (os.getpid(),)
        ])
        statusbar.push(0, status_str)
        return statusbar

    def _osx_setup_menus(self):
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

    def _launcher_ui_bootstrap(self):
        self._restore_window_size()
        self._update_toolbar_style()

        self.hide_app(empty=True)

        self._check_demo_mode()
        self._birthdays_bar = None
        self._check_client_birthdays()
        # json will restore tuples as lists. We need to convert them
        # to tuples or the comparison bellow won't work.
        actual_version = tuple(api.user_settings.get('actual-version', (0,)))
        if stoq.stoq_version > actual_version:
            api.user_settings.set('last-version-check', None)
            self._display_changelog_message()
            # Display the changelog message only once. Most users will never
            # click on the "See what's new" button, and that will affect its
            # visual identity.
            api.user_settings.set('actual-version', stoq.stoq_version)

        self._check_information()

        if not stoq.stable and not api.is_developer_mode():
            self._display_unstable_version_message()

        if not self.in_ui_test:
            # Initial fullscreen state for launcher must be handled
            # separate since the window is not realized when the state loading
            # is run in hide_app() the first time.
            window = self.get_toplevel()
            window.realize()
            self.ToggleFullscreen.set_active(
                self._app_settings.get('show-fullscreen', False))
            self.ToggleFullscreen.notify('active')

        toplevel = self.get_toplevel()
        toplevel.connect('configure-event', self._on_toplevel__configure)
        toplevel.connect('delete-event', self._on_toplevel__delete_event)
        toplevel.add_accel_group(self.uimanager.get_accel_group())

        # A GtkWindowGroup controls grabs (blocking mouse/keyboard interaction),
        # by default all windows are added to the same window group.
        # We want to avoid setting modallity on other windows
        # when running a dialog using gtk_dialog_run/run_dialog.
        window_group = gtk.WindowGroup()
        window_group.add_window(toplevel)

    def _check_demo_mode(self):
        if not api.sysparam.get_bool('DEMO_MODE'):
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

    def _check_client_birthdays(self):
        if not api.sysparam.get_bool('BIRTHDAY_NOTIFICATION'):
            return

        # Display the info bar once per day
        date = api.user_settings.get('last-birthday-check')
        last_check = date and datetime.datetime.strptime(date, '%Y-%m-%d').date()
        if last_check and last_check >= datetime.date.today():
            return

        # Only display the infobar if the user has access to calendar (because
        # clicking on the button will open it) and to sales (because it
        # requires that permission to be able to check client details)
        user = api.get_current_user(self.store)
        if not all([user.profile.check_app_permission(u'calendar'),
                    user.profile.check_app_permission(u'sales')]):
            return

        branch = api.get_current_branch(self.store)
        clients_count = ClientWithSalesView.find_by_birth_date(
            self.store, datetime.datetime.today(), branch=branch).count()

        if clients_count:
            msg = stoqlib_ngettext(
                _("There is %s client doing birthday today!"),
                _("There are %s clients doing birthday today!"),
                clients_count) % (clients_count, )
            button = gtk.Button(_("Check the calendar"))
            button.connect('clicked', self._on_check_calendar__clicked)

            self._birthdays_bar = self.add_info_bar(
                gtk.MESSAGE_INFO,
                "<b>%s</b>" % (glib.markup_escape_text(msg), ),
                action_widget=button)

    def _check_information(self):
        """Check some information with Stoq Web API

        - Check if there are new versions of Stoq Available
        - Check if this Stoq Instance uses Stoq Link (and send data to us if
          it does).
        """
        # Check version
        self._version_checker = VersionChecker(self.store, self)
        self._version_checker.check_new_version()

    def _display_changelog_message(self):
        msg = _("Welcome to Stoq version %s!") % stoq.version

        button = gtk.Button(_("See what's new"))
        button.connect('clicked', self._on_show_changelog__clicked)

        self._changelog_bar = self.add_info_bar(gtk.MESSAGE_INFO, msg,
                                                action_widget=button)

    def _display_unstable_version_message(self):
        msg = _(
            'You are currently using an <b>unstable version</b> of Stoq that '
            'is under development,\nbe aware that it may behave incorrectly, '
            'crash or even loose your data.\n<b>Do not use in production.</b>')
        self.add_info_bar(gtk.MESSAGE_WARNING, msg)

    def _save_window_size(self):
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

    def _restore_window_size(self):
        d = api.user_settings.get('launcher-geometry', {})
        try:
            width = int(d.get('width', -1))
            height = int(d.get('height', -1))
            x = int(d.get('x', -1))
            y = int(d.get('y', -1))
        except ValueError:
            pass

        # Setup the default window size, for smaller sizes use
        # 75% of the height or 600px if it's higher than 800px
        if height == -1:
            screen = gtk.gdk.screen_get_default()
            height = min(int(screen.get_height() * 0.75), 600)
        toplevel = self.get_toplevel()
        toplevel.set_default_size(width, height)
        if x != -1 and y != -1:
            toplevel.move(x, y)

    def _read_resource(self, domain, name):
        from stoqlib.lib.kiwilibrary import library

        # On development, documentation resources (e.g. COPYING) will
        # be located directly on the library's root
        devpath = os.path.join(library.get_root(), name)
        if os.path.exists(devpath):
            with open(devpath) as f:
                return f.read()

        return environ.get_resource_string('stoq', domain, name)

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
        lines.append('')  # separate authors from contributors
        data = self._read_resource('docs', 'CONTRIBUTORS')
        lines.extend([c.strip() for c in data.split('\n')])
        about.set_authors(lines)

        about.set_transient_for(get_current_toplevel())
        about.run()
        about.destroy()

    def _hide_current_application(self):
        if not self.current_app:
            return False

        if self._shutdown_application():
            self.hide_app()
        return True

    def _show_uri(self, uri):
        toplevel = self.get_toplevel()
        open_browser(uri, toplevel.get_screen())

    def _get_action_group(self, name):
        action_group = self._action_groups.get(name)
        if action_group is None:
            action_group = gtk.ActionGroup(name)
            self.uimanager.insert_action_group(action_group, 0)
            self._action_groups[name] = action_group
        return action_group

    def _update_toggle_actions(self, app_name):
        self._current_app_settings = d = self._app_settings.setdefault(app_name, {})
        self.ToggleToolbar.set_active(d.get('show-toolbar', True))
        self.ToggleStatusbar.set_active(d.get('show-statusbar', True))
        self.ToggleToolbar.notify('active')
        self.ToggleStatusbar.notify('active')

    def _empty_message_area(self):
        area = self.statusbar.message_area
        for child in area.get_children()[1:]:
            child.destroy()

    def _shutdown_application(self, restart=False, force=False):
        """Shutdown the application:
        There are 3 possible outcomes of calling this function, depending
        on how many windows and applications are open::

        * Hide application, save state, show launcher
        * Close window, save state, show launcher
        * Close window, save global state, terminate application

        This function is called in the following situations:
        * When closing a window (delete-event)
        * When clicking File->Close in an application
        * When clicking File->Quit in the launcher
        * When clicking enable production mode (restart=True)
        * Pressing Ctrl-w/F5 in an application
        * Pressing Ctrl-q in the launcher
        * Pressing Alt-F4 on Win32
        * Pressing Cmd-q on Mac

        :returns: True if shutdown was successful, False if not
        """

        log.debug("Shutting down launcher")

        # Ask the application if we can close, currently this only happens
        # when trying to close the POS app if there's a sale in progress
        current_app = self.current_app
        if current_app and not current_app.can_close_application():
            return False

        # We can currently only close a window if the currently active
        # application is the launcher application, unless we force it
        # (e.g. when enabling production mode)
        if current_app and current_app.app_name != 'launcher' and not force:
            return True

        # Here we save app specific state such as object list
        # column position/ordering
        if current_app and current_app.search:
            current_app.search.save_columns()

        self._save_window_size()

        self.shell.close_window(self)

        # If there are other windows open, do not terminate the application, just
        # close the current window and leave the others alone
        if self.shell.windows:
            return True

        self.shell.quit(restart=restart)

    def _create_ui(self):
        if self._osx_app:
            self._osx_setup_menus()
        self._create_shared_ui()
        toplevel = self.get_toplevel().get_toplevel()
        add_current_toplevel(toplevel)

    def _load_shell_app(self, app_name):
        user = api.get_current_user(self.store)

        # FIXME: Move over to domain
        if (app_name != 'launcher' and
                not user.profile.check_app_permission(app_name)):
            error(_("This user lacks credentials \nfor application %s") %
                  app_name)
            return None
        module = __import__("stoq.gui.%s" % (app_name, ),
                            globals(), locals(), [''])
        attribute = app_name.capitalize() + 'App'
        shell_app_class = getattr(module, attribute, None)
        if shell_app_class is None:
            raise SystemExit("%s app misses a %r attribute" % (
                app_name, attribute))

        shell_app = shell_app_class(window=self,
                                    store=self.store)
        shell_app.app_name = app_name

        return shell_app

    #
    # Public API
    #

    def show_app(self, app, app_window, **params):
        app_window.reparent(self.application_box)
        self.application_box.set_child_packing(app_window, True, True, 0,
                                               gtk.PACK_START)
        # Default action settings for applications
        self.Print.set_visible(True)
        self.Print.set_sensitive(False)
        self.ExportSpreadSheet.set_visible(True)
        self.ExportSpreadSheet.set_sensitive(False)
        self.ChangePassword.set_visible(False)
        self.SignOut.set_visible(False)
        self.Close.set_sensitive(True)
        self.HomeToolItem.set_sensitive(True)
        # We only care about Quit on OSX
        self.Quit.set_visible(bool(self._osx_app))

        self.NewToolItem.set_tooltip("")
        self.NewToolItem.set_sensitive(True)
        self.SearchToolItem.set_tooltip("")
        self.SearchToolItem.set_sensitive(True)
        self._update_toggle_actions(app.app_name)

        self.get_toplevel().set_title(app.get_title())
        self.application_box.show()
        app.toplevel = self.get_toplevel()
        if app.app_name != 'launcher':
            self.application_actions[app.app_name].set_visible(False)

        if self._birthdays_bar is not None:
            if app.app_name in ['launcher', 'sales']:
                self._birthdays_bar.show()
            else:
                self._birthdays_bar.hide()

        # StartApplicationEvent must be emitted before calling app.activate(),
        # so that the plugins can have the chance to modify the application
        # before any other event is emitted.
        StartApplicationEvent.emit(app.app_name, app)
        app.activate(**params)

        self.uimanager.ensure_update()
        self.current_app = app
        self.current_widget = app_window

        if not self.in_ui_test:
            while gtk.events_pending():
                gtk.main_iteration()
            app_window.show()
        app.setup_focus()

    def hide_app(self, empty=False):
        """
        Hide the current application in this window

        :param bool empty: if ``True``, do not add the default launcher application
        """
        self.application_box.hide()
        if self.current_app:
            if self.current_app.app_name != 'launcher':
                self.application_actions[self.current_app.app_name].set_visible(True)
            inventory_bar = getattr(self.current_app, 'inventory_bar', None)
            if inventory_bar:
                inventory_bar.hide()
            if self.current_app.search:
                self.current_app.search.save_columns()
            self.current_app.deactivate()
            if self._help_ui:
                self.uimanager.remove_ui(self._help_ui)
                self._help_ui = None
            self.current_widget.destroy()

            StopApplicationEvent.emit(self.current_app.app_name,
                                      self.current_app)
            self.current_app = None

        self._empty_message_area()
        for item in self.tool_items:
            item.destroy()
        self.tool_items = []
        self._update_toggle_actions('launcher')

        if not empty:
            self.run_application(app_name=u'launcher')

    def add_info_bar(self, message_type, label, action_widget=None):
        """Show an information bar to the user.

        :param message_type: message type, a gtk.MessageType
        :param label: label to display
        :param action_widget: optional, most likely a button
        :returns: the infobar
        """
        infobar = MessageBar(label, message_type)

        if action_widget:
            infobar.add_action_widget(action_widget, 0)
            action_widget.show()
        infobar.show()

        self.main_vbox.pack_start(infobar, False, False, 0)
        self.main_vbox.reorder_child(infobar, 2)

        return infobar

    def add_ui_actions(self, ui_string,
                       actions,
                       name='Actions',
                       action_type='normal',
                       filename=None,
                       instance=None):
        if instance is None:
            instance = self
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

        self.action_permissions.update(self.common_action_permissions)
        pm = PermissionManager.get_permission_manager()
        for action in ag.list_actions():
            action_name = action.get_name()
            setattr(instance, action_name, action)

            # Check permissions
            key, required = instance.action_permissions.get(action_name,
                                                            (None, pm.PERM_ALL))
            if not pm.get(key) & required:
                action.set_visible(False)
                # Disable keyboard shortcut
                path = action.get_accel_path()
                gtk.accel_map_change_entry(path, 0, 0, True)

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
        self._help_ui = self.add_ui_actions(
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
            ('Introspect', None, _('Introspect slaves')),
            ('RemoveSettingsCache', None, _('Remove settings cache')),
        ]

        self.add_ui_actions(ui_string, actions, 'DebugActions')

    def set_new_menu_sensitive(self, sensitive):
        new_items = self.NewToolItem.get_proxies()
        if not new_items:
            return
        widget = new_items[0].get_children()
        if isinstance(widget, gtk.Container):
            button = widget.get_children()[0]
            button.set_sensitive(sensitive)

    def add_new_items(self, actions):
        self.tool_items.extend(
            self.NewToolItem.add_actions(self.uimanager, actions))

    def add_search_items(self, actions):
        self.tool_items.extend(
            self.SearchToolItem.add_actions(self.uimanager, actions))

    def new_window(self):
        """
        Creates a new shell window, with an application selector in it
        """
        shell_window = self.shell.create_window()
        shell_window.run_application(u'launcher')
        shell_window.show()

    def close(self):
        """
        Closes this window
        """
        self.hide_app(empty=True)
        self.toplevel.destroy()
        self.hide()

    def switch_application(self, app_name, **params):
        params['hide'] = True
        self.run_application(app_name, **params)

    def run_application(self, app_name, **params):
        """
        Load and show an application in a shell window.

        :param ShellWindow shell_window: shell window to run application in
        :param str appname: the name of the application to run
        :param params: extra arguments passed to the application
        :returns: the shell application or ``None`` if the user doesn't have
          access to open the application
        :rtype: ShellApp
        """
        # FIXME: Maybe we should really have an app that would be responsible
        # for doing administration tasks related to stoqlink here? Right now
        # we are only going to open the stoq.link url
        if app_name == 'link':
            toplevel = self.get_toplevel()
            open_browser('http://stoq.link?source=stoq', toplevel.get_screen())
            return

        if params.pop('hide', False):
            self.hide_app(empty=True)

        shell_app = self._load_shell_app(app_name)
        if shell_app is None:
            return None

        # Set the icon for the application
        app_icon = get_application_icon(app_name)
        toplevel = self.get_toplevel()
        icon = toplevel.render_icon(app_icon, gtk.ICON_SIZE_MENU)
        toplevel.set_icon(icon)

        # FIXME: We should remove the toplevel windows of all ShellApp's
        #        glade files, as we don't use them any longer.
        shell_app_window = shell_app.get_toplevel()
        self.show_app(shell_app, shell_app_window.get_child(), **params)
        shell_app_window.hide()

        return shell_app

    def get_available_applications(self):
        user = api.get_current_user(self.store)

        permissions = user.profile.get_permissions()
        descriptions = get_utility(IApplicationDescriptions).get_descriptions()

        available_applications = []

        # sorting by app_full_name
        for name, full, icon, descr in locale_sorted(
                descriptions, key=operator.itemgetter(1)):
            # FIXME:
            # if name in self._hidden_apps:
            #    continue
            # and name not in self._blocked_apps:
            if permissions.get(name):
                available_applications.append(
                    Application(name, full, icon, descr))
        return available_applications

    #
    # Kiwi callbacks
    #

    def key_F5(self):
        # Backwards-compatibility
        if self.current_app and self.current_app.can_change_application():
            self.hide_app()
        return True

    def _on_osx__block_termination(self, app):
        return not self._shutdown_application()

    def _on_show_changelog__clicked(self, button):
        show_section('changelog')
        self._changelog_bar.hide()

    def _on_check_calendar__clicked(self, button):
        self.switch_application(u'calendar')
        api.user_settings.set('last-birthday-check',
                              datetime.date.today().strftime('%Y-%m-%d'))
        self._birthdays_bar.hide()
        self._birthdays_bar = None

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

        self._shutdown_application()

    def on_uimanager__connect_proxy(self, uimgr, action, widget):
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

    def on_uimanager__disconnect_proxy(self, uimgr, action, widget):
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

    def _on_menu_item__select(self, menuitem, tooltip):
        self.statusbar.push(0xff, tooltip)

    def _on_menu_item__deselect(self, menuitem):
        self.statusbar.pop(0xff)

    def _on_tool_item__enter_notify_event(self, toolitem, event, tooltip):
        self.statusbar.push(0xff, tooltip)

    def _on_tool_item__leave_notify_event(self, toolitem, event):
        self.statusbar.pop(0xff)

    def _on_enable_production__clicked(self, button):
        if not self.current_app.can_close_application():
            return
        if not yesno(_(u"This will enable production mode and finish the "
                       u"demonstration. Are you sure?"),
                     gtk.RESPONSE_NO,
                     _(u"Enable production mode"), _(u"Continue testing")):
            return

        api.config.set('Database', 'enable_production', 'True')
        api.config.flush()
        self._shutdown_application(restart=True, force=True)

    # File

    def on_NewToolItem__activate(self, action):
        if self.current_app:
            self.current_app.new_activate()
        else:
            self.new_window()

    def on_SearchToolItem__activate(self, action):
        if self.current_app:
            self.current_app.search_activate()
        else:
            print('FIXME')

    def on_NewWindow__activate(self, action):
        self.new_window()

    def on_Print__activate(self, action):
        if self.current_app:
            self.current_app.print_activate()
        else:
            print('FIXME')

    def on_ExportSpreadSheet__activate(self, action):
        if self.current_app:
            self.current_app.export_spreadsheet_activate()
        else:
            print('FIXME')

    def on_Close__activate(self, action):
        self._hide_current_application()

    def on_ChangePassword__activate(self, action):
        from stoqlib.gui.slaves.userslave import PasswordEditor
        store = api.new_store()
        user = api.get_current_user(store)
        retval = run_dialog(PasswordEditor, self, store, user)
        store.confirm(retval)
        store.close()

    def on_SignOut__activate(self, action):
        from stoqlib.lib.interfaces import ICookieFile
        get_utility(ICookieFile).clear()
        self._shutdown_application(restart=True)

    def on_Quit__activate(self, action):
        if self._hide_current_application():
            return

        self._shutdown_application()
        self.get_toplevel().destroy()

    def on_HomeToolItem__activate(self, action):
        self._hide_current_application()

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

    # View

    def on_Preferences__activate(self, action):
        with api.new_store() as store:
            run_dialog(PreferencesEditor, self, store)
        self._update_toolbar_style()

    # Help

    def on_HelpContents__activate(self, action):
        show_contents()

    def on_HelpTranslate__activate(self, action):
        self._show_uri("https://www.transifex.com/projects/p/stoq")

    def on_HelpChat__activate(self, action):
        self._show_uri("http://chat.stoq.com.br/")

    def on_HelpSupport__activate(self, action):
        self._show_uri("http://www.stoq.com.br/suporte")

    def on_HelpAbout__activate(self, action):
        self._run_about()

    # Debug

    def on_Introspect__activate(self, action):
        window = self.get_toplevel()
        introspect_slaves(window)

    def on_RemoveSettingsCache__activate(self, action):
        keys = ['app-ui', 'launcher-geometry']
        keys.append('search-columns-%s' % (
            api.get_current_user(api.get_default_store()).username, ))

        for key in keys:
            try:
                api.user_settings.remove(key)
            except KeyError:
                pass


class VersionChecker(object):
    DAYS_BETWEEN_CHECKS = 7

    #
    #   Private API
    #

    def __init__(self, store, window):
        self.store = store
        self.window = window

    def _display_new_version_message(self, latest_version):
        # Only display version message in admin app
        if 'AdminApp' not in self.window.__class__.__name__:
            return
        button = gtk.LinkButton(
            'http://www.stoq.com.br/novidades',
            _(u'Learn More...'))
        msg = _('<b>There is a new Stoq version available (%s)</b>') % (
            latest_version, )
        self.window.add_info_bar(gtk.MESSAGE_INFO, msg, action_widget=button)

    def _check_details(self, latest_version):
        current_version = tuple(stoq.version.split('.'))
        if tuple(latest_version.split('.')) > current_version:
            self._display_new_version_message(latest_version)
        else:
            log.debug('Using latest version %r, not showing message' % (
                stoq.version, ))

    def _download_details(self):
        log.debug('Downloading new version information')
        webapi = WebService()
        response = webapi.version(self.store, stoq.version)
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
