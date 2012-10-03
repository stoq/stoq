# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import datetime

from stoqlib.domain.product import Storable
from stoqlib.gui.uitestutils import GUITest
from stoqlib.gui.wizards.purchasewizard import PurchaseWizard
from stoqlib.lib.parameters import sysparam


class TestPurchaseWizard(GUITest):
    def _check_start_step(self, uitest='', order_number="12345"):
        start_step = self.wizard.get_current_step()
        start_step.order_number.update("12345")
        if uitest:
            self.check_wizard(self.wizard, uitest)
        self.click(self.wizard.next_button)

    def _check_item_step(self, uitest=''):
        item_step = self.wizard.get_current_step()
        product = self.create_product()
        Storable(product=product, connection=self.trans)
        item_step.sellable_selected(product.sellable)
        self.click(item_step.add_sellable_button)
        if uitest:
            self.check_wizard(self.wizard, uitest)
        self.click(self.wizard.next_button)

    def _check_payment_step(self, uitest=''):
        if uitest:
            self.check_wizard(self.wizard, uitest)
        self.click(self.wizard.next_button)

    def testCreate(self):
        # Allow creating purchases in the past.
        sysparam(self.trans).update_parameter("ALLOW_OUTDATED_OPERATIONS", "1")

        self.wizard = PurchaseWizard(self.trans)
        self.wizard.model.identifier = 12345
        self.wizard.model.open_date = datetime.date(2010, 1, 3)
        self._check_start_step('wizard-purchase-start-step')
        self._check_item_step('wizard-purchase-item-step')
        self._check_payment_step('wizard-purchase-payment-step')

        purchase = self.wizard.model
        models = [purchase]
        models.extend(purchase.get_items())
        models.extend(purchase.payments)
        models.append(purchase.group)

        self.check_wizard(self.wizard, 'wizard-purchase-finish-step',
                          models=models)

        self.click(self.wizard.next_button)

    def testCreateAndReceive(self):
        self.wizard = PurchaseWizard(self.trans)
        self.wizard.model.identifier = 12345
        self.wizard.model.open_date = datetime.date(2010, 1, 3)
        self._check_start_step()
        self._check_item_step()
        self._check_payment_step()

        finish_step = self.wizard.get_current_step()
        finish_step.receive_now.set_active(True)

        self.click(self.wizard.next_button)

        receiving_step = self.wizard.get_current_step()
        receiving_step.invoice_slave.order_number.update("12345")
        receiving_step.invoice_slave.invoice_number.update(67890)

        self.check_wizard(self.wizard, 'wizard-purchase-invoice-step')

        self.click(self.wizard.next_button)

        purchase = self.wizard.model
        models = [purchase]
        models.extend(purchase.get_items())
        models.extend(purchase.payments)
        models.append(purchase.group)

        receive = self.wizard.receiving_model
        models.append(receive)
        models.extend(receive.get_items())
        for item in receive.get_items():
            models.extend(list(item.sellable.product_storable.get_stock_items()))

        self.check_wizard(self.wizard, 'wizard-purchase-done-received',
                          models=models)
