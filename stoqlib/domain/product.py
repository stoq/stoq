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
from zope.interface import implements

from stoqlib.database.orm import PriceCol, DecimalCol
from stoqlib.database.orm import (UnicodeCol, ForeignKey, MultipleJoin, DateTimeCol,
                                  BoolCol, BLOBCol, IntCol)
from stoqlib.database.orm import const
from stoqlib.domain.base import Domain, ModelAdapter
from stoqlib.domain.person import Person
from stoqlib.domain.interfaces import (IStorable, IContainer,
                                       IBranch)
from stoqlib.exceptions import StockError, DatabaseInconsistency
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
    """Supplier information for a Product

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
        - I{lead_time}: the number of days needed to deliver the product to
                        purchaser.
        - I{minimum_purchase}: the minimum amount that we can buy from this
                               supplier.
    """

    base_cost = PriceCol(default=0)
    notes = UnicodeCol(default='')
    is_main_supplier = BoolCol(default=False)
    lead_time = IntCol(default=1)
    minimum_purchase = DecimalCol(default=Decimal(1))
    # This is Brazil-specific information
    icms = DecimalCol(default=0)
    supplier =  ForeignKey('PersonAdaptToSupplier', notNone=True)
    product =  ForeignKey('Product')

    #
    # Classmethods
    #

    @classmethod
    def get_info_by_supplier(cls, conn, supplier):
        """Retuns all the products information provided by the given supplier.
        """
        return cls.selectBy(supplier=supplier, connection=conn)

    #
    # Auxiliary methods
    #

    def get_name(self):
        if self.supplier:
            return self.supplier.get_description()

    def get_lead_time_str(self):
        if self.lead_time > 1:
            day_str = _(u"Days")
            lead_time = self.lead_time
        else:
            day_str = _(u"Day")
            lead_time = self.lead_time or 0

        return "%d %s" % (lead_time, day_str)


class ProductRetentionHistory(Domain):
    """Class responsible to store information about product's retention."""

    quantity = DecimalCol(default=0)
    reason = UnicodeCol(default='')
    product = ForeignKey('Product')
    retention_date = DateTimeCol(default=None)
    cfop = ForeignKey('CfopData', default=None)

    def cancel_retention(self, branch):
        """Remove the ProductRetentionHistory entry and return the
        product quantity retained to stock again.

        @param branch: the branch containing the stock
        """
        storable = IStorable(self.product)
        storable.increase_stock(self.quantity, branch)
        ProductRetentionHistory.delete(
            self.id, connection=self.get_connection())


class Product(Domain):
    """Class responsible to store basic products informations."""

    suppliers = MultipleJoin('ProductSupplierInfo')
    image = BLOBCol(default='')
    location = UnicodeCol(default='')
    manufacturer = UnicodeCol(default='')
    part_number = UnicodeCol(default='')
    sellable = ForeignKey('Sellable')

    #
    # Facet hooks
    #

    def facet_IStorable_add(self, **kwargs):
        return ProductAdaptToStorable(self, **kwargs)

    #
    # General Methods
    #

    def retain(self, quantity, branch, reason, product, cfop=None):
        storable = IStorable(self)
        storable.decrease_stock(quantity, branch)
        today = datetime.date.today()
        conn = self.get_connection()
        retained_item = ProductRetentionHistory(quantity=quantity,
                                                retention_date=today,
                                                product=product,
                                                reason=reason,
                                                cfop=cfop,
                                                connection=conn)
        ProductHistory.add_retained_item(conn, branch, retained_item)
        return retained_item

    #
    # Acessors
    #

    def get_main_supplier_name(self):
        supplier_info = self.get_main_supplier_info()
        return supplier_info.get_name()

    def get_main_supplier_info(self):
        """Gets a list of main suppliers for a Product, the main supplier
        is the most recently selected supplier.

        @returns: main supplier info
        @rtype: ProductSupplierInfo or None if a product lacks
           a main suppliers
        """
        return ProductSupplierInfo.selectOneBy(
            product=self,
            is_main_supplier=True,
            connection=self.get_connection())

    def get_suppliers_info(self):
        """Returns a list of suppliers for this product

        @returns: a list of suppliers
        @rtype: list of ProductSupplierInfo
        """
        return ProductSupplierInfo.selectBy(
            product=self, connection=self.get_connection())

    def get_components(self):
        """Returns the products which are our components.

        @returns: a sequence of Product instances
        """
        for component in ProductComponent.selectBy(
            product=self, connection=self.get_connection()):
            yield component

    def get_production_cost(self):
        """ Return the production cost of a Product. The production cost
        is defined as the sum of the product cost plus the costs of its
        components.

        @returns: the production cost
        """
        value = self.sellable.cost
        for component in self.get_components():
            value += (component.component.get_production_cost() *
                      component.quantity)
        return value

    def is_supplied_by(self, supplier):
        """If this product is supplied by the given supplier, returns the
        object with the supplier information. Returns None otherwise
        """
        return ProductSupplierInfo.selectOneBy(
                        product=self, supplier=supplier,
                        connection=self.get_connection()) is not None

    def is_composed_by(self, product):
        """Returns if we are composed by a given product or not.

        @param product: a possible component of this product
        @returns: True if the given product is one of our component or a
        component of our components, otherwise False.
        """
        for component in self.get_components():
            if product is component.component:
                return True
            if component.component.is_composed_by(product):
                return True
        return False


class ProductHistory(Domain):
    """Stores product history, such as sold, received, transfered and
    retained quantities.
    """
    # We keep a reference to Sellable instead of Product because we want to
    # display the sellable id in the interface instead of the product id for
    # consistency with interfaces that display both
    quantity_sold = DecimalCol(default=None)
    quantity_received = DecimalCol(default=None)
    quantity_transfered = DecimalCol(default=None)
    quantity_retained = DecimalCol(default=None)
    sold_date = DateTimeCol(default=None)
    received_date = DateTimeCol(default=None)
    branch = ForeignKey("PersonAdaptToBranch")
    sellable = ForeignKey("Sellable")

    @classmethod
    def add_sold_item(cls, conn, branch, product_sellable_item):
        """Adds a sold item, populates the ProductHistory table using a
        product_sellable_item created during a sale.

        @param conn: a database connection
        @param branch: the branch
        @param product_sellable_item: the sellable item for the sold
        """
        cls(branch=branch,
            sellable=product_sellable_item.sellable,
            quantity_sold=product_sellable_item.quantity,
            sold_date=const.NOW(),
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


    @classmethod
    def add_transfered_item(cls, conn, branch, transfer_order_item):
        """
        Adds a transfered_item, populates the ProductHistory table using a
        transfered_order_item created during a transfer order

        @param conn: a database connection
        @param branch: the source branch
        @param transfer_order_item: the item transfered from source branch
        """
        cls(branch=branch, sellable=transfer_order_item.sellable,
            quantity_transfered=transfer_order_item.quantity,
            received_date=transfer_order_item.transfer_order.receival_date,
            connection=conn)

    @classmethod
    def add_retained_item(cls, conn, branch, retained_item):
        """
        Adds a retained_item, populates the ProductHistory table using a
        product_retention_history created during a product retention

        @param conn: a database connection
        @param branch: the source branch
        @param retained_item: a ProductRetentionHistory instance
        """
        cls(branch=branch, sellable=retained_item.product.sellable,
            quantity_retained=retained_item.quantity,
            received_date=datetime.date.today(),
            connection=conn)


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


class ProductAdaptToStorable(ModelAdapter):
    """A product implementation as a storable facet."""

    minimum_quantity = DecimalCol(default=0)
    maximum_quantity = DecimalCol(default=0)

    implements(IStorable, IContainer)

    retention = MultipleJoin('ProductRetentionHistory')

    #
    # Private
    #

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
        if stock_item is None:
            # If the stock_item is missing create a new one
            stock_item = ProductStockItem(
                storable=self,
                branch=branch,
                connection=self.get_connection())

        # If previously lacked quantity change the status of the sellable
        if not stock_item.quantity:
            sellable = self.product.sellable
            if sellable:
                # Rename see bug 2669
                sellable.can_sell()
        stock_item.quantity += quantity

    def decrease_stock(self, quantity, branch):
        # The function get_full_balance returns the current amount of items
        # in the stock. If get_full_balance == 0 we have no more stock for
        # this product and we need to set it as sold.

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
        if stock_item.quantity < 0:
            raise ValueError("Quantity cannot be negative")

        # We emptied the entire stock, we need to change the status of the
        # sellable, but only if there is no stock in any other branch.
        has_stock = any([s.quantity > 0 for s in self.get_stock_items()])
        if not has_stock:
            sellable = self.product.sellable
            if sellable:
                # FIXME: rename sell() to something more useful which is not
                #        confusing a sale and a sellable, Bug 2669
                sellable.sell()

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
        value = Decimal(0)
        if not stocks:
            return value
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
        if not qty:
            return False
        elif qty > 1:
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


class ProductComponent(Domain):
    """A product and it's related component eg other product
    """
    quantity = DecimalCol(default=Decimal(1))
    product = ForeignKey('Product')
    component = ForeignKey('Product')
