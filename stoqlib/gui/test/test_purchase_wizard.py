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

from stoqlib.gui.uitestutils import GUITest
from stoqlib.gui.wizards.purchasewizard import PurchaseWizard
from stoqlib.domain.product import Storable


class TestPurchaseWizard(GUITest):
    def _check_start_step(self, uitest='', order_number="12345"):
        start_step = self.wizard.get_current_step()
        start_step.order_number.update("12345")
        if uitest:
            self.check_wizard(self.wizard, uitest)
        self.assertSensitive(self.wizard, ['next_button'])
        self.wizard.next_button.clicked()

    def _check_item_step(self, uitest=''):
        item_step = self.wizard.get_current_step()
        product = self.create_product()
        Storable(product=product, connection=self.trans)
        item_step.sellable_selected(product.sellable)
        self.assertSensitive(item_step, ['add_sellable_button'])
        item_step.add_sellable_button.clicked()
        if uitest:
            self.check_wizard(self.wizard, uitest)
        self.assertSensitive(self.wizard, ['next_button'])
        self.wizard.next_button.clicked()

    def _check_payment_step(self, uitest=''):
        if uitest:
            self.check_wizard(self.wizard, uitest,
                              ignores=[str(self.wizard.model.identifier)])
        self.assertSensitive(self.wizard, ['next_button'])
        self.wizard.next_button.clicked()

    def testCreate(self):
        self.wizard = PurchaseWizard(self.trans)
        self._check_start_step('wizard-purchase-start-step')
        self._check_item_step('wizard-purchase-item-step')
        self._check_payment_step('wizard-purchase-payment-step')

        purchase = self.wizard.model
        models = [purchase]
        models.extend(purchase.get_items())
        models.extend(purchase.payments)
        models.append(purchase.group)

        p = list(purchase.payments)[0]
        p.description = p.description.rsplit(' ', 1)[0]
        self.check_wizard(self.wizard, 'wizard-purchase-finish-step',
                          models=models)

        self.assertSensitive(self.wizard, ['next_button'])
        self.wizard.next_button.clicked()

    def testCreateAndReceive(self):
        self.wizard = PurchaseWizard(self.trans)
        self._check_start_step()
        self._check_item_step()
        self._check_payment_step()

        finish_step = self.wizard.get_current_step()
        finish_step.receive_now.set_active(True)

        self.assertSensitive(self.wizard, ['next_button'])
        self.wizard.next_button.clicked()

        receiving_step = self.wizard.get_current_step()
        receiving_step.invoice_slave.order_number.update("12345")
        receiving_step.invoice_slave.invoice_number.update(67890)

        self.check_wizard(self.wizard, 'wizard-purchase-invoice-step')

        self.assertSensitive(self.wizard, ['next_button'])
        self.wizard.next_button.clicked()

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
        p = list(purchase.payments)[0]
        p.description = p.description.rsplit(' ', 1)[0]

        self.check_wizard(self.wizard, 'wizard-purchase-done-received',
                          models=models)
