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
from stoqlib.domain.sale import Delivery
from stoqlib.domain.stockdecrease import StockDecrease, StockDecreaseItem
from stoq.lib.gui.editors.deliveryeditor import CreateDeliveryModel
from stoq.lib.gui.test.uitestutils import GUITest
from stoq.lib.gui.wizards.salewizard import PaymentMethodStep
from stoq.lib.gui.wizards.stockdecreasewizard import StockDecreaseWizard
from stoqlib.lib.parameters import sysparam


class TestStockDecreaseWizard(GUITest):
    @mock.patch('stoq.lib.gui.wizards.stockdecreasewizard.'
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
        module = 'stoq.lib.gui.events.StockDecreaseWizardFinishEvent.emit'
        with mock.patch(module) as emit:
            with mock.patch.object(self.store, 'commit'):
                self.click(wizard.next_button)
            self.assertEqual(emit.call_count, 1)
            args, kwargs = emit.call_args
            self.assertTrue(isinstance(args[0], StockDecrease))

        self.assertEqual(receipt_dialog.call_count, 1)

        # Assert wizard decreased stock.
        self.assertEqual(storable.get_balance_for_branch(branch), 0)

    @mock.patch('stoq.lib.gui.wizards.stockdecreasewizard.yesno')
    def test_wizard_create_payment(self, yesno):
        yesno.return_value = False

        sysparam.set_bool(self.store, 'CREATE_PAYMENTS_ON_STOCK_DECREASE', True)

        till = self.create_till()
        till.open_till(self.current_user)

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

    @mock.patch('stoq.lib.gui.wizards.stockdecreasewizard.yesno')
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
        self.assertEqual(len(list(entry)), 0)

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

        self.assertEqual(wizard.model.cost_center, cost_center)
        entry = self.store.find(CostCenterEntry,
                                cost_center=wizard.model.cost_center)
        self.assertEqual(len(list(entry)), 1)

    @mock.patch('stoq.lib.gui.wizards.stockdecreasewizard.yesno')
    def test_wizard_with_receiving_order(self, yesno):
        yesno.return_value = False
        branch = api.get_current_branch(self.store)

        # Use a package product for covering the case
        package_product = self.create_product(is_package=True)

        # Create to storables, one for being a child
        storable = self.create_storable(stock=2, branch=branch)
        sellable = storable.product.sellable
        other_storable = self.create_storable(stock=1, branch=branch)
        other_sellable = other_storable.product.sellable

        order = self.create_receiving_order(branch=branch)
        parent = self.create_receiving_order_item(receiving_order=order,
                                                  sellable=package_product.sellable)
        self.create_receiving_order_item(receiving_order=order, quantity=1,
                                         sellable=sellable, parent_item=parent)
        self.create_receiving_order_item(receiving_order=order, quantity=1,
                                         sellable=other_sellable)

        # Run the wizard
        wizard = StockDecreaseWizard(self.store, receiving_order=order)
        self.assertEqual(wizard.model.branch, order.branch)
        self.assertEqual(wizard.model.person, order.receiving_invoice.supplier.person)
        step = wizard.get_current_step()
        step.reason.update('test')
        self.check_wizard(wizard, 'stock-decrease-with-receiving-order')
        self.click(wizard.next_button)
        self.assertEqual(wizard.model.get_items().count(), 2)
        with mock.patch.object(self.store, 'commit'):
            self.click(wizard.next_button)

        # Run the wizard with the same order again to check if there is no item
        # left to return
        wizard = StockDecreaseWizard(self.store, receiving_order=order)
        step = wizard.get_current_step()
        step.reason.update('test')
        self.click(wizard.next_button)
        self.assertEqual(wizard.model.get_items().count(), 0)
        self.assertNotSensitive(wizard, ['next_button'])

    def test_wizard_with_delivery(self):
        branch = api.get_current_branch(self.store)
        storable = self.create_storable(branch=branch, stock=1)
        sellable = storable.product.sellable
        # Run the wizard
        wizard = StockDecreaseWizard(self.store)
        step = wizard.get_current_step()
        step.reason.update('test')
        self.click(wizard.next_button)
        step = wizard.get_current_step()
        self.assertNotSensitive(step, ['delivery_button'])
        step.sellable_selected(sellable)
        step.quantity.update(1)
        self.click(step.add_sellable_button)
        item = step.slave.klist[0]
        self.assertSensitive(step, ['delivery_button'])

        delivery_sellable = sysparam.get_object(self.store, 'DELIVERY_SERVICE').sellable
        delivery = CreateDeliveryModel(price=delivery_sellable.price,
                                       recipient=wizard.model.person)

        module = 'stoq.lib.gui.wizards.stockdecreasewizard.run_dialog'
        with mock.patch(module) as run_dialog:
            # Nothing done with the editor, no delivery returned
            run_dialog.return_value = None
            self.click(step.delivery_button)
            self.assertIsNone(step._delivery)
            self.assertIsNone(step._delivery_item)

            # Delivery set
            run_dialog.return_value = delivery
            self.click(step.delivery_button)
            self.assertEqual(step._delivery, delivery)
            self.assertTrue(isinstance(step._delivery_item, StockDecreaseItem))

            # Edit the delivery item
            run_dialog.return_value = delivery
            step.slave.klist.select(step.slave.klist[1])
            self.click(step.slave.edit_button)
            self.assertEqual(step._delivery, delivery)
            self.assertTrue(isinstance(step._delivery_item, StockDecreaseItem))

        # Finishing the wizard must create a Delivery object
        module = 'stoq.lib.gui.wizards.stockdecreasewizard.yesno'
        with mock.patch(module) as yesno:
            with mock.patch.object(self.store, 'commit'):
                yesno.return_value = False
                item.deliver = True
                self.click(wizard.next_button)
                self.assertTrue(isinstance(item.delivery, Delivery))

    @mock.patch('stoq.lib.gui.base.lists.yesno')
    def test_wizard_remove_delivery(self, yesno):
        yesno.return_value = True
        branch = api.get_current_branch(self.store)
        storable = self.create_storable(branch=branch, stock=1)
        sellable = storable.product.sellable
        # Run the wizard
        wizard = StockDecreaseWizard(self.store)
        step = wizard.get_current_step()
        step.reason.update('test')
        self.click(wizard.next_button)
        step = wizard.get_current_step()
        self.assertNotSensitive(step, ['delivery_button'])
        step.sellable_selected(sellable)
        step.quantity.update(1)
        self.click(step.add_sellable_button)
        self.assertSensitive(step, ['delivery_button'])

        delivery_sellable = sysparam.get_object(self.store, 'DELIVERY_SERVICE').sellable
        delivery = CreateDeliveryModel(price=delivery_sellable.price,
                                       recipient=wizard.model.person)

        module = 'stoq.lib.gui.wizards.stockdecreasewizard.run_dialog'
        with mock.patch(module) as run_dialog:
            # Delivery set
            run_dialog.return_value = delivery
            self.click(step.delivery_button)
            self.assertEqual(step._delivery, delivery)
            self.assertTrue(isinstance(step._delivery_item, StockDecreaseItem))

            # Remove the delivery item
            run_dialog.return_value = delivery
            step.slave.klist.select(step.slave.klist[1])
            self.click(step.slave.delete_button)
            self.assertIsNone(step._delivery)
            self.assertIsNone(step._delivery_item)
