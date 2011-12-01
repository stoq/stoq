# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008 Async Open Source <http://www.async.com.br>
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

import datetime
from decimal import Decimal

from stoqlib.database.orm import QuantityCol, PriceCol
from stoqlib.database.orm import ForeignKey, DateTimeCol, IntCol, UnicodeCol
from stoqlib.database.orm import const, AND, ISNOTNULL
from stoqlib.domain.base import Domain
from stoqlib.domain.interfaces import IBranch, IStorable
from stoqlib.domain.fiscal import FiscalBookEntry
from stoqlib.domain.person import Person
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class InventoryItem(Domain):
    """The InventoryItem belongs to an Inventory. It contains the
    recorded quantity and the actual quantity related to a specific product.
    If those quantities are not identitical, it will also contain a reason
    and a cfop describing that.

    @ivar product: the item
    @ivar recorded_quantity: the recorded quantity of a product
    @ivar actual_quantity: the actual quantity of a product
    @ivar product_cost: the product's cost when the product was adjusted.
    @ivar inventory: the inventory process that contains this item
    @ivar cfop: the cfop used to adjust this item, this is only set when
        an adjustment is done
    @ivar reason: the reason of why this item has been adjusted
    """

    product = ForeignKey("Product")
    recorded_quantity = QuantityCol()
    actual_quantity = QuantityCol(default=None)
    product_cost = PriceCol()
    reason = UnicodeCol(default=u"")
    cfop_data = ForeignKey("CfopData", default=None)
    inventory = ForeignKey("Inventory")

    def _add_inventory_fiscal_entry(self, invoice_number):
        inventory = self.inventory
        return FiscalBookEntry(
            entry_type=FiscalBookEntry.TYPE_INVENTORY,
            invoice_number=inventory.invoice_number,
            branch=inventory.branch,
            cfop=self.cfop_data,
            connection=self.get_connection())

    def adjust(self, invoice_number):
        """Create an entry in fiscal book registering the adjustment
        with the related cfop data and change the product quantity
        available in stock.
        """
        storable = IStorable(self.product, None)
        if storable is None:
            raise TypeError(
                "The adjustment item must be a storable product.")

        adjustment_qty = self.get_adjustment_quantity()
        if not adjustment_qty:
            return
        elif adjustment_qty > 0:
            storable.increase_stock(adjustment_qty,
                                    self.inventory.branch)
        else:
            storable.decrease_stock(abs(adjustment_qty),
                                    self.inventory.branch)

        self._add_inventory_fiscal_entry(invoice_number)

    def adjusted(self):
        """Returns True if the item have already been adjusted,
        False otherwise.
        """
        # We check reason and cfop_data attributes because they only
        # exist after the item be adjusted
        return self.reason and self.cfop_data

    def get_code(self):
        """Returns the product code"""
        sellable = self.product.sellable
        return sellable.code

    def get_description(self):
        """Returns the product description"""
        sellable = self.product.sellable
        return sellable.get_description()

    def get_fiscal_description(self):
        """Returns a description of the product tax constant"""
        sellable = self.product.sellable
        return sellable.tax_constant.get_description()

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
        if not self.adjusted():
            return Decimal(0)

        return self.product_cost * self.actual_quantity


class Inventory(Domain):
    """ The Inventory handles the logic related to creating inventories
    for the available products (or a group of) in a certain branch.
    It has two different states:

        - open: an inventory is opened, at this point the products which
          are going to be counted (and eventually adjusted) are
          selected.
          And then, the inventory items are available for counting and
          adjustment.

        - closed: all the inventory items have been counted (and
          eventually) adjusted.

    @cvar STATUS_OPEN: The inventory process is open
    @cvar STATUS_CLOSED: The inventory process is closed
    @ivar open_date: the date inventory process was started
    @ivar close_date: the date inventory process was closed
    @ivar branch: branch where the inventory process was done
    """

    (STATUS_OPEN, STATUS_CLOSED, STATUS_CANCELLED) = range(3)

    statuses = {STATUS_OPEN: _(u'Opened'),
                STATUS_CLOSED: _(u'Closed'),
                STATUS_CANCELLED: _(u'Cancelled')}

    status = IntCol(default=STATUS_OPEN)
    invoice_number = IntCol(default=None)
    open_date = DateTimeCol(default=datetime.datetime.now)
    close_date = DateTimeCol(default=None)
    branch = ForeignKey("PersonAdaptToBranch")

    #
    # Public API
    #

    def is_open(self):
        """Returns True if the inventory process is open, False
        otherwise.
        """
        return self.status == self.STATUS_OPEN

    def close(self, close_date=None):
        """Closes the inventory process

        @param close_date: the closing date or None for right now.
        @type: datetime.datetime
        """
        if not close_date:
            close_date = const.NOW()

        if not self.is_open():
            raise AssertionError("You can not close an inventory which is "
                                 "already closed!")

        self.close_date = close_date
        self.status = Inventory.STATUS_CLOSED

    def all_items_counted(self):
        """Returns True if all inventory items are counted, False
        otherwise.
        """
        if self.status == self.STATUS_CLOSED:
            return False

        conn = self.get_connection()
        not_counted = InventoryItem.selectBy(inventory=self,
                                             actual_quantity=None,
                                             connection=conn)
        return not_counted.count() == 0

    def get_items(self):
        """Returns all the inventory items related to this inventory

        @returns: items
        @rtype: a sequence of L{InventoryItem}
        """
        conn = self.get_connection()
        return InventoryItem.selectBy(inventory=self, connection=conn)

    @classmethod
    def get_open_branches(cls, conn):
        """Retuns all the branches available to open the inventory
        process.

        @returns: branches
        @rtype: a sequence of L{PersonAdaptToBranch}
        """
        for branch in Person.iselect(IBranch, connection=conn):
            if not cls.selectOneBy(branch=branch, status=cls.STATUS_OPEN,
                                   connection=conn):
                yield branch

    @classmethod
    def has_open(cls, conn, branch):
        """Returns if there is an inventory opened at the moment or not.

        @returns: The open inventory, if there is one. None otherwise.
        """
        return cls.selectOneBy(status=Inventory.STATUS_OPEN,
                               branch=branch, connection=conn)

    def get_items_for_adjustment(self):
        """Returns all the inventory items that needs adjustment, that is
        the recorded quantity is different from the actual quantity.

        @returns: items
        @rtype: a sequence of L{InventoryItem}
        """
        query = AND(InventoryItem.q.inventoryID == self.id,
                    InventoryItem.q.recorded_quantity !=
                        InventoryItem.q.actual_quantity,
                    InventoryItem.q.cfop_dataID == None,
                    InventoryItem.q.reason == u"")
        conn = self.get_connection()
        return InventoryItem.select(query, connection=conn)

    def has_adjusted_items(self):
        """Returns if we already have an item adjusted or not.

        @returns: True if there is one or more items adjusted, False
        otherwise.
        """
        query = AND(InventoryItem.q.inventoryID == self.id,
                    ISNOTNULL(InventoryItem.q.cfop_dataID),
                    InventoryItem.q.reason != u"")
        conn = self.get_connection()
        return InventoryItem.select(query, connection=conn).count() > 0

    def cancel(self):
        """Cancel this inventory. Notice that, to cancel an inventory no
        products should have been adjusted.
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
