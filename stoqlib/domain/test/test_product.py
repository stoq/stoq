# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2007 Async Open Source <http://www.async.com.br>
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
## Author(s):   Grazieno Pellegrino         <grazieno1@yahoo.com.br>
##              Evandro Vale Miquelito      <evandro@async.com.br>
##              Johan Dahlin                <jdahlin@async.com.br>
##
""" This module test all class in stoqlib/domain/product.py """


from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.sellable import BaseSellableInfo
from stoqlib.domain.person import Person
from stoqlib.domain.product import (ProductSupplierInfo, Product,
                                    ProductSellableItem)
from stoqlib.domain.interfaces import IStorable, IBranch, ISellable

from stoqlib.domain.test.domaintest import DomainTest

class TestProductSupplierInfo(DomainTest):

    def testGetName(self):
        product = self.create_product()
        supplier = self.create_supplier()
        info = ProductSupplierInfo(connection=self.trans,
                                   product=product,
                                   supplier=supplier)
        self.assertEqual(info.get_name(), supplier.get_description())

class TestProduct(DomainTest):
    def setUp(self):
        DomainTest.setUp(self)
        self.product = Product(connection=self.trans)

    def test_facet_IStorable_add(self):
        self.failIf(IStorable(self.product, None))
        storable = self.product.addFacet(IStorable, connection=self.trans)
        branches_count = Person.iselect(IBranch, connection=self.trans).count()
        self.assertEqual(storable.get_stock_items().count(), branches_count)

    def test_get_main_supplier_info(self):
        self.failIf(self.product.get_main_supplier_info())
        supplier = self.create_supplier()
        ProductSupplierInfo(connection=self.trans, supplier=supplier,
                            product=self.product, is_main_supplier=True)
        self.failUnless(self.product.get_main_supplier_info())

class TestProductSellableItem(DomainTest):

    def testSell(self):
        sale = self.create_sale()
        product = Product(connection=self.trans)
        base_sellable_info = BaseSellableInfo(connection=self.trans)
        sellable = product.addFacet(ISellable, barcode='xyz',
                                    base_sellable_info=base_sellable_info,
                                    connection=self.trans)
        product_sellable_item = ProductSellableItem(connection=self.trans,
                                                    sellable=sellable,
                                                    quantity=1,
                                                    price=1,
                                                    sale=sale)
        storable = product.addFacet(IStorable, connection=self.trans)

        branch = get_current_branch(self.trans)
        stock_item = storable.get_stock_item(branch)
        assert stock_item is not None
        current_stock = stock_item.quantity
        if current_stock:
            storable.decrease_stock(branch, current_stock)
        assert not storable.get_stock_item(branch).quantity
        sold_qty = 2
        storable.increase_stock(sold_qty, branch)
        assert storable.get_stock_item(branch) is not None
        assert storable.get_stock_item(branch).quantity == sold_qty
        # now setting the proper sold quantity in the sellable item
        product_sellable_item.quantity = sold_qty
        product_sellable_item.sell(branch)
        assert not storable.get_stock_item(branch).quantity
