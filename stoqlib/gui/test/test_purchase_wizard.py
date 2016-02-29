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
from stoqlib.domain.person import Supplier
from stoqlib.domain.product import Storable
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.gui.wizards.purchasewizard import PurchaseWizard, FinishPurchaseStep
from stoqlib.lib.dateutils import localdate
from stoqlib.lib.parameters import sysparam


class TestFinishPurchaseStep(GUITest):
    def test_post_init(self):
        purchase_order = self.create_purchase_order()
        receiving_order = self.create_receiving_order(
            purchase_order=purchase_order)
        self.create_receiving_order_item(
            receiving_order=receiving_order)
        wizard = PurchaseWizard(store=self.store)
        finish_step = FinishPurchaseStep(model=wizard.model,
                                         store=self.store,
                                         wizard=wizard)
        sellable = self.create_sellable()
        purchase_item = purchase_order.add_item(sellable=sellable)
        receiving_order.add_purchase_item(purchase_item)
        finish_step.post_init()


class TestPurchaseWizard(GUITest):
    def _check_start_step(self, uitest='', identifier="12345"):
        start_step = self.wizard.get_current_step()
        start_step.identifier.update(identifier)
        if uitest:
            self.check_wizard(self.wizard, uitest)
        self.click(self.wizard.next_button)

    def _check_item_step(self, uitest=''):
        item_step = self.wizard.get_current_step()
        product = self.create_product()
        Storable(product=product, store=self.store)
        item_step.sellable_selected(product.sellable)
        self.click(item_step.add_sellable_button)
        if uitest:
            self.check_wizard(self.wizard, uitest)
        self.click(self.wizard.next_button)

    def _check_payment_step(self, uitest=''):
        if uitest:
            self.check_wizard(self.wizard, uitest)
        self.click(self.wizard.next_button)

    def test_create(self):
        # Allow creating purchases in the past.
        sysparam.set_bool(self.store, 'ALLOW_OUTDATED_OPERATIONS', True)

        with self.sysparam(MANDATORY_CHECK_NUMBER=True):
            self.wizard = PurchaseWizard(self.store)
            purchase_branch = self.create_branch()
            purchase_order = PurchaseOrder(branch=purchase_branch)
            sellable = self.create_sellable()
            purchase_order.add_item(sellable=sellable)
            self.wizard.model.identifier = 12345
            self.wizard.model.open_date = localdate(2010, 1, 3).date()
            self._check_start_step('wizard-purchase-start-step')
            self._check_item_step('wizard-purchase-item-step')
            payment_step = self.wizard.get_current_step()
            payment_step.slave.bank_first_check_number.set_text('12')
            self._check_payment_step('wizard-purchase-payment-step')

            purchase = self.wizard.model
            models = [purchase]
            models.extend(purchase.get_items())
            models.extend(purchase.payments)
            models.append(purchase.group)

            self.check_wizard(self.wizard, 'wizard-purchase-finish-step',
                              models=models)

            self.click(self.wizard.next_button)

    def test_create_without_active_supplier(self):
        # Inactivating all the suppliers, so they wont show on PurchaseWizard
        suppliers = self.store.find(Supplier)
        for supplier in suppliers:
            supplier.status = Supplier.STATUS_INACTIVE

        wizard = PurchaseWizard(self.store)
        step = wizard.get_current_step()
        self.assertEquals(step.edit_supplier.get_sensitive(), False)
        step.supplier.set_text('Invalid supplier')
        self.assertEquals(step.edit_supplier.get_sensitive(), False)

        # Activating the suppliers back
        for supplier in suppliers:
            supplier.status = Supplier.STATUS_ACTIVE

    def test_edit_purchase_without_open_date(self):
        purchase_order = self.create_purchase_order()
        self.create_purchase_order_item(purchase_order)
        purchase_order.status = PurchaseOrder.ORDER_PENDING
        self.wizard = PurchaseWizard(self.store, purchase_order)
        start_step = self.wizard.get_current_step()
        start_step.open_date.update(None)
        self.assertEquals(start_step.open_date.mandatory, True)
        self.assertNotSensitive(self.wizard, ['next_button'])

    def test_create_and_receive(self):
        with self.sysparam(MANDATORY_CHECK_NUMBER=True):
            self.wizard = PurchaseWizard(self.store)
            self.wizard.model.identifier = 12345
            self.wizard.model.open_date = localdate(2010, 1, 3).date()
            self._check_start_step()
            self._check_item_step()
            payment_step = self.wizard.get_current_step()
            payment_step.slave.bank_first_check_number.set_text('12')
            self._check_payment_step()

            finish_step = self.wizard.get_current_step()
            finish_step.receive_now.set_active(True)
            self.wizard.model.expected_receival_date = localdate(2010, 1, 4).date()

            self.wizard.enable_next()
            self.click(self.wizard.next_button)

            receiving_step = self.wizard.get_current_step()
            receiving_step.invoice_slave.identifier.set_text("12345")
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
                models.extend(
                    list(item.sellable.product_storable.get_stock_items()))

            self.check_wizard(self.wizard, 'wizard-purchase-done-received',
                              models=models)

    def test_no_receive_now_for_batch_items(self):
        with self.sysparam(MANDATORY_CHECK_NUMBER=True):
            sellable = self.create_sellable()
            self.create_storable(product=sellable.product, is_batch=True)

            wizard = PurchaseWizard(self.store)
            self.click(wizard.next_button)

            step = wizard.get_current_step()
            step.sellable_selected(sellable)
            self.click(step.add_sellable_button)
            self.click(wizard.next_button)

            payment_step = wizard.get_current_step()
            payment_step.slave.bank_first_check_number.set_text('12')
            self.click(wizard.next_button)

            step = wizard.get_current_step()
            self.assertNotVisible(step, ['receive_now'])

    def test_purchase_package(self):
        package = self.create_product(description=u'Package', is_package=True)
        component = self.create_product(description=u'component')
        self.create_product_component(product=package, component=component)
        wizard = PurchaseWizard(self.store)

        wizard = PurchaseWizard(self.store)
        self.click(wizard.next_button)

        # Item step
        step = wizard.get_current_step()
        step.sellable_selected(package.sellable)
        self.click(step.add_sellable_button)

        klist = step.slave.klist
        klist.select(klist[0])
        self.assertSensitive(step.slave, ['delete_button'])
        selected = klist.get_selected_rows()
        child = klist.get_descendants(selected[0])
        klist.select(child)
        self.assertNotSensitive(step.slave, ['delete_button'])
