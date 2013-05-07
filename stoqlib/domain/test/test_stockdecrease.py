# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2010 Async Open Source <http://www.async.com.br>
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

from kiwi.currency import currency

from stoqlib.domain.test.domaintest import DomainTest


class TestStockDecrease(DomainTest):

    def testGetItems(self):
        decrease = self.create_stock_decrease()
        sellable = self.create_sellable()
        decrease.add_sellable(sellable, quantity=5)

        items = decrease.get_items()
        self.assertEqual(items.count(), 1)
        self.assertEqual(sellable, items[0].sellable)

    def testRemoveItem(self):
        decrease = self.create_stock_decrease()
        sellable = self.create_sellable()
        decrease.add_sellable(sellable, quantity=5)

        item = decrease.get_items()[0]
        decrease.remove_item(item)
        self.assertEqual(decrease.get_items().count(), 0)

    def test_get_status_name(self):
        decrease = self.create_stock_decrease()
        self.failUnlessRaises(TypeError,
                              decrease.get_status_name, u'invalid status')

    def testConfirm(self):
        decrease = self.create_stock_decrease()
        sellable = self.create_sellable()
        decrease.add_sellable(sellable, quantity=5)

        branch = decrease.branch
        storable = self.create_storable(sellable.product, branch, 100)

        self.assertEqual(storable.get_stock_item(branch, None).quantity, 100)

        self.failUnless(decrease.can_confirm())
        decrease.confirm()
        self.failIf(decrease.can_confirm())

        self.assertEqual(storable.get_stock_item(branch, None).quantity, 95)

    def test_get_total_cost(self):
        decrease = self.create_stock_decrease()
        sellable1 = self.create_sellable()
        sellable1.cost = currency('100')
        sellable2 = self.create_sellable()
        sellable2.cost = currency('10')
        decrease.add_sellable(sellable1, quantity=2)
        decrease.add_sellable(sellable2, quantity=5)

        self.assertEquals(decrease.get_total_cost(), 250)


class TestStockDecreaseItem(DomainTest):

    def testGetDescription(self):
        decrease = self.create_stock_decrease()
        product = self.create_product()
        decrease_item = decrease.add_sellable(product.sellable)
        self.assertEqual(decrease_item.get_description(), u'Description')

    def test_get_total(self):
        item = self.create_stock_decrease_item()
        item.cost = currency('100')
        item.quantity = 10
        self.assertEqual(item.get_total(), 1000)
