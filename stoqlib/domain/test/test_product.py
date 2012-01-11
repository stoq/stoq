# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2007 Async Open Source <http://www.async.com.br>
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
""" This module test all class in stoqlib/domain/product.py """

import decimal

from stoqlib.database.runtime import get_current_branch, new_transaction
from stoqlib.domain.events import (ProductCreateEvent, ProductEditEvent,
                                   ProductRemoveEvent)
from stoqlib.domain.interfaces import IStorable
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.product import (ProductSupplierInfo, Product,
                                    ProductHistory, ProductComponent)
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.domain.sellable import Sellable

from stoqlib.domain.test.domaintest import DomainTest


class TestProductSupplierInfo(DomainTest):

    def testGetName(self):
        product = self.create_product()
        supplier = self.create_supplier()
        info = ProductSupplierInfo(connection=self.trans,
                                   product=product,
                                   supplier=supplier)
        self.assertEqual(info.get_name(), supplier.get_description())

    def testDefaultLeadTimeValue(self):
        product = self.create_product()
        supplier = self.create_supplier()
        info = ProductSupplierInfo(connection=self.trans,
                                   product=product,
                                   supplier=supplier)
        default_lead_time = 1
        self.assertEqual(info.lead_time, default_lead_time)


class _ProductEventData(object):

    def __init__(self):
        self.reset()

    def reset(self):
        self.product = None
        self.emmit_count = 0
        self.was_created = False
        self.was_edited = False
        self.was_deleted = False

    def on_create(self, product, **kwargs):
        self.product = product
        self.was_created = True
        self.emmit_count += 1

    def on_edit(self, product, **kwargs):
        self.product = product
        self.was_edited = True
        self.emmit_count += 1

    def on_delete(self, product, **kwargs):
        self.product = product
        self.was_deleted = True
        self.emmit_count += 1


class TestProduct(DomainTest):

    def setUp(self):
        DomainTest.setUp(self)
        sellable = self.create_sellable()
        self.product = Product(sellable=sellable,
                               connection=self.trans)

    def test_get_main_supplier_info(self):
        self.failIf(self.product.get_main_supplier_info())
        supplier = self.create_supplier()
        ProductSupplierInfo(connection=self.trans, supplier=supplier,
                            product=self.product, is_main_supplier=True)
        self.failUnless(self.product.get_main_supplier_info())

    def testGetComponents(self):
        self.assertEqual(list(self.product.get_components()), [])

        components = []
        for i in range(3):
            component = self.create_product()
            product_component = ProductComponent(product=self.product,
                                                 component=component,
                                                 connection=self.trans)
            components.append(product_component)
        self.assertEqual(list(self.product.get_components()),
                        components)

    def testHasComponents(self):
        self.assertFalse(self.product.has_components())

        component = self.create_product()
        ProductComponent(product=self.product,
                         component=component,
                         connection=self.trans)
        self.assertTrue(self.product.has_components())

    def testGetProductionCost(self):
        product = self.create_product()
        sellable = product.sellable
        sellable.cost = 50
        production_cost = sellable.cost
        self.assertEqual(product.get_production_cost(), production_cost)

    def testIsComposedBy(self):
        component = self.create_product()
        self.assertEqual(self.product.is_composed_by(component), False)

        ProductComponent(product=self.product, component=component,
                         connection=self.trans)
        self.assertEqual(self.product.is_composed_by(component), True)

        component2 = self.create_product()
        ProductComponent(product=component, component=component2,
                         connection=self.trans)
        self.assertEqual(self.product.is_composed_by(component2), True)
        self.assertEqual(component.is_composed_by(component2), True)

        component3 = self.create_product()
        ProductComponent(product=self.product, component=component3,
                         connection=self.trans)
        self.assertEqual(self.product.is_composed_by(component3), True)
        self.assertEqual(component.is_composed_by(component3), False)
        self.assertEqual(component2.is_composed_by(component3), False)

    def testSuppliers(self):
        product = self.create_product()
        supplier = self.create_supplier()

        info = ProductSupplierInfo(connection=self.trans,
                                   product=product,
                                   supplier=supplier)

        suppliers = list(product.get_suppliers_info())

        # self.create_product already adds a supplier. so here we must have 2
        self.assertEqual(len(suppliers), 2)
        self.assertEqual(info in suppliers, True)

        # product.suppliers should behave just like get_suppliers_info()
        self.assertEqual(len(list(product.suppliers)), 2)
        self.assertEqual(info in product.suppliers, True)

        self.assertEqual(product.is_supplied_by(supplier), True)

    def testCanRemove(self):
        product = self.create_product()
        storable = product.addFacet(IStorable, connection=self.trans)
        self.assertTrue(product.can_remove())

        storable.increase_stock(1, get_current_branch(self.trans))
        self.assertFalse(product.can_remove())

        # Product was sold.
        sale = self.create_sale()
        sale.add_sellable(product.sellable, quantity=1, price=10)

        method = PaymentMethod.get_by_name(self.trans, 'money')
        method.create_inpayment(sale.group, sale.get_sale_subtotal())

        sale.order()
        sale.confirm()

        self.assertFalse(product.can_remove())

        # Product is a component.
        from stoqlib.domain.product import ProductComponent
        product = self.create_product(10)
        component = self.create_product(5)
        component.addFacet(IStorable, connection=self.trans)
        self.assertTrue(component.can_remove())

        ProductComponent(product=product,
                         component=component,
                         connection=self.trans)

        self.assertFalse(component.can_remove())

        # Product is used in a production.
        from stoqlib.domain.production import ProductionItem
        product = self.create_product()
        storable = product.addFacet(IStorable, connection=self.trans)
        self.assertTrue(product.can_remove())
        order = self.create_production_order()
        ProductionItem(product=product,
                       order=order,
                       quantity=1,
                       connection=self.trans)

        self.assertFalse(product.can_remove())

    def testRemove(self):
        product = self.create_product()
        product.addFacet(IStorable, connection=self.trans)

        total = Product.selectBy(id=product.id, connection=self.trans).count()
        self.assertEquals(total, 1)

        product.remove()
        total = Product.selectBy(id=product.id, connection=self.trans).count()
        self.assertEquals(total, 0)

    def testIncreaseDecreaseStock(self):
        branch = get_current_branch(self.trans)
        product = self.create_product()
        storable = product.addFacet(IStorable, connection=self.trans)
        stock_item = storable.get_stock_item(branch)
        self.failIf(stock_item is not None)

        storable.increase_stock(1, branch)
        stock_item = storable.get_stock_item(branch)
        self.assertEquals(stock_item.stock_cost, 0)

        storable.increase_stock(1, branch, unit_cost=10)
        stock_item = storable.get_stock_item(branch)
        self.assertEquals(stock_item.stock_cost, 5)

        stock_item = storable.decrease_stock(1, branch)
        self.assertEquals(stock_item.stock_cost, 5)

        storable.increase_stock(1, branch)
        stock_item = storable.get_stock_item(branch)
        self.assertEquals(stock_item.stock_cost, 5)

        storable.increase_stock(2, branch, unit_cost=15)
        stock_item = storable.get_stock_item(branch)
        self.assertEquals(stock_item.stock_cost, 10)

    def test_lead_time(self):
        product = self.create_product()
        product.addFacet(IStorable, connection=self.trans)
        branch = get_current_branch(self.trans)
        #storable.increase_stock(1, get_current_branch(self.trans))

        supplier1 = self.create_supplier()
        ProductSupplierInfo(connection=self.trans, product=product,
                            supplier=supplier1, lead_time=10)

        self.assertEqual(product.get_max_lead_time(1, branch), 10)

        supplier2 = self.create_supplier()
        ProductSupplierInfo(connection=self.trans, product=product,
                            supplier=supplier2, lead_time=20)
        self.assertEqual(product.get_max_lead_time(1, branch), 20)

        # Now for composed products
        product = self.create_product(create_supplier=False)
        product.is_composed = True
        product.production_time = 5
        product.addFacet(IStorable, connection=self.trans)

        component = self.create_product(create_supplier=False)
        component.addFacet(IStorable, connection=self.trans)
        ProductSupplierInfo(connection=self.trans, product=component,
                            supplier=supplier1, lead_time=7)
        self.assertEqual(component.get_max_lead_time(1, branch), 7)

        pc = ProductComponent(product=product, component=component, quantity=1,
                         connection=self.trans)

        self.assertEqual(product.get_max_lead_time(1, branch), 12)

        # Increase the component stock
        IStorable(component).increase_stock(1, branch)

        self.assertEqual(product.get_max_lead_time(1, branch), 5)

        # Increase the quantity required:
        pc.quantity = 2
        self.assertEqual(product.get_max_lead_time(1, branch), 12)


class TestProductSellableItem(DomainTest):

    def testSell(self):
        sale = self.create_sale()
        sellable = Sellable(barcode='xyz',
                            connection=self.trans)
        product = Product(sellable=sellable, connection=self.trans)
        sale_item = sale.add_sellable(product.sellable)
        storable = product.addFacet(IStorable, connection=self.trans)

        branch = get_current_branch(self.trans)
        storable.increase_stock(2, branch)
        stock_item = storable.get_stock_item(branch)
        assert stock_item is not None
        current_stock = stock_item.quantity
        if current_stock:
            storable.decrease_stock(current_stock, branch)
        assert not storable.get_stock_item(branch).quantity
        sold_qty = 2
        storable.increase_stock(sold_qty, branch)
        assert storable.get_stock_item(branch) is not None
        assert storable.get_stock_item(branch).quantity == sold_qty
        # now setting the proper sold quantity in the sellable item
        sale_item.quantity = sold_qty
        sale_item.sell(branch)
        assert not storable.get_stock_item(branch).quantity


class TestProductHistory(DomainTest):

    def testAddReceivedQuantity(self):
        order_item = self.create_receiving_order_item()
        order_item.receiving_order.purchase.status = PurchaseOrder.ORDER_PENDING
        order_item.receiving_order.purchase.confirm()
        self.failIf(
            ProductHistory.selectOneBy(connection=self.trans,
                                       sellable=order_item.sellable))
        order_item.receiving_order.confirm()
        prod_hist = ProductHistory.selectOneBy(connection=self.trans,
                                               sellable=order_item.sellable)
        self.failUnless(prod_hist)
        self.assertEqual(prod_hist.quantity_received,
                         order_item.quantity)

    def testAddSoldQuantity(self):
        sale = self.create_sale()
        sellable = self.create_sellable()
        sellable.status = Sellable.STATUS_AVAILABLE
        product = sellable.product
        storable = product.addFacet(IStorable, connection=self.trans)
        storable.increase_stock(100, get_current_branch(self.trans))
        sale_item = sale.add_sellable(sellable, quantity=5)

        method = PaymentMethod.get_by_name(self.trans, 'money')
        method.create_inpayment(sale.group, sale.get_sale_subtotal())

        self.failIf(ProductHistory.selectOneBy(connection=self.trans,
                                               sellable=sellable))
        sale.order()
        sale.confirm()
        prod_hist = ProductHistory.selectOneBy(connection=self.trans,
                                               sellable=sellable)
        self.failUnless(prod_hist)
        self.assertEqual(prod_hist.quantity_sold, 5)
        self.assertEqual(prod_hist.quantity_sold,
                         sale_item.quantity)

    def testAddTransferedQuantity(self):
        qty = 10
        order = self.create_transfer_order()
        transfer_item = self.create_transfer_order_item(order, quantity=qty)
        self.failIf(ProductHistory.selectOneBy(
                    connection=self.trans, sellable=transfer_item.sellable))

        order.send_item(transfer_item)
        order.receive()
        prod_hist = ProductHistory.selectOneBy(connection=self.trans,
                                               sellable=transfer_item.sellable)
        self.failUnless(prod_hist)
        self.assertEqual(prod_hist.quantity_transfered, qty)


from stoqlib.domain.product import ProductQualityTest
from decimal import Decimal


class TestProductQuality(DomainTest):

    def test_quality_tests(self):
        product = self.create_product()
        product.addFacet(IStorable, connection=self.trans)

        # There are still no tests for this product
        self.assertEqual(product.quality_tests.count(), 0)

        test1 = ProductQualityTest(connection=self.trans, product=product,
                                   test_type=ProductQualityTest.TYPE_BOOLEAN,
                                   success_value='True')
        # Now there sould be one
        self.assertEqual(product.quality_tests.count(), 1)
        # and it should be the one we created
        self.assertTrue(test1 in product.quality_tests)

        # Different product
        product2 = self.create_product()
        product2.addFacet(IStorable, connection=self.trans)

        # With different test
        test2 = ProductQualityTest(connection=self.trans, product=product2,
                                   test_type=ProductQualityTest.TYPE_BOOLEAN,
                                   success_value='True')

        # First product still should have only one
        self.assertEqual(product.quality_tests.count(), 1)
        # And it should not be the second test.
        self.assertTrue(test2 not in product.quality_tests)

    def test_boolean_value(self):
        product = self.create_product()
        bool_test = ProductQualityTest(connection=self.trans, product=product,
                                   test_type=ProductQualityTest.TYPE_BOOLEAN)
        bool_test.set_boolean_value(True)
        self.assertEqual(bool_test.get_boolean_value(), True)
        self.assertTrue(bool_test.result_value_passes(True))
        self.assertFalse(bool_test.result_value_passes(False))

        bool_test.set_boolean_value(False)
        self.assertEqual(bool_test.get_boolean_value(), False)
        self.assertTrue(bool_test.result_value_passes(False))
        self.assertFalse(bool_test.result_value_passes(True))

        self.assertRaises(AssertionError, bool_test.get_range_value)

    def test_decimal_value(self):
        product = self.create_product()
        test = ProductQualityTest(connection=self.trans, product=product,
                                   test_type=ProductQualityTest.TYPE_DECIMAL)
        test.set_range_value(Decimal(10), Decimal(20))
        self.assertEqual(test.get_range_value(), (Decimal(10), Decimal(20)))

        self.assertFalse(test.result_value_passes(Decimal(9.99)))
        self.assertTrue(test.result_value_passes(Decimal(10)))
        self.assertTrue(test.result_value_passes(Decimal(15)))
        self.assertTrue(test.result_value_passes(Decimal(20)))
        self.assertFalse(test.result_value_passes(Decimal(20.0001)))
        self.assertFalse(test.result_value_passes(Decimal(30)))

        test.set_range_value(Decimal(30), Decimal(40))
        self.assertEqual(test.get_range_value(), (Decimal(30), Decimal(40)))
        self.assertTrue(test.result_value_passes(Decimal(30)))

        # Negative values
        test.set_range_value(Decimal(-5), Decimal(5))
        self.assertEqual(test.get_range_value(), (Decimal(-5), Decimal(5)))

        self.assertRaises(AssertionError, test.get_boolean_value)


class TestProductEvent(DomainTest):
    def testCreateEvent(self):
        trans_list = []
        p_data = _ProductEventData()
        ProductCreateEvent.connect(p_data.on_create)
        ProductEditEvent.connect(p_data.on_edit)
        ProductRemoveEvent.connect(p_data.on_delete)

        # Test product being created
        trans = new_transaction()
        trans_list.append(trans)
        sellable = Sellable(
            connection=trans,
            description='Test 1234',
            price=decimal.Decimal(2),
            )
        product = Product(
            connection=trans,
            sellable=sellable,
            )
        trans.commit()
        self.assertTrue(p_data.was_created)
        self.assertFalse(p_data.was_edited)
        self.assertFalse(p_data.was_deleted)
        self.assertEqual(p_data.product, product)
        p_data.reset()

        # Test product being edited and emmiting the event just once
        trans = new_transaction()
        trans_list.append(trans)
        sellable = trans.get(sellable)
        product = trans.get(product)
        sellable.notes = 'Notes'
        sellable.description = 'Test 666'
        product.weight = decimal.Decimal(10)
        trans.commit()
        self.assertTrue(p_data.was_edited)
        self.assertFalse(p_data.was_created)
        self.assertFalse(p_data.was_deleted)
        self.assertEqual(p_data.product, product)
        self.assertEqual(p_data.emmit_count, 1)
        p_data.reset()

        # Test product being edited, editing Sellable
        trans = new_transaction()
        trans_list.append(trans)
        sellable = trans.get(sellable)
        product = trans.get(product)
        sellable.notes = 'Notes for test'
        trans.commit()
        self.assertTrue(p_data.was_edited)
        self.assertFalse(p_data.was_created)
        self.assertFalse(p_data.was_deleted)
        self.assertEqual(p_data.product, product)
        self.assertEqual(p_data.emmit_count, 1)
        p_data.reset()

        # Test product being edited, editing Product itself
        trans = new_transaction()
        trans_list.append(trans)
        sellable = trans.get(sellable)
        product = trans.get(product)
        product.weight = decimal.Decimal(1)
        trans.commit()
        self.assertTrue(p_data.was_edited)
        self.assertFalse(p_data.was_created)
        self.assertFalse(p_data.was_deleted)
        self.assertEqual(p_data.product, product)
        self.assertEqual(p_data.emmit_count, 1)
        p_data.reset()

        # Test product being edited, editing Product itself
        trans = new_transaction()
        trans_list.append(trans)
        sellable = trans.get(sellable)
        product = trans.get(product)
        product.weight = decimal.Decimal(1)
        trans.commit()
        self.assertTrue(p_data.was_edited)
        self.assertFalse(p_data.was_created)
        self.assertFalse(p_data.was_deleted)
        self.assertEqual(p_data.product, product)
        self.assertEqual(p_data.emmit_count, 1)
        p_data.reset()

        # Test product being removed
        trans = new_transaction()
        trans_list.append(trans)
        sellable = trans.get(sellable)
        product = trans.get(product)
        sellable.remove()
        trans.commit()
        self.assertTrue(p_data.was_deleted)
        self.assertFalse(p_data.was_created)
        self.assertFalse(p_data.was_edited)
        self.assertEqual(p_data.product, product)
        self.assertEqual(p_data.emmit_count, 1)
        p_data.reset()

        for trans in trans_list:
            trans.close()
