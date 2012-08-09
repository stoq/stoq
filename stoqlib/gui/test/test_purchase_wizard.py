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


class TestPurchaseWizard(GUITest):
    def testCreate(self):
        wizard = PurchaseWizard(self.trans)
        purchase = wizard.model

        # Start Step
        self.check_wizard(wizard, 'wizard-purchase-start-step',
                          ignores=[purchase.get_order_number_str()])
        self.assertSensitive(wizard, ['next_button'])
        wizard.next_button.clicked()

        # Item Step
        item_step = wizard.get_current_step()
        product = self.create_product()
        item_step.sellable_selected(product.sellable)
        self.assertSensitive(item_step, ['add_sellable_button'])
        item_step.add_sellable_button.clicked()
        self.check_wizard(wizard, 'wizard-purchase-item-step')
        self.assertSensitive(wizard, ['next_button'])
        wizard.next_button.clicked()

        # Payment Step
        self.check_wizard(wizard, 'wizard-purchase-payment-step',
                          ignores=[str(wizard.model.id)])
        self.assertSensitive(wizard, ['next_button'])
        wizard.next_button.clicked()

        # Finish Step
        models = [purchase]
        models.extend(purchase.get_items())
        models.extend(purchase.payments)
        models.append(purchase.group)

        self.check_wizard(wizard, 'wizard-purchase-finish-step',
                          models=models,
                          ignores=[str(wizard.model.id)])
