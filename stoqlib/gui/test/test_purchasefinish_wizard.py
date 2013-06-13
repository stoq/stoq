# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2009 Async Open Source <http://www.async.com.br>
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

import datetime

from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.gui.wizards.purchasefinishwizard import PurchaseFinishWizard


class TestPurchaseFinishWizard(GUITest):
    def test_confirm_overpaid(self):
        purchase = self.create_purchase_order()

        purchase.add_item(self.create_sellable(), 1)
        purchase.add_item(self.create_sellable(), 5)
        purchase.status = PurchaseOrder.ORDER_CONFIRMED

        wizard = PurchaseFinishWizard(self.store, purchase)

        self.check_wizard(wizard,
                          'wizard-purchase-finish-product-list-step-overpaid')
        self.click(wizard.next_button)

        self.click(wizard.next_button)
        wizard.retval.description = u'description'
        self.check_wizard(wizard,
                          'wizard-purchase-finish-payment-adjust-step-overpaid',
                          [wizard.purchase.group, wizard.retval, wizard.purchase]
                          + list(wizard.purchase.get_items()))

    def test_confirm_underpaid(self):
        purchase = self.create_purchase_order()

        purchase.status = PurchaseOrder.ORDER_CONFIRMED
        purchase.add_item(self.create_sellable(), 1)
        purchase.add_item(self.create_sellable(), 5)
        for item in list(purchase.get_items()):
            item.quantity_received = 1
        self.add_payments(purchase)
        purchase.payments[0].description = u'purchase payment description'
        purchase.payments[0].due_date = datetime.date.today()
        purchase.payments[0].identifier = 33333

        wizard = PurchaseFinishWizard(self.store, purchase)

        self.check_wizard(wizard,
                          'wizard-purchase-finish-product-list-step-underpaid')
        self.click(wizard.next_button)

        self.check_wizard(wizard,
                          'wizard-purchase-finish-payment-adjust-step-underpaid')
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        step.slave.payment_list.payment_list[0].description = u'finish description'
        self.click(wizard.next_button)

        self.check_wizard(wizard, 'wizard-purchase-finish-payment-step-underpaid',
                          [wizard.purchase.group, wizard.purchase] +
                          list(wizard.retval))
