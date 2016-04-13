# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008-2014 Async Open Source <http://www.async.com.br>
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
__tests__ = 'stoqlib/domain/inventory.py'

from decimal import Decimal

from kiwi.currency import currency

from stoqlib.domain.fiscal import FiscalBookEntry
from stoqlib.domain.inventory import (Inventory, InventoryView,
                                      InventoryItemsView, InventoryItem)
from stoqlib.domain.product import StockTransactionHistory
from stoqlib.domain.sellable import Sellable
from stoqlib.domain.test.domaintest import DomainTest


class TestInventory(DomainTest):

    def test_create_inventory(self):
        branch = self.create_branch()
        # A category so that we can filter the products we want in the
        # inventory
        cat = self.create_sellable_category()

        #  First, lets create some sellables for our test
        # One storable with stock (it should be in the inventory)
        storable1 = self.create_storable(branch=branch, stock=10)
        storable1.product.sellable.category = cat

        # One storable without stock (it should NOT be in the inventory)
        storable2 = self.create_storable()
        storable2.product.sellable.category = cat

        # One storable with one batch, and stock (it should be in the inventory)
        storable3 = self.create_storable()
        storable3.is_batch = True
        storable3.product.sellable.category = cat
        batch1 = self.create_storable_batch(storable3, u'123')
        storable3.increase_stock(3, branch, batch=batch1,
                                 type=StockTransactionHistory.TYPE_INITIAL,
                                 object_id=None, unit_cost=10)

        # One storable with one batch and a stock item (but without stock).
        # it should be on the inventory
        storable4 = self.create_storable()
        storable4.is_batch = True
        storable4.product.sellable.category = cat
        batch2 = self.create_storable_batch(storable4, u'124')
        storable4.increase_stock(1, branch, batch=batch2,
                                 type=StockTransactionHistory.TYPE_INITIAL,
                                 object_id=None, unit_cost=10)
        storable4.decrease_stock(1, branch, batch=batch2,
                                 type=StockTransactionHistory.TYPE_INITIAL,
                                 object_id=None)

        # Then, lets open the inventory
        responsible = self.create_user()
        query = Sellable.category == cat
        inventory = Inventory.create_inventory(self.store, branch, responsible, query)

        self.assertEquals(inventory.branch, branch)
        self.assertEquals(inventory.responsible, responsible)

        # There should be only 3 items in the inventory
        items = inventory.get_items()
        self.assertEqual(items.count(), 3)
        self.assertEqual(set(i.product for i in items),
                         set([storable1.product,
                              storable3.product,
                              storable4.product]))

        # Use this examples to also test get_inventory_data
        data = list(inventory.get_inventory_data())
        self.assertEquals(len(data), 3)

        # each row should have 5 items
        row = data[0]
        self.assertEquals(len(row), 5)

        self.assertEquals(set(i[0] for i in data), set(items))
        self.assertEquals(set(i[1] for i in data),
                          set([storable1, storable3, storable4]))
        self.assertEquals(set(i[4] for i in data),
                          set([None, batch1, batch2]))

    def test_add_storable(self):
        inventory = self.create_inventory()
        sellable = self.create_sellable()
        storable = self.create_storable(product=sellable.product)
        result = inventory.add_storable(storable, 10)

        item = self.store.find(InventoryItem, product=sellable.product).one()
        self.assertEquals(result, item)

        storable.is_batch = True
        batch = self.create_storable_batch(storable=storable,
                                           batch_number=u'1')
        item = inventory.add_storable(storable, 5, batch_number=u'1')
        result = self.store.find(InventoryItem, batch=batch).one()
        self.assertEquals(item, result)

    def test_is_open(self):
        inventory = self.create_inventory()
        self.failUnless(inventory.is_open())

        inventory.close()
        self.failIf(inventory.is_open())

    def test_cancel(self):
        inventory = self.create_inventory()
        inventory.cancel()
        self.assertEqual(inventory.status, Inventory.STATUS_CANCELLED)

        inventory = self.create_inventory()
        inventory.close()
        self.assertRaises(AssertionError, inventory.cancel)
        self.assertEqual(inventory.status, Inventory.STATUS_CLOSED)

        inventory = self.create_inventory()
        item = self.create_inventory_item(inventory)
        item.counted_quantity = item.recorded_quantity - 1
        item.actual_quantity = item.recorded_quantity - 1
        item.cfop_data = self.create_cfop_data()
        item.reason = u"Test"
        item.adjust(invoice_number=13)
        self.assertRaises(AssertionError, inventory.cancel)
        self.assertEqual(inventory.status, Inventory.STATUS_OPEN)

    def test_status_str(self):
        inventory = self.create_inventory()
        for status in inventory.statuses:
            inventory.status = status
            self.assertEquals(inventory.status_str,
                              inventory.statuses[status])

    def test_has_adjusted_items(self):
        inventory = self.create_inventory()
        items = []
        for i in range(3):
            item = self.create_inventory_item(inventory)
            item.counted_quantity = item.recorded_quantity - 1
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

    def test_get_items(self):
        inventory = self.create_inventory()
        items = []
        for i in range(3):
            item = self.create_inventory_item(inventory)
            items.append(item)

        inventory_items = inventory.get_items()
        self.assertEqual(inventory_items.count(), 3)
        self.assertEqual(sorted(inventory_items), sorted(items))

    def test_has_open(self):
        inventory = self.create_inventory()
        branch = self.create_branch()
        result = inventory.has_open(store=self.store, branch=branch)
        self.assertIsNone(result)
        inventory.branch = branch
        inventory.is_open()
        result = inventory.has_open(store=self.store, branch=branch)
        self.assertEquals(result, inventory)

    def test_get_items_for_adjustment(self):
        inventory = self.create_inventory()
        items = []
        for i in range(5):
            item = self.create_inventory_item(inventory)
            if i % 2 == 0:
                item.counted_quantity = item.recorded_quantity - 1
                items.append(item)

        adjustment_items = inventory.get_items_for_adjustment()
        self.assertEqual(adjustment_items.count(), len(items))
        self.assertEqual(sorted(adjustment_items), sorted(items))

    def test_close(self):
        inventory = self.create_inventory()
        for i in range(5):
            if i % 5 == 0:
                item = self.create_inventory_item(inventory=inventory)
                item.counted_quantity = item.recorded_quantity = 1
                item.actual_quantity = 2
            else:
                not_adjusted_item = self.create_inventory_item(inventory=inventory)

        self.assertEqual(inventory.status, inventory.STATUS_OPEN)

        inventory.close()
        self.assertEqual(inventory.status, inventory.STATUS_CLOSED)

        self.assertEqual(item.is_adjusted, True)
        self.assertEqual(not_adjusted_item.is_adjusted, False)

        self.assertRaises(AssertionError, inventory.close)

        inventory = self.create_inventory()
        inventory.cancel()
        self.assertRaises(AssertionError, inventory.close)

    def test_all_items_counted(self):
        inventory = self.create_inventory()
        item1 = self.create_inventory_item(inventory)
        item2 = self.create_inventory_item(inventory)
        self.failIf(inventory.all_items_counted())

        item1.counted_quantity = 3
        self.failIf(inventory.all_items_counted())

        item2.counted_quantity = 2
        self.failUnless(inventory.all_items_counted())

        inventory.status = inventory.STATUS_CLOSED
        self.assertFalse(inventory.all_items_counted())

    def test_branch_name(self):
        inventory = self.create_inventory()
        inventory.branch = self.create_branch(name=u'Dummy',
                                              phone_number=u'12345678',
                                              fax_number=u'6125371231')
        self.assertEqual(inventory.branch_name, u'Dummy shop')


class TestInventoryItem(DomainTest):

    def test_adjust(self):
        item = self.create_inventory_item()
        self.assertFalse(item.is_adjusted)
        item.counted_quantity = item.recorded_quantity - 1
        item.actual_quantity = item.recorded_quantity - 1
        item.cfop_data = self.create_cfop_data()
        item.reason = u"test adjust"
        invoice_number = 13
        item.adjust(invoice_number)

        storable = item.product.storable
        current_stock = storable.get_balance_for_branch(item.inventory.branch)
        self.assertEqual(current_stock, item.counted_quantity)

        entry = self.store.find(FiscalBookEntry,
                                entry_type=FiscalBookEntry.TYPE_INVENTORY).one()
        self.failIf(entry is None)
        self.assertEqual(entry.cfop, item.cfop_data)
        self.assertEqual(entry.branch, item.inventory.branch)

        item.is_adjusted = False
        item.actual_quantity = item.recorded_quantity
        item.inventory.status = Inventory.STATUS_OPEN
        self.assertEquals(item.adjust(invoice_number=invoice_number), None)

        for i in storable.get_stock_items():
            for transaction_history in i.transactions:
                self.store.remove(transaction_history)
            self.store.remove(i)
        self.store.remove(storable)

        item.is_adjusted = False
        item.inventory.status = Inventory.STATUS_OPEN
        with self.assertRaises(TypeError) as error:
            item.adjust(invoice_number=invoice_number)
        expected = "The adjustment item must be a storable product."
        self.assertEquals(str(error.exception), expected)

    def test_get_code(self):
        item = self.create_inventory_item()
        item.product.sellable.code = u'81726'
        self.assertEquals(item.get_code(), u'81726')

    def test_get_description(self):
        item = self.create_inventory_item()
        self.assertEquals(item.get_description(), u'Description')

    def test_unit_description(self):
        item = self.create_inventory_item()
        self.assertIsNone(item.unit_description)
        unit = self.create_sellable_unit(description=u'Kg')
        item.product.sellable.unit = unit
        self.assertEquals(item.unit_description, u'Kg')

    def test_get_total_cost(self):
        item = self.create_inventory_item()
        self.assertEquals(item.get_total_cost(), Decimal(0))
        item.is_adjusted = True
        item.product_cost = Decimal(100)
        item.actual_quantity = 8
        self.assertEquals(item.get_total_cost(), currency(800))

    def test_adjusted(self):
        item = self.create_inventory_item()
        self.assertFalse(item.is_adjusted)

        item.counted_quantity = item.recorded_quantity - 1
        item.actual_quantity = item.recorded_quantity - 1
        item.cfop_data = self.create_cfop_data()
        item.reason = u"test adjust"
        invoice_number = 13
        item.adjust(invoice_number)
        self.assertTrue(item.is_adjusted)

    def test_get_adjustment_quantity(self):
        recorded_qty = Decimal(10)
        item = self.create_inventory_item(None, recorded_qty)
        self.assertEqual(None, item.difference)

        actual = Decimal(5)
        item.counted_quantity = actual
        self.assertEqual(actual - recorded_qty, item.difference)

        actual = Decimal(12)
        item.counted_quantity = actual
        self.assertEqual(actual - recorded_qty, item.difference)


class TestInventoryItemsView(DomainTest):

    def test_find_by_inventory(self):
        inventory1 = self.create_inventory()
        inventory2 = self.create_inventory()
        item1 = self.create_inventory_item(inventory=inventory1)
        self.create_inventory_item(inventory=inventory2)

        views = InventoryItemsView.find_by_inventory(self.store, inventory1)
        self.assertEquals(views.count(), 1)
        self.assertEquals(views[0].id, item1.id)

    def test_find(self):
        inventory = self.create_inventory()
        item1 = self.create_inventory_item(inventory=inventory)
        item2 = self.create_inventory_item(inventory=inventory)

        results = self.store.find(InventoryItemsView)
        self.assertEqual(set([(item1, inventory), (item2, inventory)]),
                         set([(r.inventory_item, r.inventory) for r in
                              results]))

    def test_find_by_product(self):
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
    def test_find(self):
        inventory1 = self.create_inventory()
        inventory2 = self.create_inventory()
        results = self.store.find(InventoryView)
        self.assertEqual(set([inventory1, inventory2]),
                         set([r.inventory for r in results]))

    def test_find_by_branch(self):
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
