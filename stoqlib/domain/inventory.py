# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008-2013 Async Open Source <http://www.async.com.br>
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

from decimal import Decimal
from storm.expr import And, Eq
from storm.references import Reference, ReferenceSet

from stoqlib.database.expr import StatementTimestamp
from stoqlib.database.properties import (QuantityCol, PriceCol, DateTimeCol,
                                         IntCol, UnicodeCol, IdentifierCol,
                                         IdCol, BoolCol)
from stoqlib.domain.base import Domain
from stoqlib.domain.fiscal import FiscalBookEntry
from stoqlib.domain.product import StockTransactionHistory, StorableBatch
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

    #: the recorded quantity of a product
    recorded_quantity = QuantityCol()

    #: the actual quantity of a product
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

        adjustment_qty = self.get_adjustment_quantity()
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

    def get_unit_description(self):
        """Returns the product unit description or None if it's not set
        """
        sellable = self.product.sellable
        if sellable.unit:
            return sellable.unit.description

    def get_adjustment_quantity(self):
        """Returns the adjustment quantity, the actual quantity minus
        the recorded quantity or None if there is no actual quantity yet.
        """
        if self.actual_quantity is not None:
            return self.actual_quantity - self.recorded_quantity

    def get_total_cost(self):
        """Returns the total cost of this item, the actual quantity multiplied
        by the product cost in the moment it was adjusted. If the item was not
        adjusted yet, the total cost will be zero.
        """
        if not self.is_adjusted:
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
    STATUS_OPEN = 0

    #: The inventory process is closed
    STATUS_CLOSED = 1

    #: The inventory process was cancelled, eg never finished
    STATUS_CANCELLED = 2

    statuses = {STATUS_OPEN: _(u'Opened'),
                STATUS_CLOSED: _(u'Closed'),
                STATUS_CANCELLED: _(u'Cancelled')}

    #: A numeric identifier for this object. This value should be used instead of
    #: :obj:`Domain.id` when displaying a numerical representation of this object to
    #: the user, in dialogs, lists, reports and such.
    identifier = IdentifierCol()

    #: status of the inventory, either STATUS_OPEN, STATUS_CLOSED or
    #: STATUS_CANCELLED
    status = IntCol(default=STATUS_OPEN)

    #: number of the invoice if this inventory generated an adjustment
    invoice_number = IntCol(default=None)

    #: the date inventory process was started
    open_date = DateTimeCol(default_factory=localnow)

    #: the date inventory process was closed
    close_date = DateTimeCol(default=None)

    branch_id = IdCol()

    #: branch where the inventory process was done
    branch = Reference(branch_id, 'Branch.id')

    #: the |inventoryitems| of this inventory
    inventory_items = ReferenceSet('id', 'InventoryItem.inventory_id')

    #
    # Public API
    #

    def add_sellable(self, sellable, batch_number=None):
        """Add a sellable in this inventory

        Note that the :attr:`item's quantity <InventoryItem.recorded_quantity>`
        will be set based on the registered sellable's stock

        :param sellable: the |sellable| to be added
        :param batch_number: a batch number representing a |batch|
            for the given sellable. It's used like that instead of
            getting the |batch| directly since we may be adding an item
            not registered before
        """
        product = sellable.product
        storable = product.storable
        if storable is None:
            raise TypeError("product %r has no storable" % (product, ))

        if batch_number is not None:
            batch = StorableBatch.get_or_create(self.store,
                                                storable=storable,
                                                batch_number=batch_number)
            quantity = batch.get_balance_for_branch(self.branch)
        else:
            batch = None
            quantity = storable.get_balance_for_branch(self.branch)

        self.validate_batch(batch, sellable)

        return InventoryItem(store=self.store,
                             product=sellable.product,
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
            if item.actual_quantity != item.recorded_quantity:
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

        return self.inventory_items.find(actual_quantity=None).is_empty()

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
        :attr:`InventoryItem.actual_quantity`.

        :returns: items
        :rtype: a sequence of :class:`InventoryItem`
        """
        return self.inventory_items.find(
            And(InventoryItem.recorded_quantity != InventoryItem.actual_quantity,
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

    def get_status_str(self):
        return self.statuses[self.status]
