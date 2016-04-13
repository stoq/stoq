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

from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.fiscal import Invoice
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.gui.wizards.salereturnwizard import (SaleReturnWizard,
                                                  SaleTradeWizard)
from stoqlib.lib.dateutils import localdate
from stoqlib.lib.parameters import sysparam


class TestSaleReturnWizard(GUITest):
    def test_create(self):
        sale = self.create_sale()
        self.add_product(sale)
        self.add_product(sale, quantity=2)
        self.add_payments(sale)
        sale.order()
        sale.confirm()
        returned_sale = sale.create_sale_return_adapter()
        SaleReturnWizard(self.store, returned_sale)

        for item in returned_sale.returned_items:
            self.assertTrue(item.will_return)
            self.assertEqual(item.quantity, item.max_quantity)

    @mock.patch('stoqlib.gui.wizards.salereturnwizard.info')
    def test_sale_return_items_step(self, info):
        sale = self.create_sale()
        package = self.create_product(description=u'Package', is_package=True)
        component = self.create_product(description=u'Component', stock=5,
                                        storable=True)
        p_comp = self.create_product_component(product=package, component=component,
                                               component_quantity=5, price=2)

        self.add_product(sale, code=u'1234')
        self.add_product(sale, quantity=2, code=u'5678')
        package_item = sale.add_sellable(package.sellable)
        package_qty = package_item.quantity
        sale.add_sellable(component.sellable,
                          quantity=package_qty * p_comp.quantity,
                          price=package_qty * p_comp.price,
                          parent=package_item)
        self.add_payments(sale)
        sale.order()
        sale.confirm()
        returned_sale = sale.create_sale_return_adapter()

        wizard = SaleReturnWizard(self.store, returned_sale)
        step = wizard.get_current_step()
        objecttree = step.slave.klist

        def _reset_objectlist(objecttree):
            for item in objecttree:
                item.quantity = item.max_quantity
                item.will_return = bool(item.quantity)
                objecttree.update(item)

        self.check_wizard(wizard, 'wizard-sale-return-items-step')
        self.assertSensitive(wizard, ['next_button'])

        # If we don't have anything marked as will_return, wizard's
        # next_button should not be sensiive.
        for item in objecttree:
            item.will_return = False
            objecttree.update(item)
        step.force_validation()
        self.assertNotSensitive(wizard, ['next_button'])

        _reset_objectlist(objecttree)
        step.force_validation()
        self.assertSensitive(wizard, ['next_button'])

        # If we don't have a quantity to return of anything, wizard's
        # next_button should not be sensiive.
        for item in objecttree:
            item.quantity = 0
            objecttree.update(item)
        step.force_validation()
        self.assertNotSensitive(wizard, ['next_button'])

        _reset_objectlist(objecttree)
        step.force_validation()
        self.assertSensitive(wizard, ['next_button'])

        for item in objecttree:
            item.quantity = item.max_quantity + 1
            # If anything is marked to return with more than max_quantity
            # wizard's next_button should not be sensitive
            step.force_validation()
            self.assertNotSensitive(wizard, ['next_button'])
            _reset_objectlist(objecttree)

        _reset_objectlist(objecttree)
        # None of the siblings are being returned, so the parent will be
        # unchecked
        for item in objecttree:
            if item.parent_item:
                item.quantity = 0
                objecttree.emit('cell-edited', item, 'quantity')
                self.assertFalse(item.parent_item.will_return)

        _reset_objectlist(objecttree)
        # Return all siblings, so return its parent as well
        for item in objecttree:
            if item.parent_item:
                item.quantity = 5
                objecttree.emit('cell-edited', item, 'quantity')
                self.assertTrue(item.parent_item.will_return)

        _reset_objectlist(objecttree)
        for item in objecttree:
            if item.parent_item:
                item.will_return = True
                objecttree.emit('cell-edited', item, 'will_return')
                self.assertTrue(item.parent_item.will_return)

        _reset_objectlist(objecttree)
        for item in objecttree:
            if item.parent_item:
                item.will_return = False
                objecttree.emit('cell-edited', item, 'will_return')
                self.assertFalse(item.parent_item.will_return)

    def test_sale_return_invoice_step(self):
        main_branch = get_current_branch(self.store)
        sale = self.create_sale(branch=main_branch)
        self.add_product(sale)
        self.add_product(sale, quantity=2)
        self.add_payments(sale)
        sale.order()
        sale.confirm()
        returned_sale = sale.create_sale_return_adapter()
        wizard = SaleReturnWizard(self.store, returned_sale)
        self.click(wizard.next_button)
        step = wizard.get_current_step()

        self.check_wizard(wizard, 'wizard-sale-return-invoice-step')
        self.assertNotSensitive(wizard, ['next_button'])

        self.assertInvalid(step, ['reason'])
        step.reason.update(
            "Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed\n"
            "do eiusmod tempor incididunt ut labore et dolore magna aliqua.")
        self.assertValid(step, ['reason'])

        # XXX: changed because invoice_number is no longer mandatory
        self.assertSensitive(wizard, ['next_button'])

        step.invoice_number.update(0)
        self.assertInvalid(step, ['invoice_number'])
        step.invoice_number.update(1000000000)
        self.assertInvalid(step, ['invoice_number'])
        self.assertNotSensitive(wizard, ['next_button'])

        # Check if the invoice number already exists in Invoice table
        invoice = Invoice(invoice_type=Invoice.TYPE_OUT, branch=main_branch)
        invoice.invoice_number = 123
        step.invoice_number.update(123)
        self.assertInvalid(step, ['invoice_number'])
        self.assertNotSensitive(wizard, ['next_button'])

        step.invoice_number.update(1)
        self.assertValid(step, ['invoice_number'])
        invoice.branch = self.create_branch()
        step.invoice_number.update(123)
        self.assertValid(step, ['invoice_number'])
        self.assertSensitive(wizard, ['next_button'])

    @mock.patch('stoqlib.gui.wizards.salereturnwizard.info')
    def test_sale_return_payment_step_not_paid(self, info):
        sale = self.create_sale()
        sale.identifier = 1234
        self.add_product(sale, price=50, quantity=6)
        self.add_payments(sale, method_type=u'check', installments=3,
                          date=localdate(2012, 1, 1).date())
        sale.order()
        sale.confirm()
        returned_sale = sale.create_sale_return_adapter()
        returned_sale.reason = u'reason'
        returned_sale.invoice_number = 1
        list(returned_sale.returned_items)[0].quantity = 1
        wizard = SaleReturnWizard(self.store, returned_sale)
        self.click(wizard.next_button)
        self.click(wizard.next_button)
        step = wizard.get_current_step()

        info.assert_called_once_with(
            ("The client's debt has changed. "
             "Use this step to adjust the payments."),
            ("The debt before was $300.00 and now is $250.00. "
             "Cancel some unpaid installments and create new ones."))
        self.assertVisible(step.slave, ['remove_button'])
        self.assertEqual(step.slave.total_value.read(),
                         returned_sale.total_amount_abs +
                         returned_sale.paid_total)
        self.check_wizard(wizard,
                          'wizard-sale-return-payment-step-not-paid')

    @mock.patch('stoqlib.gui.wizards.salereturnwizard.info')
    def test_sale_return_payment_step_partially_paid(self, info):
        sale = self.create_sale()
        sale.identifier = 1234
        self.add_product(sale, price=50, quantity=6)
        payments = self.add_payments(sale, method_type=u'check', installments=3,
                                     date=localdate(2012, 1, 1).date())
        sale.order()
        sale.confirm()
        payments[0].pay()
        returned_sale = sale.create_sale_return_adapter()
        returned_sale.reason = u'reason'
        returned_sale.invoice_number = 1
        list(returned_sale.returned_items)[0].quantity = 1
        wizard = SaleReturnWizard(self.store, returned_sale)
        self.click(wizard.next_button)
        self.click(wizard.next_button)
        step = wizard.get_current_step()

        info.assert_called_once_with(
            ("The client's debt has changed. "
             "Use this step to adjust the payments."),
            ("The debt before was $200.00 and now is $150.00. "
             "Cancel some unpaid installments and create new ones."))
        self.assertVisible(step.slave, ['remove_button'])
        self.assertEqual(step.slave.total_value.read(),
                         returned_sale.total_amount_abs +
                         returned_sale.paid_total)
        self.check_wizard(wizard,
                          'wizard-sale-return-payment-step-partially-paid')

    @mock.patch('stoqlib.gui.wizards.salereturnwizard.info')
    def test_finish_with_group_cancelling(self, info):
        sale = self.create_sale()
        self.add_product(sale)
        payment, = self.add_payments(sale)
        sale.order()
        sale.confirm()
        returned_sale = sale.create_sale_return_adapter()
        returned_sale.invoice_number = 123456
        returned_sale.reason = u"Reason"
        wizard = SaleReturnWizard(self.store, returned_sale)
        self.click(wizard.next_button)

        module = 'stoqlib.gui.events.SaleReturnWizardFinishEvent.emit'
        with mock.patch(module) as emit:
            # Cancel the payment, so returned_sale.total_amount will be 0
            payment.cancel()
            with mock.patch.object(self.store, 'commit'):
                self.click(wizard.next_button)
            info.assert_called_once_with(
                "The client does not have a debt to this sale anymore. "
                "Any existing unpaid installment will be cancelled.")
            emit.assert_called_once_with(returned_sale)

    @mock.patch('stoqlib.gui.wizards.salereturnwizard.info')
    def test_finish_with_reversal_payment(self, info):
        sale = self.create_sale()
        self.add_product(sale)
        payment, = self.add_payments(sale)
        sale.order()
        sale.confirm()
        returned_sale = sale.create_sale_return_adapter()
        returned_sale.invoice_number = 123456
        returned_sale.reason = u"Reason"
        wizard = SaleReturnWizard(self.store, returned_sale)
        self.click(wizard.next_button)

        module = 'stoqlib.gui.events.SaleReturnWizardFinishEvent.emit'
        with mock.patch(module) as emit:
            with mock.patch.object(self.store, 'commit'):
                self.click(wizard.next_button)
            info.assert_called_once_with(
                "A reversal payment to the client will be created. "
                "You can see it on the Payable Application.")
            emit.assert_called_once_with(returned_sale)


class TestSaleTradeWizard(GUITest):
    def test_create(self):
        SaleTradeWizard(self.store)

    def test_sale_selection_step_known_sale(self):
        wizard = SaleTradeWizard(self.store)
        step = wizard.get_current_step()
        results = step.slave.results

        # Since ALLOW_TRADE_NOT_REGISTERED_SALES is False (default),
        # the user should not be able to check this
        self.assertNotVisible(step, ['unknown_sale_check'])

        # next_button should only be sensitive if a sale is selected
        self.assertNotSensitive(wizard, ['next_button'])
        results.select(results[0])
        self.assertSensitive(wizard, ['next_button'])
        results.unselect_all()
        self.assertNotSensitive(wizard, ['next_button'])

        self.check_wizard(wizard, 'wizard-trade-sale-selection-step-known-sale')

        # Go to items step
        results.select(results[0])
        self.click(wizard.next_button)

        # Go to details step
        self.click(wizard.next_button)
        step = wizard.get_current_step()
        self.assertNotSensitive(wizard, ['next_button'])
        step.invoice_number.update(41235)
        self.assertNotSensitive(wizard, ['next_button'])
        step.reason.update('Just because')
        self.assertSensitive(wizard, ['next_button'])

        module = 'stoqlib.gui.events.SaleTradeWizardFinishEvent.emit'
        with mock.patch(module) as emit:
            self.click(wizard.next_button)
            emit.assert_called_once_with(wizard.model)

    def test_sale_selection_step_unknown_sale(self):
        sysparam.set_bool(self.store, 'ALLOW_TRADE_NOT_REGISTERED_SALES', True)
        wizard = SaleTradeWizard(self.store)
        step = wizard.get_current_step()
        results = step.slave.results

        # Since ALLOW_TRADE_NOT_REGISTERED_SALES is True,
        # the user should be able to check this
        self.assertVisible(step, ['unknown_sale_check'])

        # next_button should only be sensitive if a sale is selected
        self.assertNotSensitive(wizard, ['next_button'])
        results.select(results[0])
        self.assertSensitive(wizard, ['next_button'])
        results.unselect_all()
        self.assertNotSensitive(wizard, ['next_button'])

        self.click(step.unknown_sale_check)
        self.assertSensitive(wizard, ['next_button'])

        self.check_wizard(wizard, 'wizard-trade-sale-selection-step-unknown-sale')

    def test_unknown_sale_item_step(self):
        with self.sysparam(ALLOW_TRADE_NOT_REGISTERED_SALES=True):
            package = self.create_product(description=u'Package', is_package=True)
            package.sellable.barcode = u'666'
            component = self.create_product(description=u'Component', stock=2)
            self.create_product_component(product=package, component=component)
            production = self.create_production_item()
            production.product.sellable.barcode = u'333'

            wizard = SaleTradeWizard(self.store)
            step = wizard.get_current_step()
            self.click(step.unknown_sale_check)
            self.click(wizard.next_button)

            item_step = wizard.get_current_step()
            # Testing add package_item
            item_step.barcode.set_text(u'666')
            self.activate(item_step.barcode)
            self.click(item_step.add_sellable_button)
            # Children must be added to the list
            self.assertEquals(len(list(item_step.slave.klist)), 2)

            # Testing add production item
            item_step.barcode.set_text(u'333')
            self.activate(item_step.barcode)
            self.click(item_step.add_sellable_button)
            # For production item, we should not add its components to the list
            self.assertEquals(len(list(item_step.slave.klist)), 3)
