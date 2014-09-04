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

from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.domain.product import (ProductStockItem,
                                    StockTransactionHistory,
                                    Storable)
from stoqlib.gui.editors.purchaseeditor import InConsignmentItemEditor
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.gui.wizards.consignmentwizard import (CloseInConsignmentWizard,
                                                   ConsignmentWizard)
from stoqlib.gui.wizards.receivingwizard import ReceivingInvoiceStep
from stoqlib.lib.dateutils import localdatetime
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class TestConsignmentWizard(GUITest):
    def test_consignment_wizard(self):
        sellable = self.create_sellable()

        wizard = ConsignmentWizard(self.store)
        wizard.model.open_date = localdatetime(2012, 1, 1, 0, 0)

        step = wizard.get_current_step()
        step.identifier.update('333')
        self.check_wizard(wizard, 'wizard-start-consignment-step')
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        step.barcode.set_text(sellable.barcode)
        step.sellable_selected(sellable)
        step.quantity.update(1)
        self.click(step.add_sellable_button)
        self.check_wizard(wizard, 'wizard-consignment-item-step')
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        self.assertTrue(isinstance(step, ReceivingInvoiceStep))

    @mock.patch('stoqlib.gui.wizards.consignmentwizard.info')
    @mock.patch('stoqlib.gui.wizards.consignmentwizard.run_dialog')
    def test_close_in_consignment_wizard(self, run_dialog, info):
        purchase_item = self.create_purchase_order_item()
        self.create_receiving_order_item(purchase_item=purchase_item)

        # Create storable.
        product = purchase_item.sellable.product
        Storable(store=self.store, product=product)
        storable = product.storable
        branch = purchase_item.order.branch
        storable.increase_stock(10, branch,
                                StockTransactionHistory.TYPE_INITIAL, None)
        stock_quantity = storable.get_stock_item(branch, None).quantity
        self.assertEquals(stock_quantity, 10)

        purchase_item.quantity_received = 10
        purchase_item.quantity_returned = 1
        purchase_item.quantity_sold = 1
        purchase_item.order.status = PurchaseOrder.ORDER_CONSIGNED
        purchase_item.order.identifier = 333
        purchase_item.order.open_date = localdatetime(2012, 1, 1)
        purchase_item.order.expected_receival_date = localdatetime(2012, 2, 2)

        wizard = CloseInConsignmentWizard(self.store)

        step = wizard.get_current_step()
        self.click(step.search.search_button)

        product_stock_item = self.store.find(ProductStockItem,
                                             storable=storable).one()
        self.check_wizard(wizard, 'wizard-consignment-selection-step')

        order_view = step.search.results[0]
        step.search.results.select(order_view)
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        step.consignment_items.select(step.consignment_items[0])

        self.click(step.edit_button)
        self.assertEquals(run_dialog.call_count, 1)
        args, kwargs = run_dialog.call_args
        editor, parent, store, item = args
        self.assertEquals(editor, InConsignmentItemEditor)
        self.assertEquals(parent, wizard)
        self.assertEquals(item, purchase_item)
        self.assertTrue(store is not None)

        purchase_item.quantity_sold = 2
        purchase_item.quantity_returned = 2
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        self.assertNotSensitive(wizard, ['next_button'])

        self.click(step.slave.add_button)
        step.slave.payments[0].due_date = localdatetime(2012, 10, 10)
        self.check_wizard(wizard, 'wizard-consignment-payment-step')
        self.assertSensitive(wizard, ['next_button'])

        self.click(wizard.next_button)
        stock_quantity = storable.get_stock_item(branch, None).quantity
        self.assertEquals(stock_quantity, 9)
        self.check_wizard(wizard, 'wizard-close-in-consignment-confirm',
                          [wizard.retval, purchase_item, product_stock_item])

    @mock.patch('stoqlib.gui.wizards.consignmentwizard.info')
    @mock.patch('stoqlib.gui.wizards.consignmentwizard.run_dialog')
    def test_close_returned_in_consignment_wizard(self, run_dialog, info):
        purchase_item = self.create_purchase_order_item()
        self.create_receiving_order_item(purchase_item=purchase_item)

        # Create storable.
        product = purchase_item.sellable.product
        Storable(store=self.store, product=product)
        storable = product.storable
        branch = purchase_item.order.branch
        storable.increase_stock(5, branch,
                                StockTransactionHistory.TYPE_INITIAL, None)
        stock_quantity = storable.get_stock_item(branch, None).quantity
        self.assertEquals(stock_quantity, 5)

        purchase_item.quantity_received = 5
        purchase_item.order.status = PurchaseOrder.ORDER_CONSIGNED
        purchase_item.order.identifier = 334
        purchase_item.order.open_date = localdatetime(2012, 1, 1)
        purchase_item.order.expected_receival_date = localdatetime(2012, 2, 2)

        wizard = CloseInConsignmentWizard(self.store)

        step = wizard.get_current_step()
        self.click(step.search.search_button)

        product_stock_item = self.store.find(ProductStockItem,
                                             storable=storable).one()
        self.check_wizard(wizard, 'wizard-return-consignment-selection-step')

        order_view = step.search.results[0]
        step.search.results.select(order_view)
        self.click(wizard.next_button)

        step = wizard.get_current_step()

        # Select consignment.
        step.consignment_items.emit('row_activated', step.consignment_items[0])
        self.assertEquals(run_dialog.call_count, 1)
        args, kwargs = run_dialog.call_args
        editor, parent, store, item = args
        self.assertEquals(editor, InConsignmentItemEditor)
        self.assertEquals(parent, wizard)
        self.assertEquals(item, purchase_item)
        self.assertTrue(store is not None)

        # Return the total received.
        purchase_item.quantity_returned = 5

        self.click(wizard.next_button)
        # After return. Item quantity in stock must be decreased.
        stock_quantity = storable.get_stock_item(branch, None).quantity
        self.assertEquals(stock_quantity, 0)
        self.check_wizard(wizard,
                          'wizard-close-returned-in-consignment-confirm',
                          [wizard.retval, purchase_item, product_stock_item])
