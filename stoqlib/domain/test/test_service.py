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
## Author(s):   Johan Dahlin      <jdahlin@async.com.br>
##
""" This module test all class in stoq/domain/station.py """

from stoqlib.domain.interfaces import IDelivery
from stoqlib.domain.product import ProductSellableItem
from stoqlib.domain.service import DeliveryItem, ServiceSellableItem

from stoqlib.domain.test.domaintest import DomainTest

class TestServiceSellableItem(DomainTest):
    def test_addItem(self):
        sale = self.create_sale()
        sellable = self.create_sellable()
        product_item = ProductSellableItem(
            sellable=sellable,
            quantity=1, price=10,
            sale=sale, connection=self.trans)

        service_item = ServiceSellableItem(
            sellable=sellable,
            quantity=1, price=10,
            sale=sale, connection=self.trans)
        delivery_item = DeliveryItem.create_from_sellable_item(product_item)

        delivery = service_item.addFacet(IDelivery, connection=self.trans)
        self.assertEquals(list(delivery.get_items()), [])
        delivery.add_item(delivery_item)
        self.assertEquals(list(delivery.get_items()), [delivery_item])
