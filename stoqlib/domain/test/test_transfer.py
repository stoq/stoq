# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007-2013 Async Open Source <http://www.async.com.br>
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

from stoqlib.domain.product import Product, ProductHistory
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.domain.transfer import TransferOrderItem

__tests__ = 'stoqlib/domain/transfer.py'


class TestTransferOrderItem(DomainTest):

    def test_get_total(self):
        order = self.create_transfer_order()
        item = self.create_transfer_order_item(order)
        self.assertEquals(item.get_total(), 625)


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
