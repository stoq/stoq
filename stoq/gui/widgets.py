# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

#
# Copyright (C) 2018 Async Open Source <http://www.async.com.br>
# All rights reserved
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., or visit: http://www.gnu.org/.
#
# Author(s): Stoq Team <stoq-devel@async.com.br>
#


from gi.repository import Gtk, Gdk, GObject, Pango
from kiwi.utils import gsignal


class ButtonGroup(Gtk.HBox):
    def __init__(self, buttons):
        super(ButtonGroup, self).__init__()
        self.get_style_context().add_class(Gtk.STYLE_CLASS_LINKED)
        for b in buttons:
            self.pack_start(b, False, False, 0)


@GObject.type_register
class AppEntry(Gtk.FlowBoxChild):
    __gtype_name__ = 'AppEntry'

    def __init__(self, app, icon_size, size_group):
        self.app = app
        super(AppEntry, self).__init__()

        self.connect('realize', self._on_realize)
        pixbuf = self.render_icon(app.icon, icon_size)
        image = Gtk.Image.new_from_pixbuf(pixbuf)
        name = Gtk.Label.new(app.fullname)
        desc = Gtk.Label.new(app.description)

        desc.set_max_width_chars(20)
        desc.set_line_wrap(True)
        desc.set_lines(2)
        desc.set_xalign(0)
        desc.set_yalign(0)
        size_group.add_widget(desc)

        name.set_xalign(0)
        desc.set_ellipsize(Pango.EllipsizeMode.END)
        name.get_style_context().add_class('title')
        desc.get_style_context().add_class('subtitle')

        grid = Gtk.Grid()
        grid.set_row_spacing(0)
        grid.set_column_spacing(12)

        grid.attach(image, 0, 0, 1, 2)
        grid.attach(name, 1, 0, 1, 1)
        grid.attach(desc, 1, 1, 1, 1)
        self.add(grid)

    def _on_realize(self, widget):
        display = Gdk.Display.get_default()
        cursor = Gdk.Cursor.new_for_display(display, Gdk.CursorType.HAND1)
        self.get_window().set_cursor(cursor)


@GObject.type_register
class AppGrid(Gtk.ScrolledWindow):
    __gtype_name__ = 'AppGrid'

    gsignal('app-selected', object)

    def __init__(self, window, large_icons=False):
        self._current_row = None
        if large_icons:
            icon_size = Gtk.IconSize.DIALOG
        else:
            icon_size = Gtk.IconSize.DND

        super(AppGrid, self).__init__()

        box = Gtk.FlowBox()
        box.set_homogeneous(True)
        box.connect('child-activated', self._on_row_activated)

        self.box = box
        self.add(box)

        sg = Gtk.SizeGroup.new(Gtk.SizeGroupMode.BOTH)

        for app in window.get_available_applications():
            entry = AppEntry(app, icon_size, sg)
            box.add(entry)
            if window.current_app == app:
                self._current_row = entry

    def update_selection(self):
        if self._current_row:
            self.box.select_child(self._current_row)
            self._current_row.grab_focus()

    def _on_row_activated(self, listbox, row):
        self._current_row = row
        self.emit('app-selected', row.app)


class PopoverMenu(Gtk.Popover):

    def __init__(self, window):
        self._window = window

        super(PopoverMenu, self).__init__()
        self.set_relative_to(window.home_button)

        self.apps = AppGrid(window)
        self.apps.connect('app-selected', self._on_app_selected)
        self.apps.set_size_request(650, 350)
        self.apps.show_all()

        self.add(self.apps)

    def toggle(self):
        self.set_visible(not self.is_visible())
        self.apps.update_selection()

    def _on_app_selected(self, widget, app):
        self.toggle()

        cur = self._window.current_app
        if cur and cur.can_change_application():
            self._window.run_application(app.name, hide=True)


class SideMenu(Gtk.Box):
    def __init__(self, window):
        self._window = window
        super(SideMenu, self).__init__()

        self.revealer = Gtk.Revealer()
        self.revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_RIGHT)
        self.menu = Gtk.ListBox()
        self.menu.connect('row-activated', self._on_row_activated)

        sw = Gtk.ScrolledWindow()
        sw.set_size_request(350, 350)
        sw.set_shadow_type(Gtk.ShadowType.ETCHED_OUT)
        sw.add(self.menu)

        self.revealer.add(sw)
        self.revealer.set_reveal_child(False)

        for app in self._window.get_available_applications():
            self.menu.add(AppEntry(app))

        self.add(self.revealer)

    def toggle(self):
        reveal = self.revealer.get_reveal_child()
        self.revealer.set_reveal_child(not reveal)

    def _on_row_activated(self, listbox, row):
        self.toggle()

        cur = self._window.current_app
        if cur and cur.can_change_application():
            self._window.run_application(row.app.name, hide=True)
