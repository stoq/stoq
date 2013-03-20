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

from kiwi.currency import currency
from storm.references import Reference, ReferenceSet
from zope.interface import implements

from stoqlib.database.properties import PriceCol, DecimalCol, QuantityCol
from stoqlib.database.properties import (UnicodeCol, DateTimeCol,
                                         BoolCol, IntCol, PercentCol)
from stoqlib.database.expr import TransactionTimestamp
from stoqlib.database.runtime import get_current_user
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

    __storm_table__ = 'product_supplier_info'

    #: the cost which helps the purchaser to define the main cost of a
    #: certain product. Each product can have multiple |suppliers| and for
    #: each |supplier| a base_cost is available. The purchaser in this case
    #: must decide how to define the main cost based in the base cost avarage
    #: of all suppliers.
    base_cost = PriceCol(default=0)

    notes = UnicodeCol(default=u'')

    #: if this object stores information for the main |supplier|.
    is_main_supplier = BoolCol(default=False)

    #: the number of days needed to deliver the product to purchaser.
    lead_time = IntCol(default=1)

    #: the minimum amount that we can buy from this supplier.
    minimum_purchase = QuantityCol(default=Decimal(1))

    #: a Brazil-specific attribute that means 'Imposto sobre circulacao
    #: de mercadorias e prestacao de servicos'
    icms = PercentCol(default=0)

    supplier_id = IntCol()

    #: the |supplier|
    supplier = Reference(supplier_id, 'Supplier.id')

    product_id = IntCol()

    #: the |product|
    product = Reference(product_id, 'Product.id')

    #: the product code in the supplier
    supplier_code = UnicodeCol(default=u'')

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

        return u"%d %s" % (lead_time, day_str)


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

    __storm_table__ = 'product'

    sellable_id = IntCol()

    #: |sellable| for this product
    sellable = Reference(sellable_id, 'Sellable.id')

    suppliers = ReferenceSet('id', 'ProductSupplierInfo.product_id')

    #: if this product is loaned from the |supplier|
    consignment = BoolCol(default=False)

    #: ``True`` if this product has |components|.
    #: This is stored on Product to avoid a join to find out if there is any
    #: components or not.
    is_composed = BoolCol(default=False)

    #: physical location of this product, like a drawer or shelf number
    location = UnicodeCol(default=u'')

    model = UnicodeCol(default=u'')

    #: a number representing this part
    part_number = UnicodeCol(default=u'')

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

    manufacturer_id = IntCol(default=None)

    #: name of the manufacturer for this product
    manufacturer = Reference(manufacturer_id, 'ProductManufacturer.id')

    icms_template_id = IntCol(default=None)

    icms_template = Reference(icms_template_id, 'ProductIcmsTemplate.id')

    ipi_template_id = IntCol(default=None)

    ipi_template = Reference(ipi_template_id, 'ProductIpiTemplate.id')

    #: Used for composed products only
    quality_tests = ReferenceSet('id', 'ProductQualityTest.product_id')

    #: list of |suppliers| that sells this product
    suppliers = ReferenceSet('id', 'ProductSupplierInfo.product_id')

    #
    # General Methods
    #

    def has_quality_tests(self):
        return not self.quality_tests.find().is_empty()

    @property
    def description(self):
        return self.sellable.description

    @property
    def storable(self):
        return self.store.find(Storable, product=self).one()

    def remove(self):
        """Deletes this product from the database.
        """
        storable = self.storable
        if storable:
            self.store.remove(storable)
        for i in self.get_suppliers_info():
            self.store.remove(i)
        for i in self.get_components():
            self.store.remove(i)

        self.store.remove(self)

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
        elif self.store.find(ProductComponent,
                             component=self).count():
            return False
        # Return False if the component(product) is used in a production.
        elif self.store.find(ProductionItem,
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
            if stock >= needed:
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
            return self.suppliers.find().max(ProductSupplierInfo.lead_time) or 0

    def get_history(self):
        """Returns the list of :class:`ProductHistory` for this product.
        """
        return self.store.find(ProductHistory, sellable=self.sellable)

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
        store = self.store
        return store.find(ProductSupplierInfo,
                          product=self, is_main_supplier=True).one()

    def get_suppliers_info(self):
        """Returns a list of suppliers for this product

        :returns: a list of suppliers
        :rtype: list of ProductSupplierInfo
        """
        return self.store.find(ProductSupplierInfo,
                               product=self)

    def get_components(self):
        """Returns the products which are our |components|.

        :returns: a sequence of |components|
        """
        return self.store.find(ProductComponent, product=self)

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
        store = self.store
        return store.find(ProductSupplierInfo, product=self,
                          supplier=supplier).one() is not None

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
        store = self.store
        emitted_store_list = getattr(self, '_emitted_store_list', set())

        # Since other classes can propagate this event (like Sellable),
        # emit the event only once for each store.
        if not store in emitted_store_list:
            ProductEditEvent.emit(self)
            emitted_store_list.add(store)

        self._emitted_store_list = emitted_store_list


class ProductManufacturer(Domain):
    """Product manufacturer.

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/product_manufacturer.html>`__
    """

    implements(IDescribable)

    __storm_table__ = 'product_manufacturer'

    #: manufacturer's name
    name = UnicodeCol()

    #
    # IDescribable
    #

    def get_description(self):
        return self.name

    def can_remove(self):
        """ Check if the manufacturer is used in some product."""
        return not self.store.find(Product, manufacturer=self).count()

    def remove(self):
        """Remove this registry from the database."""
        self.delete(self.id, self.store)


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
    __storm_table__ = 'product_history'

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

    branch_id = IntCol()

    #: the |branch|
    branch = Reference(branch_id, 'Branch.id')

    sellable_id = IntCol()

    #: the |sellable|
    sellable = Reference(sellable_id, 'Sellable.id')

    @classmethod
    def add_sold_item(cls, store, branch, product_sellable_item):
        """Adds a |saleitem| to the history. *product_sale_item* is an item
        that was created during a |sale|.

        :param store: a store
        :param branch: the |branch|
        :param product_sellable_item: the |saleitem| for the sold |product|
        """
        cls(branch=branch,
            sellable=product_sellable_item.sellable,
            quantity_sold=product_sellable_item.quantity,
            sold_date=TransactionTimestamp(),
            store=store)

    @classmethod
    def add_received_item(cls, store, branch, receiving_order_item):
        """
        Adds a received item, populates the ProductHistory table using a
        *receiving_order_item* created during a |purchase|

        :param store: a store
        :param branch: the |branch|
        :param receiving_order_item: the item received for |purchase|
        """
        cls(branch=branch, sellable=receiving_order_item.sellable,
            quantity_received=receiving_order_item.quantity,
            received_date=receiving_order_item.receiving_order.receival_date,
            store=store)

    @classmethod
    def add_transfered_item(cls, store, branch, transfer_order_item):
        """
        Adds a transfered_item, populates the ProductHistory table using a
        *transfered_order_item* created during a |transfer|.

        :param store: a store
        :param branch: the source branch
        :param transfer_order_item: the item transfered from source branch
        """
        cls(branch=branch, sellable=transfer_order_item.sellable,
            quantity_transfered=transfer_order_item.quantity,
            received_date=transfer_order_item.transfer_order.receival_date,
            store=store)

    @classmethod
    def add_consumed_item(cls, store, branch, consumed_item):
        """
        Adds a consumed_item, populates the ProductHistory table using a
        production_material item that was used in a |production|.

        :param store: a store
        :param branch: the source branch
        :param retained_item: a ProductionMaterial instance
        """
        cls(branch=branch, sellable=consumed_item.product.sellable,
            quantity_consumed=consumed_item.consumed,
            production_date=datetime.date.today(),
            store=store)

    @classmethod
    def add_produced_item(cls, store, branch, produced_item):
        """
        Adds a produced_item, populates the ProductHistory table using a
        production_item that was produced in a production order.

        :param store: a store
        :param branch: the source branch
        :param retained_item: a ProductionItem instance
        """
        cls(branch=branch, sellable=produced_item.product.sellable,
            quantity_produced=produced_item.produced,
            production_date=datetime.date.today(), store=store)

    @classmethod
    def add_lost_item(cls, store, branch, lost_item):
        """
        Adds a lost_item, populates the ProductHistory table using a
        production_item/product_material that was lost in a production order.

        :param store: a store
        :param branch: the source branch
        :param lost_item: a ProductionItem or ProductionMaterial instance
        """
        cls(branch=branch, sellable=lost_item.product.sellable,
            quantity_lost=lost_item.lost,
            production_date=datetime.date.today(), store=store)

    @classmethod
    def add_decreased_item(cls, store, branch, item):
        """
        Adds a decreased item, populates the ProductHistory table informing
        how many items wore manually decreased from stock.

        :param store: a store
        :param branch: the source |branch|
        :param item: a StockDecreaseItem instance
        """
        cls(branch=branch, sellable=item.sellable,
            quantity_decreased=item.quantity,
            decreased_date=datetime.date.today(),
            store=store)


class ProductStockItem(Domain):
    """Class that makes a reference to the |product| stock of a
    certain |branch|.

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/product_stock_item.html>`__
    """

    __storm_table__ = 'product_stock_item'

    #: the average stock price, will be updated as new stock items are
    #: received.
    stock_cost = PriceCol(default=0)

    #: number of storables in the stock item
    quantity = QuantityCol(default=0)

    branch_id = IntCol()

    #: the |branch| this stock item belongs to
    branch = Reference(branch_id, 'Branch.id')

    storable_id = IntCol()

    #: the |storable| the stock item refers to
    storable = Reference(storable_id, 'Storable.id')

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

    __storm_table__ = 'storable'

    product_id = IntCol()

    #: the |product| the stock represents
    product = Reference(product_id, 'Product.id')

    #: minimum quantity of stock items allowed
    minimum_quantity = QuantityCol(default=0)

    #: maximum quantity of stock items allowed
    maximum_quantity = QuantityCol(default=0)

    #
    # Properties
    #

    def increase_stock(self, quantity, branch, type, object_id, unit_cost=None):
        """When receiving a product, update the stock reference for this new
        item on a specific |branch|.

        :param quantity: amount to increase
        :param branch: |branch| that stores the stock
        :param type: the type of the stock increase. One of the
            StockTransactionHistory.types
        :param object_id: the id of the object responsible for the transaction
        :param unit_cost: unit cost of the new stock or `None`
        """
        assert isinstance(type, int)

        if quantity <= 0:
            raise ValueError(_(u"quantity must be a positive number"))
        if branch is None:
            raise ValueError(u"branch cannot be None")
        stock_item = self.get_stock_item(branch)
        # If the stock_item is missing create a new one
        if stock_item is None:
            store = self.store
            stock_item = ProductStockItem(
                storable=self,
                branch=store.fetch(branch),
                store=store)

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

        StockTransactionHistory(product_stock_item=stock_item,
                                quantity=quantity,
                                stock_cost=stock_item.stock_cost,
                                responsible=get_current_user(self.store),
                                type=type,
                                object_id=object_id,
                                store=self.store)

        ProductStockUpdateEvent.emit(self.product, branch, old_quantity,
                                     stock_item.quantity)

    def decrease_stock(self, quantity, branch, type, object_id,
                       cost_center=None):
        """When receiving a product, update the stock reference for the sold item
        this on a specific |branch|. Returns the stock item that was
        decreased.

        :param quantity: amount to decrease
        :param branch: a |branch|
        :param type: the type of the stock increase. One of the
            StockTransactionHistory.types
        :param object_id: the id of the object responsible for the transaction
        :param cost_center: the |costcenter| to which this stock decrease is
            related, if any
        """
        # FIXME: Put this back once 1.6 is released
        # assert isinstance(type, int)

        if quantity <= 0:
            raise ValueError(_(u"quantity must be a positive number"))
        if branch is None:
            raise ValueError(u"branch cannot be None")

        stock_item = self.get_stock_item(branch)
        if stock_item is None or quantity > stock_item.quantity:
            raise StockError(
                _('Quantity to sell is greater than the available stock.'))

        old_quantity = stock_item.quantity
        stock_item.quantity -= quantity

        # We emptied the entire stock in all branches, we need to change
        # the status of the sellable to unavailable as we cannot sell
        # it anymore
        if not self.store.find(ProductStockItem,
                               storable=self).sum(ProductStockItem.quantity):
            sellable = self.product.sellable
            if sellable:
                sellable.set_unavailable()

        stock_transaction = StockTransactionHistory(
            product_stock_item=stock_item,
            quantity=-quantity,
            stock_cost=stock_item.stock_cost,
            responsible=get_current_user(self.store),
            type=type,
            object_id=object_id,
            store=self.store)

        if cost_center is not None:
            cost_center.add_stock_transaction(stock_transaction)

        ProductStockUpdateEvent.emit(self.product, branch, old_quantity,
                                     stock_item.quantity)

        return stock_item

    def register_initial_stock(self, quantity, branch):
        """Register initial stock, by increasing the amount of this storable,
        for the given |quantity| and |branch|

        :param quantity: The inital stock quantity for this storable
        :param branch: The branch where the given quantity is avaiable for this
          storable
        """
        self.increase_stock(quantity, branch,
                            StockTransactionHistory.TYPE_INITIAL,
                            object_id=None)

    def get_balance_for_branch(self, branch):
        """Return the stock balance for the |product| in a |branch|.

        :param branch: the |branch| to get the stock balance for
        :returns: the amount of stock available in the |branch|
        """
        store = self.store
        stock_items = store.find(ProductStockItem, storable=self,
                                 branch=branch)
        return stock_items.sum(ProductStockItem.quantity) or Decimal(0)

    def get_stock_items(self):
        """Fetches the stock items available for all |branches|.

        :returns: a sequence of stock items
        """
        return self.store.find(ProductStockItem, storable=self)

    def get_stock_item(self, branch):
        """Fetch a stock item for a specific |branch|

        :returns: a stock item
        """
        store = self.store
        return store.find(ProductStockItem, branch=branch, storable=self).one()


class StockTransactionHistory(Domain):
    """ This class stores information about all transactions made in the
    stock

    Everytime a |storable| has its stock increased or decreased, an object of
    this class will be created, registering the quantity, cost, responsible and
    reason for the transaction
    """

    __storm_table__ = 'stock_transaction_history'

    #: the transaction is an initial stock adustment. Note that with this
    #: transaction, there is no related object.
    TYPE_INITIAL = 0

    #: the transaction is a sale
    TYPE_SELL = 1

    #: the transaction is a return of a sale
    TYPE_RETURNED_SALE = 2

    #: the transaction is the cancellation of a sale
    TYPE_CANCELED_SALE = 3

    #: the transaction is the receival of a purchase
    TYPE_RECEIVED_PURCHASE = 4

    #: the transaction is the return of a loan
    TYPE_RETURNED_LOAN = 5

    #: the transaction is a loan
    TYPE_LOANED = 6

    #: the transaction is the allocation of a product to a production
    TYPE_PRODUCTION_ALLOCATED = 7

    #: the transaction is the production of a product
    TYPE_PRODUCTION_PRODUCED = 8

    #: the transaction is the return of an item from a production
    TYPE_PRODUCTION_RETURNED = 9

    #: the transaction is a stock decrease
    TYPE_STOCK_DECREASE = 10

    #: the transaction is a transfer from a branch
    TYPE_TRANSFER_FROM = 11

    #: the transaction is a transfer to a branch
    TYPE_TRANSFER_TO = 12

    #: the transaction is the adjustment of an inventory
    TYPE_INVENTORY_ADJUST = 13

    #: the transaction is the production of a product that didn't enter
    #: stock right after its creation
    TYPE_PRODUCTION_SENT = 14

    #: this transaction was created automatically by an upgrade from a previous
    #: version of Stoq, when this history didn't exist.
    TYPE_IMPORTED = 15

    #: the transaction is the return of a product to another company (ie, this
    #: shop is giving the product back to the other company).
    TYPE_CONSIGNMENT_RETURNED = 16

    #: the transaction is the utilization of a
    #: |product|/|service| on a |workorderitem|
    TYPE_WORK_ORDER_USED = 17

    types = {TYPE_INVENTORY_ADJUST: _(u'Adjustment for inventory %s'),
             TYPE_RETURNED_LOAN: _(u'Returned from loan %s'),
             TYPE_LOANED: _(u'Loaned for loan %s'),
             TYPE_PRODUCTION_ALLOCATED: _(u'Allocated for production %s'),
             TYPE_PRODUCTION_PRODUCED: _(u'Produced in production %s'),
             TYPE_PRODUCTION_SENT: _(u'Produced in production %s'),
             TYPE_PRODUCTION_RETURNED: _(u'Returned remaining from '
                                         u'production %s'),
             TYPE_RECEIVED_PURCHASE: _(u'Received for receiving order %s'),
             TYPE_RETURNED_SALE: _(u'Returned sale %s'),
             TYPE_CANCELED_SALE: _(u'Returned from canceled sale %s'),
             TYPE_SELL: _(u'Sold in sale %s'),
             TYPE_STOCK_DECREASE: _(u'Product removal for stock decrease %s'),
             TYPE_TRANSFER_FROM: _(u'Transfered from branch in transfer '
                                   u'order %s'),
             TYPE_TRANSFER_TO: _(u'Transfered to this branch in transfer '
                                 u'order %s'),
             TYPE_INITIAL: _(u'Registred initial stock'),
             TYPE_IMPORTED: _(u'Imported from previous version'),
             TYPE_CONSIGNMENT_RETURNED: _(u'Consigned product returned.'),
             TYPE_WORK_ORDER_USED: _(u'Used on work order %s.'),
             }

    #: the date and time the transaction was made
    date = DateTimeCol(default_factory=datetime.datetime.now)

    product_stock_item_id = IntCol()

    #: the |productstockitem| used in the transaction
    product_stock_item = Reference(product_stock_item_id, 'ProductStockItem.id')

    #: the stock cost of the transaction on the time it was made
    stock_cost = PriceCol()

    #: The quantity that was removed or added to the stock.
    #: Positive value if the value was increased, negative if decreased.
    quantity = QuantityCol()

    responsible_id = IntCol()

    #: the |loginuser| responsible for the transaction
    responsible = Reference(responsible_id, 'LoginUser.id')

    #: the id of the object who altered the stock
    object_id = IntCol()

    #: the type of the transaction
    type = IntCol()

    @property
    def total(self):
        return currency(abs(self.stock_cost * self.quantity))

    def get_object(self):
        if self.type in [self.TYPE_INITIAL, self.TYPE_IMPORTED]:
            return None
        elif self.type in [self.TYPE_SELL, self.TYPE_CANCELED_SALE]:
            from stoqlib.domain.sale import SaleItem
            return self.store.get(SaleItem, self.object_id)
        elif self.type == self.TYPE_RETURNED_SALE:
            from stoqlib.domain.returnedsale import ReturnedSaleItem
            return self.store.get(ReturnedSaleItem, self.object_id)
        elif self.type == self.TYPE_PRODUCTION_PRODUCED:
            from stoqlib.domain.production import ProductionItem
            return self.store.get(ProductionItem, self.object_id)
        elif self.type in [self.TYPE_PRODUCTION_ALLOCATED,
                           self.TYPE_PRODUCTION_RETURNED]:
            from stoqlib.domain.production import ProductionMaterial
            return self.store.get(ProductionMaterial, self.object_id)
        elif self.type == self.TYPE_RECEIVED_PURCHASE:
            from stoqlib.domain.receiving import ReceivingOrderItem
            return self.store.get(ReceivingOrderItem, self.object_id)
        elif self.type in [self.TYPE_RETURNED_LOAN, self.TYPE_LOANED]:
            from stoqlib.domain.loan import LoanItem
            return self.store.get(LoanItem, self.object_id)
        elif self.type == self.TYPE_STOCK_DECREASE:
            from stoqlib.domain.stockdecrease import StockDecreaseItem
            return self.store.get(StockDecreaseItem, self.object_id)
        elif self.type in [self.TYPE_TRANSFER_FROM, self.TYPE_TRANSFER_TO]:
            from stoqlib.domain.transfer import TransferOrderItem
            return self.store.get(TransferOrderItem, self.object_id)
        elif self.type == self.TYPE_INVENTORY_ADJUST:
            from stoqlib.domain.inventory import InventoryItem
            return self.store.get(InventoryItem, self.object_id)
        elif self.type == self.TYPE_PRODUCTION_SENT:
            from stoqlib.domain.production import ProductionProducedItem
            return self.store.get(ProductionProducedItem, self.object_id)
        elif self.type == self.TYPE_CONSIGNMENT_RETURNED:
            from stoqlib.domain.purchase import PurchaseItem
            return self.store.get(PurchaseItem, self.object_id)
        elif self.type == self.TYPE_CONSIGNMENT_RETURNED:
            from stoqlib.domain.purchase import PurchaseItem
            return self.store.get(PurchaseItem, self.object_id)
        elif self.type == self.TYPE_WORK_ORDER_USED:
            from stoqlib.domain.workorder import WorkOrderItem
            return self.store.get(WorkOrderItem, self.object_id)
        else:
            raise ValueError(_('%s has invalid type: %s.') % (self, self.type))

    def get_object_parent(self):
        obj = self.get_object()
        if not obj:
            return None

        from stoqlib.domain.inventory import InventoryItem
        from stoqlib.domain.loan import LoanItem
        from stoqlib.domain.production import ProductionItem
        from stoqlib.domain.production import ProductionMaterial
        from stoqlib.domain.purchase import PurchaseItem
        from stoqlib.domain.receiving import ReceivingOrderItem
        from stoqlib.domain.returnedsale import ReturnedSaleItem
        from stoqlib.domain.sale import SaleItem
        from stoqlib.domain.stockdecrease import StockDecreaseItem
        from stoqlib.domain.workorder import WorkOrderItem
        from stoqlib.domain.transfer import TransferOrderItem

        if isinstance(obj, SaleItem):
            return obj.sale
        elif isinstance(obj, ReturnedSaleItem):
            return obj.returned_sale
        elif isinstance(obj, ProductionItem):
            return obj.order
        elif isinstance(obj, ProductionMaterial):
            return obj.order
        elif isinstance(obj, ReceivingOrderItem):
            return obj.receiving_order
        elif isinstance(obj, LoanItem):
            return obj.loan
        elif isinstance(obj, StockDecreaseItem):
            return obj.stock_decrease
        elif isinstance(obj, TransferOrderItem):
            return obj.transfer_order
        elif isinstance(obj, InventoryItem):
            return obj.inventory
        elif isinstance(obj, PurchaseItem):
            return obj.inventory
        elif isinstance(obj, WorkOrderItem):
            return obj.order
        else:
            raise TypeError(_('Object %s has invalid type (%s)') %
                            (obj, type(obj)))

    def get_description(self):
        """ Based on the type of the transaction, returns the string
        description
        """
        if self.type in [self.TYPE_INITIAL, self.TYPE_IMPORTED]:
            return self.types[self.type]
        return self.types[self.type] % self.get_object_parent().identifier


class ProductComponent(Domain):
    """A |product| and it's related |component| eg other product

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/product_component.html>`__
    """

    __storm_table__ = 'product_component'

    quantity = QuantityCol(default=Decimal(1))
    product_id = IntCol()
    product = Reference(product_id, 'Product.id')
    component_id = IntCol()
    component = Reference(component_id, 'Product.id')
    design_reference = UnicodeCol(default=u'')


class ProductQualityTest(Domain):
    """A quality test that a manufactured product will be submitted to.

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/product_quality_test.html>`__
    """

    implements(IDescribable)

    __storm_table__ = 'product_quality_test'

    (TYPE_BOOLEAN,
     TYPE_DECIMAL) = range(2)

    types = {
        TYPE_BOOLEAN: _(u'Boolean'),
        TYPE_DECIMAL: _(u'Decimal'),
    }

    product_id = IntCol()
    product = Reference(product_id, 'Product.id')
    test_type = IntCol(default=TYPE_BOOLEAN)
    description = UnicodeCol(default=u'')
    notes = UnicodeCol(default=u'')
    success_value = UnicodeCol(default=u'True')

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
        if self.success_value == u'True':
            return True
        elif self.success_value == u'False':
            return False
        else:
            raise ValueError(self.success_value)

    def get_range_value(self):
        assert self.test_type == self.TYPE_DECIMAL
        a, b = self.success_value.split(u' - ')
        return Decimal(a), Decimal(b)

    def set_boolean_value(self, value):
        self.success_value = unicode(value)

    def set_range_value(self, min_value, max_value):
        self.success_value = u'%s - %s' % (min_value, max_value)

    def result_value_passes(self, value):
        if self.test_type == self.TYPE_BOOLEAN:
            return self.get_boolean_value() == value
        else:
            a, b = self.get_range_value()
            return a <= value <= b

    def can_remove(self):
        from stoqlib.domain.production import ProductionItemQualityResult
        if self.store.find(ProductionItemQualityResult, quality_test=self).count():
            return False
        return True
