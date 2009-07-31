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
from stoqlib.domain.production import ProductionOrder
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


class TestProductionMaterial(DomainTest):

    def testAllocate(self):
        material = self.create_production_material()
        branch = material.order.branch
        product = material.product
        storable = IStorable(product, None)
        if storable is None:
            storable = product.addFacet(IStorable, connection=self.trans)
        storable.increase_stock(10, branch)
        material.needed = 10
        stock_qty = material.get_stock_quantity()
        self.assertEqual(stock_qty, 10)

        material.allocate()
        stock_qty = material.get_stock_quantity()
        self.assertEqual(stock_qty, 0)
        material.allocate()
        self.assertEqual(stock_qty, 0)
