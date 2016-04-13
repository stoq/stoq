# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2009-2013 Async Open Source <http://www.async.com.br>
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

import mock

from stoqlib.domain.product import (ProductHistory, ProductQualityTest,
                                    StockTransactionHistory)
from stoqlib.domain.production import (ProductionOrder, ProductionMaterial,
                                       ProductionItem, ProductionService,
                                       ProductionProducedItem,
                                       ProductionItemQualityResult,
                                       ProductionOrderProducingView)
from stoqlib.domain.test.domaintest import DomainTest

__tests__ = 'stoqlib/domain/production.py'


class TestProductionOrder(DomainTest):

    def test_get_service_items(self):
        order = self.create_production_order()
        self.assertEqual(list(order.get_service_items()), [])

        service_item = self.create_production_service()
        service_item.order = order
        self.assertEqual(list(order.get_service_items()), [service_item])

    def test_get_material_items(self):
        order = self.create_production_order()
        self.assertEqual(list(order.get_material_items()), [])

        material_item = self.create_production_material()
        material_item.order = order
        self.assertEqual(list(order.get_material_items()), [material_item])

    def test_start_production(self):
        order = self.create_production_order()
        self.assertEqual(order.status, ProductionOrder.ORDER_OPENED)
        order.start_production()
        self.assertEqual(order.status, ProductionOrder.ORDER_PRODUCING)

    def test_set_production_waiting(self):
        order = self.create_production_order()
        self.assertEqual(order.status, ProductionOrder.ORDER_OPENED)
        order.set_production_waiting()
        self.assertEqual(order.status, ProductionOrder.ORDER_WAITING)

    def test_add_item(self):
        order = self.create_production_order()
        sellable = self.create_sellable()
        item = order.add_item(sellable)
        self.assertTrue(isinstance(item, ProductionItem))
        self.assertEquals(item.order, order)

    def test_remove_item(self):
        order = self.create_production_order()
        item = ProductionItem(store=self.store)
        with self.assertRaisesRegexp(
            ValueError,
            (u'Argument item must have an order attribute '
             u'associated with the current production '
             u'order instance.')):
            order.remove_item(item)

        item = self.create_production_item()
        order = item.order
        order.remove_item(item)
        self.assertEquals(order.get_items().count(), 0)

        with self.sysparam(SYNCHRONIZED_MODE=True):
            item = self.create_production_item()
            order = item.order

            before_remove = self.store.find(ProductionItem).count()
            order.remove_item(item)
            after_remove = self.store.find(ProductionItem).count()

            # The item should still be on the database
            self.assertEqual(before_remove, after_remove)

            # But not related to the loan
            self.assertEquals(self.store.find(ProductionItem, order=order).count(), 0)

    def test_remove_service_item(self):
        order = self.create_production_order()
        item = ProductionService(store=self.store)
        with self.assertRaisesRegexp(
            ValueError, (u'Argument item must have an order attribute '
                         u'associated with the current production '
                         u'order instance.')):
            order.remove_service_item(item)

        item = self.create_production_service()
        order = item.order
        order.remove_service_item(item)
        self.assertEquals(order.get_service_items().count(), 0)

        with self.sysparam(SYNCHRONIZED_MODE=True):
            item = self.create_production_service()
            order = item.order

            before_remove = self.store.find(ProductionService).count()
            order.remove_service_item(item)
            after_remove = self.store.find(ProductionService).count()

            # The item should still be on the database
            self.assertEqual(before_remove, after_remove)

            # But not related to the loan
            self.assertEquals(self.store.find(ProductionService, order=order).count(), 0)

    def test_get_status_string(self):
        order = self.create_production_order()
        order.status = ProductionOrder.ORDER_OPENED
        self.assertEquals(order.get_status_string(), u'Opened')
        order.status = ProductionOrder.ORDER_WAITING
        self.assertEquals(order.get_status_string(), u'Waiting')
        order.status = ProductionOrder.ORDER_PRODUCING
        self.assertEquals(order.get_status_string(), u'Producing')
        order.status = ProductionOrder.ORDER_CLOSED
        self.assertEquals(order.get_status_string(), u'Closed')
        order.status = ProductionOrder.ORDER_QA
        self.assertEquals(order.get_status_string(), u'Quality Assurance')

    def test_is_completely_tested(self):
        item = self.create_production_item(quantity=10)
        order = item.order
        self.assertTrue(order.is_completely_tested())

        test1 = ProductQualityTest(store=self.store,
                                   product=item.product,
                                   test_type=ProductQualityTest.TYPE_BOOLEAN)
        test1.set_boolean_value(True)

        for material in item.order.get_material_items():
            material.product.storable.increase_stock(
                10, item.order.branch, StockTransactionHistory.TYPE_INITIAL, None)

        order.start_production()
        user = self.create_user()
        item.produce(1, produced_by=user, serials=[1])

        produced_item = order.produced_items.any()
        produced_item.test_passed = False
        self.assertFalse(order.is_completely_tested())
        produced_item.test_passed = True
        self.assertTrue(order.is_completely_tested())

    def test_get_branch_name(self):
        branch = self.create_branch()
        branch.person.company.fancy_name = u'foo'
        order = self.create_production_order(branch=branch)
        self.assertEquals(order.get_branch_name(), u'foo')

    def test_get_responsible_name(self):
        order = self.create_production_order()
        order.responsible = None
        self.assertEquals(order.get_responsible_name(), u'')
        order.responsible = self.create_employee(name=u'employee')
        self.assertEquals(order.get_responsible_name(), u'employee')

    def test_get_description(self):
        order = self.create_production_order()
        order.description = u'Description'
        self.assertEquals(order.get_description(), u'Description')

    def test_can_cancel(self):
        order = self.create_production_order()
        # We can cancel orders that have not yet started
        order.status = ProductionOrder.ORDER_OPENED
        self.assertTrue(order.can_cancel())
        order.status = ProductionOrder.ORDER_WAITING
        self.assertTrue(order.can_cancel())

        # After a production starts, it is not possible to cancel
        order.start_production()
        self.assertFalse(order.can_cancel())

    def test_can_finalize(self):
        order = self.create_production_order()
        # We can't cancel orders that havent yet started
        order.status = ProductionOrder.ORDER_OPENED
        self.assertFalse(order.can_finalize())
        # After a production starts, we can cancel the orders
        order.start_production()
        self.assertTrue(order.can_finalize())
        # We can finalize QA orders
        order = self.create_production_order()
        order.status = ProductionOrder.ORDER_QA
        self.assertTrue(order.can_finalize())

    def test_cancel(self):
        # The order is cancelled when can_cancel returns true
        order = self.create_production_order()
        self.assertNotEqual(order.status, ProductionOrder.ORDER_CANCELLED)
        order.cancel()
        self.assertEquals(order.status, ProductionOrder.ORDER_CANCELLED)
        order = self.create_production_order()
        order.status = ProductionOrder.ORDER_WAITING
        order.cancel()
        self.assertEquals(order.status, ProductionOrder.ORDER_CANCELLED)
        # We can't cancel started orders
        order = self.create_production_order()
        order.start_production()
        with self.assertRaises(AssertionError):
            order.cancel()

    def test_try_finalize_production(self):
        # The order can be cancelled when the production is started
        order = self.create_production_order()
        order.start_production()
        order.try_finalize_production(ignore_completion=True)
        self.assertEquals(order.status, ProductionOrder.ORDER_CLOSED)
        order = self.create_production_order()
        # This order didnt start. So we cannot finalize
        with self.assertRaises(AssertionError):
            order.try_finalize_production(ignore_completion=False)


class TestProductionItem(DomainTest):

    def test_get_description(self):
        item = self.create_production_item()
        item.product.sellable.description = u'product'
        self.assertEquals(item.get_description(), u'product')

    def test_unit_description(self):
        item = self.create_production_item()
        item.product.sellable.unit = self.create_sellable_unit(description=u'un')
        self.assertEquals(item.unit_description, u'un')

    def test_can_produce(self):
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

    def test_produce(self):
        item = self.create_production_item(quantity=2)
        branch = item.order.branch
        for material in item.order.get_material_items():
            storable = material.product.storable
            storable.increase_stock(2, branch,
                                    StockTransactionHistory.TYPE_INITIAL, None)

        order = item.order

        self.assertEqual(order.status, ProductionOrder.ORDER_OPENED)
        item.order.start_production()
        self.assertEqual(order.status, ProductionOrder.ORDER_PRODUCING)

        with mock.patch(
            'stoqlib.domain.production.ProductionMaterial.consume') as consume:
            consume.side_effect = ValueError()
            with self.assertRaises(ValueError):
                item.produce(1)
            assert self.store.find(ProductHistory,
                                   sellable=item.product.sellable).is_empty()

        item.produce(1)
        self.assertEqual(order.status, ProductionOrder.ORDER_PRODUCING)
        self.assertEqual(item.produced, 1)

        item.produce(1)

        # When the total produced reaches the total quantity to produce,
        # order automatically changes the status.
        self.assertEqual(order.status, ProductionOrder.ORDER_CLOSED)
        self.assertEqual(item.produced, 2)

    def test_add_lost(self):
        item = self.create_production_item(quantity=2)
        order = item.order
        branch = order.branch
        for component in item.get_components():
            storable = component.component.storable
            storable.increase_stock(2, branch,
                                    StockTransactionHistory.TYPE_INITIAL, None)

        self.assertEqual(order.status, ProductionOrder.ORDER_OPENED)
        order.start_production()
        self.assertEqual(order.status, ProductionOrder.ORDER_PRODUCING)

        self.assertRaises(AssertionError, item.add_lost, 0)

        with mock.patch(
            'stoqlib.domain.production.ProductionMaterial.add_lost') as add_lost:
            add_lost.side_effect = ValueError
            with self.assertRaises(ValueError):
                item.add_lost(1)
            assert self.store.find(ProductHistory,
                                   sellable=item.product.sellable).is_empty()

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
                              order=order, quantity=1, store=self.store)
        service = ProductionService(service=self.create_service(),
                                    order=order, store=self.store)

        self.assertTrue(item in order.get_items())
        self.assertTrue(service in order.get_service_items())

        self.assertRaises(AssertionError, order.remove_item, service)
        self.assertRaises(AssertionError, order.remove_service_item, item)

        order.remove_item(item)
        self.assertEqual(list(order.get_items()), [])

        order.remove_service_item(service)
        self.assertEqual(list(order.get_service_items()), [])


class TestProductionMaterial(DomainTest):

    def test_get_description(self):
        material = self.create_production_material()
        material.product.sellable.description = u'product'
        self.assertEquals(material.get_description(), u'product')

    def test_unit_description(self):
        material = self.create_production_material()
        material.product.sellable.unit = self.create_sellable_unit(description=u'un')
        self.assertEquals(material.unit_description, u'un')

    def test_can_add_lost(self):
        material = self.create_production_material()
        self.assertFalse(material.can_add_lost(1))

    def test_can_consume(self):
        material = self.create_production_material()
        self.assertFalse(material.can_consume(1))
        material.order.start_production()
        self.assertTrue(material.can_consume(1))
        self.assertFalse(material.can_consume(2))

    def test_allocate(self):
        material = self.create_production_material()

        branch = material.order.branch
        product = material.product
        storable = product.storable
        storable.increase_stock(10, branch,
                                StockTransactionHistory.TYPE_INITIAL, None)
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
        storable.increase_stock(25, branch,
                                StockTransactionHistory.TYPE_INITIAL, None)
        material.allocate()
        self.assertEqual(material.get_stock_quantity(), 15)
        self.assertEqual(material.allocated, 20)

        for i in storable.get_stock_items():
            for transaction_history in i.transactions:
                self.store.remove(transaction_history)
            self.store.remove(i)
        self.store.remove(storable)

        material.allocate()
        self.assertEquals(material.allocated, material.needed)

    def test_allocate_partial(self):
        material = self.create_production_material()
        branch = material.order.branch
        product = material.product
        storable = product.storable
        storable.increase_stock(10, branch,
                                StockTransactionHistory.TYPE_INITIAL, None)
        self.assertEqual(material.get_stock_quantity(), 10)

        material.allocate(5)
        self.assertEqual(material.allocated, 5)
        self.assertEqual(material.get_stock_quantity(), 5)

        material.allocate(5)
        self.assertEqual(material.allocated, 10)
        self.assertEqual(material.get_stock_quantity(), 0)

        self.assertRaises(ValueError, material.allocate, 1)

    def test_return_remaining(self):
        item = self.create_production_item(quantity=1)
        order = item.order
        branch = order.branch
        for material in order.get_material_items():
            storable = material.product.storable
            storable.increase_stock(10, branch,
                                    StockTransactionHistory.TYPE_INITIAL, None)

        order.status = ProductionOrder.ORDER_CLOSED
        material = order.get_material_items()[0]
        material.allocated = 10
        material.return_remaining()

        self.assertTrue(
            self.store.find(StockTransactionHistory,
                            object_id=material.id,
                            type=StockTransactionHistory.TYPE_PRODUCTION_RETURNED).one())

    def test_return_remaining_component_without_storable(self):
        item = self.create_production_item(quantity=1, storable=False)

        order = item.order
        order.status = ProductionOrder.ORDER_CLOSED
        material = order.get_material_items()[0]
        material.allocated = 10
        material.return_remaining()

        self.assertFalse(
            self.store.find(StockTransactionHistory,
                            object_id=material.id,
                            type=StockTransactionHistory.TYPE_PRODUCTION_RETURNED).one())

    def test_add_lost(self):
        item = self.create_production_item(quantity=3)
        order = item.order
        branch = order.branch
        for component in item.get_components():
            storable = component.component.storable
            storable.increase_stock(3, branch,
                                    StockTransactionHistory.TYPE_INITIAL, None)

        order.start_production()
        self.assertRaises(AssertionError, item.add_lost, 0)

        # Trigger the lost of materials
        item.add_lost(1)

        for component in item.get_components():
            material = self.store.find(ProductionMaterial, order=order,
                                       product=component.component).one()
            lost = component.quantity
            self.assertEqual(material.lost, lost)

        with self.assertRaisesRegexp(
            ValueError, u'Cannot loose this quantity.'):
            material.add_lost(100)
        material.allocated = 2
        with self.assertRaisesRegexp(
            ValueError, u'Can not allocate this quantity.'):
            material.add_lost(2)

    def test_consume(self):
        item = self.create_production_item(quantity=3)
        order = item.order
        branch = order.branch
        for material in item.order.get_material_items():
            storable = material.product.storable
            storable.increase_stock(10, branch,
                                    StockTransactionHistory.TYPE_INITIAL, None)

        item.order.start_production()

        # Trigger the consume of materials
        item.produce(1)
        self.assertEqual(item.produced, 1)

        for component in item.get_components():
            material = self.store.find(ProductionMaterial, order=order,
                                       product=component.component).one()
            consumed = component.quantity
            self.assertEqual(material.consumed, consumed)

        with self.assertRaisesRegexp(
            ValueError, u'Can not consume this quantity.'):
            material.consume(100)


class TestProductionQuality(DomainTest):
    def test_production_quality_complete_process(self):
        # Order with one product to produce 4 units
        order = self.create_production_order()
        item = self.create_production_item(quantity=4, order=order)
        for material in item.order.get_material_items():
            storable = material.product.storable
            storable.increase_stock(4, order.branch,
                                    StockTransactionHistory.TYPE_INITIAL, None)

        test1 = ProductQualityTest(store=self.store, product=item.product,
                                   test_type=ProductQualityTest.TYPE_BOOLEAN)
        test1.set_boolean_value(True)
        test2 = ProductQualityTest(store=self.store, product=item.product,
                                   test_type=ProductQualityTest.TYPE_DECIMAL)
        test2.set_range_value(10, 20)
        order.start_production()
        self.assertEqual(order.status, ProductionOrder.ORDER_PRODUCING)

        # Since the item has tests, we cant produce anonimously
        self.assertRaises(AssertionError, item.produce, 1)
        user = self.create_user()

        # We still dont have any stock for this product
        storable = item.product.storable
        self.assertEqual(storable.get_balance_for_branch(order.branch), 0)

        self.assertEqual(order.produced_items.count(), 0)
        item.produce(1, user, [123456])
        self.assertEqual(order.produced_items.count(), 1)
        self.assertEqual(list(order.produced_items)[0].serial_number, 123456)

        self.assertEqual(order.status, ProductionOrder.ORDER_PRODUCING)

        # Produce the rest
        item.produce(3, user, [123457, 123458, 1234569])
        self.assertEqual(order.status, ProductionOrder.ORDER_QA)

        # For a produced item, initially, the tests should be empty
        p_item = list(order.produced_items.order_by(u'id'))[0]
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
        for p_item in order.produced_items.order_by(u'id'):
            p_item.set_test_result_value(test1, True, user)
            p_item.set_test_result_value(test2, Decimal(15), user)

        # Order should be now  CLOSED
        self.assertEqual(order.status, ProductionOrder.ORDER_CLOSED)

        # Items should have entered stock
        for p_item in order.produced_items:
            self.assertEqual(p_item.entered_stock, True)

        storable = item.product.storable
        self.assertEqual(storable.get_balance_for_branch(order.branch), 4)


class TestProductionService(DomainTest):
    def test_get_description(self):
        item = ProductionService(store=self.store)
        item.service = self.create_service()
        item.service.sellable.description = u'service'
        self.assertEquals(item.get_description(), u'service')

    def test_unit_description(self):
        item = ProductionService(store=self.store)
        item.service = self.create_service()
        item.service.sellable.unit = self.create_sellable_unit(description=u'un')
        self.assertEquals(item.unit_description, u'un')


class TestProductionProducedItem(DomainTest):
    def test_get_pending_tests(self):
        pitem = ProductionProducedItem(store=self.store)
        pitem.product = self.create_product()
        self.assertEquals(pitem.get_pending_tests(), [])

    def test_get_last_serial_number(self):
        pitem = ProductionProducedItem(store=self.store)
        pitem.product = self.create_product()
        last = ProductionProducedItem.get_last_serial_number(pitem.product,
                                                             self.store)
        self.assertEquals(last, 0)

        pitem.serial_number = 10
        last = ProductionProducedItem.get_last_serial_number(pitem.product,
                                                             self.store)
        self.assertEquals(last, 10)

    def test_is_valid_serial_range(self):
        pitem = ProductionProducedItem(store=self.store)
        pitem.product = self.create_product()
        self.assertTrue(ProductionProducedItem.is_valid_serial_range(
            pitem.product, 1, 2, self.store))
        pitem.serial_number = 1
        self.assertFalse(ProductionProducedItem.is_valid_serial_range(
            pitem.product, 1, 2, self.store))

    def test_send_to_stock(self):
        pitem = ProductionProducedItem(store=self.store)
        pitem.order = self.create_production_order()
        pitem.product = self.create_storable().product
        pitem.send_to_stock()

        self.assertTrue(
            self.store.find(StockTransactionHistory,
                            object_id=pitem.id,
                            type=StockTransactionHistory.TYPE_PRODUCTION_SENT).one())
        pitem.send_to_stock()
        self.assertTrue(
            self.store.find(StockTransactionHistory,
                            object_id=pitem.id,
                            type=StockTransactionHistory.TYPE_PRODUCTION_SENT).one())


class TestProductionItemQualityResult(DomainTest):
    def test_get_description(self):
        r = ProductionItemQualityResult(store=self.store)
        r.quality_test = ProductQualityTest(store=self.store,
                                            description=u'description')
        self.assertEquals(r.get_description(), u'description')

    def test_result_value_str(self):
        r = ProductionItemQualityResult(store=self.store)
        r.result_value = u'True'
        self.assertEquals(r.result_value_str, u'True')

    def test_get_boolean_value(self):
        r = ProductionItemQualityResult(store=self.store)

        r.result_value = u'True'
        self.assertEquals(r.get_boolean_value(), True)
        r.result_value = u'False'
        self.assertEquals(r.get_boolean_value(), False)
        r.result_value = u'broken'
        with self.assertRaises(ValueError):
            r.get_boolean_value()


class TestProductionOrderProducingView(DomainTest):
    def test_is_product_being_produced(self):
        order = self.create_production_order()
        production_item = self.create_production_item(order=order)
        product = production_item.product
        self.assertFalse(
            ProductionOrderProducingView.is_product_being_produced(product))

        order.start_production()
        self.assertTrue(
            ProductionOrderProducingView.is_product_being_produced(product))
