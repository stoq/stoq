# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
##
""" This module test all class in stoq/domain/product.py """


from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.sellable import BaseSellableInfo
from stoqlib.domain.person import Person, EmployeeRole
from stoqlib.domain.sale import Sale
from stoqlib.domain.till import Till
from stoqlib.domain.product import (ProductSupplierInfo, Product,
                                    ProductStockReference,
                                    ProductSellableItem)
from stoqlib.domain.interfaces import (IStorable, IBranch, ISellable,
                                       ISalesPerson, IEmployee, IIndividual)

from stoqlib.domain.test.domaintest import BaseDomainTest, DomainTest

def get_sellable(conn):
    product = Product(connection=conn)
    base_sellable_info = BaseSellableInfo(connection=conn)
    return product.addFacet(ISellable, barcode='abcd',
                            base_sellable_info=base_sellable_info,
                            connection=conn)


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
        self.assertEqual(storable.get_stocks().count(), branches_count)

    def test_get_main_supplier_info(self):
        self.failIf(self.product.get_main_supplier_info())
        supplier = self.create_supplier()
        ProductSupplierInfo(connection=self.trans, supplier=supplier,
                            product=self.product, is_main_supplier=True)
        self.failUnless(self.product.get_main_supplier_info())

class TestProductStockReference(BaseDomainTest):
    _table = ProductStockReference

    @classmethod
    def get_foreign_key_data(cls):
        sellable = get_sellable(cls.conn)
        sales = Sale.select(connection=cls.conn)
        assert sales
        sale = sales[0]
        product_item = sellable.add_sellable_item(sale)
        branch = get_current_branch(cls.conn)
        return branch, product_item


class TestProductSellableItem(BaseDomainTest):
    _table = ProductSellableItem

    def get_foreign_key_data(self):
        till = Till.get_current(self.trans)
        person = Person(name='mr been', connection=self.trans)
        person.addFacet(IIndividual, connection=self.trans)
        role = EmployeeRole(connection=self.trans, name="god")
        person.addFacet(IEmployee, connection=self.trans, role=role)
        salesperson = person.addFacet(ISalesPerson, connection=self.trans)
        sales = Sale.select(connection=self.trans)
        assert sales
        sale = sales[0]
        sellable = get_sellable(self.trans)
        return sale, sellable

    def test_sell(self):
        self.create_instance()
        # Makes the whole process a bit more consistent and creating a new
        # sellable from the beginning
        product = Product(connection=self.trans)
        base_sellable_info = BaseSellableInfo(connection=self.trans)
        sellable = product.addFacet(ISellable, barcode='xyz',
                                    base_sellable_info=base_sellable_info,
                                    connection=self.trans)
        self._instance.sellable = sellable
        storable = product.addFacet(IStorable, connection=self.trans)

        branch = get_current_branch(self.trans)
        stock_results = storable.get_stocks(branch)
        assert stock_results.count() == 1
        current_stock = stock_results[0].quantity
        if current_stock:
            storable.decrease_stock(branch, current_stock)
        assert not storable.get_stocks(branch)[0].quantity
        sold_qty = 2
        storable.increase_stock(sold_qty, branch)
        assert storable.get_stocks(branch).count() == 1
        assert storable.get_stocks(branch)[0].quantity == sold_qty
        # now setting the proper sold quantity in the sellable item
        self._instance.quantity = sold_qty
        self._instance.sell(branch)
        assert not storable.get_stocks(branch)[0].quantity
