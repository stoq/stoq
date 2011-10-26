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


from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.interfaces import IStorable
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.product import (ProductSupplierInfo, Product,
                                    ProductHistory, ProductComponent)
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
