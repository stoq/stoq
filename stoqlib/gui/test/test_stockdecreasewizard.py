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

import mock

from stoqlib.api import api
from stoqlib.domain.costcenter import CostCenterEntry
from stoqlib.domain.stockdecrease import StockDecrease
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.gui.wizards.salewizard import PaymentMethodStep
from stoqlib.gui.wizards.stockdecreasewizard import StockDecreaseWizard
from stoqlib.lib.parameters import sysparam


class TestStockDecreaseWizard(GUITest):
    @mock.patch('stoqlib.gui.wizards.stockdecreasewizard.'
                'StockDecreaseWizard._receipt_dialog')
    def test_wizard(self, receipt_dialog):
        branch = api.get_current_branch(self.store)
        storable = self.create_storable(branch=branch, stock=1)
        sellable = storable.product.sellable
        wizard = StockDecreaseWizard(self.store)

        step = wizard.get_current_step()
        self.assertFalse(step.create_payments.get_visible())
        self.assertNotSensitive(wizard, ['next_button'])
        step.reason.update('text')
        self.assertSensitive(wizard, ['next_button'])
        self.check_wizard(wizard, 'start-stock-decrease-step')
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        self.assertNotSensitive(wizard, ['next_button'])
        step.barcode.set_text(sellable.barcode)
        step.sellable_selected(sellable)
        step.quantity.update(1)
        self.click(step.add_sellable_button)
        self.check_wizard(wizard, 'decrease-item-step')

        self.assertSensitive(wizard, ['next_button'])
        module = 'stoqlib.gui.events.StockDecreaseWizardFinishEvent.emit'
        with mock.patch(module) as emit:
            with mock.patch.object(self.store, 'commit'):
                self.click(wizard.next_button)
            self.assertEquals(emit.call_count, 1)
            args, kwargs = emit.call_args
            self.assertTrue(isinstance(args[0], StockDecrease))

        self.assertEquals(receipt_dialog.call_count, 1)

        # Assert wizard decreased stock.
        self.assertEquals(storable.get_balance_for_branch(branch), 0)

    @mock.patch('stoqlib.gui.wizards.stockdecreasewizard.yesno')
    def test_wizard_create_payment(self, yesno):
        yesno.return_value = False

        sysparam.set_bool(self.store, 'CREATE_PAYMENTS_ON_STOCK_DECREASE', True)

        till = self.create_till()
        till.open_till()

        branch = api.get_current_branch(self.store)
        storable = self.create_storable(branch=branch, stock=1)
        sellable = storable.product.sellable
        wizard = StockDecreaseWizard(self.store)

        step = wizard.get_current_step()
        self.assertTrue(step.create_payments.get_visible())
        step.create_payments.update(True)
        step.reason.update('reason')
        self.check_wizard(wizard, 'start-stock-decrease-step-create-payments')
        self.assertSensitive(wizard, ['next_button'])
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        step.barcode.set_text(sellable.barcode)
        step.sellable_selected(sellable)
        step.quantity.update(1)
        self.click(step.add_sellable_button)
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        self.assertTrue(isinstance(step, PaymentMethodStep))

    @mock.patch('stoqlib.gui.wizards.stockdecreasewizard.yesno')
    def test_wizard_with_cost_center(self, yesno):
        sysparam.set_bool(self.store, 'CREATE_PAYMENTS_ON_STOCK_DECREASE', True)
        yesno.return_value = False

        branch = api.get_current_branch(self.store)
        storable = self.create_storable(branch=branch, stock=1)
        sellable = storable.product.sellable
        cost_center = self.create_cost_center()

        wizard = StockDecreaseWizard(self.store)

        entry = self.store.find(CostCenterEntry,
                                cost_center=wizard.model.cost_center)
        self.assertEquals(len(list(entry)), 0)

        step = wizard.get_current_step()
        step.reason.update('test')
        step.cost_center.select(cost_center)
        self.check_wizard(wizard, 'stock-decrease-with-cost-center')

        self.click(wizard.next_button)

        step = wizard.get_current_step()
        step.barcode.set_text(sellable.barcode)
        step.sellable_selected(sellable)
        step.quantity.update(1)
        self.click(step.add_sellable_button)
        with mock.patch.object(self.store, 'commit'):
            self.click(wizard.next_button)

        self.assertEquals(wizard.model.cost_center, cost_center)
        entry = self.store.find(CostCenterEntry,
                                cost_center=wizard.model.cost_center)
        self.assertEquals(len(list(entry)), 1)
