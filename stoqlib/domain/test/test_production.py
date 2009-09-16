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
## Author(s):   George Y. Kussumoto     <george@async.com.br>
##
""" This module test all class in stoqlib/domain/production.py """


from stoqlib.domain.interfaces import IStorable
from stoqlib.domain.production import ProductionOrder, ProductionMaterial
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
        # quantity defaults to 1
        self.assertRaises(AssertionError, item.can_produce, 0)
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
        item = self.create_production_item()
        branch = item.order.branch
        item.product.addFacet(IStorable, connection=self.trans)
        for material in item.order.get_material_items():
            storable = material.product.addFacet(IStorable,
                                                 connection=self.trans)
            storable.increase_stock(10, branch)

        item.produce(1)
        self.assertEqual(item.produced, 1)

    def testAddLost(self):
        item = self.create_production_item()
        order = item.order
        branch = order.branch
        item.product.addFacet(IStorable, connection=self.trans)
        for component in item.get_components():
            storable = component.component.addFacet(IStorable,
                                                    connection=self.trans)
            storable.increase_stock(1, branch)

        order.start_production()

        self.assertRaises(AssertionError, item.add_lost, 0)

        item.add_lost(1)
        self.assertEqual(item.lost, 1)
        self.assertRaises(ValueError, item.add_lost, 1)

        item = self.create_production_item()
        invalid_qty = item.quantity + 1
        self.assertRaises(ValueError, item.add_lost, invalid_qty)

        item = self.create_production_item()
        item.produced = 1
        self.assertRaises(ValueError, item.add_lost, 1)


class TestProductionMaterial(DomainTest):

    def testAllocateAll(self):
        material = self.create_production_material()
        branch = material.order.branch
        product = material.product
        storable = IStorable(product, None)
        if storable is None:
            storable = product.addFacet(IStorable, connection=self.trans)
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
        storable = product.addFacet(IStorable, connection=self.trans)
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
        item.product.addFacet(IStorable, connection=self.trans)
        for component in item.get_components():
            storable = component.component.addFacet(IStorable,
                                                    connection=self.trans)
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
        item.product.addFacet(IStorable, connection=self.trans)
        for material in item.order.get_material_items():
            storable = material.product.addFacet(IStorable,
                                                 connection=self.trans)
            storable.increase_stock(10, branch)

        # Trigger the consume of materials
        item.produce(1)
        self.assertEqual(item.produced, 1) 

        for component in item.get_components():
            material = ProductionMaterial.selectOneBy(order=order,
                          product=component.component, connection=self.trans) 
            lost = component.quantity
            self.assertEqual(material.consumed, lost) 
