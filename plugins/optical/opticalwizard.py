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
""" Wizard for optical pre-sale"""

import gtk
from kiwi.ui.objectlist import Column

from stoqlib.domain.workorder import WorkOrder, WorkOrderItem
from stoqlib.gui.dialogs.batchselectiondialog import BatchDecreaseSelectionDialog
from stoqlib.gui.utils.printing import print_report
from stoqlib.gui.wizards.workorderquotewizard import (WorkOrderQuoteWizard,
                                                      WorkOrderQuoteStartStep,
                                                      WorkOrderQuoteWorkOrderStep,
                                                      WorkOrderQuoteItemStep)
from stoqlib.lib.message import yesno
from stoqlib.lib.translation import stoqlib_gettext as _

from .opticaldomain import OpticalWorkOrder
from .opticalslave import WorkOrderOpticalSlave
from .opticalreport import OpticalWorkOrderReceiptReport


class OpticalStartSaleQuoteStep(WorkOrderQuoteStartStep):
    """First step of the pre-sale for optical stores.

    This is just like the first step of the regular pre-sale, but it has a
    different next step.
    """

    #
    #  WorkOrderQuoteStartStep
    #

    def next_step(self):
        return OpticalWorkOrderStep(
            self.store, self.wizard, self, self.model)


class OpticalWorkOrderStep(WorkOrderQuoteWorkOrderStep):
    """Second step of the pre-sale for optical stores.

    In this step, the sales person will create the workorders required for this
    sale (one for each spectacles)
    """

    #
    #  WorkOrderQuoteWorkOrderStep
    #

    def next_step(self):
        return OpticalItemStep(self.wizard, self, self.store, self.model)

    def get_work_order_slave(self, work_order):
        return WorkOrderOpticalSlave(self.store, work_order,
                                     show_finish_date=True)


class OpticalItemStep(WorkOrderQuoteItemStep):
    """Third step of the optical pre-sale.

    Besides using the <stoqlib.gui.wizards.abstractwizard.SellableItemSlave> to
    add items to the sale, this step has a widget on the top to let the user
    choose on what work order he is adding the items.

    If the sale has more than 4 work orders, then the widget will be a combo
    box.  Otherwise, there will be up to 3 radio buttons for the user to choose
    the work order.
    """

    batch_selection_dialog = BatchDecreaseSelectionDialog
    allow_no_batch = True

    #
    #  WorkOrderQuoteItemStep
    #

    def get_order_item(self, sellable, price, quantity, batch=None):
        sale_item = super(OpticalItemStep, self).get_order_item(
            sellable, price, quantity, batch=batch)
        self._setup_patient(sale_item)

        wo_item = WorkOrderItem.get_from_sale_item(self.store, sale_item)
        # Now we must remove the products added to the workorders from the
        # stock and we can associate the category selected to the workorders
        storable = sale_item.sellable.product_storable
        if storable:
            if sale_item.batch is not None:
                balance = sale_item.batch.get_balance_for_branch(
                    sale_item.sale.branch)
            else:
                balance = storable.get_balance_for_branch(
                    sale_item.sale.branch)
        else:
            # No storable, consume it all
            balance = sale_item.quantity

        quantity_to_reserve = min(balance, sale_item.quantity)
        if quantity_to_reserve:
            sale_item.reserve(quantity_to_reserve)

        wo_item.quantity_decreased = sale_item.quantity_decreased
        return sale_item

    def get_saved_items(self):
        for item in super(OpticalItemStep, self).get_saved_items():
            self._setup_patient(item)
            yield item

    def get_extra_columns(self):
        return [Column('_patient', title=_(u'Owner'), data_type=str)]

    def setup_work_order(self, work_order):
        optical_wo = self.store.find(
            OpticalWorkOrder, work_order=work_order).one()

        work_order.description = _('Work order for %s') % optical_wo.patient
        work_order.estimated_start = work_order.estimated_finish

    #
    #  Private
    #

    def _setup_patient(self, sale_item):
        wo_item = WorkOrderItem.get_from_sale_item(self.store, sale_item)
        optical_wo = self.store.find(
            OpticalWorkOrder, work_order=wo_item.order).one()
        sale_item._patient = optical_wo.patient


class OpticalSaleQuoteWizard(WorkOrderQuoteWizard):
    """Wizard for optical pre-sales.

    This is similar to the regular pre-sale, but has an additional step to
    create some workorders, and the item step is changed a little bit, to allow
    the sales person to select in what work order the item should be added to.
    """

    #
    #  WorkOrderQuoteWizard
    #

    def get_first_step(self, store, model):
        return OpticalStartSaleQuoteStep(store, self, model)

    def print_quote_details(self, model, payments_created=False):
        msg = _('Would you like to print the quote details now?')
        # We can only print the details if the quote was confirmed.
        if yesno(msg, gtk.RESPONSE_YES,
                 _("Print quote details"), _("Don't print")):
            orders = WorkOrder.find_by_sale(self.model.store, self.model)
            print_report(OpticalWorkOrderReceiptReport, list(orders))
