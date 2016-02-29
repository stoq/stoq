# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##

import collections
import datetime
import decimal

import gtk

from kiwi import ValueUnset
from kiwi.currency import currency
from kiwi.datatypes import ValidationError
from kiwi.python import Settable
from kiwi.ui.forms import PriceField, NumericField
from kiwi.ui.objectlist import Column
import pango
from storm.expr import And, Eq, Or

from stoqlib.api import api
from stoqlib.database.expr import Field
from stoqlib.domain.person import Employee
from stoqlib.domain.sellable import Sellable
from stoqlib.domain.views import SellableFullStockView
from stoqlib.domain.workorder import (WorkOrder, WorkOrderItem,
                                      WorkOrderHistoryView)
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.dialogs.batchselectiondialog import BatchDecreaseSelectionDialog
from stoqlib.gui.dialogs.credentialsdialog import CredentialsDialog
from stoqlib.gui.editors.baseeditor import BaseEditorSlave, BaseEditor
from stoqlib.gui.editors.noteeditor import NoteEditor
from stoqlib.gui.wizards.abstractwizard import SellableItemSlave
from stoqlib.lib.dateutils import localtoday
from stoqlib.lib.decorators import cached_property
from stoqlib.lib.defaults import QUANTITY_PRECISION, MAX_INT
from stoqlib.lib.formatters import format_quantity, format_sellable_description
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class _WorkOrderItemBatchSelectionDialog(BatchDecreaseSelectionDialog):
    # When indicating the batches to reserve items bellow, make sure the user
    # doesn't select more batches than he selected to reserve.
    validate_max_quantity = True


class _WorkOrderItemEditor(BaseEditor):
    model_name = _(u'Work order item')
    model_type = WorkOrderItem
    confirm_widgets = ['price', 'quantity', 'quantity_reserved']

    @cached_property()
    def fields(self):
        return collections.OrderedDict(
            price=PriceField(_(u'Price'), proxy=True, mandatory=True),
            quantity=NumericField(_(u'Quantity'), proxy=True, mandatory=True),
            quantity_reserved=NumericField(_(u'Reserved quantity')),
        )

    def __init__(self, store, model, visual_mode=False):
        self._original_quantity_decreased = model.quantity_decreased
        self.manager = None
        BaseEditor.__init__(self, store, model, visual_mode=visual_mode)
        self.price.set_icon_activatable(gtk.ENTRY_ICON_PRIMARY,
                                        activatable=True)

    #
    #  BaseEditor
    #

    def setup_proxies(self):
        unit = self.model.sellable.unit
        digits = QUANTITY_PRECISION if unit and unit.allow_fraction else 0
        for widget in [self.quantity, self.quantity_reserved]:
            widget.set_digits(digits)

        self.quantity.set_range(1, MAX_INT)
        # If there's a sale, we can't change it's quantity, but we can
        # reserve/return_to_stock them. On the other hand, if there's no sale,
        # the quantity_reserved must be in sync with quantity
        # *Only products with stock control can be reserved
        storable = self.model.sellable.product_storable
        if self.model.order.sale_id is not None and storable:
            self.price.set_sensitive(False)
            self.quantity.set_sensitive(False)
            self.quantity_reserved.set_range(0, self.model.quantity)
        else:
            self.quantity_reserved.set_range(0, MAX_INT)
            self.quantity_reserved.set_visible(False)
            self.fields['quantity_reserved'].label_widget.set_visible(False)

        # We need to add quantity_reserved to a proxy or else it's validate
        # method won't do anything
        self.add_proxy(
            Settable(quantity_reserved=self.model.quantity_decreased),
            ['quantity_reserved'])

    def on_confirm(self):
        diff = (self.quantity_reserved.read() -
                self._original_quantity_decreased)

        if diff == 0:
            return
        elif diff < 0:
            self.model.return_to_stock(-diff)
            return

        storable = self.model.sellable.product_storable
        # This can only happen for diff > 0. If the product is marked to
        # control batches, no decreased should have been made without
        # specifying a batch on the item
        if storable and storable.is_batch and self.model.batch is None:
            # The only way self.model.batch is None is that this item
            # was created on a sale quote and thus it has a sale_item
            sale_item = self.model.sale_item

            batches = run_dialog(
                _WorkOrderItemBatchSelectionDialog, self, self.store,
                model=storable, quantity=diff)
            if not batches:
                return

            for s_item in [sale_item] + sale_item.set_batches(batches):
                wo_item = WorkOrderItem.get_from_sale_item(self.store,
                                                           s_item)
                if wo_item.batch is not None:
                    wo_item.reserve(wo_item.quantity)
        elif storable:
            self.model.reserve(diff)

    #
    #  Private
    #

    def _validate_quantity(self, value):
        storable = self.model.sellable.product_storable
        if storable is None:
            return

        if self.model.batch is not None:
            balance = self.model.batch.get_balance_for_branch(
                self.model.order.branch)
        else:
            balance = storable.get_balance_for_branch(self.model.order.branch)

        if value > self._original_quantity_decreased + balance:
            return ValidationError(
                _(u"This quantity is not available in stock"))

    #
    #  Callbacks
    #

    def on_price__validate(self, widget, value):
        if value <= 0:
            return ValidationError(_(u"The price must be greater than 0"))

        sellable = self.model.sellable
        self.manager = self.manager or api.get_current_user(self.store)

        # FIXME: Because of the design of the editor, the client
        # could not be set yet.
        category = self.model.order.client and self.model.order.client.category
        valid_data = sellable.is_valid_price(value, category, self.manager)
        if not valid_data['is_valid']:
            return ValidationError(
                (_(u'Max discount for this product is %.2f%%.') %
                 valid_data['max_discount']))

    def on_price__icon_press(self, entry, icon_pos, event):
        if icon_pos != gtk.ENTRY_ICON_PRIMARY:
            return

        # Ask for the credentials of a different user that can possibly allow a
        # bigger discount.
        self.manager = run_dialog(CredentialsDialog, self, self.store)
        if self.manager:
            self.price.validate(force=True)

    def on_quantity__content_changed(self, entry):
        # Check if 'quantity' widget is valid, before update the 'quantity_reserved'.
        # We need make this, because the 'validate' signal of 'quantity_reserved'
        # is not emitted when force the update of that widget
        if self.quantity.validate() is not ValueUnset:
            self.quantity_reserved.update(entry.read())

    def on_quantity__validate(self, entry, value):
        if value <= 0:
            return ValidationError("The quantity must be greater than 0")

        return self._validate_quantity(value)

    def on_quantity_reserved__validate(self, widget, value):
        return self._validate_quantity(value)


class _WorkOrderItemSlave(SellableItemSlave):
    model_type = WorkOrder
    summary_label_text = '<b>%s</b>' % api.escape(_("Total:"))
    sellable_view = SellableFullStockView
    item_editor = _WorkOrderItemEditor
    validate_stock = True
    validate_price = True
    value_column = 'price'
    batch_selection_dialog = BatchDecreaseSelectionDialog

    def __init__(self, store, parent, model=None, visual_mode=False):
        super(_WorkOrderItemSlave, self).__init__(store, parent, model=model,
                                                  visual_mode=visual_mode)

        # If the workorder already has a sale, we cannot add items directly
        # to the work order, but must use the sale editor to do so.
        self.hide_add_button()
        if model.sale_id:
            self.hide_del_button()
            self.hide_item_addition_toolbar()
            self.slave.set_message(
                _(u"This order is related to a sale. Edit the sale if you "
                  u"need to change the items"))

        # If the os is not on it's original branch, don't allow
        # the user to edit it (the edit is used to change quantity or
        # reserve/return_to_stock them)
        if model.branch_id != model.current_branch_id:
            self.hide_del_button()
            self.hide_item_addition_toolbar()
            self.hide_edit_button()

    #
    #  SellableItemSlave
    #

    def get_columns(self, editable=True):
        return [
            Column('sellable.code', title=_(u'Code'),
                   data_type=str, visible=False),
            Column('sellable.barcode', title=_(u'Barcode'),
                   data_type=str, visible=False),
            Column('sellable.description', title=_(u'Description'),
                   data_type=str, expand=True,
                   format_func=self._format_description, format_func_data=True),
            Column('price', title=_(u'Price'),
                   data_type=currency),
            Column('quantity', title=_(u'Quantity'),
                   data_type=decimal.Decimal, format_func=format_quantity),
            Column('quantity_decreased', title=_(u'Consumed quantity'),
                   data_type=decimal.Decimal, format_func=format_quantity),
            Column('total', title=_(u'Total'),
                   data_type=currency),
        ]

    def get_remaining_quantity(self, sellable, batch=None):
        # The original get_remaining_quantity will take items of the same
        # sellable on the list here and discount them from the balance. We
        # can't allow that since, unlike other SellableItemSlave subclasses,
        # the stock is decreased as soon as the item is added.
        storable = sellable.product_storable
        if storable:
            return storable.get_balance_for_branch(self.model.branch)
        else:
            return None

    def get_saved_items(self):
        return self.model.order_items

    def get_order_item(self, sellable, price, quantity, batch=None, parent=None):
        item = self.model.add_sellable(sellable, price=price,
                                       quantity=quantity, batch=batch)
        # Storable items added here are consumed at the same time
        storable = item.sellable.product_storable
        if storable:
            item.reserve(quantity)
        return item

    def get_sellable_view_query(self):
        return (self.sellable_view,
                # FIXME: How to do this using sellable_view.find_by_branch ?
                And(Or(Field('_stock_summary', 'branch_id') == self.model.branch.id,
                       Eq(Field('_stock_summary', 'branch_id'), None)),
                    Sellable.get_available_sellables_query(self.store)))

    def get_batch_items(self):
        # FIXME: Since the item will have it's stock synchronized above
        # (on sellable_selected) and thus having it's stock decreased,
        # we can't pass anything here. Find a better way to do this
        return []

    #
    #  Private
    #

    def _format_description(self, item, data):
        return format_sellable_description(item.sellable, item.batch)


class WorkOrderOpeningSlave(BaseEditorSlave):
    gladefile = 'WorkOrderOpeningSlave'
    model_type = WorkOrder
    proxy_widgets = [
        'defect_reported',
        'open_date',
    ]

    #
    #  BaseEditorSlave
    #

    def setup_proxies(self):
        # Set sensitivity before adding the proxy, otherwise, the open date will
        # be changed.
        if not api.sysparam.get_bool('ALLOW_OUTDATED_OPERATIONS'):
            self.open_date.set_sensitive(False)

        self.add_proxy(self.model, self.proxy_widgets)


class WorkOrderQuoteSlave(BaseEditorSlave):
    gladefile = 'WorkOrderQuoteSlave'
    model_type = WorkOrder
    proxy_widgets = [
        'defect_detected',
        'quote_responsible',
        'description',
        'estimated_cost',
        'estimated_finish',
        'estimated_hours',
        'estimated_start',
    ]

    #: If we should show an entry for the description
    #: (allowing it to be set or changed).
    show_description_entry = False

    #
    #  BaseEditorSlave
    #

    def setup_proxies(self):
        self._new_model = False
        self._fill_quote_responsible_combo()

        if not self.show_description_entry:
            self.description.hide()
            self.description_lbl.hide()

        self.add_proxy(self.model, self.proxy_widgets)

    def on_attach(self, editor):
        self._new_model = not editor.edit_mode

    #
    #  Private
    #

    def _fill_quote_responsible_combo(self):
        employees = Employee.get_active_employees(self.store)
        self.quote_responsible.prefill(api.for_person_combo(employees))

    #
    #  Callbacks
    #

    def on_estimated_start__validate(self, widget, value):
        if (self._new_model and value < localtoday() and
            not api.sysparam.get_bool('ALLOW_OUTDATED_OPERATIONS')):
            return ValidationError(u"The start date cannot be on the past")

        self.estimated_finish.validate(force=True)

    def on_estimated_finish__validate(self, widget, value):
        if (self._new_model and value < localtoday() and
            not api.sysparam.get_bool('ALLOW_OUTDATED_OPERATIONS')):
            return ValidationError(u"The end date cannot be on the past")

        estimated_start = self.estimated_start.read()
        if estimated_start and value < estimated_start:
            return ValidationError(
                _(u"Finished date needs to be after start date"))


class WorkOrderExecutionSlave(BaseEditorSlave):
    gladefile = 'WorkOrderExecutionSlave'
    model_type = WorkOrder
    proxy_widgets = [
        'execution_responsible',
    ]

    #
    #  BaseEditorSlave
    #

    def __init__(self, parent, *args, **kwargs):
        self.parent = parent
        BaseEditorSlave.__init__(self, *args, **kwargs)

    def setup_proxies(self):
        self._fill_execution_responsible_combo()

        self.proxy = self.add_proxy(self.model, self.proxy_widgets)

    def setup_slaves(self):
        self.sellable_item_slave = _WorkOrderItemSlave(
            self.store, self.parent, self.model, visual_mode=self.visual_mode)
        self.attach_slave('sellable_item_holder', self.sellable_item_slave)

    #
    #  Private
    #

    def _fill_execution_responsible_combo(self):
        employees = Employee.get_active_employees(self.store)
        self.execution_responsible.prefill(api.for_person_combo(employees))


class WorkOrderHistorySlave(BaseEditorSlave):
    """Slave responsible to show the history of a |workorder|"""

    gladefile = 'WorkOrderHistorySlave'
    model_type = WorkOrder

    #
    #  Public API
    #

    def update_items(self):
        """Update the items on the list

        Useful when a history is created when using this slave and
        we want it to show here at the same time.
        """
        self.details_list.add_list(
            WorkOrderHistoryView.find_by_work_order(self.store, self.model))

    #
    #  BaseEditorSlave
    #

    def setup_proxies(self):
        self.details_btn.set_sensitive(False)

        # TODO: Show a tooltip for each row displaying the reason
        self.details_list.set_columns([
            Column('date', _(u"Date"), data_type=datetime.datetime, sorted=True),
            Column('user_name', _(u"Who"), data_type=str, expand=True,
                   ellipsize=pango.ELLIPSIZE_END),
            Column('what', _(u"What"), data_type=str, expand=True),
            Column('old_value', _(u"Old value"), data_type=str, visible=False),
            Column('new_value', _(u"New value"), data_type=str),
            Column('notes', _(u"Notes"), data_type=str,
                   format_func=self._format_notes,
                   ellipsize=pango.ELLIPSIZE_END)])
        self.update_items()

    #
    #  Private
    #

    def _format_notes(self, notes):
        return notes.split('\n')[0]

    def _show_details(self, item):
        parent = self.get_toplevel().get_toplevel()
        # XXX: The window here is not decorated on gnome-shell, and because of
        # the visual_mode it gets no buttons. What to do?
        run_dialog(NoteEditor, parent, self.store, model=item,
                   attr_name='notes', title=_(u"Notes"), visual_mode=True)

    #
    #  Callbacks
    #

    def on_details_list__row_activated(self, details_list, item):
        if self.details_btn.get_sensitive():
            self._show_details(item)

    def on_details_list__selection_changed(self, details_list, item):
        self.details_btn.set_sensitive(bool(item and item.notes))

    def on_details_btn__clicked(self, button):
        selected = self.details_list.get_selected()
        self._show_details(selected)
