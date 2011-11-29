# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

from decimal import Decimal

from stoqlib.domain.fiscal import FiscalBookEntry
from stoqlib.domain.interfaces import IStorable
from stoqlib.domain.inventory import Inventory
from stoqlib.domain.test.domaintest import DomainTest


class TestInventory(DomainTest):

    def testIsOpen(self):
        inventory = self.create_inventory()
        self.failUnless(inventory.is_open())

        inventory.close()
        self.failIf(inventory.is_open())

    def testCancel(self):
        inventory = self.create_inventory()
        inventory.cancel()
        self.assertEqual(inventory.status, Inventory.STATUS_CANCELLED)

        inventory = self.create_inventory()
        inventory.close()
        self.assertRaises(AssertionError, inventory.cancel)
        self.assertEqual(inventory.status, Inventory.STATUS_CLOSED)

        inventory = self.create_inventory()
        item = self.create_inventory_item(inventory)
        item.actual_quantity = item.recorded_quantity - 1
        item.cfop_data = self.create_cfop_data()
        item.reason = "Test"
        item.adjust(invoice_number=13)
        self.assertRaises(AssertionError, inventory.cancel)
        self.assertEqual(inventory.status, Inventory.STATUS_OPEN)

    def testHasAdjustedItems(self):
        inventory = self.create_inventory()
        items = []
        for i in range(3):
            item = self.create_inventory_item(inventory)
            item.actual_quantity = item.recorded_quantity - 1
            items.append(item)

        self.assertEqual(inventory.has_adjusted_items(), False)

        for item in items:
            item.actual_quantity = 3

        self.assertEqual(inventory.has_adjusted_items(), False)
        cfop = self.create_cfop_data()

        items[0].reason = "Test"
        items[0].cfop_data = cfop
        items[0].adjust(invoice_number=13)
        self.assertEqual(inventory.has_adjusted_items(), True)

        items[1].reason = "Test"
        items[1].cfop_data = cfop
        items[1].adjust(invoice_number=13)
        self.assertEqual(inventory.has_adjusted_items(), True)

        items[2].reason = "Test"
        items[2].cfop_data = cfop
        items[2].adjust(invoice_number=13)
        self.assertEqual(inventory.has_adjusted_items(), True)

    def testGetItems(self):
        inventory = self.create_inventory()
        items = []
        for i in range(3):
            item = self.create_inventory_item(inventory)
            items.append(item)

        inventory_items = inventory.get_items()
        self.assertEqual(inventory_items.count(), 3)
        self.assertEqual(sorted(inventory_items), sorted(items))

    def testGetItemsForAdjustment(self):
        inventory = self.create_inventory()
        items = []
        for i in range(5):
            item = self.create_inventory_item(inventory)
            if i % 2 == 0:
                item.actual_quantity = item.recorded_quantity - 1
                items.append(item)

        adjustment_items = inventory.get_items_for_adjustment()
        self.assertEqual(adjustment_items.count(), len(items))
        self.assertEqual(sorted(adjustment_items), sorted(items))

    def testClose(self):
        inventory = self.create_inventory()
        self.assertEqual(inventory.status, inventory.STATUS_OPEN)

        inventory.close()
        self.assertEqual(inventory.status, inventory.STATUS_CLOSED)

        self.assertRaises(AssertionError, inventory.close)

        inventory = self.create_inventory()
        inventory.cancel()
        self.assertRaises(AssertionError, inventory.close)

    def testAllItemsCounted(self):
        inventory = self.create_inventory()
        item1 = self.create_inventory_item(inventory)
        item2 = self.create_inventory_item(inventory)
        self.failIf(inventory.all_items_counted())

        item1.actual_quantity = 3
        self.failIf(inventory.all_items_counted())

        item2.actual_quantity = 2
        self.failUnless(inventory.all_items_counted())


class TestInventoryItem(DomainTest):

    def testAdjust(self):
        item = self.create_inventory_item()
        self.failIf(item.adjusted())
        item.actual_quantity = item.recorded_quantity - 1
        item.cfop_data = self.create_cfop_data()
        item.reason = "test adjust"
        invoice_number = 13
        item.adjust(invoice_number)

        storable = IStorable(item.product)
        current_stock = storable.get_full_balance(item.inventory.branch)
        self.assertEqual(current_stock, item.actual_quantity)

        entry = FiscalBookEntry.selectOneBy(
                            entry_type=FiscalBookEntry.TYPE_INVENTORY,
                            connection=self.trans)
        self.failIf(entry is None)
        self.assertEqual(entry.cfop, item.cfop_data)
        self.assertEqual(entry.branch, item.inventory.branch)

    def testAdjusted(self):
        item = self.create_inventory_item()
        self.failIf(item.adjusted())

        item.actual_quantity = item.recorded_quantity - 1
        item.cfop_data = self.create_cfop_data()
        item.reason = "test adjust"
        invoice_number = 13
        item.adjust(invoice_number)
        self.failUnless(item.adjusted())

    def testGetAdjustmentQuantity(self):
        recorded_qty = Decimal(10)
        item = self.create_inventory_item(None, recorded_qty)
        self.assertEqual(None, item.get_adjustment_quantity())

        actual = Decimal(5)
        item.actual_quantity = actual
        self.assertEqual(actual - recorded_qty, item.get_adjustment_quantity())

        actual = Decimal(12)
        item.actual_quantity = actual
        self.assertEqual(actual - recorded_qty, item.get_adjustment_quantity())
