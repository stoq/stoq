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
import mock

from stoqlib.domain.product import Storable
from stoqlib.gui.uitestutils import GUITest
from stoqlib.gui.wizards.purchasequotewizard import QuotePurchaseWizard
from stoqlib.lib.parameters import sysparam


class TestPurchaseeWizard(GUITest):
    def _check_start_step(self, uitest=''):
        start_step = self.wizard.get_current_step()
        start_step.quote_deadline.update(datetime.datetime(2020, 1, 1))
        start_step.quote_group.set_text("12345")
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

    def _check_supplier_step(self, uitest=''):
        if uitest:
            self.check_wizard(self.wizard, uitest)
        self.click(self.wizard.next_button)

    @mock.patch('stoqlib.database.orm.Transaction.commit')
    @mock.patch('stoqlib.domain.purchase.PurchaseOrder.delete')
    def testCreate(self, delete, commit):
        # Allow creating purchases in the past.
        sysparam(self.trans).update_parameter("ALLOW_OUTDATED_OPERATIONS", "1")

        self.wizard = QuotePurchaseWizard(self.trans)
        self.wizard.model.branch = self.create_branch()
        self.wizard.model.identifier = 12345
        self.wizard.model.open_date = datetime.date(2010, 1, 3)
        self._check_start_step('wizard-purchasequote-start-step')
        self._check_item_step('wizard-purchasequote-item-step')
        self._check_supplier_step('wizard-purchasequote-supplier-step')

        delete.assert_called_once_with(self.wizard.model.id,
                                       connection=self.trans)
        commit.assert_call_count(2)

        purchase = self.wizard.model
        models = [purchase]
        models.extend(purchase.get_items())

        self.check_wizard(self.wizard, 'wizard-purchasequote-finish-step',
                          models=models)

        self.click(self.wizard.next_button)
