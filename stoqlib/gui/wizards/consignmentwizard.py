# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2009 Async Open Source <http://www.async.com.br>
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
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##              Johan Dahlin                <jdahlin@async.com.br>
##              George Kussumoto            <george@async.com.br>
##
##
""" Purchase wizard definition """

import datetime
from decimal import Decimal
import sys

import gtk

from kiwi.datatypes import currency, ValidationError
from kiwi.ui.widgets.list import Column

from stoqlib.database.runtime import (get_current_branch, new_transaction,
                                      finish_transaction, get_current_user)
from stoqlib.domain.interfaces import IBranch, ITransporter, ISupplier
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.operation import register_payment_operations
from stoqlib.domain.person import Person
from stoqlib.domain.product import ProductSupplierInfo
from stoqlib.domain.purchase import PurchaseOrder, PurchaseItem
from stoqlib.domain.receiving import (ReceivingOrder, ReceivingOrderItem,
                                      get_receiving_items_by_purchase_order)
from stoqlib.domain.sellable import Sellable
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.validators import format_quantity, get_formatted_cost
from stoqlib.gui.base.wizards import WizardEditorStep, BaseWizard
from stoqlib.gui.editors.purchaseeditor import PurchaseItemEditor
from stoqlib.gui.printing import print_report
from stoqlib.gui.wizards.personwizard import run_person_role_dialog
from stoqlib.gui.wizards.receivingwizard import ReceivingInvoiceStep
from stoqlib.gui.wizards.abstractwizard import SellableItemStep
from stoqlib.gui.editors.personeditor import SupplierEditor, TransporterEditor
from stoqlib.gui.slaves.paymentslave import (CheckMethodSlave,
                                             BillMethodSlave, MoneyMethodSlave)
from stoqlib.reporting.purchase import PurchaseOrderReport

from stoqlib.gui.wizards.purchasewizard import (StartPurchaseStep,
                                                PurchaseItemStep,
                                                PurchasePaymentStep,
                                                FinishPurchaseStep,
                                                PurchaseWizard
                                                )

_ = stoqlib_gettext


#
# Wizard Steps
#

from stoqlib.gui.wizards.receivingwizard import ReceivingInvoiceStep


class StartConsignmentStep(StartPurchaseStep):
    pass
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

#class ConsignmentPaymentStep(PurchasePaymentStep):
#    pass
#
#class FinishConsignmentStep(FinishPurchaseStep):
#    pass



#
# Main wizard
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
