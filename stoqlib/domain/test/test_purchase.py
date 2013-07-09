# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2009 Async Open Source <http://www.async.com.br>
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
""" This module test all class in stoq/domain/purchase.py """


from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.purchase import PurchaseOrder, QuoteGroup

from stoqlib.domain.test.domaintest import DomainTest


class TestPurchaseOrder(DomainTest):
    def test_confirm_order(self):
        order = self.create_purchase_order()
        self.assertRaises(ValueError, order.confirm)
        order.status = PurchaseOrder.ORDER_PENDING

        order.confirm()

    def test_close(self):
        order = self.create_purchase_order()
        self.assertRaises(ValueError, order.close)
        order.status = PurchaseOrder.ORDER_PENDING
        self.add_payments(order)
        order.confirm()

        payments = list(order.payments)
        self.failUnless(len(payments) > 0)

        for payment in payments:
            self.assertEqual(payment.status, Payment.STATUS_PENDING)

        order.close()
        self.assertEqual(order.status, PurchaseOrder.ORDER_CLOSED)

    def test_close_consigned(self):
        order = self.create_purchase_order()
        order.consigned = True
        order.status = PurchaseOrder.ORDER_PENDING
        order.set_consigned()
        self.failIf(order.can_close())

    def test_cancel_not_paid(self):
        order = self.create_purchase_order()
        self.assertRaises(ValueError, order.close)
        order.status = PurchaseOrder.ORDER_PENDING
        self.add_payments(order)
        order.confirm()

        payments = list(order.payments)
        self.failUnless(len(payments) > 0)

        for payment in payments:
            self.assertEqual(payment.status, Payment.STATUS_PENDING)

        order.cancel()
        self.assertEqual(order.status, PurchaseOrder.ORDER_CANCELLED)

        for payment in payments:
            self.assertEqual(payment.status, Payment.STATUS_CANCELLED)

    def test_remove_item(self):
        purchase_order = self.create_purchase_order()
        self.create_purchase_order_item(order=purchase_order)

        items = purchase_order.get_items()

        purchase_order.remove_item(items.one())

        items = purchase_order.get_items()

        self.assertFalse(items)

    def test_cancel_paid(self):
        order = self.create_purchase_order()
        self.assertRaises(ValueError, order.close)
        order.status = PurchaseOrder.ORDER_PENDING
        order.add_item(self.create_sellable(), 1)
        self.add_payments(order, method_type=u'money')
        order.confirm()

        payments = list(order.payments)
        payments_before_cancel = len(payments)
        self.failUnless(payments_before_cancel > 0)

        for payment in payments:
            payment.pay()
            self.assertEqual(payment.status, Payment.STATUS_PAID)

        total_paid = order.group.get_total_paid()

        order.cancel()
        self.assertEqual(order.status, PurchaseOrder.ORDER_CANCELLED)

        payments = list(order.payments)
        payments_after_cancel = len(payments)
        self.assertEqual(payments_after_cancel, payments_before_cancel + 1)

        for payment in payments:
            # Ok, paid payments of cancelled purchases remain paid...
            self.assertEqual(payment.status, Payment.STATUS_PAID)

            # ... but there is one payback.
            if payment.is_inpayment():
                self.assertEqual(payment.value, total_paid)

    def test_can_cancel_partial(self):
        order = self.create_purchase_order()
        self.assertEqual(order.can_cancel(), True)
        sellable = self.create_sellable()
        purchase_item = order.add_item(sellable, 2)
        order.receive_item(purchase_item, 1)
        self.assertEqual(order.can_cancel(), False)

    def test_can_cancel(self):
        order = self.create_purchase_order()
        self.assertEqual(order.can_cancel(), True)
        order.cancel()
        self.assertEqual(order.can_cancel(), False)
        sellable = self.create_sellable()
        order.add_item(sellable, 2)

    def test_confirm_supplier(self):
        order = self.create_purchase_order()
        self.assertRaises(ValueError, order.confirm)
        order.status = PurchaseOrder.ORDER_PENDING

        order.supplier = self.create_supplier()
        order.confirm()
        self.assertEquals(order.group.recipient, order.supplier.person)

    def test_is_paid(self):
        order = self.create_purchase_order()
        order.status = PurchaseOrder.ORDER_PENDING
        order.add_item(self.create_sellable(), 1)
        self.add_payments(order)
        order.confirm()

        self.assertEqual(order.is_paid(), False)

        for payment in order.payments:
            payment.pay()

        self.assertEqual(order.is_paid(), True)

    def test_account_transaction_check(self):
        order = self.create_purchase_order()
        order.status = PurchaseOrder.ORDER_PENDING
        order.add_item(self.create_sellable(), 1)
        payment = self.add_payments(order, method_type=u'check')[0]
        account = self.create_account()
        payment.method.destination_account = account
        self.assertTrue(account.transactions.is_empty())
        order.confirm()

        for payment in order.payments:
            payment.pay()

        self.assertFalse(account.transactions.is_empty())
        self.assertEquals(account.transactions.count(), order.payments.count())

        t = account.transactions[0]
        self.assertEquals(t.payment, payment)
        self.assertEquals(t.value, -payment.value)

    def test_account_transaction_money(self):
        order = self.create_purchase_order()
        order.status = PurchaseOrder.ORDER_PENDING
        order.add_item(self.create_sellable(), 1)
        payment = self.add_payments(order, method_type=u'money')[0]
        account = self.create_account()
        payment.method.destination_account = account
        self.assertTrue(account.transactions.is_empty())
        order.confirm()

        for payment in order.payments:
            payment.pay()

        self.assertFalse(account.transactions.is_empty())

    def test_payments(self):
        order = self.create_purchase_order()
        order.add_item(self.create_sellable(), 2)

        check_payment = self.add_payments(order, method_type=u'check')[0]
        self.assertEqual(order.payments.count(), 1)
        self.assertTrue(check_payment in order.payments)
        self.assertEqual(order.group.payments.count(), 1)
        self.assertTrue(check_payment in order.group.payments)

        check_payment.cancel()
        # Cancelled payments should not appear on order, just on group
        self.assertEqual(order.payments.count(), 0)
        self.assertFalse(check_payment in order.payments)
        self.assertEqual(order.group.payments.count(), 1)
        self.assertTrue(check_payment in order.group.payments)

        money_payment = self.add_payments(order, method_type=u'money')[0]
        self.assertEqual(order.payments.count(), 1)
        self.assertTrue(money_payment in order.payments)
        self.assertEqual(order.group.payments.count(), 2)
        self.assertTrue(money_payment in order.group.payments)

    def test_has_batch_item(self):
        order = self.create_purchase_order()
        order.add_item(self.create_sellable(), 3)
        self.assertFalse(order.has_batch_item())

        sellable = self.create_sellable()
        product = self.create_product()
        storable = self.create_storable(is_batch=True)
        storable.product = product
        sellable.product = product

        order = self.create_purchase_order()
        order.add_item(sellable, 2)
        self.assertTrue(order.has_batch_item())

        order = self.create_purchase_order()
        order.add_item(self.create_sellable(), 3)
        order.add_item(sellable, 2)
        self.assertTrue(order.has_batch_item())


class TestQuoteGroup(DomainTest):

    def test_cancel(self):
        order = self.create_purchase_order()
        quote = QuoteGroup(store=self.store, branch=order.branch)
        order.status = PurchaseOrder.ORDER_QUOTING
        quote.add_item(order)

        self.assertEqual(order.status, PurchaseOrder.ORDER_QUOTING)
        order.cancel()
        self.assertEqual(order.status, PurchaseOrder.ORDER_CANCELLED)

    def test_close(self):
        order = self.create_purchase_order()
        quote = QuoteGroup(store=self.store, branch=order.branch)
        order.status = PurchaseOrder.ORDER_QUOTING
        quote.add_item(order)

        self.assertEqual(order.status, PurchaseOrder.ORDER_QUOTING)
        quotations = quote.get_items()
        self.assertEqual(quotations.count(), 1)

        self.assertFalse(quotations[0].is_closed())
        quotations[0].close()
        self.assertTrue(quotations[0].is_closed())

        self.assertEqual(order.status, PurchaseOrder.ORDER_CANCELLED)

    def test_remove_item(self):
        order = self.create_purchase_order()
        quote = QuoteGroup(store=self.store, branch=order.branch)
        order.status = PurchaseOrder.ORDER_QUOTING
        quote.add_item(order)

        items = quote.get_items()
        item = items.one()
        self.assertEquals(item.purchase, order)

        quote.remove_item(item)
        items = quote.get_items()
        self.assertFalse(items)
