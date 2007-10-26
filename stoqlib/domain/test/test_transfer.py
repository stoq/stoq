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
## Author(s):   George Kussumoto    <george@async.com.br>
##

from stoqlib.domain.interfaces import IStorable
from stoqlib.domain.product import ProductHistory
from stoqlib.domain.test.domaintest import DomainTest


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

        storable = IStorable(item.sellable)
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

        storable = IStorable(item.sellable)
        if storable.has_stock_by_branch(order.destination_branch):
            before_qty = storable.get_full_balance()
        else:
            before_qty = 0
        order.receive()
        after_qty = storable.get_full_balance(order.destination_branch)
        self.assertEqual(order.can_close(), False)

        self.assertEqual(after_qty, before_qty + sent_qty)
