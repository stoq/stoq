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
## Author(s):   Grazieno Pellegrino         <grazieno1@yahoo.com.br>
##              Evandro Vale Miquelito      <evandro@async.com.br>
##              Johan Dahlin                <jdahlin@async.com.br>
##              Fabio Morbec                <fabio@async.com.br>
##
""" This module test all class in stoqlib/domain/product.py """


from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.interfaces import IStorable
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.renegotiation import PaymentRenegotiation
from stoqlib.domain.product import (ProductSupplierInfo, Product,
                                    ProductHistory, ProductComponent,
                                    ProductRetentionHistory)
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.domain.sellable import BaseSellableInfo, Sellable

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

        component1 = self.create_product()
        sellable1 = component1.sellable
        sellable1.cost = 100
        production_cost += sellable1.cost
        product_component = ProductComponent(product=product,
                                             component=component1,
                                             connection=self.trans)
        self.assertEqual(product.get_production_cost(), production_cost)

        product_component.quantity = 3
        # one component1 is already in product_cost
        production_cost += (sellable1.cost * 2)
        self.assertEqual(product.get_production_cost(), production_cost)

        component2 = self.create_product()
        sellable2 = component2.sellable
        sellable2.cost = 10
        ProductComponent(product=component1, component=component2,
                         connection=self.trans)
        component1_production = sellable1.cost + sellable2.cost
        self.assertEqual(component1.get_production_cost(),
                         component1_production)

        # times three, because product is composed by 3 items of
        # component1
        production_cost += (sellable2.cost * 3)
        self.assertEqual(product.get_production_cost(), production_cost)

        ProductComponent(product=product, component=component2,
                         connection=self.trans)
        production_cost += sellable2.cost
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

        self.assertEqual(product.is_supplied_by(supplier), True)

    def test_can_remove(self):
        product = self.create_product()
        storable = product.addFacet(IStorable, connection=self.trans)
        self.assertTrue(product.can_remove())

        storable.increase_stock(1, get_current_branch(self.trans))
        self.assertFalse(product.can_remove())

        sale = self.create_sale()
        sale.add_sellable(product.sellable, quantity=1, price=10)

        method = PaymentMethod.get_by_name(self.trans, 'money')
        method.create_inpayment(sale.group, sale.get_sale_subtotal())

        sale.order()
        sale.confirm()

        self.assertFalse(product.can_remove())

    def test_remove(self):
        product = self.create_product()
        storable = product.addFacet(IStorable, connection=self.trans)
        product_id = product.id

        total = Product.selectBy(id=product_id, connection=self.trans).count()
        self.assertEquals(total, 1)

        product.remove()
        total = Product.selectBy(id=product_id, connection=self.trans).count()
        self.assertEquals(total, 0)


    def test_increase_decrease_stock(self):
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


class TestProductSellableItem(DomainTest):

    def testSell(self):
        sale = self.create_sale()
        base_sellable_info = BaseSellableInfo(connection=self.trans)
        sellable = Sellable(barcode='xyz',
                            base_sellable_info=base_sellable_info,
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
        order_item.receiving_order.set_valid()
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

    def testAddRetainedQuantity(self):
        sellable = self.create_sellable()
        sellable.status = Sellable.STATUS_AVAILABLE
        product = sellable.product
        storable = product.addFacet(IStorable, connection=self.trans)
        storable.increase_stock(10, get_current_branch(self.trans))
        self.failIf(ProductHistory.selectOneBy(connection=self.trans,
                                               sellable=sellable))

        retained_qty = 4
        retained = self.create_retained_product(product, retained_qty)
        self.assertEqual(sellable, retained.product.sellable)
        prod_hist = ProductHistory.selectOneBy(connection=self.trans,
                                               sellable=sellable)
        self.failUnless(prod_hist)
        self.assertEqual(prod_hist.quantity_retained, retained_qty)


class TestProductRetentionHistory(DomainTest):

    def testCancelRetention(self):
        sellable = self.create_sellable()
        sellable.status = Sellable.STATUS_AVAILABLE
        product = sellable.product
        storable = product.addFacet(IStorable, connection=self.trans)
        branch = get_current_branch(self.trans)
        quantity = 10
        storable.increase_stock(quantity, branch)
        retained_quantity = 3
        retained = self.create_retained_product(product, retained_quantity)
        history_entry = ProductRetentionHistory.selectOneBy(product=product,
            quantity=retained_quantity, connection=self.trans)

        self.failIf(history_entry is None)
        self.assertEqual(storable.get_full_balance(branch),
                         quantity - retained_quantity)

        retained.cancel_retention(branch)
        history_entry = ProductRetentionHistory.selectOneBy(product=product,
            quantity=retained_quantity, connection=self.trans)

        self.failUnless(history_entry is None)
        self.assertEqual(storable.get_full_balance(branch), quantity)
