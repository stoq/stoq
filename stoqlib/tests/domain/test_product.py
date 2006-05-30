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


from stoqlib.tests.domain.base import BaseDomainTest
from stoqlib.lib.runtime import get_current_branch
from stoqlib.domain.sellable import BaseSellableInfo
from stoqlib.domain.person import Person, EmployeeRole
from stoqlib.domain.sale import Sale
from stoqlib.domain.till import get_current_till_operation
from stoqlib.domain.product import (ProductSupplierInfo, Product,
                                    ProductStockReference,
                                    ProductSellableItem)
from stoqlib.domain.interfaces import (ISupplier, ICompany, IStorable,
                                       IBranch, ISellable, ISalesPerson,
                                       IEmployee, IIndividual)


def get_supplier(conn):
    person = Person(name='Gilberto', connection=conn)
    person.addFacet(ICompany, fancy_name='Lojas ABC', connection=conn)
    return person.addFacet(ISupplier, connection=conn)


def get_sellable(conn):
    product = Product(connection=conn)
    base_sellable_info = BaseSellableInfo(connection=conn)
    return product.addFacet(ISellable, barcode='abcd',
                            base_sellable_info=base_sellable_info,
                            connection=conn)


class TestProductSupplierInfo(BaseDomainTest):
    _table = ProductSupplierInfo

    @classmethod
    def get_foreign_key_data(cls):
        return (Product(connection=cls.conn), get_supplier(cls.conn))

    def test_get_name(self):
        assert (self._instance.get_name()
                == self._instance.supplier.get_adapted().name)

class TestProduct(BaseDomainTest):
    _table = Product

    def test_facet_IStorable_add (self):
        assert not IStorable(self._instance, connection=self.conn)
        storable = self._instance.addFacet(IStorable, connection=self.conn)
        table = Person.getAdapterClass(IBranch)
        branches_count = table.select(connection=self.conn).count()
        assert storable.get_stocks().count() == branches_count

    def test_get_main_supplier_info (self):
        assert not self._instance.get_main_supplier_info()
        supplier = get_supplier(self.conn)
        ProductSupplierInfo(connection=self.conn, supplier=supplier,
                            product=self._instance, is_main_supplier=True)
        assert self._instance.get_main_supplier_info() is not None


class TestProductStockReference(BaseDomainTest):
    _table = ProductStockReference

    @classmethod
    def get_foreign_key_data(cls):
        sellable = get_sellable(cls.conn)
        sales = Sale.select(connection=cls.conn)
        assert sales.count() > 0
        sale = sales[0]
        product_item = sellable.add_sellable_item(sale)
        branch = get_current_branch(cls.conn)
        return branch, product_item


class TestProductSellableItem(BaseDomainTest):
    _table = ProductSellableItem

    @classmethod
    def get_foreign_key_data(cls):
        till = get_current_till_operation(cls.conn)
        person = Person(name='mr been', connection=cls.conn)
        person.addFacet(IIndividual, connection=cls.conn)
        role = EmployeeRole(connection=cls.conn, name="god")
        person.addFacet(IEmployee, connection=cls.conn, role=role)
        salesperson = person.addFacet(ISalesPerson, connection=cls.conn)
        sales = Sale.select(connection=cls.conn)
        assert sales.count() > 0
        sale = sales[0]
        sellable = get_sellable(cls.conn)
        return sale, sellable

    def test_sell(self):
        # Makes the whole process a bit more consistent and creating a new
        # sellable from the beginning
        product = Product(connection=self.conn)
        base_sellable_info = BaseSellableInfo(connection=self.conn)
        sellable = product.addFacet(ISellable, barcode='xyz',
                                    base_sellable_info=base_sellable_info,
                                    connection=self.conn)
        self._instance.sellable = sellable
        storable = product.addFacet(IStorable, connection=self.conn)

        branch = get_current_branch(self.conn)
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
