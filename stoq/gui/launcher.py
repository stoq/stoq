# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011 Async Open Source <http://www.async.com.br>
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
import gettext
import locale
import operator

import gtk
from kiwi.component import get_utility
from kiwi.environ import environ
from stoqlib.database.runtime import (new_transaction, finish_transaction,
                                      get_current_user)
from stoqlib.gui.help import show_contents
from stoqlib.gui.splash import hide_splash
from stoqlib.lib.interfaces import (IAppInfo, IApplicationDescriptions,
                                    IStoqConfig)

from stoq.gui.application import AppWindow
from stoq.lib.applist import Application

import stoq

_ = gettext.gettext
(COL_LABEL,
 COL_PIXBUF,
 COL_APP) = range(3)

class LauncherApp(object):
    def __init__(self, launcher):
        self.launcher = launcher
        self.runner = launcher.runner
        self.embedded = False
        self.main_window = launcher
        self.options = launcher.options
        self.name = 'launcher'

class Launcher(AppWindow):

    app_name = _('Stoq')
    gladefile = 'launcher'
    launchers = []

    def __init__(self, options, runner):
        self.runner = runner
        self.options = options
        self.current_app = None
        self._tool_items = []
        app = LauncherApp(self)
        AppWindow.__init__(self, app)
        toplevel = self.get_toplevel()
        toplevel.connect('delete-event', self._shutdown)
        toplevel.connect('configure-event', self._on_toplevel__configure)
        hide_splash()
        Launcher.launchers.append(self)
        self._restore_window_size()
        self.hide_app()

    #
    # AppWindow
    #

    def get_title(self):
        return self.app_name

    def create_actions(self):
        actions = [
            ('menubar', ),
            ('toolbar', ),

            ('FileMenu', None, _("_File")),
            ('FileMenuNew', None),
            ("NewMenu", None, _("New")),
            ('NewWindow', None, _("_Window"), '<control>n',
            _('Opens up a new window')),
            ('Close', None, _('Close'), '<control>w',
            _('Close the current view and go back to the initial screen')),
            ('ChangePassword', None, _('Change password...'), '',
            _('Change the password for the currently logged in user')),
            ('SignOut', None, _('Sign out...'), '',
            _('Sign out the currently logged in user and login as another')),
            ("Quit", gtk.STOCK_QUIT, _('Quit'), '<control>q',
             _('Exit the application')),

            # Edit
            ('EditMenu', None, _("_Edit")),
            ('Preferences', None, _("_Preferences")),

            # View
            ('ViewMenu', None, _("_View")),

            # Help
            ("HelpMenu", None, _("_Help")),
            ("HelpContents", gtk.STOCK_HELP, _("Contents"), '<Shift>F1'),
            ("HelpTranslate", None, _("Translate Stoq..."), None,
             _("Translate this application online")),
            ("HelpSupport", None, _("Get support online..."), None,
             _("Get support for Stoq online")),
            ("HelpAbout", gtk.STOCK_ABOUT),

            # Toolbar
            ("NewToolMenu", None, _("New")),
            ("SearchToolMenu", None, _("Search")),
            ]
        self.add_ui_actions(None, actions, filename='launcher.xml')
        self.Close.set_sensitive(False)
        toogle_actions = [
            ('ToggleToolbar', None, _("_Toolbar"), '',
             _('Show or hide the toolbar')),
            ('ToggleStatusbar', None, _("_Statusbar"), '',
             _('Show or hide the statusbar')),
            ('ToggleFullscreen', None, _("_Fullscreen"), 'F11',
             _('Enter or leave fullscreen mode')),
            ]
        self.add_ui_actions('', toogle_actions, 'ToogleActions',
                            'toogle')
        self.ToggleToolbar.props.active = True
        self.ToggleStatusbar.props.active = True

        self.add_tool_menu_actions([
            ("NewToolItem", _("New"), '', gtk.STOCK_NEW),
            ("SearchToolItem", _("Search"), None, gtk.STOCK_FIND),
            ])
        self.NewToolItem.props.is_important = True
        self.SearchToolItem.props.is_important = True

    def create_ui(self):
        self.uimanager.connect('connect-proxy',
            self._on_uimanager__connect_proxy)
        self.uimanager.connect('disconnect-proxy',
            self._on_uimanager__disconnect_proxy)

        menubar = self.uimanager.get_widget('/menubar')
        self.main_vbox.pack_start(menubar, False, False)
        self.main_vbox.reorder_child(menubar, 0)

        toolbar = self.uimanager.get_widget('/toolbar')
        self.main_vbox.pack_start(toolbar, False, False)
        self.main_vbox.reorder_child(toolbar, 1)

        self.model.set_sort_column_id(COL_LABEL, gtk.SORT_ASCENDING)
        self.iconview.set_markup_column(COL_LABEL)
        self.iconview.set_pixbuf_column(COL_PIXBUF)
        self.iconview.set_item_orientation(gtk.ORIENTATION_HORIZONTAL)
        self.iconview.set_item_width(300)
        self.iconview.set_selection_mode(gtk.SELECTION_BROWSE)
        self.iconview.set_spacing(10)

        for app in self._get_available_applications():
            pixbuf = self.get_toplevel().render_icon(app.icon, gtk.ICON_SIZE_DIALOG)
            text = '<b>%s</b>\n<small>%s</small>' % (app.fullname, app.description)
            self.model.append([text, pixbuf, app])

        # FIXME: last opened application
        self.iconview.select_path(self.model[0].path)
        self.iconview.grab_focus()

        # Disable border on statusbar
        children = self.statusbar.get_children()
        if children and isinstance(children[0], gtk.Frame):
            frame = children[0]
            frame.set_shadow_type(gtk.SHADOW_NONE)

        user = get_current_user(self.conn)
        self.statusbar.push(0, _("User: %s") % (user.person.name, ))

    #
    # Public API
    #

    def add_new_items(self, actions):
        self._add_actions_to_tool_item(self.NewToolItem, actions)

    def add_search_items(self, actions):
        self._add_actions_to_tool_item(self.SearchToolItem, actions)

    def set_new_menu_sensitive(self, sensitive):
        new_item = self.NewToolItem.get_proxies()[0]
        button = new_item.get_children()[0].get_children()[0]
        button.set_sensitive(sensitive)

    def show_app(self, app, app_window):
        app_window.reparent(self.application_box)
        self.application_box.set_child_packing(app_window, True, True, 0,
                                               gtk.PACK_START)
        self.Close.set_sensitive(True)
        self.ChangePassword.set_visible(False)
        self.SignOut.set_visible(False)
        self.Quit.set_visible(False)
        self.NewToolItem.set_tooltip("")
        self.NewToolItem.set_sensitive(True)
        self.SearchToolItem.set_tooltip("")
        self.SearchToolItem.set_sensitive(True)

        self.iconview_vbox.hide()

        self.get_toplevel().set_title(app.get_title())
        self.application_box.show()
        app.activate()
        app_window.show()
        app.toplevel = self.get_toplevel()
        app.setup_focus()

        self.current_app = app
        self.current_widget = app_window

    def hide_app(self):
        self.application_box.hide()
        if self.current_app:
            self.current_app.deactivate()
            if self.current_app.help_ui:
                self.uimanager.remove_ui(self.current_app.help_ui)
                self.current_app.help_ui = None
            self.current_widget.destroy()
            self.current_app = None

        self.get_toplevel().set_title(self.get_title())
        message_area = self.statusbar.get_message_area()
        for child in message_area.get_children()[1:]:
            child.destroy()
        for item in self._tool_items:
            item.destroy()
        self._tool_items = []
        self.Close.set_sensitive(False)
        self.ChangePassword.set_visible(True)
        self.SignOut.set_visible(True)
        self.Quit.set_visible(True)
        self.set_new_menu_sensitive(True)
        self.NewToolItem.set_tooltip(_("Open a new window"))
        self.SearchToolItem.set_tooltip("")
        self.SearchToolItem.set_sensitive(False)
        self.iconview.grab_focus()
        self.iconview_vbox.show()

    #
    # Private
    #

    def _add_actions_to_tool_item(self, toolitem, actions):
        new_item = toolitem.get_proxies()[0]
        menu = new_item.get_menu()
        for action in actions:
            action.set_accel_group(self.uimanager.get_accel_group())
            menu_item = action.create_menu_item()
            self._tool_items.append(menu_item)
            menu.insert(menu_item, len(list(menu))-2)
        sep = gtk.SeparatorMenuItem()
        self._tool_items.append(sep)
        menu.insert(sep, len(list(menu))-2)

    def _restore_window_size(self):
        config = get_utility(IStoqConfig)
        try:
            width = int(config.get('Launcher', 'window_width') or -1)
            height = int(config.get('Launcher', 'window_height') or -1)
            x = int(config.get('Launcher', 'window_x') or -1)
            y = int(config.get('Launcher', 'window_y') or -1)
        except ValueError:
            pass
        toplevel = self.get_toplevel()
        toplevel.set_default_size(width, height)
        if x != -1 and y != -1:
            toplevel.move(x, y)

    def _save_window_size(self):
        config = get_utility(IStoqConfig)
        config.set('Launcher', 'window_width', str(self._width))
        config.set('Launcher', 'window_height', str(self._height))
        config.set('Launcher', 'window_x', str(self._x))
        config.set('Launcher', 'window_y', str(self._y))
        config.flush()

    def _shutdown(self, *args):
        if self.current_app and not self.current_app.shutdown_application():
            # We must return True to avoid closing
            return True

        Launcher.launchers.remove(self)
        # There are other launchers running
        if Launcher.launchers:
            return

        self._save_window_size()
        raise SystemExit

    def _get_available_applications(self):
        user = get_current_user(self.conn)

        permissions = {}
        for settings in user.profile.profile_settings:
            permissions[settings.app_dir_name] = settings.has_permission

        descriptions = get_utility(IApplicationDescriptions).get_descriptions()

        available_applications = []

        # sorting by app_full_name
        for name, full, icon, descr in sorted(descriptions,
                                              key=operator.itemgetter(1)):
            #FIXME:
            #if name in self._hidden_apps:
            #    continue
            # and name not in self._blocked_apps:
            if permissions.get(name):
                available_applications.append(
                    Application(name, full, icon, descr))

        return available_applications

    def _show_uri(self, uri):
        toplevel = self.get_toplevel()
        gtk.show_uri(toplevel.get_screen(), uri, gtk.gdk.CURRENT_TIME)

    def _run_about(self, *args):
        info = get_utility(IAppInfo)
        about = gtk.AboutDialog()
        about.set_name(info.get("name"))
        about.set_version(info.get("version"))
        about.set_website(stoq.website)
        release_date = stoq.release_date
        about.set_comments('Release Date: %s' %
                           datetime.datetime(*release_date).strftime('%x'))
        about.set_copyright('Copyright (C) 2005-2011 Async Open Source')

        # Logo
        icon_file = environ.find_resource('pixmaps', 'stoq_logo.svg')
        logo = gtk.gdk.pixbuf_new_from_file(icon_file)
        about.set_logo(logo)

        # License

        if locale.getlocale()[0] == 'pt_BR':
            filename = 'COPYING.pt_BR'
        else:
            filename = 'COPYING'
        fp = self._read_resource('docs', filename)
        about.set_license(fp.read())

        # Authors & Contributors
        fp = self._read_resource('docs', 'AUTHORS')
        lines = [a.strip() for a in fp.readlines()]
        lines.append('') # separate authors from contributors
        fp = self._read_resource('docs', 'CONTRIBUTORS')
        lines.extend([c.strip() for c in fp.readlines()])
        about.set_authors(lines)

        about.run()
        about.destroy()

    def _new_window(self):
        launcher = Launcher(self.options, self.runner)
        launcher.show()

    #
    # Kiwi callbacks
    #

    # Backwards-compatibility
    def key_F5(self):
        if self.current_app and self.current_app.can_change_application():
            self.hide_app()
        return True

    def _on_toplevel__configure(self, widget, event):
        rect = widget.window.get_frame_extents()
        self._x = rect.x
        self._y = rect.y
        self._width = event.width
        self._height = event.height

    def _on_menu_item__select(self, menuitem, tooltip):
        self.statusbar.push(-1, tooltip)

    def _on_menu_item__deselect(self, menuitem):
        self.statusbar.pop(-1)

    def _on_tool_item__enter_notify_event(self, toolitem, event, tooltip):
        self.statusbar.push(-1, tooltip)

    def _on_tool_item__leave_notify_event(self, toolitem, event):
        self.statusbar.pop(-1)

    def _on_uimanager__connect_proxy(self, uimgr, action, widget):
        tooltip = action.get_tooltip()
        if not tooltip:
            return
        if isinstance(widget, gtk.MenuItem):
            widget.connect('select', self._on_menu_item__select, tooltip)
            widget.connect('deselect', self._on_menu_item__deselect)
        elif isinstance(widget, gtk.ToolItem):
            widget.child.connect('enter-notify-event',
                    self._on_tool_item__enter_notify_event, tooltip)
            widget.child.connect('leave-notify-event',
                    self._on_tool_item__leave_notify_event)

    def _on_uimanager__disconnect_proxy(self, uimgr, action, widget):
        tooltip = action.get_tooltip()
        if not tooltip:
            return
        if isinstance(widget, gtk.MenuItem):
            widget.disconnect_by_func(self._on_menu_item__select)
            widget.disconnect_by_func(self._on_menu_item__deselect)
        elif isinstance(widget, gtk.ToolItem):
            try:
                widget.child.disconnect_by_func(
                    self._on_tool_item__enter_notify_event)
                widget.child.disconnect_by_func(
                    self._on_tool_item__leave_notify_event)
            except TypeError:
                pass

    def on_iconview__item_activated(self, iconview, path):
        app = self.model[path][COL_APP]
        self.runner.run(app, self)

    # File

    def on_NewToolItem__activate(self, action):
        if self.current_app:
            self.current_app.new_activate()
        else:
            self._new_window()

    def on_SearchToolItem__activate(self, action):
        if self.current_app:
            self.current_app.search_activate()
        else:
            print 'FIXME'

    def on_NewWindow__activate(self, action):
        self._new_window()

    def on_Close__activate(self, action):
        if self.current_app and self.current_app.shutdown_application():
            self.hide_app()

    def on_ChangePassword__activate(self, action):
        from stoqlib.gui.slaves.userslave import PasswordEditor
        trans = new_transaction()
        user = get_current_user(trans)
        retval = self.run_dialog(PasswordEditor, trans, user)
        finish_transaction(trans, retval)

    def on_SignOut__activate(self, action):
        from stoqlib.lib.interfaces import ICookieFile
        get_utility(ICookieFile).clear()
        self.get_toplevel().hide()
        self.app.runner.relogin()

    def on_Quit__activate(self, action):
        if self.current_app and not self.current_app.shutdown_application():
            return

        self._save_window_size()
        raise SystemExit

    # View

    def on_Preferences__activate(self, action):
        pass

    # Edit

    def on_ToggleToolbar__toggled(self, action):
        toolbar = self.uimanager.get_widget('/toolbar')
        toolbar.set_visible(action.get_active())

    def on_ToggleStatusbar__toggled(self, action):
        self.statusbar.set_visible(action.get_active())

    def on_ToggleFullscreen__toggled(self, action):
        self.toggle_fullscreen()


    # Help

    def on_HelpContents__activate(self, action):
        show_contents()

    def on_HelpTranslate__activate(self, action):
        self._show_uri("https://translations.launchpad.net/stoq")

    def on_HelpSupport__activate(self, action):
        self._show_uri("http://www.stoq.com.br/support")

    def on_HelpAbout__activate(self, action):
        self._run_about()
