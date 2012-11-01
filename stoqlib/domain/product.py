# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2012 Async Open Source <http://www.async.com.br>
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
## Author(s): Stoq Team <stoq-devel@async.com.br>

""" Base classes to manage product's informations """

import datetime
from decimal import Decimal

from zope.interface import implements

from stoqlib.database.orm import PriceCol, DecimalCol, QuantityCol
from stoqlib.database.orm import (UnicodeCol, ForeignKey, MultipleJoin, DateTimeCol,
                                  BoolCol, IntCol, PercentCol)
from stoqlib.database.orm import const, AND, LeftJoin
from stoqlib.domain.base import Domain
from stoqlib.domain.events import (ProductCreateEvent, ProductEditEvent,
                                   ProductRemoveEvent, ProductStockUpdateEvent)
from stoqlib.domain.interfaces import IDescribable
from stoqlib.domain.person import Person
from stoqlib.exceptions import StockError
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

#
# pyflakes
#
Person


class ProductSupplierInfo(Domain):
    """Supplier information for a |product|.

    Each product can has more than one |supplier|.

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/product_supplier_info.html>`__
    """

    #: the cost which helps the purchaser to define the main cost of a
    #: certain product. Each product can have multiple |suppliers| and for
    #: each |supplier| a base_cost is available. The purchaser in this case
    #: must decide how to define the main cost based in the base cost avarage
    #: of all suppliers.
    base_cost = PriceCol(default=0)

    notes = UnicodeCol(default='')

    #: if this object stores information for the main |supplier|.
    is_main_supplier = BoolCol(default=False)

    #: the number of days needed to deliver the product to purchaser.
    lead_time = IntCol(default=1)

    #: the minimum amount that we can buy from this supplier.
    minimum_purchase = QuantityCol(default=Decimal(1))

    #: a Brazil-specific attribute that means 'Imposto sobre circulacao
    #: de mercadorias e prestacao de servicos'
    icms = PercentCol(default=0)

    #: the |supplier|
    supplier = ForeignKey('Supplier')

    #: the |product|
    product = ForeignKey('Product')

    #
    # Classmethods
    #

    @classmethod
    def get_info_by_supplier(cls, conn, supplier, consigned=False):
        """Retuns all the products information provided by the given
        |supplier|.

        :param conn: a database connection
        :param supplier: the |supplier|
        :param consigned: the consigned |product|
        """
        if consigned:
            join = LeftJoin(Product,
                        ProductSupplierInfo.q.product_id == Product.q.id)
            query = AND(ProductSupplierInfo.q.supplier_id == supplier.id,
                        Product.q.consignment == consigned)
        else:
            join = None
            query = AND(ProductSupplierInfo.q.supplier_id == supplier.id)
        return cls.select(clause=query, join=join, connection=conn)

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


class Product(Domain):
    """A Product is a thing that can be:

      * ordered (via |purchase|)
      * stored (via |storable|)
      * sold (via |sellable|)
      * manufactured (via |production|)

    A manufactured product can have several |components|, which are parts
    that when combined create the product.

    A consigned product is borrowed from a |supplier|. You can also loan out
    your own products via |loan|.

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/product.html>`__
    """

    #: |sellable| for this product
    sellable = ForeignKey('Sellable')

    #: if this product is loaned from the |supplier|
    consignment = BoolCol(default=False)

    #: ``True`` if this product has |components|.
    #: This is stored on Product to avoid a join to find out if there is any
    #: components or not.
    is_composed = BoolCol(default=False)

    #: physical location of this product, like a drawer or shelf number
    location = UnicodeCol(default='')

    model = UnicodeCol(default='')

    #: a number representing this part
    part_number = UnicodeCol(default='')

    #: physical width of this product, unit not enforced
    width = DecimalCol(default=0)

    #: physical height of this product, unit not enforced
    height = DecimalCol(default=0)

    #: depth in this product, unit not enforced
    depth = DecimalCol(default=0)

    #: physical weight of this product, unit not enforced
    weight = DecimalCol(default=0)

    #: The time in days it takes to manufacter this product
    production_time = IntCol(default=1)

    #: Brazil specific: NFE: nomenclature comon do mercuosol
    ncm = UnicodeCol(default=None)

    #: NFE: see ncm
    ex_tipi = UnicodeCol(default=None)

    #: NFE: see ncm
    genero = UnicodeCol(default=None)

    #: name of the manufacturer for this product
    manufacturer = ForeignKey('ProductManufacturer', default=None)

    #: ICMS tax template, brazil specific
    icms_template = ForeignKey('ProductIcmsTemplate', default=None)

    #: IPI tax template, brazil specific
    ipi_template = ForeignKey('ProductIpiTemplate', default=None)

    #: Used for composed products only
    quality_tests = MultipleJoin('ProductQualityTest', 'product_id')

    #: list of |suppliers| that sells this product
    suppliers = MultipleJoin('ProductSupplierInfo', 'product_id')

    #
    # General Methods
    #

    def has_quality_tests(self):
        return bool(self.quality_tests)

    @property
    def description(self):
        return self.sellable.description

    @property
    def storable(self):
        return Storable.selectOneBy(product=self,
                                    connection=self.get_connection())

    def remove(self):
        """Deletes this product from the database.
        """
        storable = self.storable
        if storable:
            storable.delete(storable.id, self.get_connection())
        for i in self.get_suppliers_info():
            i.delete(i.id, self.get_connection())
        for i in self.get_components():
            i.delete(i.id, self.get_connection())

        self.delete(self.id, self.get_connection())

    def can_remove(self):
        """Whether we can delete this product and it's |sellable| from the
        database.

        ``False`` if the product was sold, received or used in a
        production. ``True`` otherwise.
        """
        from stoqlib.domain.production import ProductionItem
        if self.get_history().count():
            return False
        storable = self.storable
        if storable and storable.get_stock_items().count():
            return False
        # Return False if the product is component of other.
        elif ProductComponent.selectBy(connection=self.get_connection(),
                                       component=self).count():
            return False
        # Return False if the component(product) is used in a production.
        elif ProductionItem.selectBy(connection=self.get_connection(),
                                     product=self).count():
            return False
        return True

    #
    # Acessors
    #

    def get_manufacture_time(self, quantity, branch):
        """Returns the estimated time in days to manufacture a product

        If the |components| don't have enough stock, the estimated time to
        obtain missing |components| will also be considered (using the max
        lead time from the |suppliers|)

        :param quantity:
        :param branch: the |branch|
        """
        assert self.is_composed

        # Components maximum lead time
        comp_max_time = 0
        for i in self.get_components():
            storable = i.component.storable
            needed = quantity * i.quantity
            stock = storable.get_balance_for_branch(branch)
            # We have enought of this component items to produce.
            if  stock >= needed:
                continue
            comp_max_time = max(comp_max_time,
                                i.component.get_max_lead_time(needed, branch))
        return self.production_time + comp_max_time

    def get_max_lead_time(self, quantity, branch):
        """Returns the longest lead time for this product.

        If this is a composed product, the lead time will be the time to
        manufacture the product plus the time to obtain all the missing
        components

        If its a regular product this will be the longest lead time for a
        supplier to deliver the product (considering the worst case).

        quantity and |branch| are used only when the product is composed
        """
        if self.is_composed:
            return self.get_manufacture_time(quantity, branch)
        else:
            return self.suppliers.max('lead_time') or 0

    def get_history(self):
        """Returns the list of :class:`ProductHistory` for this product.
        """
        return ProductHistory.selectBy(sellable=self.sellable,
                                       connection=self.get_connection())

    def get_main_supplier_name(self):
        supplier_info = self.get_main_supplier_info()
        return supplier_info.get_name()

    def get_main_supplier_info(self):
        """Gets a list of main suppliers for a Product, the main supplier
        is the most recently selected supplier.

        :returns: main supplier info
        :rtype: ProductSupplierInfo or None if a product lacks
           a main suppliers
        """
        return ProductSupplierInfo.selectOneBy(
            product=self,
            is_main_supplier=True,
            connection=self.get_connection())

    def get_suppliers_info(self):
        """Returns a list of suppliers for this product

        :returns: a list of suppliers
        :rtype: list of ProductSupplierInfo
        """
        return ProductSupplierInfo.selectBy(
            product=self, connection=self.get_connection())

    def get_components(self):
        """Returns the products which are our |components|.

        :returns: a sequence of |components|
        """
        return ProductComponent.selectBy(product=self,
                                         connection=self.get_connection())

    def has_components(self):
        """Returns if this product has a |component| or not.

        :returns: ``True`` if this product has |components|, ``False`` otherwise.
        """
        return self.get_components().count() > 0

    def get_production_cost(self):
        """ Return the production cost of one unit of the product.

        :returns: the production cost
        """
        return self.sellable.cost

    def is_supplied_by(self, supplier):
        """If this product is supplied by the given |supplier|, returns the
        object with the supplier information. Returns ``None`` otherwise
        """
        return ProductSupplierInfo.selectOneBy(
                        product=self, supplier=supplier,
                        connection=self.get_connection()) is not None

    def is_composed_by(self, product):
        """Returns if we are composed by a given product or not.

        :param product: a possible component of this product
        :returns: ``True`` if the given product is one of our component or a
          component of our components, otherwise ``False``.
        """
        for component in self.get_components():
            if product is component.component:
                return True
            if component.component.is_composed_by(product):
                return True
        return False

    def is_being_produced(self):
        from stoqlib.domain.production import ProductionOrderProducingView
        return ProductionOrderProducingView.is_product_being_produced(self)

    #
    # Domain
    #

    def on_create(self):
        ProductCreateEvent.emit(self)

    def on_delete(self):
        ProductRemoveEvent.emit(self)

    def on_update(self):
        trans = self.get_connection()
        emitted_trans_list = getattr(self, '_emitted_trans_list', set())

        # Since other classes can propagate this event (like Sellable),
        # emit the event only once for each transaction.
        if not trans in emitted_trans_list:
            ProductEditEvent.emit(self)
            emitted_trans_list.add(trans)

        self._emitted_trans_list = emitted_trans_list


class ProductManufacturer(Domain):
    """Product manufacturer.

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/product_manufacturer.html>`__
    """

    implements(IDescribable)

    #: manufacturer's name
    name = UnicodeCol()

    #
    # IDescribable
    #

    def get_description(self):
        return self.name

    def can_remove(self):
        """ Check if the manufacturer is used in some product."""
        return not Product.selectBy(manufacturer=self,
                                    connection=self.get_connection()).count()

    def remove(self):
        """Remove this registry from the database."""
        self.delete(self.id, self.get_connection())


class ProductHistory(Domain):
    """Stores |product| history, such as sold (via |sale|),
    received (via |receive|), transfered (via |transfer|) and
    decreased quantities.

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/product_history.html>`__

    .. note:: We keep a reference to |sellable| instead of |product| because
              we want to display the sellable id in the interface instead
              of the product id for consistency with interfaces that display
              both.
    """
    quantity_sold = QuantityCol(default=None)
    quantity_received = QuantityCol(default=None)
    quantity_transfered = QuantityCol(default=None)
    quantity_produced = QuantityCol(default=None)
    quantity_consumed = QuantityCol(default=None)
    quantity_lost = QuantityCol(default=None)
    quantity_decreased = QuantityCol(default=None)
    production_date = DateTimeCol(default=None)
    sold_date = DateTimeCol(default=None)
    received_date = DateTimeCol(default=None)
    decreased_date = DateTimeCol(default=None)

    #: the |branch|
    branch = ForeignKey("Branch")

    #: the |sellable|
    sellable = ForeignKey("Sellable")

    @classmethod
    def add_sold_item(cls, conn, branch, product_sellable_item):
        """Adds a |saleitem| to the history. *product_sale_item* is an item
        that was created during a |sale|.

        :param conn: a database connection
        :param branch: the |branch|
        :param product_sellable_item: the |saleitem| for the sold |product|
        """
        cls(branch=branch,
            sellable=product_sellable_item.sellable,
            quantity_sold=product_sellable_item.quantity,
            sold_date=const.NOW(),
            connection=conn)

    @classmethod
    def add_received_item(cls, conn, branch, receiving_order_item):
        """
        Adds a received item, populates the ProductHistory table using a
        *receiving_order_item* created during a |purchase|

        :param conn: a database connection
        :param branch: the |branch|
        :param receiving_order_item: the item received for |purchase|
        """
        cls(branch=branch, sellable=receiving_order_item.sellable,
            quantity_received=receiving_order_item.quantity,
            received_date=receiving_order_item.receiving_order.receival_date,
            connection=conn)

    @classmethod
    def add_transfered_item(cls, conn, branch, transfer_order_item):
        """
        Adds a transfered_item, populates the ProductHistory table using a
        *transfered_order_item* created during a |transfer|.

        :param conn: a database connection
        :param branch: the source branch
        :param transfer_order_item: the item transfered from source branch
        """
        cls(branch=branch, sellable=transfer_order_item.sellable,
            quantity_transfered=transfer_order_item.quantity,
            received_date=transfer_order_item.transfer_order.receival_date,
            connection=conn)

    @classmethod
    def add_consumed_item(cls, conn, branch, consumed_item):
        """
        Adds a consumed_item, populates the ProductHistory table using a
        production_material item that was used in a |production|.

        :param conn: a database connection
        :param branch: the source branch
        :param retained_item: a ProductionMaterial instance
        """
        cls(branch=branch, sellable=consumed_item.product.sellable,
            quantity_consumed=consumed_item.consumed,
            production_date=datetime.date.today(),
            connection=conn)

    @classmethod
    def add_produced_item(cls, conn, branch, produced_item):
        """
        Adds a produced_item, populates the ProductHistory table using a
        production_item that was produced in a production order.

        :param conn: a database connection
        :param branch: the source branch
        :param retained_item: a ProductionItem instance
        """
        cls(branch=branch, sellable=produced_item.product.sellable,
            quantity_produced=produced_item.produced,
            production_date=datetime.date.today(), connection=conn)

    @classmethod
    def add_lost_item(cls, conn, branch, lost_item):
        """
        Adds a lost_item, populates the ProductHistory table using a
        production_item/product_material that was lost in a production order.

        :param conn: a database connection
        :param branch: the source branch
        :param lost_item: a ProductionItem or ProductionMaterial instance
        """
        cls(branch=branch, sellable=lost_item.product.sellable,
            quantity_lost=lost_item.lost,
            production_date=datetime.date.today(), connection=conn)

    @classmethod
    def add_decreased_item(cls, conn, branch, item):
        """
        Adds a decreased item, populates the ProductHistory table informing
        how many items wore manually decreased from stock.

        :param conn: a database connection
        :param branch: the source |branch|
        :param item: a StockDecreaseItem instance
        """
        cls(branch=branch, sellable=item.sellable,
            quantity_decreased=item.quantity,
            decreased_date=datetime.date.today(),
            connection=conn)


class ProductStockItem(Domain):
    """Class that makes a reference to the |product| stock of a
    certain |branch|.

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/product_stock_item.html>`__
    """

    #: the average stock price, will be updated as new stock items are
    #: received.
    stock_cost = PriceCol(default=0)

    #: number of storables in the stock item
    quantity = QuantityCol(default=0)

    #: the |branch| this stock item belongs to
    branch = ForeignKey('Branch')

    #: the |storable| the stock item refers to
    storable = ForeignKey('Storable')

    def update_cost(self, new_quantity, new_cost):
        """Update the stock_item according to new quantity and cost.

        :param new_quantity: The new quantity added to stock.
        :param new_cost: The cost of one unit of the added stock.
        """
        total_cost = self.quantity * self.stock_cost
        total_cost += new_quantity * new_cost
        total_items = self.quantity + new_quantity
        self.stock_cost = total_cost / total_items


class Storable(Domain):
    '''Storable represents the stock of a |product|.

    The actual stock of an item is in ProductStockItem.

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/storable.html>`__
    '''

    #: the |product| the stock represents
    product = ForeignKey('Product')

    #: minimum quantity of stock items allowed
    minimum_quantity = QuantityCol(default=0)

    #: maximum quantity of stock items allowed
    maximum_quantity = QuantityCol(default=0)

    #
    # Properties
    #

    def increase_stock(self, quantity, branch, unit_cost=None):
        """When receiving a product, update the stock reference for this new
        item on a specific |branch|.

        :param quantity: amount to increase
        :param branch: |branch| that stores the stock
        :param cost: unit cost of the new stock or `None`
        """
        if quantity <= 0:
            raise ValueError(_("quantity must be a positive number"))
        if branch is None:
            raise ValueError("branch cannot be None")
        stock_item = self.get_stock_item(branch)
        # If the stock_item is missing create a new one
        if stock_item is None:
            conn = self.get_connection()
            stock_item = ProductStockItem(
                storable=self,
                branch=conn.get(branch),
                connection=conn)

        # Unit cost must be updated here as
        # 1) we need the stock item which might not exist
        # 2) it needs to be updated before we change the quantity of the
        #    stock item
        if unit_cost is not None:
            stock_item.update_cost(quantity, unit_cost)

        old_quantity = stock_item.quantity
        stock_item.quantity += quantity

        # If previously lacked quantity change the status of the sellable
        if not old_quantity:
            sellable = self.product.sellable
            if sellable:
                sellable.can_sell()

        ProductStockUpdateEvent.emit(self.product, branch, old_quantity,
                                     stock_item.quantity)

    def decrease_stock(self, quantity, branch):
        """When receiving a product, update the stock reference for the sold item
        this on a specific |branch|. Returns the stock item that was
        decreased.

        :param quantity: amount to decrease
        :param branch: a |branch|
        """
        if quantity <= 0:
            raise ValueError(_("quantity must be a positive number"))
        if branch is None:
            raise ValueError("branch cannot be None")

        stock_item = self.get_stock_item(branch)
        if stock_item is None or quantity > stock_item.quantity:
            raise StockError(
                _('Quantity to sell is greater than the available stock.'))

        old_quantity = stock_item.quantity
        stock_item.quantity -= quantity

        # We emptied the entire stock in all branches, we need to change
        # the status of the sellable to unavailable as we cannot sell
        # it anymore
        if not ProductStockItem.selectBy(
            storable=self,
            connection=self.get_connection()).sum(ProductStockItem.q.quantity):
            sellable = self.product.sellable
            if sellable:
                sellable.set_unavailable()

        ProductStockUpdateEvent.emit(self.product, branch, old_quantity,
                                     stock_item.quantity)
        return stock_item

    def get_balance_for_branch(self, branch):
        """Return the stock balance for the |product| in a |branch|.

        :param branch: the |branch| to get the stock balance for
        :returns: the amount of stock available in the |branch|
        """
        conn = self.get_connection()
        stock_items = ProductStockItem.selectBy(storable=self,
                                                connection=conn,
                                                branch=branch)
        return stock_items.sum(ProductStockItem.q.quantity) or Decimal(0)

    def get_stock_items(self):
        """Fetches the stock items available for all |branches|.

        :returns: a sequence of stock items
        """
        return ProductStockItem.selectBy(storable=self,
                                         connection=self.get_connection())

    def get_stock_item(self, branch):
        """Fetch a stock item for a specific |branch|

        :returns: a stock item
        """
        return ProductStockItem.selectOneBy(branch=branch,
                                            storable=self,
                                            connection=self.get_connection())


class ProductComponent(Domain):
    """A |product| and it's related |component| eg other product

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/product_component.html>`__
    """
    quantity = QuantityCol(default=Decimal(1))
    product = ForeignKey('Product')
    component = ForeignKey('Product')
    design_reference = UnicodeCol(default=u'')


class ProductQualityTest(Domain):
    """A quality test that a manufactured product will be submitted to.

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/product_quality_test.html>`__
    """

    implements(IDescribable)

    (TYPE_BOOLEAN,
     TYPE_DECIMAL) = range(2)

    types = {
        TYPE_BOOLEAN: _('Boolean'),
        TYPE_DECIMAL: _('Decimal'),
    }

    product = ForeignKey('Product')
    test_type = IntCol(default=TYPE_BOOLEAN)
    description = UnicodeCol(default='')
    notes = UnicodeCol(default='')
    success_value = UnicodeCol(default='True')

    def get_description(self):
        return self.description

    @property
    def type_str(self):
        return self.types[self.test_type]

    @property
    def success_value_str(self):
        return _(self.success_value)

    def get_boolean_value(self):
        assert self.test_type == self.TYPE_BOOLEAN
        if self.success_value == 'True':
            return True
        elif self.success_value == 'False':
            return False
        else:
            raise ValueError(self.success_value)

    def get_range_value(self):
        assert self.test_type == self.TYPE_DECIMAL
        a, b = self.success_value.split(' - ')
        return Decimal(a), Decimal(b)

    def set_boolean_value(self, value):
        self.success_value = str(value)

    def set_range_value(self, min_value, max_value):
        self.success_value = '%s - %s' % (min_value, max_value)

    def result_value_passes(self, value):
        if self.test_type == self.TYPE_BOOLEAN:
            return self.get_boolean_value() == value
        else:
            a, b = self.get_range_value()
            return a <= value <= b

    def can_remove(self):
        from stoqlib.domain.production import ProductionItemQualityResult
        if ProductionItemQualityResult.selectBy(quality_test=self,
                    connection=self.get_connection()).count():
            return False
        return True
