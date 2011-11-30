# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007-2009 Async Open Source <http://www.async.com.br>
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

""" This module test all class in stoq/domain/receiving.py """

from decimal import Decimal
from kiwi.datatypes import currency

from stoqlib.database.exceptions import IntegrityError
from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.product import ProductStockItem
from stoqlib.domain.interfaces import IStorable
from stoqlib.domain.test.domaintest import DomainTest


class TestReceivingOrder(DomainTest):

    def _testInvoiceNumber(self, value):
        order = self.create_receiving_order()
        try:
            order.invoice_number = value
        except IntegrityError, e:
            self.failUnless('valid_invoice_number' in e.pgerror)
        else:
            raise AssertionError

    def testInvoiceNumberLow(self):
        self._testInvoiceNumber(0)

    def testInvoiceNumberHigh(self):
        self._testInvoiceNumber(1000000)

    def testInvoiceNumberNegative(self):
        self._testInvoiceNumber(-1229)

    def testGetTotal(self):
        order = self.create_receiving_order()
        self.create_receiving_order_item(order)
        self.assertEqual(order.get_total(), currency(1000))

        order.discount_value = 10
        self.assertEqual(order.get_total(), currency(990))
        order.purchase.discount_value = 5
        self.assertEqual(order.get_total(), currency(985))
        order.purchase.surcharge_value = 8
        order.surcharge_value = 15
        self.assertEqual(order.get_total(), currency(1008))
        order.ipi_total = 10
        self.assertEqual(order.get_total(), currency(1018))
        order.freight_total = 6
        self.assertEqual(order.get_total(), currency(1024))
        order.secure_value = 6
        self.assertEqual(order.get_total(), currency(1030))
        order.expense_value = 12
        self.assertEqual(order.get_total(), currency(1042))

        order.purchase.status = order.purchase.ORDER_PENDING
        order.purchase.confirm()
        order.confirm()
        self.assertEqual(order.invoice_total, order.get_total())

    def testConfirm(self):
        order = self.create_receiving_order()
        order.quantity = 8
        order_item = self.create_receiving_order_item(order)
        order_item.quantity_received = 10
        self.assertRaises(ValueError, order.confirm)
        order_item.quantity_received = 8
        self.assertRaises(ValueError, order.confirm)
        self.assertRaises(ValueError, order.confirm)

        storable = IStorable(order_item.sellable.product)
        stock_item = storable.get_stock_item(branch=order.branch)
        for item in order.purchase.get_items():
            item.quantity_received = 0
        order.purchase.status = order.purchase.ORDER_PENDING
        self.assertEquals(stock_item.quantity, 8)
        order.purchase.confirm()
        order.confirm()
        installment_count = order.payments.count()
        for pay in order.payments:
            self.assertEqual(pay.value,
                order.get_total() / installment_count)
            self.assertEqual(pay.value,
                order.get_total() / installment_count)
        self.assertEqual(order.invoice_total, order.get_total())
        self.assertEquals(stock_item.quantity, 16)

    def testOrderReceiveSell(self):
        product = self.create_product()
        storable = product.addFacet(IStorable, connection=self.trans)
        self.failIf(ProductStockItem.selectOneBy(storable=storable,
                                                 connection=self.trans))
        purchase_order = self.create_purchase_order()
        purchase_item = purchase_order.add_item(product.sellable, 1)
        purchase_order.status = purchase_order.ORDER_PENDING
        method = PaymentMethod.get_by_name(self.trans, 'money')
        method.create_outpayment(purchase_order.group,
                                 purchase_order.get_purchase_total())
        purchase_order.confirm()

        receiving_order = self.create_receiving_order(purchase_order)
        receiving_order.branch = get_current_branch(self.trans)
        self.create_receiving_order_item(
            receiving_order=receiving_order,
            sellable=product.sellable,
            purchase_item=purchase_item,
            quantity=1)
        self.failIf(ProductStockItem.selectOneBy(storable=storable,
                                                 connection=self.trans))
        receiving_order.confirm()
        product_stock_item = ProductStockItem.selectOneBy(storable=storable,
                                                          connection=self.trans)
        self.failUnless(product_stock_item)
        self.assertEquals(product_stock_item.quantity, 1)

        sale = self.create_sale()
        sale.add_sellable(product.sellable)
        sale.order()
        method = PaymentMethod.get_by_name(self.trans, 'check')
        method.create_inpayment(sale.group, Decimal(100))
        sale.confirm()
        self.assertEquals(product_stock_item.quantity, 0)

    def testUpdatePaymentValues(self):
        order = self.create_receiving_order()
        self.create_receiving_order_item(order)
        self.assertEqual(order.get_total(), currency(1000))

        for item in order.purchase.get_items():
            item.quantity_received = 0
        order.purchase.status = order.purchase.ORDER_PENDING
        order.purchase.confirm()

        installment_count = order.payments.count()
        payment_dict = {}
        for pay in order.payments:
            self.assertEqual(pay.value,
                order.get_total() / installment_count)
            payment_dict[pay] = pay.value

        order.discount_value = 20
        order.surcharge_value = 100
        order.freight_total = 10
        order.secure_value = 15
        order.expense_value = 5
        order.update_payments()

        for pay in order.payments:
            self.assertEqual(pay.value, order.get_total() / installment_count)
            self.failIf(pay.value <= payment_dict[pay])

    def testUpdatePaymentValuesWithFreightPayment(self):
        order = self.create_receiving_order()
        self.create_receiving_order_item(order)
        self.assertEqual(order.get_total(), currency(1000))

        for item in order.purchase.get_items():
            item.quantity_received = 0
        order.purchase.status = order.purchase.ORDER_PENDING
        order.purchase.confirm()

        installment_count = order.payments.count()
        payment_dict = {}
        for pay in order.payments:
            self.assertEqual(pay.value,
                order.get_total() / installment_count)
            payment_dict[pay] = pay.value

        order.discount_value = 20
        order.surcharge_value = 100
        order.freight_total = 10
        order.secure_value = 15
        order.expense_value = 5
        order.update_payments(create_freight_payment=True)

        for pay in order.payments:
            if pay not in payment_dict.keys():
                self.assertEqual(pay.value, order.freight_total)
            else:
                self.failIf(pay.value <= payment_dict[pay])


class TestReceivingOrderItem(DomainTest):

    def testGetRemainingQuantity(self):
        order_item = self.create_receiving_order_item()
        self.assertEqual(order_item.get_remaining_quantity(), 8)
        self.assertNotEqual(order_item.get_remaining_quantity(), 4)
        self.assertNotEqual(order_item.get_remaining_quantity(), 5)
        self.assertNotEqual(order_item.get_remaining_quantity(), 18)
        self.assertNotEqual(order_item.get_remaining_quantity(), 0)

        order_item.purchase_item.quantity_received = 7
        self.assertEqual(order_item.get_remaining_quantity(), 1)
        self.assertNotEqual(order_item.get_remaining_quantity(), 5)
        self.assertNotEqual(order_item.get_remaining_quantity(), 8)

        order_item.purchase_item.quantity_received = 8
        self.assertEqual(order_item.get_remaining_quantity(), 0)
        self.assertNotEqual(order_item.get_remaining_quantity(), 1)
        self.assertNotEqual(order_item.get_remaining_quantity(), 8)
