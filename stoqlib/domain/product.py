# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2007 Async Open Source <http://www.async.com.br>
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
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##              Johan Dahlin                <jdahlin@async.com.br>

""" Base classes to manage product's informations """

import datetime
from decimal import Decimal

from kiwi.datatypes import currency
from kiwi.argcheck import argcheck
from sqlobject import (UnicodeCol, ForeignKey, MultipleJoin, DateTimeCol,
                       BoolCol, BLOBCol)
from sqlobject.sqlbuilder import AND
from zope.interface import implements

from stoqlib.database.columns import PriceCol, DecimalCol
from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.base import Domain, ModelAdapter
from stoqlib.domain.person import Person
from stoqlib.domain.interfaces import (ISellable, IStorable, IContainer,
                                       IDelivery, IBranch)
from stoqlib.domain.sellable import ASellable, ASellableItem
from stoqlib.exceptions import (StockError, SellError, DatabaseInconsistency,
                                StoqlibError)
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.parameters import sysparam

_ = stoqlib_gettext

#
# pyflakes
#
Person

#
# Base Domain Classes
#


class ProductSupplierInfo(Domain):
    """
    Supplier information for a Product

    Each product can has more than one supplier.

    B{Important attributes}:
        - I{is_main_supplier}: defines if this object stores information
                               for the main supplier.
        - I{base_cost}: the cost which helps the purchaser to define the
                        main cost of a certain product. Each product can
                        have multiple suppliers and for each supplier a
                        base_cost is available. The purchaser in this case
                        must decide how to define the main cost based in
                        the base cost avarage of all suppliers.
        - I(icms): a Brazil-specific attribute that means
                   'Imposto sobre circulacao de mercadorias e prestacao '
                   'de servicos'
    """

    base_cost = PriceCol(default=0)
    notes = UnicodeCol(default='')
    is_main_supplier = BoolCol(default=False)
    # This is Brazil-specific information
    icms = DecimalCol(default=0)
    supplier =  ForeignKey('PersonAdaptToSupplier', notNone=True)
    product =  ForeignKey('Product')


    #
    # Auxiliary methods
    #

    def get_name(self):
        return self.supplier.get_description()


class ProductRetentionHistory(Domain):
    """Class responsible to store information about product's retention."""

    quantity = DecimalCol(default=0)
    reason = UnicodeCol(default='')
    product = ForeignKey('Product')


class Product(Domain):
    """Class responsible to store basic products informations."""

    suppliers = MultipleJoin('ProductSupplierInfo')
    image = BLOBCol(default='')

    #
    # Facet hooks
    #

    def facet_IStorable_add(self, **kwargs):
        return ProductAdaptToStorable(self, **kwargs)

    #
    # General Methods
    #

    def block(self, conn, quantity, branch, reason, product):
        storable = IStorable(self)
        storable.decrease_stock(quantity, branch)
        return ProductRetentionHistory(quantity=quantity, product=product,
                                       reason=reason, connection=conn)

    #
    # Acessors
    #

    def get_main_supplier_name(self):
        supplier_info = self.get_main_supplier_info()
        return supplier_info.get_name()

    def get_main_supplier_info(self):
        """
        Gets a list of main suppliers for a Product, the main supplier
        is the most recently selected supplier.

        @returns: main supplier info
        @rtype: ProductSupplierInfo or None if a product lacks
           a main suppliers
        """
        return ProductSupplierInfo.selectOneBy(
            product=self,
            is_main_supplier=True,
            connection=self.get_connection())


class ProductHistory(Domain):
    """Stores product history, such as sold and received quantity.
    """
    # We keep a reference to ASellable instead of Product because we want to
    # display the sellable id in the interface instead of the product id for
    # consistency with interfaces that display both
    quantity_sold = DecimalCol(default=0)
    quantity_received = DecimalCol(default=0)
    sold_date = DateTimeCol(default=datetime.datetime.now)
    received_date = DateTimeCol(default=datetime.datetime.now)
    branch = ForeignKey("PersonAdaptToBranch")
    sellable = ForeignKey("ASellable")

    @classmethod
    def add_sold_item(cls, conn, branch, product_sellable_item):
        """
        Adds a sold item, populates the ProductHistory table using a
        product_sellable_item created during a sale.

        @param conn: a database connection
        @param branch: the branch
        @param product_sellable_item: the sellable item for the sold
        """
        cls(branch=branch,
            sellable=product_sellable_item.sellable,
            quantity_sold=product_sellable_item.quantity,
            sold_date=datetime.datetime.now(),
            connection=conn)

    @classmethod
    def add_received_item(cls, conn, branch, receiving_order_item):
        """
        Adds a received_item, populates the ProductHistory table using a
        receiving_order_item created during a purchase

        @param conn: a database connection
        @param branch: the branch
        @param receiving_order_item: the item received for puchase
        """
        cls(branch=branch, sellable=receiving_order_item.sellable,
            quantity_received=receiving_order_item.quantity,
            received_date=receiving_order_item.receiving_order.receival_date,
            connection=conn)


class ProductStockReference(Domain):
    """Stock informations for products.

    B{Important attributes}:
        - I{logic_quantity}: Represents the current quantity of a product
                             in the warehouse reserved for this store.
                             For example: you can have decentralized
                             servers, in this case the quantity of the
                             product in the stock will be shared between the
                             stores, or a centralized server wich contains
                             all the product.
    """

    quantity = DecimalCol(default=0)
    logic_quantity = DecimalCol(default=0)
    branch =  ForeignKey('PersonAdaptToBranch')
    product_item =  ForeignKey('ProductSellableItem')


class ProductSellableItem(ASellableItem):
    """Class responsible to store basic products informations."""

    implements(IContainer)

    _inheritable = False

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
                            " got %r" % type(item))
        ProductStockReference.delete(item.id, connection=conn)

    #
    # Basic methods
    #

    def sell(self, branch, order_product=False):
        conn = self.get_connection()
        sparam = sysparam(conn)
        if not (branch and
                branch.id == get_current_branch(conn).id):
            raise SellError("Stock still doesn't support sales for "
                            "branch companies different than the "
                            "current one")

        if order_product and not sparam.ACCEPT_ORDER_PRODUCTS:
            raise SellError(
                _("This company doesn't allow order products"))

        if not self.sellable.can_be_sold():
            raise SellError('%r is already sold' % self.sellable)

        if order_product:
            # TODO waiting for bug 2469
            raise StoqlibError("Order products is not a valid feature yet")

        # FIXME: Don't use sellable.get_adapted()
        adapted = self.sellable.get_adapted()
        storable = IStorable(adapted)
        # Update the stock
        storable.decrease_stock(self.quantity, branch)

        # The function get_full_balance returns the current amount of items
        # in the stock. If get_full_balance == 0 we have no more stock for
        # this product and we need to set it as sold.
        logic_qty = storable.get_logic_balance()
        balance = storable.get_full_balance() - logic_qty
        if not balance:
            self.sellable.sell()

    def cancel(self, branch):
        # FIXME: Don't use sellable.get_adapted()
        adapted = self.sellable.get_adapted()
        storable = IStorable(adapted)
        # Update the stock
        storable.increase_stock(self.quantity, branch)

    #
    # General methods
    #

    def get_quantity_delivered(self):
        # Avoiding circular imports here
        from stoqlib.domain.service import ServiceSellableItem
        services = ASellableItem.select(
            AND(ASellableItem.q.saleID == self.sale.id,
                ASellableItem.q.id == ServiceSellableItem.q.id),
            connection=self.get_connection())
        if not services:
            return Decimal(0)
        delivered_qty = Decimal(0)
        for service in services:
            delivery = IDelivery(service, None)
            if not delivery:
                continue
            item = delivery.get_item_by_sellable(self.sellable)
            if not item:
                continue
            delivered_qty += item.quantity
        return delivered_qty

    def has_been_totally_delivered(self):
        return self.get_quantity_delivered() == self.quantity


    def add_stock_reference(self, branch, quantity=0,
                            logic_quantity=0):
        conn = self.get_connection()
        return ProductStockReference(connection=conn, quantity=quantity,
                                     logic_quantity=logic_quantity,
                                     branch=branch, product_item=self)


class ProductStockItem(Domain):
    """Class that makes a reference to the product stock of a
    certain branch company."""

    stock_cost = PriceCol(default=0)
    quantity = DecimalCol(default=0)
    logic_quantity = DecimalCol(default=0)
    branch =  ForeignKey('PersonAdaptToBranch')
    storable = ForeignKey('ProductAdaptToStorable')


#
# Adapters
#


class ProductAdaptToSellable(ASellable):
    """A product implementation as a sellable facet."""

    _inheritable = False

    sellableitem_table = ProductSellableItem

Product.registerFacet(ProductAdaptToSellable, ISellable)


class ProductAdaptToStorable(ModelAdapter):
    """A product implementation as a storable facet."""

    implements(IStorable, IContainer)

    retention = MultipleJoin('ProductRetentionHistory')

    def _create(self, id, **kwargs):
        super(ProductAdaptToStorable, self)._create(id, **kwargs)
        self._fill_stocks()

    #
    # Private
    #

    def _fill_stocks(self):
        for branch in Person.iselect(IBranch,
                                     connection=self.get_connection()):
            self._add_stock_item(branch)

    def _check_logic_quantity(self):
        if sysparam(self.get_connection()).USE_LOGIC_QUANTITY:
            return
        raise StockError(
            "This company doesn't allow logic quantity operations")

    def _check_rejected_stocks(self, stocks, quantity, check_logic=False):
        for stock_item in stocks:
            if check_logic:
                base_qty = stock_item.logic_quantity
            else:
                base_qty = stock_item.quantity
            if base_qty < quantity:
                raise StockError('Quantity to decrease is greater than available '
                                 'stock.')

    def _has_qty_available(self, quantity, branch):
        logic_qty = self.get_logic_balance(branch)
        balance = self.get_full_balance(branch) - logic_qty
        qty_ok = quantity <= balance
        logic_qty_ok = quantity <= self.get_full_balance(branch)
        has_logic_qty = sysparam(self.get_connection()).USE_LOGIC_QUANTITY
        if not qty_ok and not (has_logic_qty and logic_qty_ok):
            raise StockError('Quantity to sell is greater than the available '
                             'stock.')
        return qty_ok

    def _add_stock_item(self, branch, stock_cost=0.0, quantity=0.0,
                        logic_quantity=0.0):
        conn = self.get_connection()
        return ProductStockItem(connection=conn, branch=branch,
                                stock_cost=stock_cost, quantity=quantity,
                                logic_quantity=logic_quantity,
                                storable=self)

    @argcheck(Person.getAdapterClass(IBranch))
    def _get_stocks(self, branch=None):
        # FIXME: Get rid of this after fixing all call sites.
        query_args = {}
        if branch:
            query_args['branch'] = branch.id
        return ProductStockItem.selectBy(storable=self,
                                         connection=self.get_connection(),
                                         **query_args)

    #
    # IContainer implementation
    #

    def add_item(self, item):
        raise NotImplementedError

    def get_items(self):
        raise NotImplementedError

    def remove_item(self, item):
        conn = self.get_connection()
        if not isinstance(item, ProductStockItem):
            raise TypeError("Item should be of type ProductStockItem, got "
                            % type(item))
        ProductStockItem.delete(item.id, connection=conn)

    #
    # Properties
    #

    @property
    def product(self):
        return self.get_adapted()

    #
    # IStorable implementation
    #

    def increase_stock(self, quantity, branch):
        if quantity <= 0:
            raise ValueError("quantity must be a positive number")

        stock_item = self.get_stock_item(branch)
        stock_item.quantity += quantity

        # FIXME: We should only need to mark the sellable facet as sellable when
        #        going from 0 -> n, but for some reasons this is not enough,
        #        perhaps when the storable is initialized with a non-zero quantity
        sellable = ISellable(self.product, None)
        if sellable:
            sellable.can_sell()

    def decrease_stock(self, quantity, branch):
        if not self._has_qty_available(quantity, branch):
            # Of course that here we must use the logic quantity balance
            # as an addition to our main stock
            logic_qty = self.get_logic_balance(branch)
            balance = self.get_full_balance(branch) - logic_qty
            logic_sold_qty = quantity - balance
            quantity -= logic_sold_qty
            self.decrease_logic_stock(logic_sold_qty, branch)

        stock_item = self.get_stock_item(branch)
        self._check_rejected_stocks([stock_item], quantity)

        stock_item.quantity -= quantity

    def increase_logic_stock(self, quantity, branch=None):
        self._check_logic_quantity()
        stocks = self._get_stocks(branch)
        for stock_item in stocks:
            stock_item.logic_quantity += quantity

    def decrease_logic_stock(self, quantity, branch=None):
        self._check_logic_quantity()

        stocks = self._get_stocks(branch)
        self._check_rejected_stocks(stocks, quantity, check_logic=True)
        for stock_item in stocks:
            stock_item.logic_quantity -= quantity

    def get_full_balance(self, branch=None):
        """ Get the stock balance and the logic balance."""
        stocks = self._get_stocks(branch)
        if not stocks:
            raise StockError, 'Invalid stock references for %s' % self
        value = Decimal(0)
        has_logic_qty = sysparam(self.get_connection()).USE_LOGIC_QUANTITY
        for stock_item in stocks:
            value += stock_item.quantity
            if has_logic_qty:
                value += stock_item.logic_quantity
        return value

    def get_logic_balance(self, branch=None):
        stocks = self._get_stocks(branch)
        assert stocks.count() >= 1
        values = [stock_item.logic_quantity for stock_item in stocks]
        return sum(values, Decimal(0))

    def get_average_stock_price(self):
        total_cost = Decimal(0)
        total_qty = Decimal(0)
        for stock_item in self.get_stock_items():
            total_cost += stock_item.stock_cost
            total_qty += stock_item.quantity

        if total_cost and not total_qty:
            raise StockError(
                '%r has inconsistent stock information: Quantity = 0 '
                'and TotalCost= %f' % (self, total_cost))
        if not total_qty:
            return currency(0)
        return currency(total_cost / total_qty)

    def has_stock_by_branch(self, branch):
        stock = self._get_stocks(branch)
        qty = stock.count()
        if not qty == 1:
            raise DatabaseInconsistency("You should have only one stock "
                                        "item for this branch, got %d"
                                        % qty)
        stock = stock[0]
        return stock.quantity + stock.logic_quantity > 0

    def get_stock_items(self):
        return ProductStockItem.selectBy(storable=self,
                                         connection=self.get_connection())


    def get_stock_item(self, branch):
        return ProductStockItem.selectOneBy(branch=branch,
                                            storable=self,
                                            connection=self.get_connection())

Product.registerFacet(ProductAdaptToStorable, IStorable)

#
# Auxiliary functions
#


def storables_set_branch(conn, branch):
    """A method that must be called always when a new branch company is
    created. It creates a new stock reference for all the products.
    """
    for storable in ProductAdaptToStorable.select(connection=conn):
        storable._add_stock_item(branch)
