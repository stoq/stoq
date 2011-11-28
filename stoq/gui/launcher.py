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

import gettext
import operator

import gtk
from kiwi.component import get_utility
from stoqlib.api import api
from stoqlib.gui.splash import hide_splash
from stoqlib.lib.interfaces import IApplicationDescriptions
from stoq.gui.application import AppWindow
from stoq.lib.applist import Application

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

    def create_ui(self):
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
        try:
            width = int(api.config.get('Launcher', 'window_width') or -1)
            height = int(api.config.get('Launcher', 'window_height') or -1)
            x = int(api.config.get('Launcher', 'window_x') or -1)
            y = int(api.config.get('Launcher', 'window_y') or -1)
        except ValueError:
            pass
        toplevel = self.get_toplevel()
        toplevel.set_default_size(width, height)
        if x != -1 and y != -1:
            toplevel.move(x, y)

    def _save_window_size(self):
        api.config.set('Launcher', 'window_width', str(self._width))
        api.config.set('Launcher', 'window_height', str(self._height))
        api.config.set('Launcher', 'window_x', str(self._x))
        api.config.set('Launcher', 'window_y', str(self._y))
        api.config.flush()

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
        user = api.get_current_user(self.conn)

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

    def on_iconview__item_activated(self, iconview, path):
        app = self.model[path][COL_APP]
        self.runner.run(app, self)

