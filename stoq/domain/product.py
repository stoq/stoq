# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2004 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
"""
stoq/domain/product.py:
    
    Base classes to manage product's informations
"""

import gettext
import operator

from stoqlib.exceptions import StockError, SellError
from sqlobject import (StringCol, FloatCol, ForeignKey, MultipleJoin, BoolCol)
from sqlobject.sqlbuilder import AND

from stoq.domain.base_model import Domain, ModelAdapter
from stoq.domain.sellable import (AbstractSellable, 
                                  AbstractSellableItem)
from stoq.domain.person import PersonAdaptToBranch
from stoq.domain.stock import AbstractStockItem
from stoq.domain.interfaces import ISellable, IStorable, IContainer
from stoq.lib.parameters import sysparam
from stoq.lib.runtime import get_connection



_ = gettext.gettext
__connection__ = get_connection()



#
# Base Domain Classes
#



class ProductSupplierInfo(Domain):
    """ This class store information of the suppliers of a product. Each
    product can has more than one supplier.  """
    
    base_cost = FloatCol(default=0.0)
    notes = StringCol(default='')
    is_main_supplier = BoolCol(default=False)
    supplier =  ForeignKey('PersonAdaptToSupplier')
    product =  ForeignKey('Product')



    #
    # Auxiliary methods
    #



    def get_name(self):
        return self.supplier.get_adapted().name


class Product(Domain):
    """ Class responsible to store basic products informations """
    
    notes = StringCol(default='')
    suppliers = MultipleJoin('ProductSupplierInfo')



    #
    # Facet hooks
    #


    
    def facet_IStorable_add(self, **kwargs):
        storable = ProductAdaptToStorable(self, **kwargs)
        storable.fill_stocks()
        return storable
    


    #   
    # Acessors
    #   
        


    def get_main_supplier_info(self):
        if not self.suppliers:
            return
        supplier_data = [supplier_info for supplier_info in self.suppliers 
                                        if supplier_info.is_main_supplier]
        assert not len(supplier_data) > 1
        return supplier_data[0]


class ProductStockReference(Domain):
    """ Base stock informations for products"""

    quantity = FloatCol(default=0.0)
    logic_quantity = FloatCol(default=0.0)
    branch =  ForeignKey('PersonAdaptToBranch')
    product_item =  ForeignKey('ProductSellableItem')


class ProductSellableItem(AbstractSellableItem):
    """ Class responsible to store basic products informations """

    __implements__ = IContainer, 



    #
    # IContainer implementation
    #



    def add_item(self, item):
        raise NotImplementedError('This method should be replaced by '
                                  'add_stock_reference')
        
    def get_items(self):
        conn = self.get_connection()
        return ProductStockReference.selectBy(connection=conn,
                                              product_item=self)

    def remove_item(self, item):
        conn = self.get_connection()
        if not isinstance(item, ProductStockReference):
            raise TypeError("Item should be of type ProductStockReference,"
                            " got " % type(item))
        ProductStockItem.delete(item.id, connection=conn)



    #
    # Basic methods
    #


    
    def sell(self, conn, branch, order_product=False):
        sparam = sysparam(conn)
        if not (branch and 
                branch.id == sparam.CURRENT_BRANCH.id or 
                branch.id == sparam.CURRENT_WAREHOUSE.id):
            msg = ("Stock still doesn't support sales for "
                   "branch companies different than the "
                   "current one or the warehouse")
            raise SellError(msg)

        if order_product and not sparam.ACCEPT_ORDER_PRODUCTS:
            msg = _("This company doesn't allow order products")
            raise SellError(msg)
        
        adapted = self.get_adapted()
        sellable_item = ISellable(adapted)
        sellable_item.setConnection(conn)
        if not sellable_item.can_be_sold():
            msg = '%s is already sold' % adapted
            raise SellError(msg)
            
        if order_product:
            # If order_product is True we will not update the stock for this
            # product
            return

        storable_item = IStorable(adapted)
        storable_item.setConnection(conn)
        # Update the stock
        storable_item.decrease_stock(self.quantity, branch)

        # The function get_balance returns the current amount of items in the
        # stock. If get_balance == 0 we have no more stock for this product
        # and we need to set it as sold.
        logic_qty = storable_item.get_logic_balance()
        balance = storable_item.get_full_balance() - logic_qty
        if not balance:
            sellable_item.set_sold()

            
            
    #
    # Auxiliary methods
    #            



    def add_stock_reference(self, branch, quantity=0.0, 
                            logic_quantity=0.0):
        conn = self.get_connection()
        return ProductStockReference(connection=conn, quantity=quantity, 
                                     logic_quantity=logic_quantity, 
                                     branch=branch, product_item=self)


class ProductStockItem(AbstractStockItem):
    """ Class that makes a reference to the product stock of a 
    certain branch company."""

    storable = ForeignKey('ProductAdaptToStorable')



#
# Adapters
#



class ProductAdaptToSellable(AbstractSellable):
    """ A product implementation as a sellable facet. """

    sellable_table = ProductSellableItem



    #
    # Auxiliary methods
    #



    def add_sellable_item(self, sale, quantity, base_price, price):
        conn = self.get_connection()
        return ProductSellableItem(connection=conn, quantity=quantity,
                                   base_price=base_price, price=price,
                                   sale=sale, sellable=self)

Product.registerFacet(ProductAdaptToSellable)


class ProductAdaptToStorable(ModelAdapter):
    """ A product implementation as a storable facet. """
    
    __implements__ = IStorable, IContainer

    def __init__(self, _original=None, *args, **kwargs):
        ModelAdapter.__init__(self, _original, *args, **kwargs)
        conn = self.get_connection()
        self.precision = sysparam(conn).STOCK_BALANCE_PRECISION



    #
    # IContainer implementation
    #

    

    def add_item(self, item):
        raise NotImplementedError('This method should be replaced '
                                  'by add_stock_item')


    def get_items(self):
        raise NotImplementedError('This method should be replaced '
                                  'by get_stocks')

    def remove_item(self, item):
        conn = self.get_connection()
        if not isinstance(item, ProductStockItem):
            raise TypeError("Item should be of type ProductStockItem, got "
                            % type(item))
        ProductStockItem.delete(item.id, connection=conn)



    #
    # IStorable implementation
    #



    def fill_stocks(self):
        conn = self.get_connection()
        branch_companies = PersonAdaptToBranch.select(connection=conn)
        for branch in branch_companies:
            self.add_stock_item(branch)

    def increase_stock(self, quantity, branch=None):
        stocks = self.get_stocks(branch)
        for stock_item in stocks:
            stock_item.quantity += quantity

    def increase_logic_stock(self, quantity, branch=None):
        self._check_logic_quantity()
        stocks = self.get_stocks(branch)
        for stock_item in stocks:
            stock_item.logic_quantity += quantity

    def check_rejected_stocks(self, stocks, quantity, check_logic=False):
        for stock_item in stocks:
            if check_logic:
                base_qty = stock_item.logic_quantity
            else:
                base_qty = stock_item.quantity
            if base_qty < quantity:
                msg = ('Quantity to decrease is greater than available '
                       'stock.')
                raise StockError(msg)

    def decrease_stock(self, quantity, branch=None):
        if not self._has_qty_available(quantity, branch):
            # Of course that here we must use the logic quantity balance 
            # as an addition to our main stock
            logic_qty = self.get_logic_balance(branch)
            balance = self.get_full_balance(branch) - logic_qty
            logic_sold_qty = quantity - balance
            quantity -= logic_sold_qty
            self.decrease_logic_stock(logic_sold_qty, branch)

        stocks = self.get_stocks(branch)
        self.check_rejected_stocks(stocks, quantity)

        for stock_item in stocks:
            stock_item.quantity -= quantity

    def decrease_logic_stock(self, quantity, branch=None):
        self._check_logic_quantity()
        rejected = []

        stocks = self.get_stocks(branch)
        self.check_rejected_stocks(stocks, quantity, check_logic=True)

        for stock_item in stocks:
            stock_item.logic_quantity -= quantity

    def get_full_balance(self, branch=None):
        """ Get the stock balance and the logic balance."""
        stocks = self.get_stocks(branch)
        if not stocks.count():
            raise StockError, 'Invalid stock references for %s' % self
        value = 0.0
        has_logic_qty = sysparam(self.get_connection()).USE_LOGIC_QUANTITY
        for stock_item in stocks:
            value += stock_item.quantity
            if has_logic_qty:
                value += stock_item.logic_quantity
        return value

    def get_logic_balance(self, branch=None):
        stocks = self.get_stocks(branch)
        assert stocks.count() >= 1
        values = [stock_item.logic_quantity for stock_item in stocks]
        return reduce(operator.add, values, 0.0)

    def get_average_stock_price(self):
        total_cost = 0.0
        total_qty = 0.0
        for stock_item in self.get_stocks():
            total_cost += stock_item.total_cost
            total_qty += stock_item.quantity

        if total_cost and not total_qty:
            msg = ('%s has inconsistent stock information: Quantity = 0 '
                   'and TotalCost= %f')
            raise StockError(msg % (self.get_adapted(), total_cost))
        if not total_qty:
            return 0.0
        return total_cost / total_qty

    def _has_qty_available(self, quantity, branch):
        logic_qty = self.get_logic_balance(branch)
        balance = self.get_full_balance(branch) - logic_qty
        qty_ok =  quantity <= balance
        logic_qty_ok = quantity <= self.get_balance(branch)
        has_logic_qty = sysparam(self.get_connection()).USE_LOGIC_QUANTITY
        if not qty_ok and not (has_logic_qty and logic_qty_ok):
            msg = ('Quantity to sell is greater than the available '
                   'stock.')
            raise StockError(msg)
        return qty_ok



    #
    # Accessors
    #



    def get_full_balance_string(self, branch=None):
        return '%.*f' % (int(self.precision), self.get_full_balance(branch))



    #
    # Auxiliary methods
    #            



    def _check_logic_quantity(self):
        if not sysparam(self.get_connection()).USE_LOGIC_QUANTITY:
            msg = ("This company doesn't allow logic quantity "
                   "operations.")
            raise StockError(msg)

    def add_stock_item(self, branch, stock_cost=0.0, quantity=0.0,
                       logic_quantity=0.0):
        conn = self.get_connection()
        return ProductStockItem(connection=conn, branch=branch,
                                stock_cost=stock_cost, quantity=quantity,
                                logic_quantity=logic_quantity,
                                storable=self)

    def get_stocks(self, branch=None):
        conn = self.get_connection()
        table, parent = ProductStockItem, AbstractStockItem
        q1 = table.q.id == parent.q.id
        q2 = table.q.storableID == self.id
        if not branch:
            query = AND(q1, q2)
        else:
            q3 = parent.q.branchID == branch.id
            query = AND(q1, q2, q3)
        return ProductStockItem.select(query, connection=conn)


Product.registerFacet(ProductAdaptToStorable)



#
# Auxiliary functions
#



def storables_set_branch(conn, branch):
    """A method that must be called always when a new branch company is
    created. It creates a new stock reference for all the products."""
    for storable in ProductAdaptToStorable.select(connection=conn):
        storable.add_stock_item(branch)
