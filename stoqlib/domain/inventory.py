# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008-2014 Async Open Source <http://www.async.com.br>
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
##
""" Inventory object and related objects implementation """

# pylint: enable=E1101

from decimal import Decimal

from storm.expr import And, Eq, Cast, Join, LeftJoin, Or, Coalesce
from storm.references import Reference, ReferenceSet

from stoqlib.database.properties import (QuantityCol, PriceCol, DateTimeCol,
                                         IntCol, UnicodeCol, IdentifierCol,
                                         IdCol, BoolCol, EnumCol)
from stoqlib.database.expr import StatementTimestamp
from stoqlib.database.viewable import Viewable
from stoqlib.domain.base import Domain
from stoqlib.domain.fiscal import FiscalBookEntry
from stoqlib.domain.person import LoginUser, Person, Branch
from stoqlib.domain.product import (StockTransactionHistory, StorableBatch, Product,
                                    Storable, ProductStockItem)
from stoqlib.domain.sellable import Sellable
from stoqlib.lib.dateutils import localnow
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class InventoryItem(Domain):
    """An |inventory| item

    It contains the recorded quantity and the actual quantity related
    to a specific product.

    If those quantities are not identitical, it will also contain a reason
    and a cfop describing that.

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/inventory_item.html>`__
    """

    __storm_table__ = 'inventory_item'

    product_id = IdCol()

    #: the item
    product = Reference(product_id, 'Product.id')

    batch_id = IdCol()

    #: If the product is a storable, the |batch| of the product that is being
    #: inventored
    batch = Reference(batch_id, 'StorableBatch.id')

    #: the recorded quantity of the |product|, that is, the product's quantity
    #: in stock at the time the inventory process started.
    recorded_quantity = QuantityCol()

    #: the counted quantity of the |product|, that is, a quantity counted by
    #: someone looking at the real physical stock
    counted_quantity = QuantityCol(default=None)

    #: the actual quantity of the |product|, that will be used to
    #: increase/decrease stock using :meth:`.adjust`. Normally this will be
    #: the same as :obj:`counted_quantity`, but it can be different if, for
    #: instance, the count was done wrong. In cases like that, be sure to
    #: mention the reason for the difference on :obj:`.reason`
    actual_quantity = QuantityCol(default=None)

    #: the product's cost when the product was adjusted.
    product_cost = PriceCol()

    #: the reason of why this item has been adjusted
    reason = UnicodeCol(default=u"")

    #: if this inventory's stock difference was adjusted
    is_adjusted = BoolCol(allow_none=False, default=False)

    cfop_data_id = IdCol(default=None)

    #: the cfop used to adjust this item, this is only set when
    #: an adjustment is done
    cfop_data = Reference(cfop_data_id, 'CfopData.id')

    inventory_id = IdCol()

    #: the inventory process that contains this item
    inventory = Reference(inventory_id, 'Inventory.id')

    @property
    def difference(self):
        """The difference between the recorded and the counted quantities

        This is the same as::

            :obj:`.counted_quantity` - :obj:`.recorded_quantity`

        Note that, if :obj:`.counted_quantity` is ``None``, this
        will also be ``None``.
        """
        if self.counted_quantity is None:
            return None

        return self.counted_quantity - self.recorded_quantity

    @property
    def unit_description(self):
        """Returns the product unit description or None if it's not set
        """
        sellable = self.product.sellable
        if sellable.unit:
            return sellable.unit.description

    #
    #  Private
    #

    def _add_inventory_fiscal_entry(self, invoice_number):
        inventory = self.inventory
        return FiscalBookEntry(
            entry_type=FiscalBookEntry.TYPE_INVENTORY,
            invoice_number=inventory.invoice_number,
            branch=inventory.branch,
            cfop=self.cfop_data,
            store=self.store)

    #
    #  Public API
    #

    def adjust(self, invoice_number):
        """Create an entry in fiscal book registering the adjustment
        with the related cfop data and change the product quantity
        available in stock.

        :param invoice_number: invoice number to register
        """
        assert self.inventory.is_open()
        assert not self.is_adjusted
        storable = self.product.storable
        if storable is None:
            raise TypeError(
                "The adjustment item must be a storable product.")

        adjustment_qty = self.actual_quantity - self.recorded_quantity
        if not adjustment_qty:
            return
        elif adjustment_qty > 0:
            storable.increase_stock(adjustment_qty,
                                    self.inventory.branch,
                                    StockTransactionHistory.TYPE_INVENTORY_ADJUST,
                                    self.id, batch=self.batch)
        else:
            storable.decrease_stock(abs(adjustment_qty),
                                    self.inventory.branch,
                                    StockTransactionHistory.TYPE_INVENTORY_ADJUST,
                                    self.id, batch=self.batch)

        self._add_inventory_fiscal_entry(invoice_number)
        self.is_adjusted = True

    def get_code(self):
        """Get the product code of this item

        :returns: the product code
        """
        return self.product.sellable.code

    def get_description(self):
        """Returns the product description"""
        return self.product.sellable.get_description()

    def get_fiscal_description(self):
        """Returns a description of the product tax constant"""
        return self.product.sellable.tax_constant.get_description()

    def get_total_cost(self):
        """Returns the total cost of this item, the actual quantity multiplied
        by the product cost in the moment it was adjusted. If the item was not
        adjusted yet, the total cost will be zero.
        """
        if not self.is_adjusted and self.actual_quantity is None:
            return Decimal(0)

        return self.product_cost * self.actual_quantity


class Inventory(Domain):
    """ The Inventory handles the logic related to creating inventories
    for the available |product| (or a group of) in a certain |branch|.

    It has the following states:

    - STATUS_OPEN: an inventory is opened, at this point the products which
      are going to be counted (and eventually adjusted) are
      selected.
      And then, the inventory items are available for counting and
      adjustment.

    - STATUS_CLOSED: all the inventory items have been counted (and
      eventually) adjusted.

    - STATUS_CANCELLED: the process was cancelled before being finished,
      this can only happen before any items are adjusted.

    .. graphviz::

       digraph inventory_status {
         STATUS_OPEN -> STATUS_CLOSED;
         STATUS_OPEN -> STATUS_CANCELLED;
       }
    """

    __storm_table__ = 'inventory'

    #: The inventory process is open
    STATUS_OPEN = u'open'

    #: The inventory process is closed
    STATUS_CLOSED = u'closed'

    #: The inventory process was cancelled, eg never finished
    STATUS_CANCELLED = u'cancelled'

    statuses = {STATUS_OPEN: _(u'Opened'),
                STATUS_CLOSED: _(u'Closed'),
                STATUS_CANCELLED: _(u'Cancelled')}

    #: A numeric identifier for this object. This value should be used instead of
    #: :obj:`Domain.id` when displaying a numerical representation of this object to
    #: the user, in dialogs, lists, reports and such.
    identifier = IdentifierCol()

    #: status of the inventory, either STATUS_OPEN, STATUS_CLOSED or
    #: STATUS_CANCELLED
    status = EnumCol(allow_none=False, default=STATUS_OPEN)

    #: number of the invoice if this inventory generated an adjustment
    invoice_number = IntCol(default=None)

    #: the date inventory process was started
    open_date = DateTimeCol(default_factory=localnow)

    #: the date inventory process was closed
    close_date = DateTimeCol(default=None)

    responsible_id = IdCol(allow_none=False)
    #: the responsible for this inventory. At the moment, the
    #: |loginuser| that opened the inventory
    responsible = Reference(responsible_id, 'LoginUser.id')

    branch_id = IdCol(allow_none=False)
    #: branch where the inventory process was done
    branch = Reference(branch_id, 'Branch.id')

    #: the |inventoryitems| of this inventory
    inventory_items = ReferenceSet('id', 'InventoryItem.inventory_id')

    #
    # Properties
    #

    @property
    def status_str(self):
        return self.statuses[self.status]

    @property
    def branch_name(self):
        """The |branch| name for this inventory"""
        return self.branch.get_description()

    @property
    def responsible_name(self):
        """The responsible for this inventory"""
        return self.responsible.get_description()

    #
    # Public API
    #

    def add_storable(self, storable, quantity,
                     batch_number=None, batch=None):
        """Add a storable to this inventory.

        The parameters product, storable and batch are passed here to avoid
        future queries, increase the performance when opening the inventory

        :param storable: the |storable| to be added
        :param quantity: the current quantity of the product in stock
        :param batch_number: a batch number representing a |batch|
            for the given sellable. It's used like that instead of
            getting the |batch| directly since we may be adding an item
            not registered before
        :param batch: the corresponding batch to the batch_number
        """
        if batch_number is not None and not batch:
            batch = StorableBatch.get_or_create(self.store,
                                                storable=storable,
                                                batch_number=batch_number)

        product = storable.product
        sellable = product.sellable
        self.validate_batch(batch, sellable, storable=storable)
        return InventoryItem(store=self.store,
                             product=product,
                             batch=batch,
                             product_cost=sellable.cost,
                             recorded_quantity=quantity,
                             inventory=self)

    def is_open(self):
        """Checks if this inventory is opened

        :returns: ``True`` if the inventory process is open,
            ``False`` otherwise
        """
        return self.status == self.STATUS_OPEN

    def close(self):
        """Closes the inventory process

        :raises: :exc:`AssertionError` if the inventory is already closed
        """
        if not self.is_open():
            # FIXME: We should be raising a better error here.
            raise AssertionError("You can not close an inventory which is "
                                 "already closed!")

        for item in self.inventory_items:
            if (item.actual_quantity is None or
                item.recorded_quantity == item.actual_quantity):
                continue

            # FIXME: We are setting this here because, when generating a
            # sintegra file, even if this item wasn't really adjusted (e.g.
            # adjustment_qty bellow is 0) it needs to be specified and not
            # setting this would result on self.get_cost returning 0.  Maybe
            # we should resolve this in another way
            # We don't call item.adjust since it needs an invoice number
            item.is_adjusted = True

        self.close_date = StatementTimestamp()
        self.status = Inventory.STATUS_CLOSED

    def all_items_counted(self):
        """Checks if all items of this inventory were counted

        :returns: ``True`` if all inventory items are counted,
            ``False`` otherwise.
        """
        # FIXME: Why would items not be counted if the status is closed?
        # The status can only be closed if the items were counted and adjusted
        if self.status == self.STATUS_CLOSED:
            return False

        return self.inventory_items.find(counted_quantity=None).is_empty()

    def get_items(self):
        """Returns all the inventory items related to this inventory

        :returns: items
        :rtype: a sequence of :class:`InventoryItem`
        """
        store = self.store
        return store.find(InventoryItem, inventory=self)

    @classmethod
    def has_open(cls, store, branch):
        """Returns if there is an inventory opened at the moment or not.

        :returns: The open inventory, if there is one. None otherwise.
        """
        return store.find(cls, status=Inventory.STATUS_OPEN,
                          branch=branch).one()

    def get_items_for_adjustment(self):
        """Gets all the inventory items that needs adjustment

        An item needing adjustment is any :class:`InventoryItem`
        with :attr:`InventoryItem.recorded_quantity` different from
        :attr:`InventoryItem.counted_quantity`.

        :returns: items
        :rtype: a sequence of :class:`InventoryItem`
        """
        return self.inventory_items.find(
            And(InventoryItem.recorded_quantity != InventoryItem.counted_quantity,
                Eq(InventoryItem.is_adjusted, False)))

    def has_adjusted_items(self):
        """Returns if we already have an item adjusted or not.

        :returns: ``True`` if there is one or more items adjusted, False
          otherwise.
        """
        return not self.inventory_items.find(is_adjusted=True).is_empty()

    def cancel(self):
        """Cancel this inventory

        Note that you can only cancel an inventory as long
        as you haven't adjusted any :class:`InventoryItem`

        :raises: :exc:`AssertionError` if the inventory is not
            open or if any item was already adjusted
        """
        if not self.is_open():
            raise AssertionError(
                "You can't cancel an inventory that is not opened!")

        if self.has_adjusted_items():
            raise AssertionError(
                "You can't cancel an inventory that has adjusted items!")

        self.status = Inventory.STATUS_CANCELLED

    def get_inventory_data(self):
        """Returns a generator with the details of the Inventory

        Each item contains:

        - The |inventoryitem|
        - the |storable|
        - the |product|
        - the |sellable|
        - the |storablebatch|
        """
        store = self.store
        tables = [InventoryItem,
                  Join(Product, Product.id == InventoryItem.product_id),
                  Join(Storable, Storable.id == Product.id),
                  Join(Sellable, Sellable.id == Product.id),
                  LeftJoin(StorableBatch, StorableBatch.id == InventoryItem.batch_id)]
        return store.using(*tables).find(
            (InventoryItem, Storable, Product, Sellable, StorableBatch),
            InventoryItem.inventory_id == self.id)

    @classmethod
    def get_sellables_for_inventory(cls, store, branch, extra_query=None):
        """Returns a generator with the necessary data about the stock to open an Inventory

        :param store: The store to fetch data from
        :param branch: The branch that is being inventoried
        :param query: A query that should be used to restrict the storables for
            the inventory. This can filter based on categories or other aspects
            of the product.

        :returns: a generator of the following objects:
            (Sellable, Product, Storable, StorableBatch, ProductStockItem)
        """
        # XXX: If we should want all storables to be inclued in the inventory, even if if
        #      never had a ProductStockItem before, than we should inclue this query in the
        #      LeftJoin with ProductStockItem below
        query = ProductStockItem.branch_id == branch.id
        if extra_query:
            query = And(query, extra_query)

        tables = [Sellable,
                  Join(Product, Product.id == Sellable.id),
                  Join(Storable, Storable.id == Product.id),
                  LeftJoin(StorableBatch, StorableBatch.storable_id == Storable.id),
                  LeftJoin(ProductStockItem,
                           And(ProductStockItem.storable_id == Storable.id,
                               Or(ProductStockItem.batch_id == StorableBatch.id,
                                  Eq(ProductStockItem.batch_id, None)))),
                  ]
        return store.using(*tables).find(
            (Sellable, Product, Storable, StorableBatch, ProductStockItem),
            query)

    @classmethod
    def create_inventory(cls, store, branch, responsible, query=None):
        """Create a inventory with products that match the given query

        :param store: A store to open the inventory in
        :param query: A query to restrict the products that should be in the inventory.
        """
        inventory = cls(store=store,
                        open_date=localnow(),
                        branch=branch,
                        responsible=responsible)

        for data in cls.get_sellables_for_inventory(store, branch, query):
            sellable, product, storable, batch, stock_item = data
            quantity = stock_item and stock_item.quantity or 0
            if storable.is_batch:
                # This used to test 'stock_item.quantity > 0' too to avoid
                # creating inventory items for old batches not used anymore.
                # We can't do that since that would make it impossible to
                # adjust a batch that was wrongly set to 0. We need to find a
                # way to mark the batches as "not used anymore" because they
                # tend to grow to very large proportions and we are duplicating
                # everyone here
                if batch and stock_item:
                    inventory.add_storable(storable, quantity, batch=batch)
            else:
                inventory.add_storable(storable, quantity)
        return inventory


class InventoryItemsView(Viewable):
    """Holds information about |inventoryitems|

    This is used to get the most information of an inventory item
    without doing lots of database queries.

    It's best used with :meth:`.find_by_product`
    """

    #: the |inventoryitem|
    inventory_item = InventoryItem

    #: the |inventory|
    inventory = Inventory

    #: the |sellable|
    sellable = Sellable

    #: The |StorableBatch|
    batch = StorableBatch

    branch = Branch

    # InventoryItem
    id = InventoryItem.id
    product_id = InventoryItem.product_id
    recorded_quantity = InventoryItem.recorded_quantity
    counted_quantity = InventoryItem.counted_quantity
    actual_quantity = InventoryItem.actual_quantity
    product_cost = InventoryItem.product_cost
    is_adjusted = InventoryItem.is_adjusted
    reason = InventoryItem.reason

    # Inventory
    inventory_identifier = Inventory.identifier
    open_date = Inventory.open_date
    close_date = Inventory.close_date

    #: The name of the person that performed the inventory
    responsible_name = Person.name

    #: The code of the sellable
    code = Sellable.code
    # XXX: Maybe we should have this in the database, since the price may change
    price = Sellable.base_price

    #: The description of the product
    description = Sellable.description

    #: The number of the batch that was adjusted
    batch_number = Coalesce(StorableBatch.batch_number, u'')
    batch_date = StorableBatch.create_date

    tables = [
        InventoryItem,
        Join(Inventory, InventoryItem.inventory_id == Inventory.id),
        Join(Product, Product.id == InventoryItem.product_id),
        Join(Sellable, Sellable.id == Product.id),
        LeftJoin(StorableBatch, InventoryItem.batch_id == StorableBatch.id),
        Join(LoginUser, Inventory.responsible_id == LoginUser.id),
        Join(Person, LoginUser.person_id == Person.id),
        Join(Branch, Inventory.branch_id == Branch.id),
    ]

    @classmethod
    def find_by_inventory(cls, store, inventory):
        """find results for this view that are related to the given inventory

        :param store: the store that will be used to find the results
        :param inventory: the |inventory| that should be filtered
        :returns: the matching views
        :rtype: a sequence of :class:`InventoryItemView`
        """
        return store.find(cls, Inventory.id == inventory.id)

    @classmethod
    def find_by_product(cls, store, product):
        """find results for this view that references *product*

        :param store: the store that will be used to find the results
        :param product: the |product| used to filter the results
        :returns: the matching views
        :rtype: a sequence of :class:`InventoryItemView`
        """
        return store.find(cls, product_id=product.id)


class InventoryView(Viewable):
    """Stores general information's about inventories"""

    inventory = Inventory
    # Inventory

    #: Inventory Id
    id = Inventory.id
    #: Inventory Identifier
    identifier = Inventory.identifier
    #: Inventory Identifier ToString
    identifier_str = Cast(Inventory.identifier, 'text')
    #: Invoice number
    invoice_number = Inventory.invoice_number
    #: Date of open operation
    open_date = Inventory.open_date
    #: Date of close operation
    close_date = Inventory.close_date
    #: Status of Inventory
    status = Inventory.status
    #: Id of referenced Branch
    branch_id = Inventory.branch_id

    tables = [Inventory]

    @classmethod
    def find_by_branch(cls, store, branch=None):
        """find results for this Inventory View that refenrences *Branch*

        :param store: the store that will be used for find the results
        :param branch: the |branch| used to filter the results
        :return: the matching views
        """
        if branch is not None:
            return store.find(cls, branch_id=branch.id)

        return store.find(cls)
