# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2010 Async Open Source <http://www.async.com.br>
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
## Author(s):   George Kussumoto            <george@async.com.br>
##              Ronaldo Maia                <romaia@async.com.br>
##
##
""" Consignment wizard definition """

import datetime
from decimal import Decimal
import sys

import gtk

from kiwi.datatypes import currency
from kiwi.ui.widgets.list import Column

from stoqlib.database.runtime import (get_current_user, new_transaction,
                                      finish_transaction)
from stoqlib.domain.interfaces import IStorable
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.domain.payment.operation import register_payment_operations
from stoqlib.domain.purchase import (PurchaseOrderView, PurchaseItemView,
                                     PurchaseOrder)
from stoqlib.domain.receiving import (ReceivingOrder,
                                      get_receiving_items_by_purchase_order)
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.lists import AdditionListSlave
from stoqlib.gui.base.wizards import BaseWizard, BaseWizardStep
from stoqlib.gui.wizards.purchasewizard import (StartPurchaseStep,
                                                PurchaseItemStep,
                                                PurchasePaymentStep,
                                                FinishPurchaseStep,
                                                PurchaseWizard)
from stoqlib.gui.wizards.receivingwizard import (PurchaseSelectionStep,
                                                 ReceivingInvoiceStep)
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.validators import format_quantity, get_formatted_cost

_ = stoqlib_gettext


#
# Wizard Steps
#

class StartConsignmentStep(StartPurchaseStep):

    def next_step(self):
        return ConsignmentItemStep(self.wizard, self, self.conn, self.model)


class ConsignmentItemStep(PurchaseItemStep):

    def _create_receiving_order(self):
        self.model.set_consigned()

        receiving_model = ReceivingOrder(
            responsible=get_current_user(self.conn),
            purchase=self.model,
            supplier=self.model.supplier,
            branch=self.model.branch,
            transporter=self.model.transporter,
            invoice_number=None,
            connection=self.conn)

        # Creates ReceivingOrderItem's
        get_receiving_items_by_purchase_order(self.model, receiving_model)

        self.wizard.receiving_model = receiving_model

    def has_next_step(self):
        return True

    def next_step(self):
        self._create_receiving_order()
        return ReceivingInvoiceStep(self.conn, self.wizard,
                                    self.wizard.receiving_model)


class ConsignmentSelectionStep(PurchaseSelectionStep):

    def get_extra_query(self, states):
        return PurchaseOrderView.q.status == PurchaseOrder.ORDER_CONSIGNED

    def next_step(self):
        self.search.save_columns()
        selected = self.search.results.get_selected()
        consignment = selected.purchase
        self.wizard.purchase_model = consignment

        return ConsignmentItemSelectionStep(self.wizard, self, self.conn, consignment)


class _InConsignmentItem(object):
    def __init__(self, item):
        self.item = item
        self.order = item.order.get_order_number_str()
        self.id = item.id
        self.code = item.sellable.code
        self.description = item.sellable.get_description()
        self.consigned = item.quantity_received
        self.cost = item.cost
        self.returned = item.quantity_returned
        self.sellable = item.sellable

        self.branch = item.order.branch

        storable = IStorable(item.sellable.product)
        self.stock = storable.get_stock_item(self.branch).quantity
        self._sold = 0
        self.sold_total = 0

    def get_sold(self):
        return self._sold

    def set_sold(self, qtd):
        self._sold = qtd
        if qtd < 0:
            self._sold = 0
            self.sold_total = 0
        else:
            self.sold_total = currency(self._sold * Decimal(self.cost))

    sold = property(get_sold, set_sold)

    def sync(self, trans):
        real_obj = trans.get(self.item)
        real_obj.quantity_sold = self._sold
        real_obj.quantity_returned = self.returned


class ConsignmentItemSelectionStep(BaseWizardStep):
    gladefile = 'ConsignmentItemSelectionStep'

    def __init__(self, wizard, previous, conn, consignment):
        self.consignment = consignment
        BaseWizardStep.__init__(self, conn, wizard, previous)
        self.reset_sold_button.set_sensitive(False)
        self.return_items_radio.hide()
        self._setup_slaves()

    def _setup_slaves(self):
        self.slave = AdditionListSlave(
            self.conn, self.get_columns(),
            klist_objects=self.get_saved_items())
        self.slave.hide_add_button()
        self.slave.hide_edit_button()
        self.slave.hide_del_button()
        self.slave.klist.connect('cell-edited',
                                 self._on_list_slave__cell_edited)
        self.attach_slave('place_holder', self.slave)

    def _set_all_sold(self):
        for item in self.slave.klist:
            item.sold = item.consigned
        self.slave.klist.refresh()
        self.new_consignment_radio.set_sensitive(False)
        self.return_items_radio.set_sensitive(False)
        self.all_sold_button.set_sensitive(False)
        self.reset_sold_button.set_sensitive(True)
        self._validate_step()

    def _unset_all_sold(self):
        for item in self.slave.klist:
            item.sold = 0
        self.slave.klist.refresh()
        self.new_consignment_radio.set_sensitive(True)
        self.return_items_radio.set_sensitive(True)
        self.all_sold_button.set_sensitive(True)
        self.reset_sold_button.set_sensitive(False)
        self._validate_step()

    def _is_all_sold(self):
        return all([i.sold == i.consigned for i in self.slave.klist])

    def _get_total_charged(self):
        if self._is_all_sold():
            return Decimal(0)
        return sum([i.sold_total for i in self.slave.klist], Decimal(0))

    def _set_error_message(self, msg):
        if not msg:
            self.error_label.hide()
        else:
            self.error_label.show()

        self.error_label.set_size('small')
        self.error_label.set_color('red')
        self.error_label.set_text('<i>%s</i>' % msg)

    def _validate_step(self, validation_value=False):
        is_valid = True
        total = 0
        for item in self.slave.klist:
            total += item.sold + item.returned
            if item.sold > item.consigned:
                is_valid = False
            if item.returned + item.sold > item.consigned:
                is_valid = False

        if not is_valid:
            error_msg = _(u'Sold and returned items quantity are greater than '
                           'the consigned quantity.')
            self._set_error_message(error_msg)
        else:
            self._set_error_message('')

        self.wizard.refresh_next(is_valid and total > 0)

    def _format_qty(self, quantity):
        # primitive validation
        if quantity >= 0:
            return format_quantity(quantity)
        return format_quantity(0)

    def _clone_consignment(self, trans):
        model = trans.get(self.consignment)
        consignment = model.clone()
        consignment.status = PurchaseOrder.ORDER_PENDING
        consignment.group = PaymentGroup(connection=trans)
        consignment.open_date = datetime.date.today()
        # since we will receive the remaining items again, we will return all
        # products remaining now.
        for item in self.slave.klist:
            item.sync(trans)
            old_item = trans.get(item.item)
            new_item = old_item.clone()
            new_item.quantity = item.consigned - item.sold - item.returned
            self._return_single_item(new_item.sellable, new_item.quantity)

            new_item.quantity_returned = Decimal(0)
            new_item.quantity_sold = Decimal(0)
            new_item.quantity_received = Decimal(0)
            new_item.order = consignment
        return consignment

    def _create_new_consignment(self):
        trans = new_transaction()
        new_consignment = self._clone_consignment(trans)
        retval = run_dialog(ConsignmentWizard, self, trans,
                            new_consignment)
        finish_transaction(trans, retval)
        trans.close()
        return retval

    def _return_single_item(self, sellable, quantity):
        storable = IStorable(sellable.product, None)
        assert storable

        branch = self.consignment.branch
        storable.decrease_stock(quantity=quantity, branch=branch)

    def _finish_consignment(self):
        trans = new_transaction()
        reconsignment = False
        for item in self.slave.klist:
            item.sync(trans)
            if item.returned:
                consignment_item = item.item
                self._return_single_item(consignment_item.sellable,
                                         consignment_item.quantity_returned)
            remaining = item.consigned - item.sold - item.returned
            if not reconsignment and remaining > 0:
                reconsignment = True
        finish_transaction(trans, True)
        trans.close()
        if reconsignment:
            retval = self._create_new_consignment()
            return bool(retval)
        return True

    def get_saved_items(self):
        for item in self.consignment.get_items():
            yield _InConsignmentItem(item)

    def get_columns(self):
        adj = gtk.Adjustment(upper=sys.maxint, step_incr=1)
        return [
            Column('order', title=_('Order'), width=60, data_type=str,
                   sorted=True),
            Column('code', title=_('Code'), width=70, data_type=str),
            Column('description', title=_('Description'),
                   data_type=str, expand=True, searchable=True),
            Column('stock', title=_('Stock'), data_type=Decimal,
                   format_func=format_quantity),
            Column('consigned', title=_('Consigned'), data_type=Decimal,
                   format_func=format_quantity),
            Column('sold', title=_('Sold'), data_type=Decimal,
                   editable=True, spin_adjustment=adj,
                   format_func=self._format_qty, width=90),
            Column('returned', title=_('Returned'), data_type=Decimal,
                   editable=True, spin_adjustment=adj,
                   format_func=self._format_qty, width=90),
            Column('cost', title=_('Cost'), data_type=currency,
                   format_func=get_formatted_cost),
            Column('sold_total', title=_('Total Sold'), data_type=currency),
            ]

    def post_init(self):
        self.register_validate_function(self._validate_step)
        self.force_validation()

    def has_previous_step(self):
        return True

    def has_next_step(self):
        return True

    def next_step(self):
        retval = self._finish_consignment()
        if not retval:
            return self
        outstanding_value = self._get_total_charged()
        return CloseConsignmentPaymentStep(self.wizard, self, self.conn,
                                           self.consignment,
                                           outstanding_value=outstanding_value)

    def _on_list_slave__cell_edited(self, widget, data, attr):
        self._validate_step()

    def on_all_sold_button__clicked(self, widget):
        self._set_all_sold()

    def on_reset_sold_button__clicked(self, widget):
        self._unset_all_sold()


class CloseConsignmentPaymentStep(PurchasePaymentStep):

    def has_previous_step(self):
        return False

    def has_next_step(self):
        return False


#
# Main wizards
#


class ConsignmentWizard(PurchaseWizard):
    title = _("New Consignment")

    def __init__(self, conn, model=None):
        model = model or self._create_model(conn)

        # If we receive the order right after the purchase.
        self.receiving_model = None
        register_payment_operations()
        first_step = StartConsignmentStep(self, conn, model)
        BaseWizard.__init__(self, conn, first_step, model)


    def _create_model(self, conn):
        model = PurchaseWizard._create_model(self, conn)
        model.consignment = True
        return model


class CloseInConsignmentWizard(BaseWizard):
    title = _('Closing In Consignment')
    size = (790, 400)

    def __init__(self, conn):
        register_payment_operations()
        self.purchase_model = None
        first_step = ConsignmentSelectionStep(self, conn)
        BaseWizard.__init__(self, conn, first_step, None)
        self.next_button.set_sensitive(False)

    #
    # WizardStep hooks
    #

    def finish(self):
        purchase = self.conn.get(self.purchase_model)
        purchase.confirm()
        purchase.close()

        self.retval = self.purchase_model
        self.close()
