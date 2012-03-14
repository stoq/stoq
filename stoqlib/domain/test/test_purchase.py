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
    def testConfirmOrder(self):
        order = self.create_purchase_order()
        self.assertRaises(ValueError, order.confirm)
        order.status = PurchaseOrder.ORDER_PENDING

        order.confirm()

    def testClose(self):
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

    def testCloseConsigned(self):
        order = self.create_purchase_order()
        order.consigned = True
        order.status = PurchaseOrder.ORDER_PENDING
        order.set_consigned()
        self.failIf(order.can_close())

    def testCancelNotPaid(self):
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

    def testCancelPaid(self):
        order = self.create_purchase_order()
        self.assertRaises(ValueError, order.close)
        order.status = PurchaseOrder.ORDER_PENDING
        order.add_item(self.create_sellable(), 1)
        self.add_payments(order, method_type='money')
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

    def testCanCancelPartial(self):
        order = self.create_purchase_order()
        self.assertEqual(order.can_cancel(), True)
        sellable = self.create_sellable()
        purchase_item = order.add_item(sellable, 2)
        order.receive_item(purchase_item, 1)
        self.assertEqual(order.can_cancel(), False)

    def testCanCancel(self):
        order = self.create_purchase_order()
        self.assertEqual(order.can_cancel(), True)
        order.cancel()
        self.assertEqual(order.can_cancel(), False)
        sellable = self.create_sellable()
        order.add_item(sellable, 2)

    def testConfirmSupplier(self):
        order = self.create_purchase_order()
        self.assertRaises(ValueError, order.confirm)
        order.status = PurchaseOrder.ORDER_PENDING

        order.supplier = self.create_supplier()
        order.confirm()
        self.assertEquals(order.group.recipient, order.supplier.person)

    def testIsPaid(self):
        order = self.create_purchase_order()
        order.status = PurchaseOrder.ORDER_PENDING
        order.add_item(self.create_sellable(), 1)
        self.add_payments(order)
        order.confirm()

        self.assertEqual(order.is_paid(), False)

        for payment in order.payments:
            payment.pay()

        self.assertEqual(order.is_paid(), True)

    def testAccountTransactionCheck(self):
        order = self.create_purchase_order()
        order.status = PurchaseOrder.ORDER_PENDING
        order.add_item(self.create_sellable(), 1)
        payment = self.add_payments(order, method_type='check')
        account = self.create_account()
        payment.method.destination_account = account
        self.failIf(account.transactions)
        order.confirm()

        for payment in order.payments:
            payment.pay()

        self.failUnless(account.transactions)
        self.assertEquals(account.transactions.count(), order.payments.count())

        t = account.transactions[0]
        self.assertEquals(t.payment, payment)
        self.assertEquals(t.value, -payment.value)

    def testAccountTransactionMoney(self):
        order = self.create_purchase_order()
        order.status = PurchaseOrder.ORDER_PENDING
        order.add_item(self.create_sellable(), 1)
        payment = self.add_payments(order, method_type='money')
        account = self.create_account()
        payment.method.destination_account = account
        self.failIf(account.transactions)
        order.confirm()

        for payment in order.payments:
            payment.pay()

        self.failIf(account.transactions)

    def testPayments(self):
        order = self.create_purchase_order()
        order.add_item(self.create_sellable(), 2)

        check_payment = self.add_payments(order, method_type='check')
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

        money_payment = self.add_payments(order, method_type='money')
        self.assertEqual(order.payments.count(), 1)
        self.assertTrue(money_payment in order.payments)
        self.assertEqual(order.group.payments.count(), 2)
        self.assertTrue(money_payment in order.group.payments)


class TestQuoteGroup(DomainTest):

    def testCancel(self):
        quote = QuoteGroup(connection=self.trans)
        order = self.create_purchase_order()
        order.status = PurchaseOrder.ORDER_QUOTING
        quote.add_item(order)

        self.assertEqual(order.status, PurchaseOrder.ORDER_QUOTING)
        order.cancel()
        self.assertEqual(order.status, PurchaseOrder.ORDER_CANCELLED)

    def testClose(self):
        quote = QuoteGroup(connection=self.trans)
        order = self.create_purchase_order()
        order.status = PurchaseOrder.ORDER_QUOTING
        quote.add_item(order)

        self.assertEqual(order.status, PurchaseOrder.ORDER_QUOTING)
        quotations = quote.get_items()
        self.assertEqual(quotations.count(), 1)

        self.assertFalse(quotations[0].is_closed())
        quotations[0].close()
        self.assertTrue(quotations[0].is_closed())

        self.assertEqual(order.status, PurchaseOrder.ORDER_CANCELLED)
