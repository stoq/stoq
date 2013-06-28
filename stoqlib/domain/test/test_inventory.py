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
from stoqlib.domain.inventory import Inventory, InventoryView, InventoryItemsView
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
        item.reason = u"Test"
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

        items[0].reason = u"Test"
        items[0].cfop_data = cfop
        items[0].adjust(invoice_number=13)
        self.assertEqual(inventory.has_adjusted_items(), True)

        items[1].reason = u"Test"
        items[1].cfop_data = cfop
        items[1].adjust(invoice_number=13)
        self.assertEqual(inventory.has_adjusted_items(), True)

        items[2].reason = u"Test"
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

    def testGetBranchName(self):
        inventory = self.create_inventory()
        inventory.branch = self.create_branch(name=u'Dummy',
                                              phone_number=u'12345678',
                                              fax_number=u'6125371231')

        inventory_branch_name = inventory.get_branch_name()
        self.assertEqual(inventory_branch_name, u'Dummy')


class TestInventoryItem(DomainTest):

    def testAdjust(self):
        item = self.create_inventory_item()
        self.assertFalse(item.is_adjusted)
        item.actual_quantity = item.recorded_quantity - 1
        item.cfop_data = self.create_cfop_data()
        item.reason = u"test adjust"
        invoice_number = 13
        item.adjust(invoice_number)

        storable = item.product.storable
        current_stock = storable.get_balance_for_branch(item.inventory.branch)
        self.assertEqual(current_stock, item.actual_quantity)

        entry = self.store.find(FiscalBookEntry,
                                entry_type=FiscalBookEntry.TYPE_INVENTORY).one()
        self.failIf(entry is None)
        self.assertEqual(entry.cfop, item.cfop_data)
        self.assertEqual(entry.branch, item.inventory.branch)

    def testAdjusted(self):
        item = self.create_inventory_item()
        self.assertFalse(item.is_adjusted)

        item.actual_quantity = item.recorded_quantity - 1
        item.cfop_data = self.create_cfop_data()
        item.reason = u"test adjust"
        invoice_number = 13
        item.adjust(invoice_number)
        self.assertTrue(item.is_adjusted)

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


class TestInventoryItemsView(DomainTest):
    def testFind(self):
        inventory = self.create_inventory()
        item1 = self.create_inventory_item(inventory=inventory)
        item2 = self.create_inventory_item(inventory=inventory)

        results = self.store.find(InventoryItemsView)
        self.assertEqual(set([(item1, inventory), (item2, inventory)]),
                         set([(r.inventory_item, r.inventory) for r in
                              results]))

    def testFindByProduct(self):
        p1 = self.create_product()
        p2 = self.create_product()

        inventory1 = self.create_inventory()
        item1 = self.create_inventory_item(inventory=inventory1, product=p1)
        item2 = self.create_inventory_item(inventory=inventory1, product=p2)

        inventory2 = self.create_inventory()
        item3 = self.create_inventory_item(inventory=inventory2, product=p1)
        item4 = self.create_inventory_item(inventory=inventory2, product=p2)

        results = InventoryItemsView.find_by_product(self.store, p1)
        self.assertEqual(set([(item1, inventory1), (item3, inventory2)]),
                         set((r.inventory_item, r.inventory) for r in results))

        results = InventoryItemsView.find_by_product(self.store, p2)
        self.assertEqual(set([(item2, inventory1), (item4, inventory2)]),
                         set((r.inventory_item, r.inventory) for r in results))


class TestInventoryView(DomainTest):
    def testFind(self):
        inventory1 = self.create_inventory()
        inventory2 = self.create_inventory()
        results = self.store.find(InventoryView)
        self.assertEqual(set([inventory1, inventory2]),
                         set([r.inventory for r in results]))

    def testFindByBranch(self):
        b1 = self.create_branch()
        b2 = self.create_branch()

        inventory1 = self.create_inventory(branch=b1)
        inventory2 = self.create_inventory(branch=b2)

        results = InventoryView.find_by_branch(self.store)
        self.assertEqual(set([inventory1, inventory2]),
                         set(r.inventory for r in results))
        results = InventoryView.find_by_branch(self.store, b1)
        r = results.one()
        self.assertEqual(inventory1, r.inventory)
        results = InventoryView.find_by_branch(self.store, b2)
        r = results.one()
        self.assertEqual(inventory2, r.inventory)
