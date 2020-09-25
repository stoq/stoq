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

from gi.repository import Gtk, GLib, Gdk, Gio
from stoqlib.lib.component import get_utility
from kiwi.environ import environ
from kiwi.ui.delegates import Delegate
from stoqlib.api import api
from stoqlib.domain.views import ClientWithSalesView
from stoq.lib.gui.base.dialogs import add_current_toplevel, get_current_toplevel, run_dialog
from stoq.lib.gui.base.messagebar import MessageBar
from stoq.lib.gui.editors.preferenceseditor import PreferencesEditor
from stoq.lib.gui.events import StartApplicationEvent, StopApplicationEvent
from stoq.lib.gui.stockicons import STOQ_LAUNCHER
from stoq.lib.gui.utils.help import show_contents, show_section
from stoq.lib.gui.utils.introspection import introspect_slaves
from stoq.lib.gui.utils.logo import render_logo_pixbuf
from stoq.lib.gui.utils.openbrowser import open_browser
from stoq.lib.gui.widgets.notification import NotificationCounter
from stoqlib.lib.interfaces import IAppInfo, IApplicationDescriptions
from stoqlib.lib.message import error, yesno
from stoqlib.lib.permissions import PermissionManager
from stoqlib.lib.pluginmanager import InstalledPlugin, get_plugin_manager
from stoqlib.lib.translation import stoqlib_gettext, stoqlib_ngettext, locale_sorted
from stoqlib.lib.webservice import WebService
from stoq.gui.shell.statusbar import ShellStatusbar
from stoq.gui.widgets import PopoverMenu, ButtonGroup
from stoq.lib.applist import get_application_icon, Application
import stoq

_ = stoqlib_gettext
log = logging.getLogger(__name__)


MENU_XML = """
<?xml version="1.0" encoding="UTF-8"?>
<interface>
  <menu id="app-menu">
    <section id='user-settings'>
      <attribute name="label" translatable="yes">{username}</attribute>
      <item>
        <attribute name="action">stoq.preferences</attribute>
        <attribute name="label" translatable="yes">{preferences}</attribute>
      </item>
      <item>
        <attribute name="action">stoq.change_password</attribute>
        <attribute name="label" translatable="yes">{password}</attribute>
      </item>
      <item>
        <attribute name="action">stoq.sign_out</attribute>
        <attribute name="label" translatable="yes">{signout}</attribute>
      </item>
    </section>
    <section id='help-section'>
      <attribute name="label" translatable="yes">{help}</attribute>
      <item>
        <attribute name="action">stoq.HelpContents</attribute>
        <attribute name="label" translatable="yes">{contents}</attribute>
      </item>
      <item>
        <attribute name="action">stoq.HelpTranslate</attribute>
        <attribute name="label" translatable="yes">{translate}</attribute>
      </item>
      <item>
        <attribute name="action">stoq.HelpSupport</attribute>
        <attribute name="label" translatable="yes">{get_support}</attribute>
      </item>
      <item>
        <attribute name="action">stoq.HelpChat</attribute>
        <attribute name="label" translatable="yes">{chat}</attribute>
      </item>
      <item>
        <attribute name="action">stoq.HelpAbout</attribute>
        <attribute name="label" translatable="yes">{about}</attribute>
      </item>
    </section>
    <section>
      <item>
        <attribute name="action">stoq.quit</attribute>
        <attribute name="label" translatable="yes">{quit}</attribute>
      </item>
    </section>
  </menu>
</interface>
"""


class ShellWindow(Delegate):
    """
    A Shell window is a

    - Window
    - Application box
    - Statusbar w/ Feedback button

    It contain common menu items for:
      - Signing out
      - Changing password
      - Closing the application
      - Printing
      - Editing user preferences
      - Spreedshet
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

    def __init__(self, options, shell, store, app):
        """Creates a new window

        :param options: optparse options
        :param shell: the shell
        :param store: a store
        :param app: a Gtk.Application instance
        """
        self._action_groups = {}
        self._help_section = None
        self._osx_app = None
        self.current_app = None
        self.shell = shell
        self.app = app
        self.in_ui_test = False
        self.options = options
        self.store = store
        self._pre_launcher_init()
        Delegate.__init__(self, toplevel=Gtk.ApplicationWindow.new(app))
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

        self._app_settings = api.user_settings.get('app-ui', {})
        self.main_vbox = Gtk.VBox()

    #
    # Private
    #

    def _create_application_actions(self):
        """Create the actions that activate the applications.

        This actions are prefixed by 'launch', followed by the app name (for
        instance launch.pos)
        """
        def callback(action, parameter, name):
            self.switch_application(name)

        group = Gio.SimpleActionGroup()
        self.toplevel.insert_action_group('launch', group)
        for app in self.get_available_applications():
            action = Gio.SimpleAction.new(app.name, None)
            action.connect('activate', callback, app.name)
            group.add_action(action)

        # Also add the launcher app
        action = Gio.SimpleAction.new('launcher', None)
        action.connect('activate', callback, 'launcher')
        group.add_action(action)

    def _create_menu2(self, actions):
        model = Gio.Menu()
        for action in actions or []:
            if isinstance(action, list):
                section = self._create_menu(action)
                model.append_section(None, section)
            else:
                label, name = action
                item = Gio.MenuItem.new(label, name)
                model.append_item(item)
        return model

    def _create_menu(self, actions):
        model = Gio.Menu()
        for action in actions or []:
            if isinstance(action, list):
                section = self._create_menu(action)
                model.append_section(None, section)
                pass
            else:
                fullname, icon, label, accel = self._action_specs[action.get_name()][:-1]
                item = Gio.MenuItem.new(label, fullname)
                if accel:
                    item.set_attribute_value('accel', GLib.Variant('s', accel))
                    self.app.set_accels_for_action(fullname, [accel])
                model.append_item(item)
        return model

    def _create_shared_ui(self):
        self.toplevel.add(self.main_vbox)

        self.application_box = Gtk.HBox()
        self.main_vbox.pack_start(self.application_box, True, True, 0)
        self.application_box.show()

        self.stoq_menu = PopoverMenu(self)
        self.main_vbox.show_all()

        self.statusbar = self._create_statusbar()
        self.statusbar.set_visible(True)

        self.main_vbox.pack_start(self.statusbar, False, False, 0)

        self.main_vbox.set_focus_chain([self.application_box])
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
        self.quit.set_visible(False)
        self.HelpAbout.set_visible(False)
        self.HelpAbout.set_label(_('About Stoq'))
        self._osx_app.set_help_menu(
            self.HelpMenu.get_proxies()[0])
        self._osx_app.insert_app_menu_item(
            self.HelpAbout.get_proxies()[0], 0)
        self._osx_app.insert_app_menu_item(
            Gtk.SeparatorMenuItem(), 1)
        self.preferences.set_visible(False)
        self._osx_app.insert_app_menu_item(
            self.Preferences.get_proxies()[0], 2)
        self._osx_app.ready()

    def _launcher_ui_bootstrap(self):
        self._restore_window_size()

        self.hide_app(empty=True)

        self._check_demo_mode()
        self._check_online_plugins()
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

        toplevel = self.get_toplevel()
        toplevel.connect('configure-event', self._on_toplevel__configure)
        toplevel.connect('delete-event', self._on_toplevel__delete_event)

        # A GtkWindowGroup controls grabs (blocking mouse/keyboard interaction),
        # by default all windows are added to the same window group.
        # We want to avoid setting modallity on other windows
        # when running a dialog using gtk_dialog_run/run_dialog.
        window_group = Gtk.WindowGroup()
        window_group.add_window(toplevel)

    def _check_online_plugins(self):
        # For each online plugin, try to download and install it.
        # Otherwise warn him
        online_plugins = InstalledPlugin.get_pre_plugin_names(self.store)
        if not online_plugins:
            return

        successes = []
        manager = get_plugin_manager()
        for plugin_name in online_plugins:
            success, msg = manager.download_plugin(plugin_name)
            successes.append(success)
            if success:
                manager.install_plugin(self.store, plugin_name)
                online_plugins.remove(plugin_name)

        if all(successes):
            return

        # Title
        title = _('You have pending plugins.')

        # Description
        url = 'https://stoq.link/?source=stoq-plugin-alert&amp;hash={}'.format(
            api.sysparam.get_string('USER_HASH'))
        desc = _(
            'The following plugins need to be enabled: <b>{}</b>.\n\n'
            'You can do it by registering on <a href="{}">Stoq.link</a>.'
        ).format(', '.join(online_plugins), url)
        msg = '<b>%s</b>\n%s' % (title, desc)
        self.add_info_bar(Gtk.MessageType.WARNING, msg)

    def _check_demo_mode(self):
        if not api.sysparam.get_bool('DEMO_MODE'):
            return

        if api.user_settings.get('hide-demo-warning'):
            return

        button_label = _('Use my own data')
        title = _('You are using Stoq with example data.')
        desc = (_("Some features are limited due to fiscal reasons. "
                  "Click on '%s' to remove the limitations.")
                % button_label)
        msg = '<b>%s</b>\n%s' % (api.escape(title), api.escape(desc))

        button = Gtk.Button(button_label)
        button.connect('clicked', self._on_enable_production__clicked)
        self.add_info_bar(Gtk.MessageType.WARNING, msg, action_widget=button)

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
            button = Gtk.Button(_("Check the calendar"))
            button.connect('clicked', self._on_check_calendar__clicked)

            self._birthdays_bar = self.add_info_bar(
                Gtk.MessageType.INFO,
                "<b>%s</b>" % (GLib.markup_escape_text(msg), ),
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

        button = Gtk.Button(_("See what's new"))
        button.connect('clicked', self._on_show_changelog__clicked)

        self._changelog_bar = self.add_info_bar(Gtk.MessageType.INFO, msg,
                                                action_widget=button)

    def _display_unstable_version_message(self):
        msg = _(
            'You are currently using an <b>unstable version</b> of Stoq that '
            'is under development,\nbe aware that it may behave incorrectly, '
            'crash or even loose your data.\n<b>Do not use in production.</b>')
        self.add_info_bar(Gtk.MessageType.WARNING, msg)

    def _save_window_size(self):
        if not hasattr(self, '_width'):
            return
        # Do not save the size of the window when we are in fullscreen
        window = self.get_toplevel()
        window = window.get_window()
        if window.get_state() & Gdk.WindowState.FULLSCREEN:
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
        screen = Gdk.Screen.get_default()
        screen_height = screen.get_height()
        screen_width = screen.get_width()

        if height == -1 or y > screen_height:
            height = min(int(screen_height * 0.75), 650)

        if width == -1 or y > screen_width:
            width = min(int(screen_width * 0.75), 800)

        # Setup window position according to the settings file, but if settings file
        # indicates values out of the screen, move the window to the outermost position
        # within the screen.
        toplevel = self.get_toplevel()
        toplevel.set_default_size(width, height)
        y = min(y, screen_height - height)
        x = min(x, screen_width - width)
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

        return environ.get_resource_string('stoq', domain, name).decode()

    def _run_about(self):
        info = get_utility(IAppInfo)
        about = Gtk.AboutDialog()
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

        self._create_headerbar()
        self._create_actions()
        self._create_shared_ui()

        toplevel = self.get_toplevel().get_toplevel()
        add_current_toplevel(toplevel)

        if self.options.debug:
            self.add_debug_ui()

    def create_button(self, icon, label=None, menu_model=None, menu=False, action=None,
                      tooltip=None, style_class=None, toggle=False, icon_size=Gtk.IconSize.BUTTON):
        if menu_model or menu:
            button = Gtk.MenuButton()
        elif toggle:
            button = Gtk.ToggleButton()
        else:
            button = Gtk.Button()

        box = Gtk.HBox(spacing=6)
        button.add(box)

        if icon:
            image = Gtk.Image.new_from_icon_name(icon, icon_size)
            box.pack_start(image, False, False, 0)
        if label:
            label = Gtk.Label.new(label)
            box.pack_start(label, False, False, 0)

        if menu_model:
            button.set_menu_model(menu_model)
        if action:
            button.set_action_name(action)
        if tooltip:
            button.set_tooltip_text(tooltip)
        if style_class:
            button.get_style_context().add_class(style_class)
        return button

    def _create_headerbar(self):
        # User/help menu
        user = api.get_current_user(self.store)
        xml = MENU_XML.format(username=api.escape(user.get_description()),
                              preferences=_('Preferences...'), password=_('Change password...'),
                              signout=_('Sign out...'), help=_('Help'),
                              contents=_('Contents'), translate=_('Translate Stoq...'),
                              get_support=_('Get support online...'), chat=_('Online chat...'),
                              about=_('About'), quit=_('Quit'))
        builder = Gtk.Builder.new_from_string(xml, -1)

        # Header bar
        self.header_bar = Gtk.HeaderBar()
        self.toplevel.set_titlebar(self.header_bar)

        # Right side
        self.close_btn = self.create_button('fa-power-off-symbolic', action='stoq.quit')
        self.close_btn.set_relief(Gtk.ReliefStyle.NONE)
        self.min_btn = self.create_button('fa-window-minimize-symbolic')
        self.min_btn.set_relief(Gtk.ReliefStyle.NONE)
        #self.header_bar.pack_end(self.close_btn)
        #self.header_bar.pack_end(self.min_btn)
        box = Gtk.Box.new(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        box.pack_start(self.min_btn, False, False, 0)
        box.pack_start(self.close_btn, False, False, 0)
        self.header_bar.pack_end(box)

        self.user_menu = builder.get_object('app-menu')
        self.help_section = builder.get_object('help-section')
        self.user_button = self.create_button('fa-cog-symbolic',
                                              menu_model=self.user_menu)
        self.search_menu = Gio.Menu()
        self.search_button = self.create_button('fa-search-symbolic', _('Searches'),
                                                menu_model=self.search_menu)
        self.main_menu = Gio.Menu()
        self.menu_button = self.create_button('fa-bars-symbolic', _('Actions'),
                                              menu_model=self.main_menu)

        self.header_bar.pack_end(
            ButtonGroup([self.menu_button, self.search_button, self.user_button]))

        self.sign_button = self.create_button('', _('Sign now'), style_class='suggested-action')
        #self.header_bar.pack_end(self.sign_button)

        # Left side
        self.home_button = self.create_button(STOQ_LAUNCHER, style_class='suggested-action')
        self.new_menu = Gio.Menu()
        self.new_button = self.create_button('fa-plus-symbolic', _('New'),
                                             menu_model=self.new_menu)

        self.header_bar.pack_start(
            ButtonGroup([self.home_button, self.new_button, ]))

        self.domain_header = None
        self.header_bar.show_all()

        self.notifications = NotificationCounter(self.home_button, blink=True)

    def _create_actions(self):
        # Gloabl actions avaiable at any time from all applications
        actions = [
            ('preferences', None),
            ('export', None),
            ('print', None),
            ('sign_out', None),
            ('change_password', None),
            ('HelpApp', None),
            ('HelpContents', None),
            ('HelpTranslate', None),
            ('HelpSupport', None),
            ('HelpChat', None),
            ('HelpAbout', None),
            ('quit', None),
        ]

        pm = PermissionManager.get_permission_manager()
        group = Gio.SimpleActionGroup()
        self.toplevel.insert_action_group('stoq', group)
        for (name, param_type) in actions:
            action = Gio.SimpleAction.new(name, param_type)
            group.add_action(action)
            # Save the action in self so that auto signal connections work
            setattr(self, name, action)

            # Check permissions
            key, required = self.action_permissions.get(name,
                                                        (None, pm.PERM_ALL))
            if not pm.get(key) & required:
                action.set_enabled(False)

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

        shell_app_class.app_name = app_name
        shell_app = shell_app_class(window=self,
                                    store=self.store)

        return shell_app

    def _wrap_action_callback(self, app, name):
        """Wraps a Gtk.Action callback to a Gio.SimpleAction callback.

        This is just a temporary wrapper untill all apps are properly migrated
        to the new gtk api.
        """
        method_name = 'on_%s__activate' % name
        try:
            old_callback = getattr(app, method_name)
        except AttributeError:
            return

        def new_callback(action, parameter):
            return old_callback(action)

        setattr(app, method_name, new_callback)

    #
    # Public API
    #

    def add_ui_actions(self, app, actions, name):
        for spec in actions:
            spec = list(spec)
            act_name, icon, label = spec[:3]
            accel, long_desc, callback = None, None, None
            spec[:3] = []
            if spec:
                accel = spec.pop(0)
            if spec:
                long_desc = spec.pop(0)
            if spec:
                callback = spec.pop(0)

            param_type = None
            if name == 'Actions':
                action = Gio.SimpleAction.new(act_name, param_type)
                self._wrap_action_callback(app, act_name)
            elif name in ('ToggleActions', 'RadioActions'):
                action = Gio.SimpleAction.new_stateful(act_name, param_type,
                                                       GLib.Variant.new_boolean(False))

                def set_active(value):
                    # TODO: colocar deprecation warning aqui.
                    action.set_state(GLib.Variant.new_boolean(value))
                    # XXX: The change-state event is not being emitted
                    method_name = 'on_%s__activate' % act_name
                    getattr(app, method_name)(action, None)

                def get_active():
                    value = action.get_state().get_boolean()
                    return value

                action.set_active = set_active
                action.get_active = get_active

            app.action_group.add_action(action)
            app.window._action_specs[act_name] = (
                app.app_name + '.' + act_name, icon, label, accel, long_desc)
            # Save the action in the app so that auto signal connections work
            setattr(app, act_name, action)

            if callback:
                action.connect('activate', callback)

    def set_close_button_icon(self, icon_name):
        image = self.close_btn.get_child().get_children()[0]
        image.set_from_icon_name(icon_name, Gtk.IconSize.BUTTON)
        image.set_size_request(16, 16)

    def show_app(self, app, app_window, **params):
        self.stoq_menu.set_visible(False)
        app_window.get_parent().remove(app_window)
        self.application_box.add(app_window)
        self.application_box.set_child_packing(app_window, True, True, 0,
                                               Gtk.PackType.START)

        self._current_app_settings = self._app_settings.setdefault(app.app_name, {})

        self.header_bar.set_title(app.get_title())
        self.header_bar.set_subtitle(app.app_title)
        self.application_box.show()
        app.toplevel = self.get_toplevel()

        if self._birthdays_bar is not None:
            if app.app_name in ['launcher', 'sales']:
                self._birthdays_bar.show()
            else:
                self._birthdays_bar.hide()

        if app.app_name == 'launcher':
            icon_name = 'fa-power-off-symbolic'
        else:
            icon_name = 'fa-chevron-left-symbolic'
        self.set_close_button_icon(icon_name)

        # StartApplicationEvent must be emitted before calling app.activate(),
        # so that the plugins can have the chance to modify the application
        # before any other event is emitted.
        StartApplicationEvent.emit(app.app_name, app)
        app.activate(**params)

        self.current_app = app
        self.current_widget = app_window

        if not self.in_ui_test:
            while Gtk.events_pending():
                Gtk.main_iteration()
            app_window.show()
        app.setup_focus()

    def hide_app(self, empty=False):
        """
        Hide the current application in this window

        :param bool empty: if ``True``, do not add the default launcher application
        """
        self.application_box.hide()
        # Reset menus/headerbar
        self.main_menu.remove_all()
        self.search_menu.remove_all()
        self.new_menu.remove_all()

        if self.current_app:
            inventory_bar = getattr(self.current_app, 'inventory_bar', None)
            if inventory_bar:
                inventory_bar.hide()
            if self.current_app.search:
                self.current_app.search.save_columns()
            self.current_app.deactivate()

            # We need to remove the accels for this app, otherwise they would
            # still be active from other applications
            for spec in self._action_specs.values():
                fullname, icon, label, accel = spec[:-1]
                if accel:
                    self.app.set_accels_for_action(fullname, [])

            if self._help_section:
                self.help_section.remove(0)
                self._help_section = None
            self.current_widget.destroy()

            StopApplicationEvent.emit(self.current_app.app_name,
                                      self.current_app)
            self.current_app = None

        self._empty_message_area()
        if not empty:
            self.run_application(app_name=u'launcher')

    def add_info_bar(self, message_type, label, action_widget=None):
        """Show an information bar to the user.

        :param message_type: message type, a Gtk.MessageType
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
        self.main_vbox.reorder_child(infobar, 0)
        return infobar

    def set_help_section(self, label, section):
        self._help_section = section
        self.help_section.insert(0, label, 'stoq.HelpApp')

    def add_debug_ui(self):
        self.toplevel.set_interactive_debugging(True)
        return
        actions = [
            ('Introspect', None, _('Introspect slaves')),
            ('RemoveSettingsCache', None, _('Remove settings cache')),
        ]

        self.add_ui_actions(self, actions, 'Actions')
        self.add_extra_items([self.Introspect, self.RemoveSettingsCache],
                             _('Debug'))

    def add_domain_header(self, options):
        if self.domain_header:
            self.header_bar.remove(self.domain_header)
            self.domain_header = None

        if not options:
            return

        buttons = []
        for (icon, label, action, in_header) in options:
            if not in_header:
                continue
            buttons.append(self.create_button(icon, action=action,
                                              tooltip=label))
        self.domain_header = ButtonGroup(buttons)
        self.domain_header.show_all()
        self.header_bar.pack_start(self.domain_header)

    def add_new_items(self, actions, label=None):
        self.new_menu.append_section(label, self._create_menu(actions))

    def add_new_items2(self, actions, label=None):
        self.new_menu.append_section(label, self._create_menu2(actions))

    def add_export_items(self, actions=None):
        self._export_menu = self._create_menu(actions)
        self._export_menu.insert(0, _('Export to spreadsheet...'), 'stoq.export')
        self.main_menu.append_section(None, self._export_menu)

    def add_print_items(self, actions=None):
        self._print_menu = self._create_menu(actions)
        self._print_menu.insert(0, _('Print this report...'), 'stoq.print')
        self.main_menu.append_section(None, self._print_menu)

    def add_print_items2(self, actions=None):
        self._print_menu = self._create_menu2(actions)
        self._print_menu.insert(0, _('Print this report...'), 'stoq.print')
        self.main_menu.append_section(None, self._print_menu)

    def add_extra_items(self, actions=None, label=None):
        self._extra_items = self._create_menu(actions)
        self.main_menu.append_section(label, self._extra_items)

    def add_extra_items2(self, actions=None, label=None):
        self._extra_items = self._create_menu2(actions)
        self.main_menu.append_section(label, self._extra_items)

    def add_search_items(self, actions, label=None):
        self.search_menu.append_section(label, self._create_menu(actions))

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
            user_hash = api.sysparam.get_string('USER_HASH')
            url = 'https://stoq.link?source=stoq&hash={}'.format(user_hash)
            open_browser(url, toplevel.get_screen())
            return

        if params.pop('hide', False):
            self.hide_app(empty=True)

        shell_app = self._load_shell_app(app_name)
        if shell_app is None:
            return None

        # Set the icon for the application
        app_icon = get_application_icon(app_name)
        toplevel = self.get_toplevel()
        toplevel.set_icon_name(app_icon)

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
            if permissions.get(name):
                available_applications.append(
                    Application(name, full, icon, descr))
        return available_applications

    #
    # Kiwi callbacks
    #

    def key_F5(self):
        self.switch_application('launcher')
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

    def _on_enable_production__clicked(self, button):
        if not self.current_app.can_close_application():
            return
        if not yesno(_(u"This will enable production mode and finish the "
                       u"demonstration. Are you sure?"),
                     Gtk.ResponseType.NO,
                     _(u"Enable production mode"), _(u"Continue testing")):
            return

        api.config.set('Database', 'enable_production', 'True')
        api.config.flush()
        self._shutdown_application(restart=True, force=True)

    def on_min_btn__clicked(self, button):
        self.get_toplevel().iconify()

    # File

    def on_SearchToolItem__activate(self, action):
        if self.current_app:
            self.current_app.search_activate()

    def on_print__activate(self, action, parameter):
        self.current_app.print_activate()

    def on_export__activate(self, action, parameter):
        self.current_app.export_spreadsheet_activate()

    def on_change_password__activate(self, action, parameter):
        from stoq.lib.gui.slaves.userslave import PasswordEditor
        store = api.new_store()
        user = api.get_current_user(store)
        retval = run_dialog(PasswordEditor, self, store, user)
        store.confirm(retval)
        store.close()

    def on_sign_out__activate(self, action, parameter):
        from stoqlib.lib.interfaces import ICookieFile
        get_utility(ICookieFile).clear()
        self._shutdown_application(restart=True)

    def on_quit__activate(self, action, parameter):
        if self._hide_current_application():
            return

        self._shutdown_application()
        self.get_toplevel().destroy()

    def on_home_button__clicked(self, action):
        self.stoq_menu.toggle()

    # View

    def on_preferences__activate(self, action, parameter):
        with api.new_store() as store:
            run_dialog(PreferencesEditor, self, store)

    # Help

    def on_HelpApp__activate(self, action, parameter):
        show_section(self._help_section)

    def on_HelpContents__activate(self, action, parameter):
        show_contents()

    def on_HelpTranslate__activate(self, action, parameter):
        self._show_uri("https://www.transifex.com/projects/p/stoq")

    def on_HelpChat__activate(self, action, parameter):
        self._show_uri("http://www.stoq.com.br/")

    def on_HelpSupport__activate(self, action, parameter):
        self._show_uri("http://www.stoq.com.br/suporte")

    def on_HelpAbout__activate(self, action, parameter):
        self._run_about()

    def on_main_menu__items_changed(self, menu, position, removed, added):
        self.menu_button.set_sensitive(menu.get_n_items() > 0)

    def on_search_menu__items_changed(self, menu, position, removed, added):
        self.search_button.set_sensitive(menu.get_n_items() > 0)

    def on_new_menu__items_changed(self, menu, position, removed, added):
        self.new_button.set_sensitive(menu.get_n_items() > 0)

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
    DAYS_BETWEEN_CHECKS = 1

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
        button = Gtk.LinkButton(
            'http://www.stoq.com.br/novidades',
            _(u'Learn More...'))
        msg = _('<b>There is a new Stoq version available (%s)</b>') % (
            latest_version, )
        self.window.add_info_bar(Gtk.MessageType.INFO, msg, action_widget=button)

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
        webapi.version(self.store, stoq.version,
                       callback=self._on_response_done)

    def _on_response_done(self, response):
        if response.status_code != 200:
            return

        details = response.json()
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
