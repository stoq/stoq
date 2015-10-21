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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
""" Consignment wizard definition """

from decimal import Decimal

from kiwi.currency import currency
from kiwi.python import Settable
from kiwi.ui.objectlist import Column

from stoqlib.api import api
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.purchase import PurchaseOrderView, PurchaseOrder
from stoqlib.domain.receiving import ReceivingOrder
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.wizards import BaseWizard, BaseWizardStep
from stoqlib.gui.editors.purchaseeditor import InConsignmentItemEditor
from stoqlib.gui.search.searchcolumns import IdentifierColumn
from stoqlib.gui.slaves.paymentslave import (register_payment_slaves,
                                             MultipleMethodSlave)
from stoqlib.gui.wizards.purchasewizard import (StartPurchaseStep,
                                                PurchaseItemStep,
                                                PurchaseWizard)
from stoqlib.gui.wizards.receivingwizard import (PurchaseSelectionStep,
                                                 ReceivingInvoiceStep)
from stoqlib.lib.message import info
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.formatters import format_quantity, get_formatted_cost

_ = stoqlib_gettext


#
# Wizard Steps
#

class StartConsignmentStep(StartPurchaseStep):

    def next_step(self):
        self.wizard.all_products = self.all_products.get_active()
        return ConsignmentItemStep(self.wizard, self, self.store, self.model)


class ConsignmentItemStep(PurchaseItemStep):

    def _create_receiving_order(self):
        self.model.set_consigned()

        receiving_model = ReceivingOrder(
            responsible=api.get_current_user(self.store),
            supplier=self.model.supplier,
            branch=self.model.branch,
            transporter=self.model.transporter,
            invoice_number=None,
            store=self.store)
        receiving_model.add_purchase(self.model)

        # Creates ReceivingOrderItem's
        for item in self.model.get_pending_items():
            receiving_model.add_purchase_item(item)

        self.wizard.receiving_model = receiving_model

    def has_next_step(self):
        return True

    def next_step(self):
        self._create_receiving_order()
        return ReceivingInvoiceStep(self.store, self.wizard,
                                    self.wizard.receiving_model)


class ConsignmentSelectionStep(PurchaseSelectionStep):

    def get_extra_query(self, states):
        return PurchaseOrderView.status == PurchaseOrder.ORDER_CONSIGNED

    def next_step(self):
        self.search.save_columns()
        # FIXME: Precisa desabilitar se tem mais de um selecionado.
        selected = self.search.result_view.get_selected_rows()[0]
        consignment = selected.purchase
        self.wizard.purchase_model = consignment

        return ConsignmentItemSelectionStep(self.wizard, self, self.store, consignment)


class ConsignmentItemSelectionStep(BaseWizardStep):
    gladefile = 'ConsignmentItemSelectionStep'

    def __init__(self, wizard, previous, store, consignment):
        self.consignment = consignment
        BaseWizardStep.__init__(self, store, wizard, previous)
        self._original_items = {}
        self._setup_widgets()

    def _setup_widgets(self):
        self.consignment_items.set_columns(self.get_columns())
        self.consignment_items.add_list(self.get_saved_items())
        self.edit_button.set_sensitive(False)

    def _validate_step(self, value):
        self.wizard.refresh_next(value)

    def _edit_item(self, item):
        retval = run_dialog(InConsignmentItemEditor, self.wizard, self.store, item)
        if retval:
            self.consignment_items.update(item)
            self._validate_step(True)

    def get_saved_items(self):
        # we keep a copy of the important data to calculate values when we
        # finish this step
        for item in self.consignment.get_items():
            self._original_items[item.id] = Settable(item_id=item.id,
                                                     sold=item.quantity_sold,
                                                     returned=item.quantity_returned)
            # self.store.fetch: used to bring the objet to this store.
            yield self.store.fetch(item)

    def get_columns(self):
        return [
            IdentifierColumn('order.identifier', title=_('Order #'), sorted=True),
            Column('sellable.code', title=_('Code'), width=70, data_type=str),
            Column('sellable.description', title=_('Description'),
                   data_type=str, expand=True, searchable=True),
            Column('quantity_received', title=_('Consigned'), data_type=Decimal,
                   format_func=format_quantity),
            Column('quantity_sold', title=_('Sold'), data_type=Decimal,
                   width=90),
            Column('quantity_returned', title=_('Returned'), data_type=Decimal,
                   width=90),
            Column('cost', title=_('Cost'), data_type=currency,
                   format_func=get_formatted_cost),
            Column('total_sold', title=_('Total Sold'), data_type=currency),
        ]

    #
    # WizardStep
    #

    def post_init(self):
        self.register_validate_function(self._validate_step)
        self.force_validation()
        self._validate_step(False)

    def has_previous_step(self):
        return True

    def has_next_step(self):
        return True

    def next_step(self):
        total_charged = Decimal(0)
        for final in self.consignment_items:
            initial = self._original_items[final.id]
            to_sold = final.quantity_sold - initial.sold
            to_return = final.quantity_returned - initial.returned

            if to_return > 0:
                final.return_consignment(to_return)
            if to_sold > 0:
                total_charged += final.cost * to_sold

        if total_charged == 0:
            #FIXME Gramatical error
            info(_(u'No payments was generated.'),
                 _(u'The changes performed does not require payment creation, '
                   'so this wizard will be finished.'))
            self.wizard.finish()

        # total_charged plus what was previously charged
        total_charged += self.consignment.group.get_total_value()
        return CloseConsignmentPaymentStep(self.wizard, self, self.store,
                                           self.consignment,
                                           outstanding_value=total_charged)

    #
    # Kiwi Callbacks
    #

    def on_consignment_items__selection_changed(self, widget, item):
        self.edit_button.set_sensitive(bool(item))

    def on_consignment_items__row_activated(self, widget, item):
        self._edit_item(item)

    def on_edit_button__clicked(self, widget):
        item = self.consignment_items.get_selected()
        self._edit_item(item)


class CloseConsignmentPaymentStep(BaseWizardStep):
    gladefile = 'HolderTemplate'
    slave_holder = 'place_holder'

    def __init__(self, wizard, previous, store, consignment,
                 outstanding_value=Decimal(0)):
        self._method = PaymentMethod.get_by_name(store, u'money')
        BaseWizardStep.__init__(self, store, wizard, previous=None)
        self._consignment = consignment
        self._outstanding_value = outstanding_value
        self._setup_slaves()

    def _setup_slaves(self):
        self.slave = MultipleMethodSlave(self.wizard, self, self.store,
                                         self.store.fetch(self._consignment),
                                         None, self._outstanding_value,
                                         finish_on_total=False)
        self.attach_slave('place_holder', self.slave)

    def _validate_step(self, value):
        can_finish = value and self.slave.can_confirm()
        self.wizard.refresh_next(can_finish)

    def validate_step(self):
        return True

    def post_init(self):
        self.register_validate_function(self._validate_step)
        self.force_validation()
        self._validate_step(False)
        self.wizard.enable_finish()

    def has_next_step(self):
        return False


#
# Main wizards
#


class ConsignmentWizard(PurchaseWizard):
    title = _("New Consignment")
    help_section = None

    def __init__(self, store, model=None):
        model = model or self._create_model(store)

        # If we receive the order right after the purchase.
        self.receiving_model = None
        first_step = StartConsignmentStep(self, store, model)
        BaseWizard.__init__(self, store, first_step, model)

    def _create_model(self, store):
        model = PurchaseWizard._create_model(self, store)
        model.consigned = True
        return model


class CloseInConsignmentWizard(BaseWizard):
    title = _('Closing In Consignment')
    size = (790, 400)

    def __init__(self, store):
        register_payment_slaves()
        self.purchase_model = None
        first_step = ConsignmentSelectionStep(self, store)
        BaseWizard.__init__(self, store, first_step, None)
        self.next_button.set_sensitive(False)

    #
    # WizardStep hooks
    #

    def finish(self):
        purchase = self.store.fetch(self.purchase_model)
        can_close = all([i.quantity_received == i.quantity_sold +
                         i.quantity_returned
                         for i in purchase.get_items()])
        for payment in purchase.group.payments:
            if payment.is_preview():
                payment.set_pending()

        if can_close:
            purchase.confirm()
            purchase.close()

        self.retval = purchase
        self.close()
