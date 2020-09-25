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

from gi.repository import Gtk
import mock

from stoqlib.database.runtime import get_current_branch
from stoq.lib.gui.test.uitestutils import GUITest
from stoq.lib.gui.wizards.salereturnwizard import SaleReturnWizard, SaleTradeWizard
from stoqlib.lib.parameters import sysparam
from stoqlib.reporting.clientcredit import ClientCreditReport


class TestSaleReturnWizard(GUITest):
    def test_create(self):
        sale = self.create_sale()
        self.add_product(sale)
        self.add_product(sale, quantity=2)
        self.add_payments(sale)
        sale.order(self.current_user)
        sale.confirm(self.current_user)
        returned_sale = sale.create_sale_return_adapter(self.current_branch, self.current_user,
                                                        self.current_station)
        SaleReturnWizard(self.store, returned_sale)

        for item in returned_sale.returned_items:
            self.assertTrue(item.will_return)
            self.assertEqual(item.quantity, item.max_quantity)

    @mock.patch('stoq.lib.gui.wizards.salereturnwizard.yesno')
    @mock.patch('stoq.lib.gui.wizards.salereturnwizard.print_report')
    def test_finish(self, print_report, yesno):
        sale = self.create_sale()
        self.add_product(sale)
        payment, = self.add_payments(sale)
        sale.order(self.current_user)
        sale.confirm(self.current_user)
        returned_sale = sale.create_sale_return_adapter(self.current_branch, self.current_user,
                                                        self.current_station)
        returned_sale.reason = u"Reason"
        wizard = SaleReturnWizard(self.store, returned_sale)
        self.click(wizard.next_button)
        step = wizard.get_current_step()

        module = 'stoq.lib.gui.events.SaleReturnWizardFinishEvent.emit'
        with mock.patch(module):
            step.reason = "123"
            step.credit.set_active(True)
            with mock.patch.object(self.store, 'commit'):
                self.click(wizard.next_button)
            yesno.assert_called_once_with('Would you like to print the credit letter?',
                                          Gtk.ResponseType.YES,
                                          'Print Letter', "Don't print")
            print_report.assert_called_once_with(ClientCreditReport, sale.client)

    def test_sale_return_items_step(self):
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
        sale.order(self.current_user)
        sale.confirm(self.current_user)
        returned_sale = sale.create_sale_return_adapter(self.current_branch, self.current_user,
                                                        self.current_station)

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

        quantity_col = objecttree.get_column_by_name('quantity')
        will_return_col = objecttree.get_column_by_name('will_return')
        _reset_objectlist(objecttree)
        # None of the siblings are being returned, so the parent will be
        # unchecked
        for item in objecttree:
            if item.parent_item:
                item.quantity = 0
                objecttree.emit('cell-edited', item, quantity_col)
                self.assertFalse(item.parent_item.will_return)

        _reset_objectlist(objecttree)
        # Return all siblings, so return its parent as well
        for item in objecttree:
            if item.parent_item:
                item.quantity = 5
                objecttree.emit('cell-edited', item, quantity_col)
                self.assertTrue(item.parent_item.will_return)

        _reset_objectlist(objecttree)
        for item in objecttree:
            if item.parent_item:
                item.will_return = True
                objecttree.emit('cell-edited', item, will_return_col)
                self.assertTrue(item.parent_item.will_return)

        _reset_objectlist(objecttree)
        for item in objecttree:
            if item.parent_item:
                item.will_return = False
                objecttree.emit('cell-edited', item, will_return_col)
                self.assertFalse(item.parent_item.will_return)

    def test_sale_return_invoice_step(self):
        main_branch = get_current_branch(self.store)
        sale = self.create_sale(branch=main_branch)
        self.add_product(sale)
        self.add_product(sale, quantity=2)
        self.add_payments(sale)
        sale.order(self.current_user)
        sale.confirm(self.current_user)
        returned_sale = sale.create_sale_return_adapter(self.current_branch, self.current_user,
                                                        self.current_station)
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
        msg = ('A reversal payment to the client will be created. '
               'You can see it on the Payable Application.')
        self.assertEqual(step.message.get_text(), msg)

        # XXX: changed because invoice_number is no longer mandatory
        self.assertSensitive(wizard, ['next_button'])

    def test_sale_return_invoice_step_with_credit(self):
        sale = self.create_sale()
        self.add_product(sale)
        payment, = self.add_payments(sale)
        sale.order(self.current_user)
        sale.confirm(self.current_user)
        returned_sale = sale.create_sale_return_adapter(self.current_branch, self.current_user,
                                                        self.current_station)
        returned_sale.reason = u"Reason"
        wizard = SaleReturnWizard(self.store, returned_sale)
        self.click(wizard.next_button)

        invoice_step = wizard.get_current_step()
        invoice_step.credit.set_active(True)
        self.check_wizard(wizard, 'wizard-sale-return-invoice-step-with-credit')


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
        step.reason.update('Just because')
        self.assertSensitive(wizard, ['next_button'])

        module = 'stoq.lib.gui.events.SaleTradeWizardFinishEvent.emit'
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
            self.assertEqual(len(list(item_step.slave.klist)), 2)

            # Testing add production item
            item_step.barcode.set_text(u'333')
            self.activate(item_step.barcode)
            self.click(item_step.add_sellable_button)
            # For production item, we should not add its components to the list
            self.assertEqual(len(list(item_step.slave.klist)), 3)
