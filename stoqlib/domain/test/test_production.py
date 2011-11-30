# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2009 Async Open Source <http://www.async.com.br>
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
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" This module test all class in stoqlib/domain/production.py """

from decimal import Decimal

from stoqlib.domain.interfaces import IStorable
from stoqlib.domain.product import ProductQualityTest
from stoqlib.domain.production import (ProductionOrder, ProductionMaterial,
                                       ProductionItem, ProductionService)
from stoqlib.domain.test.domaintest import DomainTest


class TestProductionOrder(DomainTest):

    def testGetServiceItems(self):
        order = self.create_production_order()
        self.assertEqual(list(order.get_service_items()), [])

        service_item = self.create_production_service()
        service_item.order = order
        self.assertEqual(list(order.get_service_items()), [service_item])

    def testGetMaterialItems(self):
        order = self.create_production_order()
        self.assertEqual(list(order.get_material_items()), [])

        material_item = self.create_production_material()
        material_item.order = order
        self.assertEqual(list(order.get_material_items()), [material_item])

    def testStartProduction(self):
        order = self.create_production_order()
        self.assertEqual(order.status, ProductionOrder.ORDER_OPENED)
        order.start_production()
        self.assertEqual(order.status, ProductionOrder.ORDER_PRODUCING)

    def testSetProductionWaiting(self):
        order = self.create_production_order()
        self.assertEqual(order.status, ProductionOrder.ORDER_OPENED)
        order.set_production_waiting()
        self.assertEqual(order.status, ProductionOrder.ORDER_WAITING)


class TestProductionItem(DomainTest):

    def testCanProduce(self):
        item = self.create_production_item()
        self.assertRaises(AssertionError, item.can_produce, 0)

        # Cant produce if production havent started yet
        self.assertFalse(item.can_produce(1))
        item.order.start_production()

        self.assertTrue(item.can_produce(1))
        self.assertFalse(item.can_produce(2))
        # if we lost one product we can not produce more items
        item.lost = 1
        self.assertFalse(item.can_produce(1))
        self.assertFalse(item.can_produce(2))
        # reset to test other conditions
        item.lost = 0
        # if we already have produced the item, we can not produce more items
        item.produced = 1
        self.assertFalse(item.can_produce(1))
        self.assertFalse(item.can_produce(2))

    def testProduce(self):
        item = self.create_production_item(quantity=2)
        branch = item.order.branch
        for material in item.order.get_material_items():
            storable = IStorable(material.product)
            storable.increase_stock(2, branch)

        order = item.order

        self.assertEqual(order.status, ProductionOrder.ORDER_OPENED)
        item.order.start_production()
        self.assertEqual(order.status, ProductionOrder.ORDER_PRODUCING)

        item.produce(1)
        self.assertEqual(order.status, ProductionOrder.ORDER_PRODUCING)
        self.assertEqual(item.produced, 1)

        item.produce(1)

        # When the total produced reaches the total quantity to produce,
        # order automatically changes the status.
        self.assertEqual(order.status, ProductionOrder.ORDER_CLOSED)
        self.assertEqual(item.produced, 2)

    def testAddLost(self):
        item = self.create_production_item(quantity=2)
        order = item.order
        branch = order.branch
        for component in item.get_components():
            storable = IStorable(component.component)
            storable.increase_stock(2, branch)

        self.assertEqual(order.status, ProductionOrder.ORDER_OPENED)
        order.start_production()
        self.assertEqual(order.status, ProductionOrder.ORDER_PRODUCING)

        self.assertRaises(AssertionError, item.add_lost, 0)

        item.add_lost(1)
        self.assertEqual(order.status, ProductionOrder.ORDER_PRODUCING)
        self.assertEqual(item.lost, 1)
        self.assertRaises(ValueError, item.add_lost, 2)

        # When the total produced reaches the total quantity to produce,
        # order automatically changes the status.
        item.add_lost(1)
        self.assertEqual(order.status, ProductionOrder.ORDER_CLOSED)
        self.assertEqual(item.lost, 2)
        self.assertRaises(ValueError, item.add_lost, 2)

        item = self.create_production_item()
        invalid_qty = item.quantity + 1
        self.assertRaises(ValueError, item.add_lost, invalid_qty)

        item = self.create_production_item()
        item.produced = 1
        self.assertRaises(ValueError, item.add_lost, 1)

    def test_items(self):
        order = self.create_production_order()
        item = ProductionItem(product=self.create_product(),
                              order=order, quantity=1, connection=self.trans)
        service = ProductionService(service=self.create_service(),
                                    order=order, connection=self.trans)

        self.assertTrue(item in order.get_items())
        self.assertTrue(service in order.get_service_items())

        self.assertRaises(AssertionError, order.remove_item, service)
        self.assertRaises(AssertionError, order.remove_service_item, item)

        order.remove_item(item)
        self.assertEqual(list(order.get_items()), [])

        order.remove_service_item(service)
        self.assertEqual(list(order.get_service_items()), [])


class TestProductionMaterial(DomainTest):

    def testAllocateAll(self):
        material = self.create_production_material()
        branch = material.order.branch
        product = material.product
        storable = IStorable(product)
        storable.increase_stock(10, branch)
        material.needed = 20
        self.assertEqual(material.get_stock_quantity(), 10)

        material.allocate()
        self.assertEqual(material.get_stock_quantity(), 0)
        self.assertEqual(material.allocated, 10)
        # try to allocate, but without any stock
        material.allocate()
        self.assertEqual(material.get_stock_quantity(), 0)
        self.assertEqual(material.allocated, 10)
        # try to allocate, with more stock than we need
        storable.increase_stock(25, branch)
        material.allocate()
        self.assertEqual(material.get_stock_quantity(), 15)
        self.assertEqual(material.allocated, 20)

    def testAllocatePartial(self):
        material = self.create_production_material()
        branch = material.order.branch
        product = material.product
        storable = IStorable(product)
        storable.increase_stock(10, branch)
        self.assertEqual(material.get_stock_quantity(), 10)

        material.allocate(5)
        self.assertEqual(material.allocated, 5)
        self.assertEqual(material.get_stock_quantity(), 5)

        material.allocate(5)
        self.assertEqual(material.allocated, 10)
        self.assertEqual(material.get_stock_quantity(), 0)

        self.assertRaises(ValueError, material.allocate, 1)

    def testAddLost(self):
        item = self.create_production_item()
        order = item.order
        branch = order.branch
        for component in item.get_components():
            storable = IStorable(component.component)
            storable.increase_stock(1, branch)

        order.start_production()
        self.assertRaises(AssertionError, item.add_lost, 0)

        # Trigger the lost of materials
        item.add_lost(1)

        for component in item.get_components():
            material = ProductionMaterial.selectOneBy(order=order,
                          product=component.component, connection=self.trans)
            lost = component.quantity
            self.assertEqual(material.lost, lost)

    def testConsume(self):
        item = self.create_production_item()
        order = item.order
        branch = order.branch
        for material in item.order.get_material_items():
            storable = IStorable(material.product)
            storable.increase_stock(10, branch)

        item.order.start_production()

        # Trigger the consume of materials
        item.produce(1)
        self.assertEqual(item.produced, 1)

        for component in item.get_components():
            material = ProductionMaterial.selectOneBy(order=order,
                          product=component.component, connection=self.trans)
            consumed = component.quantity
            self.assertEqual(material.consumed, consumed)


class TestProductionQuality(DomainTest):

    def testProductionQualityCompleteProcess(self):
        # Order with one product to produce 4 units
        order = self.create_production_order()
        item = self.create_production_item(quantity=4, order=order)
        for material in item.order.get_material_items():
            storable = IStorable(material.product)
            storable.increase_stock(4, order.branch)

        test1 = ProductQualityTest(connection=self.trans, product=item.product,
                                       test_type=ProductQualityTest.TYPE_BOOLEAN)
        test1.set_boolean_value(True)
        test2 = ProductQualityTest(connection=self.trans, product=item.product,
                                       test_type=ProductQualityTest.TYPE_DECIMAL)
        test2.set_range_value(10, 20)
        order.start_production()
        self.assertEqual(order.status, ProductionOrder.ORDER_PRODUCING)

        # Since the item has tests, we cant produce anonimously
        self.assertRaises(AssertionError, item.produce, 1)
        user = self.create_user()

        # We still dont have any stock for this product
        storable = IStorable(item.product)
        self.assertEqual(storable.get_full_balance(order.branch), 0)

        self.assertEqual(order.produced_items.count(), 0)
        item.produce(1, user, [123456])
        self.assertEqual(order.produced_items.count(), 1)
        self.assertEqual(order.produced_items[0].serial_number, 123456)

        self.assertEqual(order.status, ProductionOrder.ORDER_PRODUCING)

        # Produce the rest
        item.produce(3, user, [123457, 123458, 1234569])
        self.assertEqual(order.status, ProductionOrder.ORDER_QA)

        # For a produced item, initially, the tests should be empty
        p_item = order.produced_items[0]
        self.assertEqual(p_item.get_test_result(test1), None)
        self.assertEqual(p_item.get_test_result(test2), None)
        self.assertEqual(p_item.test_passed, False)

        # Add a first, faild test
        result = p_item.set_test_result_value(test1, False, user)
        self.assertEqual(p_item.get_test_result(test1), result)
        self.assertEqual(p_item.get_test_result(test2), None)

        self.assertEqual(result.get_boolean_value(), False)
        self.assertEqual(result.test_passed, False)

        # Set it to success
        p_item.set_test_result_value(test1, True, user)
        self.assertEqual(result.get_boolean_value(), True)
        self.assertEqual(result.test_passed, True)

        # Since the product has two tests, the produced item havent passed all
        # tests yet
        self.assertEqual(p_item.test_passed, False)

        # Add a result for the second test (failing)
        result = p_item.set_test_result_value(test2, Decimal(5), user)
        self.assertEqual(p_item.get_test_result(test2), result)

        self.assertEqual(result.get_decimal_value(), 5)
        self.assertEqual(result.test_passed, False)
        self.assertEqual(p_item.test_passed, False)

        # Now set the second test as a success
        p_item.set_test_result_value(test2, Decimal(15), user)
        self.assertEqual(result.test_passed, True)
        self.assertEqual(p_item.test_passed, True)

        # Lets now set the results for all tests as sucessful
        for p_item in order.produced_items:
            p_item.set_test_result_value(test1, True, user)
            p_item.set_test_result_value(test2, Decimal(15), user)

        # Order should be now  CLOSED
        self.assertEqual(order.status, ProductionOrder.ORDER_CLOSED)

        # Items should have entered stock
        for p_item in order.produced_items:
            self.assertEqual(p_item.entered_stock, True)

        storable = IStorable(item.product)
        self.assertEqual(storable.get_full_balance(order.branch), 4)
