# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2013 Async Open Source <http://www.async.com.br>
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
""" This module test all class in stoqlib/domain/service.py """

import decimal

from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.database.runtime import new_store
from stoqlib.domain.events import (ServiceCreateEvent, ServiceEditEvent,
                                   ServiceRemoveEvent)
from stoqlib.domain.sale import Delivery
from stoqlib.domain.sellable import Sellable
from stoqlib.domain.service import Service, ServiceView
from stoqlib.lib.parameters import sysparam

__tests__ = 'stoqlib/domain/service.py'


class _ServiceEventData(object):

    def __init__(self):
        self.reset()

    def reset(self):
        self.service = None
        self.emit_count = 0
        self.was_created = False
        self.was_edited = False
        self.was_deleted = False

    def on_create(self, service, **kwargs):
        self.service = service
        self.was_created = True
        self.emit_count += 1

    def on_edit(self, service, **kwargs):
        self.service = service
        self.was_edited = True
        self.emit_count += 1

    def on_delete(self, service, **kwargs):
        self.service = service
        self.was_deleted = True
        self.emit_count += 1


class TestServiceSellableItem(DomainTest):
    def test_add_item(self):
        sale = self.create_sale()
        delivery = Delivery(store=self.store)

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

    def test_events(self):
        store_list = []
        p_data = _ServiceEventData()
        ServiceCreateEvent.connect(p_data.on_create)
        ServiceEditEvent.connect(p_data.on_edit)
        ServiceRemoveEvent.connect(p_data.on_delete)

        try:
            # Test service being created
            store = new_store()
            store_list.append(store)
            sellable = Sellable(
                store=store,
                description=u'Test 1234',
                price=decimal.Decimal(2),
            )
            service = Service(
                store=store,
                sellable=sellable,
            )
            store.commit()
            self.assertTrue(p_data.was_created)
            self.assertFalse(p_data.was_edited)
            self.assertFalse(p_data.was_deleted)
            self.assertEqual(p_data.service, service)
            p_data.reset()

            # Test service being edited and emmiting the event just once
            store = new_store()
            store_list.append(store)
            sellable = store.fetch(sellable)
            service = store.fetch(service)
            sellable.notes = u'Notes'
            sellable.description = u'Test 666'
            service.weight = decimal.Decimal(10)
            store.commit()
            self.assertTrue(p_data.was_edited)
            self.assertFalse(p_data.was_created)
            self.assertFalse(p_data.was_deleted)
            self.assertEqual(p_data.service, service)
            self.assertEqual(p_data.emit_count, 1)
            p_data.reset()

            # Test service being edited, editing Sellable
            store = new_store()
            store_list.append(store)
            sellable = store.fetch(sellable)
            service = store.fetch(service)
            sellable.notes = u'Notes for test'
            store.commit()
            self.assertTrue(p_data.was_edited)
            self.assertFalse(p_data.was_created)
            self.assertFalse(p_data.was_deleted)
            self.assertEqual(p_data.service, service)
            self.assertEqual(p_data.emit_count, 1)
            p_data.reset()

        finally:
            # Test service being removed
            store = new_store()
            store_list.append(store)
            sellable = store.fetch(sellable)
            service = store.fetch(service)
            sellable.remove()
            store.commit()
            self.assertTrue(p_data.was_deleted)
            self.assertFalse(p_data.was_created)
            self.assertFalse(p_data.was_edited)
            self.assertEqual(p_data.service, service)
            self.assertEqual(p_data.emit_count, 1)
            p_data.reset()

            for store in store_list:
                store.close()

    def test_remove(self):
        service = self.create_service()
        service_id = service.id

        total = self.store.find(Service, id=service_id).count()
        self.assertEquals(total, 1)

        service.remove()
        total = self.store.find(Service, id=service_id).count()
        self.assertEquals(total, 0)

    def test_can_remove(self):
        service = self.create_service()

        old = sysparam.get_object(self.store, 'DELIVERY_SERVICE')
        try:
            sysparam.set_object(self.store, 'DELIVERY_SERVICE', service)
            self.assertFalse(service.can_remove())
        finally:
            sysparam.set_object(self.store, 'DELIVERY_SERVICE', old)

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
                          store=self.store)
        self.assertFalse(service.can_remove())

    def test_can_close(self):
        service = self.create_service()
        self.assertTrue(service.can_close())

        old = sysparam.get_object(self.store, 'DELIVERY_SERVICE')
        try:
            sysparam.set_object(self.store, 'DELIVERY_SERVICE', service)
            self.assertFalse(service.can_close())
        finally:
            sysparam.set_object(self.store, 'DELIVERY_SERVICE', old)

    def test_get_description(self):
        service = self.create_service(description=u'My Service')
        self.assertEquals(service.get_description(), u'My Service')


class TestServiceView(DomainTest):

    def test_select(self):
        service = self.store.find(Service).any()
        service_ids = [s.service_id for s in self.store.find(ServiceView)]
        self.assertIn(service.id, service_ids)

    def test_get_unit(self):
        service = self.create_service()
        sv = self.store.find(ServiceView, service_id=service.id).one()
        self.assertEquals(sv.get_unit(), u'')
        service.sellable.unit = self.create_sellable_unit(description=u'Unid.')
        sv = self.store.find(ServiceView, service_id=service.id).one()
        self.assertEquals(sv.get_unit(), u'Unid.')
