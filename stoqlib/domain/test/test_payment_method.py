# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007-2008 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import datetime
from decimal import Decimal

from stoqlib.database.runtime import get_current_station
from stoqlib.domain.interfaces import IInPayment, IOutPayment
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import (Payment,
                                            PaymentAdaptToInPayment,
                                            PaymentAdaptToOutPayment)
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.domain.till import Till
from stoqlib.exceptions import TillError
from stoqlib.lib.defaults import quantize


class _TestPaymentMethod:
    def createInPayment(self):
        sale = self.create_sale()
        method = PaymentMethod.get_by_name(self.trans, self.method_type)
        return method.create_inpayment(sale.group, Decimal(100))

    def createOutPayment(self):
        purchase = self.create_purchase_order()
        method = PaymentMethod.get_by_name(self.trans, self.method_type)
        return method.create_outpayment(purchase.group, Decimal(100))

    def createInPayments(self, no=3):
        sale = self.create_sale()
        d = datetime.datetime.today()
        method = PaymentMethod.get_by_name(self.trans, self.method_type)
        payments = method.create_inpayments(sale.group, Decimal(100),
                                            [d] * no)

        return [p.get_adapted() for p in payments]

    def createOutPayments(self, no=3):
        purchase = self.create_purchase_order()
        d = datetime.datetime.today()
        method = PaymentMethod.get_by_name(self.trans, self.method_type)
        payments = method.create_outpayments(purchase.group, Decimal(100),
                                             [d] * no)
        return [p.get_adapted() for p in payments]

    def createPayment(self, iface):
        if iface is IOutPayment:
            order = self.create_purchase_order()
        elif iface is IInPayment:
            order = self.create_sale()
        else:
            order = None

        value = Decimal(100)
        method = PaymentMethod.get_by_name(self.trans, self.method_type)
        return method.create_payment(iface, order.group, value)

    def createPayments(self, iface, no=3):
        if iface is IOutPayment:
            order = self.create_purchase_order()
        elif iface is IInPayment:
            order = self.create_sale()
        else:
            order = None

        value = Decimal(100)
        due_dates = [datetime.datetime.today()] * no
        method = PaymentMethod.get_by_name(self.trans, self.method_type)
        return method.create_payments(iface, order.group, value, due_dates)


class _TestPaymentMethodsBase(_TestPaymentMethod):
    def testCreateInPayment(self):
        payment = self.createInPayment()
        self.failUnless(isinstance(payment, PaymentAdaptToInPayment))
        payment = payment.get_adapted()
        self.failUnless(isinstance(payment, Payment))
        self.assertEqual(payment.value, Decimal(100))

    def testCreateOutPayment(self):
        payment = self.createOutPayment()
        self.failUnless(isinstance(payment, PaymentAdaptToOutPayment))
        payment = payment.get_adapted()
        self.failUnless(isinstance(payment, Payment))
        self.assertEqual(payment.value, Decimal(100))

    def testCreateInPayments(self):
        payments = self.createInPayments()
        athird = quantize(Decimal(100) / Decimal(3))
        rest = quantize(Decimal(100) - (athird * 2))
        self.assertEqual(len(payments), 3)
        self.assertEqual(payments[0].value, athird)
        self.assertEqual(payments[1].value, athird)
        self.assertEqual(payments[2].value, rest)

    def testCreateOutPayments(self):
        payments = self.createOutPayments()
        athird = quantize(Decimal(100) / Decimal(3))
        rest = quantize(Decimal(100) - (athird * 2))
        self.assertEqual(len(payments), 3)
        self.assertEqual(payments[0].value, athird)
        self.assertEqual(payments[1].value, athird)
        self.assertEqual(payments[2].value, rest)

    def testCreatePayment(self):
        inpayment = self.createPayment(IInPayment)
        self.failUnless(isinstance(inpayment, PaymentAdaptToInPayment))
        payment = inpayment.get_adapted()
        self.failUnless(isinstance(payment, Payment))
        self.assertEqual(payment.value, Decimal(100))

        outpayment = self.createPayment(IOutPayment)
        self.failUnless(isinstance(outpayment, PaymentAdaptToOutPayment))
        payment = outpayment.get_adapted()
        self.failUnless(isinstance(payment, Payment))
        self.assertEqual(payment.value, Decimal(100))

    def testCreatePayments(self):
        inpayments = self.createPayments(IInPayment)
        self.assertEqual(len(inpayments), 3)
        payments = [p.get_adapted() for p in inpayments]
        athird = quantize(Decimal(100) / Decimal(3))
        rest = quantize(Decimal(100) - (athird * 2))
        self.assertEqual(payments[0].value, athird)
        self.assertEqual(payments[1].value, athird)
        self.assertEqual(payments[2].value, rest)

        outpayments = self.createPayments(IOutPayment)
        self.assertEqual(len(outpayments), 3)
        payments = [p.get_adapted() for p in outpayments]
        athird = quantize(Decimal(100) / Decimal(3))
        rest = quantize(Decimal(100) - (athird * 2))
        self.assertEqual(payments[0].value, athird)
        self.assertEqual(payments[1].value, athird)
        self.assertEqual(payments[2].value, rest)

    def testDescribePayment(self):
        sale = self.create_sale()
        method = PaymentMethod.get_by_name(self.trans, self.method_type)
        desc = method.describe_payment(sale.group)
        self.failUnless(isinstance(desc, unicode))
        self.failUnless(method.description in desc)

        self.assertRaises(AssertionError, method.describe_payment, sale.group, 0)
        self.assertRaises(AssertionError, method.describe_payment, sale.group, 1, 0)
        self.assertRaises(AssertionError, method.describe_payment, sale.group, 2, 1)
        desc = method.describe_payment(sale.group, 123, 456)
        self.failUnless('123' in desc, desc)
        self.failUnless('456' in desc, desc)
        self.failUnless('123/456' in desc, desc)

    def testMaxInPaymnets(self):
        method = PaymentMethod.get_by_name(self.trans, self.method_type)
        max = method.max_installments
        self.assertRaises(ValueError, self.createInPayments, max + 1)

    def testMaxOutPaymnets(self):
        method = PaymentMethod.get_by_name(self.trans, self.method_type)
        self.createOutPayments(method.max_installments + 1)

    def testSelectable(self):
        method = PaymentMethod.get_by_name(self.trans, self.method_type)
        method.selectable()


class TestPaymentMethod(DomainTest, _TestPaymentMethod):
    method_type = 'check'

    def _createUnclosedTill(self):
        till = Till(station=get_current_station(self.trans),
                    connection=self.trans)
        till.open_till()
        yesterday = datetime.date.today() - datetime.timedelta(1)
        till.opening_date = yesterday

    def testCreateOutPaymentUnClosedTill(self):
        self._createUnclosedTill()
        payment = self.createOutPayment()
        self.failUnless(isinstance(payment, PaymentAdaptToOutPayment))

    def testCreateOutPaymentsUnClosedTill(self):
        # Test for bug 3270
        self._createUnclosedTill()
        self.createOutPayments()

    def testCreateInPaymentUnClosedTill(self):
        self._createUnclosedTill()
        self.assertRaises(TillError, self.createInPayment)

    def testCreateInPaymentsUnClosedTill(self):
        self._createUnclosedTill()
        self.assertRaises(TillError, self.createInPayments)

    def testCreatePaymentUnClosedTill(self):
        self._createUnclosedTill()
        self.assertRaises(TillError, self.createPayment, IInPayment)

        outpayment = self.createPayment(IOutPayment)
        self.failUnless(isinstance(outpayment, PaymentAdaptToOutPayment))

    def testCreatePaymentsUnClosedTill(self):
        self._createUnclosedTill()
        self.assertRaises(TillError, self.createPayments, IInPayment)

        outpayments = self.createPayments(IOutPayment)
        self.assertEqual(len(outpayments), 3)
        for i in range(3):
            self.failUnless(isinstance(outpayments[i],
                                       PaymentAdaptToOutPayment))


class TestMoney(DomainTest, _TestPaymentMethodsBase):
    method_type = 'money'

    def testCreateInPayments(self):
        pass

    def testCreateOutPayments(self):
        pass

    def testCreatePayments(self):
        pass


class TestCheck(DomainTest, _TestPaymentMethodsBase):
    method_type = 'check'

    def testCheckDataCreated(self):
        payment = self.createInPayment()
        method = PaymentMethod.get_by_name(self.trans, self.method_type)
        check_data = method.operation.get_check_data_by_payment(
            payment.get_adapted())
        self.failUnless(check_data)

    def testBank(self):
        sale = self.create_sale()
        method = PaymentMethod.get_by_name(self.trans, self.method_type)
        payment = method.create_outpayment(sale.group, Decimal(10))
        check_data = method.operation.get_check_data_by_payment(payment.get_adapted())
        check_data.bank_account.bank_number = 123
        self.assertEquals(payment.get_adapted().bank_account_number, 123)


class TestBill(DomainTest, _TestPaymentMethodsBase):
    method_type = 'bill'


class TestCard(DomainTest, _TestPaymentMethodsBase):
    method_type = 'card'

    def testCardData(self):
        payment = self.createInPayment()
        method = PaymentMethod.get_by_name(self.trans, self.method_type)
        card_data = method.operation.get_card_data_by_payment(
            payment.get_adapted())
        self.failUnless(card_data)


class TestDeposit(DomainTest, _TestPaymentMethodsBase):
    method_type = 'deposit'
