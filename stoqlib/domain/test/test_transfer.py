# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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

from stoqlib.domain.interfaces import IStorable
from stoqlib.domain.product import Product, ProductHistory
from stoqlib.domain.test.domaintest import DomainTest


class TestTransferOrderItem(DomainTest):

    def testGetTotal(self):
        order = self.create_transfer_order()
        item = self.create_transfer_order_item(order)
        self.assertEquals(item.get_total(), 625)


class TestTransferOrder(DomainTest):

    def testCanClose(self):
        order = self.create_transfer_order()
        self.assertEqual(order.can_close(), False)

        item = self.create_transfer_order_item(order)
        self.assertEqual(order.can_close(), True)

        order.send_item(item)
        self.assertEqual(order.can_close(), True)

        order.receive()
        self.assertEqual(order.can_close(), False)

    def testSendItem(self):
        order = self.create_transfer_order()
        self.assertEqual(order.can_close(), False)

        sent_qty = 2
        item = self.create_transfer_order_item(order, quantity=2)
        self.assertEqual(order.can_close(), True)

        product = Product.selectOneBy(sellable=item.sellable,
                                      connection=self.trans)
        storable = IStorable(product)
        before_qty = storable.get_full_balance(order.source_branch)
        order.send_item(item)
        after_qty = storable.get_full_balance(order.source_branch)
        self.assertEqual(after_qty, before_qty - sent_qty)

        history = ProductHistory.selectOneBy(sellable=item.sellable,
                                             connection=self.trans)
        self.failIf(history is None)
        self.assertEqual(history.quantity_transfered, sent_qty)

    def testReceive(self):
        order = self.create_transfer_order()
        self.assertEqual(order.can_close(), False)

        sent_qty = 2
        item = self.create_transfer_order_item(order, quantity=sent_qty)
        self.assertEqual(order.can_close(), True)
        order.send_item(item)

        storable = IStorable(item.sellable.product)
        if storable.has_stock_by_branch(order.destination_branch):
            before_qty = storable.get_full_balance()
        else:
            before_qty = 0
        order.receive()
        after_qty = storable.get_full_balance(order.destination_branch)
        self.assertEqual(order.can_close(), False)

        self.assertEqual(after_qty, before_qty + sent_qty)

    def testAddItem(self):
        order = self.create_transfer_order()

        item = self.create_transfer_order_item()
        order.add_item(item)
        self.assertEquals(item.transfer_order, order)

    def testRemoveItem(self):
        order = self.create_transfer_order()
        item = self.create_transfer_order_item(order)
        order.remove_item(item)

        order = self.create_transfer_order()
        item = self.create_transfer_order_item()
        self.assertRaises(ValueError, order.remove_item, item)

    def testGetSourceBranchName(self):
        order = self.create_transfer_order()
        self.assertEquals(order.get_source_branch_name(), 'Source')

    def testGetDestinationBranchName(self):
        order = self.create_transfer_order()
        self.assertEquals(order.get_destination_branch_name(),
                          'Dest')

    def testGetSourceResponsibleName(self):
        order = self.create_transfer_order()
        self.assertEquals(order.get_source_responsible_name(),
                          'Ipswich')

    def testGetDestinationResponsibleName(self):
        order = self.create_transfer_order()
        self.assertEquals(order.get_destination_responsible_name(),
                          'Bolton')

    def testGetTotalItemsTransfer(self):
        order = self.create_transfer_order()
        self.create_transfer_order_item(order)
        self.assertEquals(order.get_total_items_transfer(), 5)
        self.create_transfer_order_item(order)
        self.assertEquals(order.get_total_items_transfer(), 10)
