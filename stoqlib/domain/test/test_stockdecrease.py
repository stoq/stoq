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

from stoqlib.domain.interfaces import IStorable
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

        item = 'test purpose'
        self.failUnlessRaises(TypeError, decrease.remove_item, item)
        item = decrease.get_items()[0]
        decrease.remove_item(item)
        self.assertEqual(decrease.get_items().count(), 0)

    def test_get_status_name(self):
        decrease = self.create_stock_decrease()
        self.failUnlessRaises(TypeError,
                              decrease.get_status_name, 'invalid status')

    def testConfirm(self):
        decrease = self.create_stock_decrease()
        sellable = self.create_sellable()
        decrease.add_sellable(sellable, quantity=5)

        branch = decrease.branch

        storable = sellable.product.addFacet(IStorable, connection=self.trans)
        storable.increase_stock(100, branch)

        self.assertEqual(storable.get_stock_item(branch).quantity, 100)

        self.failUnless(decrease.can_confirm())
        decrease.confirm()
        self.failIf(decrease.can_confirm())

        self.assertEqual(storable.get_stock_item(branch).quantity, 95)


class TestStockDecreaseItem(DomainTest):

    def testGetDescription(self):
        decrease = self.create_stock_decrease()
        product = self.create_product()
        decrease_item = decrease.add_sellable(product.sellable)
        self.assertEqual(decrease_item.get_description(), 'Description')
