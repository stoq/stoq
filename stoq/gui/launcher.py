# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

#
# Copyright (C) 2011-2013 Async Open Source <http://www.async.com.br>
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
""" Application to launcher other application.  """


from gi.repository import Gtk, Pango, GObject, Gdk
from stoqlib.lib.translation import stoqlib_gettext

from stoq.gui.shell.shellapp import ShellApp

_ = stoqlib_gettext


@GObject.type_register
class Section(Gtk.VBox):
    __gtype_name__ = 'Section'

    def __init__(self, title):
        super(Section, self).__init__()
        label = Gtk.Label.new(title)
        label.set_xalign(0)
        self.pack_start(label, False, False, 0)


@GObject.type_register
class Shortcut(Gtk.FlowBoxChild):
    __gtype_name__ = 'Shortcut'

    def __init__(self, window, icon_name, title, subtitle, action):
        self.window = window
        super(Shortcut, self).__init__()
        self.connect('realize', self._on_realize)

        self.get_style_context().add_class('flat')
        self.set_size_request(200, -1)
        size = Gtk.IconSize.DND

        if icon_name:
            pixbuf = self.render_icon(icon_name, size)
            image = Gtk.Image.new_from_pixbuf(pixbuf)
        else:
            image = Gtk.Image.new_from_icon_name('starred', size)

        name = Gtk.Label.new(title)
        desc = Gtk.Label.new(subtitle)

        desc.set_max_width_chars(20)
        desc.set_line_wrap(True)
        desc.set_lines(1)
        desc.set_xalign(0)
        desc.set_yalign(0)

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

        self.action_name = action
        self.add(grid)

    def activate(self):
        if '.' not in self.action_name:
            return

        prefix, action = self.action_name.split('.')
        group = self.window.toplevel.get_action_group(prefix)
        if not group:
            return
        group.activate_action(action, None)

    def _on_realize(self, widget):
        display = Gdk.Display.get_default()
        cursor = Gdk.Cursor.new_for_display(display, Gdk.CursorType.HAND1)
        self.get_window().set_cursor(cursor)


class LauncherApp(ShellApp):

    gladefile = "launcher"

    app_title = "Stoq"

    def _create_box(self, parent, title, min_children=3, max_children=3):
        parent.pack_start(Section(title), False, False, 0)
        box = Gtk.FlowBox()
        box.set_min_children_per_line(min_children)
        box.set_max_children_per_line(max_children)
        box.set_homogeneous(True)
        box.set_row_spacing(6)
        box.set_column_spacing(6)
        box.connect('selected-children-changed', self._on_selection_changed)
        box.connect('child-activated', self._on_child_activated)
        parent.pack_start(box, False, False, 0)
        self._boxes.append(box)
        self._box_names[box] = title
        return box

    #
    # ShellApp
    #

    def create_ui(self):
        self._updating = False
        self._boxes = []
        self._box_names = {}
        self.main_box.get_style_context().add_class(Gtk.STYLE_CLASS_VIEW)

        self._apps_box = self._create_box(self.app_box, _('Applications'),
                                          min_children=3, max_children=3)
        for app in self.window.get_available_applications():
            short = Shortcut(self.window, app.icon, app.fullname,
                             app.description, 'launch.' + app.name)
            self._apps_box.add(short)

        self._sc_box = self._create_box(self.side_box, _('Shortcuts'),
                                        min_children=1, max_children=2)
        shortcuts = [
            (None, _('New sale'), _('Create a new quote for a sale'),
             'stoq.preferences'),
            (None, _('New sale with work order'), _('Create a new sale with WO'),
             'launch.sales'),
        ]
        for (icon, title, subtitle, action) in shortcuts:
            short = Shortcut(self.window, icon, title, subtitle, action)
            self._sc_box.add(short)

        self.side_box.pack_start(Section(_('Messages')), False, False, 0)
        self.main_box.show_all()

    #
    # Callbacks
    #

    def _on_child_activated(self, box, child):
        child.activate()

    def _on_selection_changed(self, box):
        selection = box.get_selected_children()
        if not selection:
            return

        for other in self._boxes:
            if other != box:
                other.unselect_all()
