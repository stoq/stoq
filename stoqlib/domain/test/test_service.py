# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
""" This module test all class in stoq/domain/station.py """

from stoqlib.domain.sale import Delivery
from stoqlib.domain.service import Service, ServiceView

from stoqlib.domain.test.domaintest import DomainTest


class TestServiceSellableItem(DomainTest):
    def test_addItem(self):
        sale = self.create_sale()
        delivery = Delivery(connection=self.trans)

        service = self.create_service()
        service_item = sale.add_sellable(service.sellable, quantity=1, price=10)
        self.assertFalse(service_item in list(delivery.delivery_items))
        self.assertFalse(service_item in delivery.get_items())
        delivery.add_item(service_item)
        self.assertTrue(service_item in list(delivery.delivery_items))
        self.assertTrue(service_item in delivery.get_items())

        product = self.create_product()
        product_item = sale.add_sellable(product.sellable, quantity=1, price=10)
        self.assertFalse(product_item in list(delivery.delivery_items))
        self.assertFalse(product_item in delivery.get_items())
        delivery.add_item(product_item)
        self.assertTrue(product_item in list(delivery.delivery_items))
        self.assertTrue(product_item in delivery.get_items())


class TestService(DomainTest):
    def test_remove(self):
        service = self.create_service()
        service_id = service.id

        total = Service.selectBy(id=service_id, connection=self.trans).count()
        self.assertEquals(total, 1)

        service.remove()
        total = Service.selectBy(id=service_id, connection=self.trans).count()
        self.assertEquals(total, 0)

    def test_can_remove(self):
        service = self.create_service()
        self.assertTrue(service.can_remove())

        # Service already used.
        sale = self.create_sale()
        sale.add_sellable(service.sellable, quantity=1, price=10)
        self.assertFalse(service.sellable.can_remove())

        # Service is used in a production.
        from stoqlib.domain.production import ProductionService
        service = self.create_service()
        self.assertTrue(service.can_remove())
        ProductionService(service=service,
                          order=self.create_production_order(),
                          connection=self.trans)
        self.assertFalse(service.can_remove())


class TestServiceView(DomainTest):

    def testServiceViewSelect(self):
        service = Service.get(1, connection=self.trans).id
        services = [s.service_id for s in
                    ServiceView.select(connection=self.trans)]
        self.failIf(service not in services)
