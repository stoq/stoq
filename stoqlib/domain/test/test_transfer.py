# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007-2015 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

from kiwi.currency import currency

from stoqlib.domain.product import Product, ProductHistory
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.domain.transfer import TransferOrderItem

__tests__ = 'stoqlib/domain/transfer.py'


class TestTransferOrderItem(DomainTest):

    def test__init__(self):
        with self.assertRaisesRegexp(
                TypeError, 'You must provide a sellable argument'):
                TransferOrderItem(store=self.store)
        item = self.create_transfer_order_item()
        self.assertIsNotNone(item.icms_info)
        self.assertIsNotNone(item.ipi_info)

    def test_get_total(self):
        order = self.create_transfer_order()
        item = self.create_transfer_order_item(order)
        self.assertEquals(item.get_total(), 625)

    def test_parent(self):
        order = self.create_transfer_order()
        item = self.create_transfer_order_item(order)
        self.assertEquals(item.parent, order)

    def test_base_price(self):
        transfer_item = self.create_transfer_order_item(stock_cost=70)
        self.assertEquals(transfer_item.base_price, 70)

    def test_price(self):
        transfer_item = self.create_transfer_order_item(stock_cost=50)
        self.assertEquals(transfer_item.price, transfer_item.stock_cost)

    def test_nfe_cfop_code(self):
        order = self.create_transfer_order()
        transfer_item = self.create_transfer_order_item(order)
        source = order.source_branch
        destination = order.destination_branch

        location = self.create_city_location(city='São Carlos',
                                             state='SP', country='Brazil')
        # Source branch address is the same of destination branch
        source.person.address.city_location = location
        destination.person.address.city_location = location
        self.assertEquals(transfer_item.nfe_cfop_code, u'5152')

        # Source branch address isn't the same of destination branch
        location = self.create_city_location(city='Salvador',
                                             state='BA', country='Brazil')
        destination.person.address.city_location = location
        self.assertEquals(transfer_item.nfe_cfop_code, u'6152')


class TestTransferOrder(DomainTest):

    def test_transfer_process(self):
        order = self.create_transfer_order()
        self.assertEqual(order.can_send(), False)
        self.assertEqual(order.can_receive(), False)

        self.create_transfer_order_item(order)
        self.assertEqual(order.can_send(), True)
        self.assertEqual(order.can_receive(), False)

        order.send()
        self.assertEqual(order.can_send(), False)
        self.assertEqual(order.can_receive(), True)

        order.receive(self.create_employee())
        self.assertEqual(order.can_send(), False)
        self.assertEqual(order.can_receive(), False)

    def test_add_sellable(self):
        order = self.create_transfer_order()
        product = self.create_product()
        product.manage_stock = False
        order.add_sellable(product.sellable, None)

        transfer_order_item = self.store.find(TransferOrderItem,
                                              sellable=product.sellable).one()

        self.assertFalse(transfer_order_item.sellable.product.manage_stock)

    def test_send(self):
        qty = 2
        order = self.create_transfer_order()
        item = self.create_transfer_order_item(order, quantity=qty)

        product = self.store.find(Product, sellable=item.sellable).one()
        storable = product.storable
        before_qty = storable.get_balance_for_branch(order.source_branch)
        order.send()
        after_qty = storable.get_balance_for_branch(order.source_branch)
        self.assertEqual(after_qty, before_qty - qty)

        history = self.store.find(ProductHistory, sellable=item.sellable).one()
        self.failIf(history is None)
        self.assertEqual(history.quantity_transfered, qty)

    def test_receive(self):
        sent_qty = 2
        order = self.create_transfer_order()
        item = self.create_transfer_order_item(order, quantity=sent_qty)
        order.send()

        storable = item.sellable.product_storable
        before_qty = storable.get_balance_for_branch(order.destination_branch)
        order.receive(self.create_employee())
        after_qty = storable.get_balance_for_branch(order.destination_branch)
        self.assertEqual(after_qty, before_qty + sent_qty)

    def test_cancel(self):
        quantity = 1
        order = self.create_transfer_order()
        item = self.create_transfer_order_item(order, quantity=quantity)
        storable = item.sellable.product_storable

        # Checking the balance before send
        sour_before_qty = storable.get_balance_for_branch(order.source_branch)
        dest_before_qty = storable.get_balance_for_branch(order.destination_branch)
        self.assertEquals(sour_before_qty, 1)
        self.assertEquals(dest_before_qty, 0)
        order.send()

        # Checking the balance after sending
        sour_during_qty = storable.get_balance_for_branch(order.source_branch)
        dest_during_qty = storable.get_balance_for_branch(order.destination_branch)

        self.assertEquals(sour_during_qty, 0)
        self.assertEquals(dest_during_qty, 0)

        order.cancel(self.create_employee())
        # Checking the balance after cancel
        sour_after_qty = storable.get_balance_for_branch(order.source_branch)
        dest_after_qty = storable.get_balance_for_branch(order.destination_branch)
        self.assertEquals(sour_after_qty, 1)
        self.assertEquals(dest_after_qty, 0)

    def test_add_item(self):
        order = self.create_transfer_order()

        item = self.create_transfer_order_item()
        order.add_item(item)
        self.assertEquals(item.transfer_order, order)

    def test_remove_item(self):
        order = self.create_transfer_order()
        item = self.create_transfer_order_item(order)
        order.remove_item(item)

        order = self.create_transfer_order()
        item = self.create_transfer_order_item()
        self.assertRaises(ValueError, order.remove_item, item)

        with self.sysparam(SYNCHRONIZED_MODE=True):
            item = self.create_transfer_order_item()
            order = item.transfer_order

            before_remove = self.store.find(TransferOrderItem).count()
            order.remove_item(item)
            after_remove = self.store.find(TransferOrderItem).count()

            # The item should still be on the database
            self.assertEqual(before_remove, after_remove)

            # But not related to the loan
            self.assertEquals(self.store.find(TransferOrderItem, transfer_order=order).count(), 0)

    def test_get_source_branch_name(self):
        order = self.create_transfer_order()
        self.assertEquals(order.get_source_branch_name(), u'Source shop')

    def test_get_destination_branch_name(self):
        order = self.create_transfer_order()
        self.assertEquals(order.get_destination_branch_name(), u'Dest shop')

    def test_get_source_responsible_name(self):
        order = self.create_transfer_order()
        self.assertEquals(order.get_source_responsible_name(),
                          u'Ipswich')

    def test_get_destination_responsible_name(self):
        order = self.create_transfer_order()
        self.assertEquals(order.get_destination_responsible_name(),
                          u'Bolton')

        order.destination_responsible = None
        self.assertEquals(order.get_destination_responsible_name(),
                          u'')

    def test_get_total_items_transfer(self):
        order = self.create_transfer_order()
        self.create_transfer_order_item(order)
        self.assertEquals(order.get_total_items_transfer(), 5)
        self.create_transfer_order_item(order)
        self.assertEquals(order.get_total_items_transfer(), 10)

    def test_status_str(self):
        order = self.create_transfer_order()
        self.assertEquals(order.status_str, 'Pending')

    def test_branch(self):
        order = self.create_transfer_order()
        self.assertTrue(order.branch)
        self.assertEquals(order.branch, order.source_branch)
        order.source_branch = None
        self.assertFalse(order.branch)
        self.assertEquals(order.branch, order.source_branch)

    def test_discount_value(self):
        order = self.create_transfer_order()
        self.assertEquals(order.discount_value, currency(0))

    def test_invoice_total(self):
        order = self.create_transfer_order()
        self.create_transfer_order_item(order, quantity=1, stock_cost=20)
        self.assertEquals(order.invoice_total, 20)
        self.create_transfer_order_item(order, quantity=2, stock_cost=20)
        self.assertEquals(order.invoice_total, 60)

    def test_recipient(self):
        destination_branch = self.create_branch()
        order = self.create_transfer_order(dest_branch=destination_branch)
        self.assertEquals(order.destination_branch.person, order.recipient)

    def test_operation_nature(self):
        # FIXME: Check using the operation_nature that will be saved in new field.
        order = self.create_transfer_order()
        self.assertEquals(order.operation_nature, u'Transfer')
