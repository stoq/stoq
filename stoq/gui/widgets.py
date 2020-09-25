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


from gi.repository import Gtk, Gdk, Pango
from kiwi.utils import gsignal

from stoqlib.api import api
from stoqlib.domain.inventory import Inventory
from stoq.lib.gui.base.dialogs import run_dialog
from stoq.lib.gui.search.productsearch import ProductSearch
from stoq.lib.gui.search.personsearch import ClientSearch
from stoq.lib.gui.widgets.notification import NotificationCounter
from stoq.lib.gui.widgets.section import Section
from stoq.lib.gui.wizards.salequotewizard import SaleQuoteWizard
from stoq.lib.gui.wizards.workorderquotewizard import WorkOrderQuoteWizard
from stoqlib.lib.message import warning
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class ButtonGroup(Gtk.HBox):
    """A horizontal box for grouped buttons.

    This is a quick way to create a horizontal box for grouped buttons form a list of
    widgets. Eg:

        box = ButtonGroup([Gtk.Button('foo'), Gtk.Button('bar')])
    """

    def __init__(self, buttons):
        super(ButtonGroup, self).__init__()
        self.get_style_context().add_class(Gtk.STYLE_CLASS_LINKED)
        for b in buttons:
            self.pack_start(b, False, False, 0)


class AppEntry(Gtk.FlowBoxChild):
    __gtype_name__ = 'AppEntry'

    def __init__(self, app, large_icon):
        super(AppEntry, self).__init__()
        self.set_name('AppEntry')
        self.app = app

        self.connect('realize', self._on_realize)
        if large_icon:
            icon_size = 30
        else:
            icon_size = 20

        theme = Gtk.IconTheme.get_default()
        pixbuf = theme.load_icon(app.icon, icon_size, Gtk.IconLookupFlags.FORCE_SIZE)
        image = Gtk.Image.new_from_pixbuf(pixbuf)
        image.props.margin_left = 6
        name = Gtk.Label.new(app.fullname)
        desc = Gtk.Label.new(app.description)

        desc.set_max_width_chars(20)
        desc.set_line_wrap(True)
        desc.set_lines(2)
        desc.set_xalign(0)
        desc.set_yalign(0)

        name.set_xalign(0)
        desc.set_ellipsize(Pango.EllipsizeMode.END)
        name.get_style_context().add_class('title')
        desc.get_style_context().add_class('subtitle')

        grid = Gtk.Grid()
        grid.props.margin = 6

        grid.attach(image, 0, 0, 1, 2)
        grid.attach(name, 1, 0, 1, 1)
        if large_icon:
            grid.attach(desc, 1, 1, 1, 1)
            grid.set_column_spacing(12)
        else:
            grid.set_tooltip_text(app.description)
            grid.set_column_spacing(6)

        # This event is here for a hover effect on the widget
        event_box = Gtk.EventBox()
        event_box.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
        event_box.connect('enter-notify-event', self._on_hover, True)
        event_box.connect('leave-notify-event', self._on_hover, False)
        event_box.add(grid)
        self.add(event_box)

    def _on_realize(self, widget):
        display = Gdk.Display.get_default()
        cursor = Gdk.Cursor.new_for_display(display, Gdk.CursorType.HAND1)
        self.get_window().set_cursor(cursor)

    def _on_hover(self, widget, event, hover):
        if hover:
            self.get_style_context().add_class('active')
        else:
            self.get_style_context().remove_class('active')


class AppGrid(Gtk.FlowBox):
    __gtype_name__ = 'AppGrid'

    gsignal('app-selected', object)

    def __init__(self, window, apps, size_group, large_icons=False, min_children=2, max_children=5):
        self.window = window
        super(AppGrid, self).__init__()

        self.set_row_spacing(3)
        self.set_column_spacing(3)

        self.set_homogeneous(True)
        self.set_min_children_per_line(min_children)
        self.set_max_children_per_line(max_children)
        self.connect('child-activated', self._on_row_activated)

        for app in apps:
            entry = AppEntry(app, large_icons)
            size_group.add_widget(entry)
            self.add(entry)

    def update_selection(self):
        self.unselect_all()
        for entry in self.get_children():
            if entry.app.name == self.window.current_app.app_name:
                self.select_child(entry)
                break

    def _on_row_activated(self, listbox, row):
        self.emit('app-selected', row.app)

        cur = self.window.current_app
        if cur and cur.can_change_application():
            self.window.run_application(row.app.name, hide=True)


class AppSection(Gtk.Grid):
    def __init__(self, window, name, apps, size_group, large_icons, max_children):
        super(AppSection, self).__init__()
        self.set_column_spacing(6)
        self.set_column_spacing(6)
        label = Gtk.Label(label=name)
        label.set_xalign(0)
        label.get_style_context().add_class('h1')
        if large_icons:
            label.props.margin_bottom = 6
        self.grid = AppGrid(window, apps, size_group, large_icons=large_icons,
                            max_children=max_children)
        sep = Gtk.Separator()
        sep.set_valign(Gtk.Align.CENTER)
        sep.set_hexpand(True)

        self.attach(label, 0, 0, 1, 1)
        self.attach(sep, 1, 0, 1, 1)
        self.attach(self.grid, 0, 1, 2, 1)


class Apps(Gtk.Box):

    sections = [
        (_('Sales'), [
            'pos', 'sales', 'till', 'services', 'delivery'
        ]),
        (_('Operations'), [
            'stock', 'purchase', 'production', 'inventory',
        ]),
        (_('Finances'), [
            'payable', 'receivable', 'financial'
        ]),
        (_('Others'), [
            'admin', 'calendar', 'link',
        ]),
    ]

    def __init__(self, window, large_icons=True, max_children=5):
        super(Apps, self).__init__(orientation=Gtk.Orientation.VERTICAL)
        app_map = {}
        for app in window.get_available_applications():
            app_map[app.name] = app

        sg = Gtk.SizeGroup.new(Gtk.SizeGroupMode.BOTH)
        for section, app_names in self.sections:
            apps = [app_map.get(name) for name in app_names if name in app_map]
            if not apps:
                continue
            self.pack_start(AppSection(window, section, apps, sg, large_icons,
                                       max_children), False, False, 6)

        self.show_all()

        self.boxes = self.get_flowboxes()
        for box in self.boxes:
            box.connect('selected-children-changed', self._on_selection_changed)

    def get_flowboxes(self):
        return [child.grid for child in self.get_children()]

    def update_selection(self):
        for box in self.get_flowboxes():
            box.update_selection()

    def _on_selection_changed(self, box):
        selection = box.get_selected_children()
        if not selection:
            return

        for other in self.boxes:
            if other != box:
                other.unselect_all()


class Shortcut(Gtk.FlowBoxChild):
    __gtype_name__ = 'Shortcut'

    def __init__(self, window, icon_name, title, subtitle, callback):
        self.window = window
        self.callback = callback
        super(Shortcut, self).__init__()
        self.connect('realize', self._on_realize)

        image = Gtk.Image.new_from_icon_name(icon_name or 'starred', Gtk.IconSize.BUTTON)

        name = Gtk.Label.new(title)
        name.set_xalign(0)
        name.get_style_context().add_class('title')

        grid = Gtk.Grid()
        grid.set_row_spacing(0)
        grid.set_column_spacing(12)

        grid.attach(image, 0, 0, 1, 2)
        grid.attach(name, 1, 0, 1, 1)
        grid.set_tooltip_text(subtitle)

        event_box = Gtk.EventBox()
        event_box.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
        event_box.connect('enter-notify-event', self._on_hover, True)
        event_box.connect('leave-notify-event', self._on_hover, False)
        event_box.add(grid)
        self.add(event_box)

    def _on_realize(self, widget):
        display = Gdk.Display.get_default()
        cursor = Gdk.Cursor.new_for_display(display, Gdk.CursorType.HAND1)
        self.get_window().set_cursor(cursor)

    def _on_hover(self, widget, event, hover):
        if hover:
            self.get_style_context().add_class('active')
        else:
            self.get_style_context().remove_class('active')


class ShortcutGrid(Gtk.FlowBox):
    __gtype_name__ = 'ShortcutGrid'

    def __init__(self, window, large_icons=False, min_children=1, max_children=3):
        self.window = window
        super(ShortcutGrid, self).__init__()

        self.set_homogeneous(True)
        self.set_min_children_per_line(min_children)
        self.set_max_children_per_line(max_children)
        self.set_row_spacing(6)
        self.set_column_spacing(6)
        self.set_valign(Gtk.Align.START)
        self.connect('child-activated', self._on_row_activated)

        shortcuts = [
            (None, _('New sale'), _('Create a new quote for a sale'),
             self.new_sale),
            (None, _('New sale with WO'), _('Create a new sale with work order'),
             self.new_sale_with_wo),
            (None, _('Products'), _('Open product search'),
             self.search_products),
            (None, _('Clients'), _('Open client search'),
             self.search_client),
        ]
        for (icon, title, subtitle, action) in shortcuts:
            short = Shortcut(window, icon, title, subtitle, action)
            self.add(short)

    def _on_row_activated(self, listbox, row):
        row.callback()

    def new_sale(self):
        store = self.window.store
        if Inventory.has_open(store, api.get_current_branch(store)):
            warning(_("You cannot create a quote with an open inventory."))
            return

        with api.new_store() as store:
            run_dialog(SaleQuoteWizard, None, store)

    def new_sale_with_wo(self):
        store = self.window.store
        if Inventory.has_open(store, api.get_current_branch(store)):
            warning(_("You cannot create a quote with an open inventory."))
            return

        with api.new_store() as store:
            run_dialog(WorkOrderQuoteWizard, None, store)

        if store.committed:
            # We are unable to just refresh the ui, so 'deactivate' and
            # 'activate' the launcher to mimic the refresh
            self.window.switch_application('launcher')

    def search_products(self):
        with api.new_store() as store:
            profile = api.get_current_user(store).profile
            can_create = (profile.check_app_permission('admin') or
                          profile.check_app_permission('purchase'))
            run_dialog(ProductSearch, None, store, hide_footer=True, hide_toolbar=not can_create,
                       hide_cost_column=not can_create)

    def search_client(self):
        with api.new_store() as store:
            run_dialog(ClientSearch, None, store)


class PopoverMenu(Gtk.Popover):

    def __init__(self, window):
        self._window = window

        super(PopoverMenu, self).__init__()
        self.set_relative_to(window.home_button)
        self.set_size_request(750, 500)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.switcher = Gtk.StackSwitcher()
        self.switcher.set_halign(Gtk.Align.CENTER)
        self.switcher.set_stack(self.stack)
        self.switcher.set_homogeneous(True)

        close_btn = window.create_button('fa-home-symbolic', action='launch.launcher')
        close_btn.set_halign(Gtk.Align.START)
        close_btn.set_relief(Gtk.ReliefStyle.NONE)

        overlay = Gtk.Overlay()
        overlay.add(self.switcher)
        overlay.add_overlay(close_btn)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.pack_start(overlay, False, False, 6)
        box.pack_start(self.stack, True, True, 6)
        box.set_size_request(500, -1)

        self.apps = Apps(window, large_icons=False, max_children=3)
        self.shortcuts = ShortcutGrid(window, max_children=1)
        section = Section(_('Shortcuts'))
        section.set_vexpand(False)

        apps_box = Gtk.Box()
        apps_box.pack_start(self.apps, True, True, 6)
        sc_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sc_box.pack_start(section, False, False, 6)
        sc_box.pack_start(self.shortcuts, True, True, 6)
        apps_box.pack_start(sc_box, False, False, 6)

        sw = Gtk.ScrolledWindow()
        sw.add(apps_box)
        self.stack.add_titled(sw, 'apps', _('Applications'))

        from stoq.gui.shell.statusbar import StatusBox
        self.status = StatusBox()
        self.stack.add_titled(self.status, 'messages', _('Messages'))

        box.show_all()
        self.add(box)

        self.counter = NotificationCounter(self.switcher.get_children()[-1])

    def toggle(self):
        self.set_visible(not self.is_visible())
        self.apps.update_selection()
        self.switcher.grab_focus()
