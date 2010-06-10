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

from decimal import Decimal
import sys

import gtk

from kiwi.datatypes import currency
from kiwi.ui.widgets.list import Column

from stoqlib.database.runtime import get_current_branch, get_current_user
from stoqlib.domain.interfaces import IBranch, IStorable
from stoqlib.domain.payment.operation import register_payment_operations
from stoqlib.domain.person import Person
from stoqlib.domain.receiving import (ReceivingOrder,
                                      get_receiving_items_by_purchase_order)
from stoqlib.domain.views import InConsignmentsView
from stoqlib.gui.base.lists import AdditionListSlave
from stoqlib.gui.base.wizards import BaseWizard, BaseWizardStep
from stoqlib.gui.wizards.purchasewizard import (StartPurchaseStep,
                                                PurchaseItemStep,
                                                PurchasePaymentStep,
                                                FinishPurchaseStep,
                                                PurchaseWizard)
from stoqlib.gui.wizards.receivingwizard import ReceivingInvoiceStep
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


class SupplierSelectionStep(BaseWizardStep):
    gladefile = 'SupplierSelectionStep'

    def __init__(self, wizard, conn):
        BaseWizardStep.__init__(self, conn, wizard)
        self._setup_slaves()

    def _setup_slaves(self):
        self.slave = AdditionListSlave(
            self.conn, self._get_columns(),
            klist_objects=self._get_supliers())
        self.slave.hide_add_button()
        self.slave.hide_edit_button()
        self.slave.hide_del_button()
        self.attach_slave('place_holder', self.slave)
        self.slave.klist.set_selection_mode(gtk.SELECTION_BROWSE)
        self.slave.klist.connect('selection-changed',
                        self._on_results__selection_changed)

        current_branch = get_current_branch(self.conn)
        branches = [(b.person.name, b)
                    for b in Person.iselect(IBranch, connection=self.conn)]
        self.branch.prefill(branches)
        self.branch.set_text(current_branch.person.name)


    def _get_supliers(self):
        branch = self.branch.get_selected()
        if not branch:
            return []

        items = []
        #query = InConsignment.q.status ==  InConsignment.CONSIGNMENT_CONFIRMED
        query = None
        items = InConsignmentsView.select_by_branch(
                                    query,
                                    branch = branch,
                                    connection=self.conn)
        return items

    def _get_columns(self):
        return [Column('supplier_name', title=_('Supplier'), data_type=str,
                        expand=True),
                Column('open_consignments', title=_('Open Consignments'),
                        data_type=int),
                ]

    def _update_results(self):
        self.slave.klist.clear()
        self.slave.klist.add_list(self._get_supliers())

    def _update_view(self):
        selected = self.slave.klist.get_selected()
        has_selected = selected is not None
        self.wizard.refresh_next(has_selected)

    #
    # WizardStep hooks
    #

    def next_step(self):
        selected = self.slave.klist.get_selected()
        supplier = selected.supplier
        branch = self.branch.get_selected()

        return ItemSelectionStep(self.wizard, self, self.conn,
                                 supplier, branch, selected.consignments)

    #
    # Callbacks
    #

    def _on_results__selection_changed(self, widget, item):
        self._update_view()

    def on_branch__content_changed(self, *args):
        self._update_results()


class _InConsignmentItem(object):
    def __init__(self, item):
        self.item = item
        self.order = item.order.get_order_number_str()
        self.id = item.id
        self.code = item.sellable.code
        self.description = item.sellable.get_description()
        self.consigned = item.quantity_received
        self.cost = item.cost
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


class ItemSelectionStep(BaseWizardStep):
    gladefile = 'ItemSelectionStep'

    def __init__(self, wizard, previous, conn, supplier, branch, consignments):
        self.supplier = supplier
        self.branch = branch
        self.consignments = consignments
        BaseWizardStep.__init__(self, conn, wizard, previous)
        self.reset_sold_button.set_sensitive(False)
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
            total += item.sold
            if item.sold > item.consigned:
                is_valid = False

        if not is_valid:
            error_msg = _(u'Sold items quantity are greater than the '
                           'consigned quantity.')
            self._set_error_message(error_msg)
        else:
            self._set_error_message('')

        self.wizard.refresh_next(is_valid and total > 0)

    def _format_qty(self, quantity):
        # primitive validation
        if quantity >= 0:
            return format_quantity(quantity)
        return format_quantity(0)

    def get_saved_items(self):
        for consig in self.consignments:
            for i in consig.get_items():
                yield _InConsignmentItem(i)

    def get_columns(self):
        adj = gtk.Adjustment(upper=sys.maxint, step_incr=1)
        return [
            Column('order', title=_('Order'), width=60, data_type=str,
                   sorted=True),
            Column('code', title=_('Code'), width=70, data_type=int),
            Column('description', title=_('Description'),
                   data_type=str, expand=True, searchable=True),
            Column('stock', title=_('Stock'), data_type=Decimal,
                   format_func=format_quantity),
            Column('consigned', title=_('Consigned'), data_type=Decimal,
                   format_func=format_quantity),
            Column('sold', title=_('Sold'), data_type=Decimal,
                   editable=True, spin_adjustment=adj,
                   format_func=self._format_qty, width=90),
            #Column('to_buy', title=_('Buy'), data_type=Decimal,
            #       format_func=format_quantity, width=70, editable=True),
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
        # cases:
        # a) items sold == items consigned: finalize consignment
        # b) items sold < items consigned:
        #    c) create new consignment with the remaining items
        #    d) return the remaining items
        if self._is_all_sold():
            pass # go to the final step
        if self.new_consignment_radio.is_active():
            pass # go to the new consignment step
        else:
            pass # go to the return items step


        ## Now, we should create a new PurchaseOrder with the items we sold.
        #order = self._create_order()
        #for consig_item in self.slave.klist:
        #    # add new sale item
        #    item = order.add_item(consig_item.sellable, consig_item.sold)
        #    item.cost = consig_item.avg_cost
        #    order.receive_item(item, consig_item.sold)

        #order.set_valid()

        ## Close previous consignments
        #for consig in self.consignments:
        #    consig = self.conn.get(consig)
        #    consig.purchase_order = order
        #    consig.close()

        ## Create a new one with the remaining items
        #if self.create_new_consignment.get_active():
        #    print 'Creating new consignment'

        ## Next step
        #return CloseConsignmentPaymentStep(self.wizard, self, self.conn, order)

    def _on_list_slave__cell_edited(self, widget, data, attr):
        self._validate_step()

    def on_all_sold_button__clicked(self, widget):
        self._set_all_sold()

    def on_reset_sold_button__clicked(self, widget):
        self._unset_all_sold()


class CloseConsignmentPaymentStep(PurchasePaymentStep):

    def _create_receiving_order(self):
        # since we will create a new receiving order, we should confirm the
        # purchase first.
        self.order.confirm()

        receiving_model = ReceivingOrder(
            responsible=get_current_user(self.conn),
            purchase=self.order,
            supplier=self.order.supplier,
            branch=self.order.branch,
            transporter=self.order.transporter,
            invoice_number=None,
            connection=self.conn)

        # Creates ReceivingOrderItem's
        get_receiving_items_by_purchase_order(self.order, receiving_model)

        self.wizard.receiving_model = receiving_model

    def next_step(self):
        # TODO: Create ReceivingOrder
        #return FinishCloseConsignmentStep(self.wizard, self, self.conn,
        #                                  self.order)

        self._create_receiving_order()
        return ReceivingInvoiceStep(self.conn, self.wizard,
                                    self.wizard.receiving_model)


class FinishCloseConsignmentStep(FinishPurchaseStep):

    def __init__(self, wizard, previous, conn, model):
        FinishPurchaseStep.__init__(self, wizard, previous, conn, model)
        self.receive_now.hide()

    def has_next_step(self):
        return True

    def next_step(self):
        return ReceivingInvoiceStep(self.conn, self.wizard,
                                    self.wizard.receiving_model)

#
# Main wizards
#


class ConsignmentWizard(PurchaseWizard):
    title = _("New Consignment")

    def __init__(self, conn):
        model = self._create_model(conn)

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
        self.receiving_model = None
        first_step = SupplierSelectionStep(self, conn)
        BaseWizard.__init__(self, conn, first_step, None)
        self.next_button.set_sensitive(False)

    #
    # WizardStep hooks
    #

    def finish(self):
        #if not self.receiving_model.get_valid():
        #    self.receiving_model.set_valid()
        #self.receiving_model.confirm(already_received=True)

        self.retval = False
        self.close()
