# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
#
# Copyright (C) 2018 Async Open Source <http://www.async.com.br>
# All rights reserved
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., or visit: http://www.gnu.org/.
#
#  Author(s): Stoq Team <stoq-devel@async.com.br>
#

from gi.repository import Gtk, Gdk, Gio

from storm.expr import Eq

from stoqlib.api import api
from stoqlib.domain.workorder import WorkOrderView, WorkOrder
from stoq.lib.gui.actions.workorder import WorkOrderActions
from stoq.lib.gui.widgets.section import Section
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class WorkOrderRow(Gtk.ListBoxRow):
    options = [
        (_('Details'), 'work_order.Details'),
        (_('Edit'), 'work_order.Edit'),
        (_('Print receipt'), 'work_order.PrintReceipt'),
    ]

    sale_options = [
        (_('Details'), 'sale.Details'),
        (_('Edit'), 'sale.Edit'),
    ]

    state_changes = [
        (_('Finish'), 'work_order.Finish'),
        (_('Cancel'), 'work_order.Cancel'),
        (_('Deliver'), 'work_order.Close'),
        (_('Approve'), 'work_order.Approve'),
        (_('Pause the work'), 'work_order.Pause'),
        (_('Start the work'), 'work_order.Work'),
        (_('Reject order'), 'work_order.Reject'),
        (_('Check order'), 'work_order.CheckOrder'),
        (_('Inform client'), 'work_order.InformClient'),
        (_('Undo order rejection'), 'work_order.UndoRejection'),
        (_('Repoen order'), 'work_order.Reopen'),
    ]

    def __init__(self, model):
        self.model = model
        self.actions = WorkOrderActions.get_instance()
        super(WorkOrderRow, self).__init__()
        self.props.margin = 3
        self.set_name('WorkOrderRow')
        self._create_ui(model)
        self.show_all()

    def _create_ui(self, model):
        client = '<b>%s</b>: %s' % (_('Client'), api.escape(model.client_name))
        due_date = ''
        if model.estimated_finish:
            due_date = '%s: %s' % (_('Due date'),
                                   api.escape(model.estimated_finish.strftime('%x')))

        identifier = '<b>%s</b>' % api.escape(str(model.identifier))
        salesperson = '<b>%s</b>:' % _('Salesperson')
        if model.sale:
            salesperson += ' %s' % api.escape(model.sale.get_salesperson_name())
        else:
            employee = model.work_order.quote_responsible
            if employee:
                salesperson += ' %s' % api.escape(employee.person.name)

        self.due_date = self._new_label(due_date, xalign=1)
        self.client = self._new_label(client, expand=True)
        self.identifier = self._new_label(identifier, expand=True, halign=Gtk.Align.START)
        self.salesperson = self._new_label(salesperson, expand=False, halign=Gtk.Align.START)
        self.status = self._new_label('%s' % api.escape(model.status_str),
                                      xalign=1, halign=Gtk.Align.END)
        self.status.get_style_context().add_class('tag')
        hbox = Gtk.HBox(spacing=6)
        informed_date = model.work_order.client_informed_date
        if model.status == model.work_order.STATUS_WORK_FINISHED and informed_date:
            self.status.get_style_context().add_class('client-informed')
            informed_image = Gtk.Image.new_from_icon_name('call-start-symbolic',
                                                          Gtk.IconSize.BUTTON)
            formatted_date = api.escape(informed_date.strftime('%x'))
            informed_image.set_tooltip_text(_('Client informed %s') % formatted_date)
            hbox.pack_start(informed_image, True, True, 0)
            hbox.set_halign(Gtk.Align.END)
        else:
            self.status.get_style_context().add_class(model.status)

        eb = Gtk.EventBox()
        eb.set_halign(Gtk.Align.END)
        eb.add(self.status)
        hbox.add(eb)

        grid = Gtk.Grid()
        grid.props.margin = 5
        grid.set_row_spacing(1)
        grid.set_column_spacing(3)

        grid.attach(self.identifier, 0, 0, 1, 1)
        grid.attach(self.salesperson, 0, 1, 1, 1)
        grid.attach(self.client, 0, 2, 1, 1)
        grid.attach(hbox, 1, 0, 1, 1)
        grid.attach(self.due_date, 1, 2, 1, 1)
        self.add(grid)

        eb.connect('realize', self._on_realize)
        eb.connect('button-release-event', self._on_status__clicked)

    def _new_label(self, markup, expand=False, xalign=0, halign=Gtk.Align.FILL):
        label = Gtk.Label(label=markup)
        label.set_use_markup(True)
        label.set_xalign(xalign)
        label.set_halign(halign)
        label.set_hexpand(expand)
        return label

    #
    #   Callbacks
    #

    def _on_realize(self, widget):
        display = Gdk.Display.get_default()
        cursor = Gdk.Cursor.new_for_display(display, Gdk.CursorType.HAND1)
        widget.get_window().set_cursor(cursor)

    def _on_status__clicked(self, widget, event):
        if event.button != 1:
            return
        self.actions.set_model(self.model.work_order)
        status_model = Gio.Menu()
        for spec in self.state_changes:
            action = self.actions.get_action(spec[1].split('.')[1])
            # Only add the action if its enabled. This will look better since there are a lot of
            # status changes that can happen
            if action.get_enabled():
                status_model.append_item(Gio.MenuItem.new(spec[0], spec[1]))

        wo_options = Gio.Menu()
        for spec in self.options:
            wo_options.append_item(Gio.MenuItem.new(spec[0], spec[1]))
        status_model.append_item(Gio.MenuItem.new_section(None, wo_options))
        popover = Gtk.Popover.new_from_model(widget, status_model)
        popover.set_position(Gtk.PositionType.BOTTOM)
        popover.show()
        return True


class WorkOrderList(Gtk.Box):

    def __init__(self, store):
        self.store = store
        actions = WorkOrderActions.get_instance()
        self._edited_id = actions.connect('model-edited', self._on_actions__model_edited)
        self._created_id = actions.connect('model-created', self._on_actions__model_created)

        super(WorkOrderList, self).__init__(orientation=Gtk.Orientation.VERTICAL)
        self.set_size_request(600, -1)
        self.list_box = Gtk.ListBox()
        # Only activate with a double-click
        self.list_box.set_property('activate_on_single_click', False)
        self.list_box.set_header_func(self._header_func)
        self.list_box.connect('row-activated', self._on_list_box__row_activated)

        for row in self._get_orders():
            self.list_box.add(WorkOrderRow(row))

        self.pack_start(Section(_('My Work Orders')), False, False, 0)
        self.pack_start(self.list_box, True, True, 0)

    def do_destroy(self):
        actions = WorkOrderActions.get_instance()
        actions.disconnect(self._edited_id)
        actions.disconnect(self._created_id)

    def _header_func(self, row, before):
        from stoqlib.lib.dateutils import localnow

        def _age(date):
            if not date:
                return None
            diff = (localnow().date() - date.date()).days
            if diff > 7:
                return _('More than one week')
            elif 2 <= diff <= 7:
                return _('More than two days')
            elif diff == 1:
                return _('Yesterday')
            elif diff == 0:
                return _('Today')
            elif diff == -1:
                return _('Tomorrow')
            elif -7 < diff < -1:
                return _('Next 7 days')
            else:
                return _('Future')

        row_age = _age(row.model.estimated_finish)
        before_age = None
        if before:
            before_age = _age(before.model.estimated_finish)
        if row_age != before_age:
            label = Gtk.Label(label=row_age)
            label.props.margin = 6
            row.set_header(label)
        else:
            row.set_header(Gtk.Separator())

    def _get_orders(self):
        branch = api.get_current_branch(self.store)
        query = Eq(WorkOrderView.branch_id, branch.id)
        result = WorkOrderView.find_pending(self.store).find(query)
        return result.order_by(WorkOrder.estimated_finish, WorkOrder.status)

    def _update_view(self, select_item=None):
        # Refresh
        for child in self.list_box.get_children():
            self.list_box.remove(child)

        for row in self._get_orders():
            self.list_box.add(WorkOrderRow(row))

    #
    #   Callbacks
    #

    def _on_actions__model_created(self, actions, order):
        self._update_view(select_item=order)

    def _on_actions__model_edited(self, actions, order):
        self._update_view()

    def _on_list_box__row_activated(self, action, order):
        order.actions.details(order.model.work_order)
