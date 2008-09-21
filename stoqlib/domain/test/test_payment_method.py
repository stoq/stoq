# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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
## Author(s):     Johan Dahlin <jdahlin@async.com.br>
##

import datetime
from decimal import Decimal

from stoqdrivers.enum import PaymentMethodType

from stoqlib.database.runtime import get_current_station
from stoqlib.domain.interfaces import IPaymentGroup, IInPayment, IOutPayment
from stoqlib.domain.payment.methods import (APaymentMethod,
                                            BillPM, CheckPM, FinancePM,
                                            PaymentMethodDetails,
                                            MoneyPM, GiftCertificatePM)
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
        group = sale.addFacet(IPaymentGroup,
                              connection=self.trans)

        method = self.method_type.selectOne(connection=self.trans)
        return method.create_inpayment(group, Decimal(100))

    def createOutPayment(self):
        purchase = self.create_purchase_order()
        group = IPaymentGroup(purchase)

        method = self.method_type.selectOne(connection=self.trans)
        return method.create_outpayment(group, Decimal(100))

    def createInPayments(self, no=3):
        sale = self.create_sale()
        group = sale.addFacet(IPaymentGroup,
                              connection=self.trans)

        d = datetime.datetime.today()
        method = self.method_type.selectOne(connection=self.trans)
        payments = method.create_inpayments(group, Decimal(100),
                                            [d] * no)

        return [p.get_adapted() for p in payments]

    def createOutPayments(self, no=3):
        purchase = self.create_purchase_order()
        group = IPaymentGroup(purchase)

        d = datetime.datetime.today()
        method = self.method_type.selectOne(connection=self.trans)
        payments = method.create_outpayments(group, Decimal(100),
                                             [d] * no)
        return [p.get_adapted() for p in payments]

    def createPayment(self, iface):
        if iface is IOutPayment:
            order = self.create_purchase_order()
        elif iface is IInPayment:
            order = self.create_sale()
            order.addFacet(IPaymentGroup, connection=self.trans)
        else:
            order = None

        group = IPaymentGroup(order)
        value = Decimal(100)
        method = self.method_type.selectOne(connection=self.trans)
        return method.create_payment(iface, group, value)

    def createPayments(self, iface, no=3):
        if iface is IOutPayment:
            order = self.create_purchase_order()
        elif iface is IInPayment:
            order = self.create_sale()
            order.addFacet(IPaymentGroup, connection=self.trans)
        else:
            order = None

        group = IPaymentGroup(order)
        value = Decimal(100)
        due_dates = [datetime.datetime.today()] * no
        method = self.method_type.selectOne(connection=self.trans)
        return method.create_payments(iface, group, value, due_dates)

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
        if self.method_type in (MoneyPM, GiftCertificatePM):
            return

        payments = self.createInPayments()
        athird = quantize(Decimal(100) / Decimal(3))
        rest = quantize(Decimal(100) - (athird * 2))
        self.assertEqual(len(payments), 3)
        self.assertEqual(payments[0].value, athird)
        self.assertEqual(payments[1].value, athird)
        self.assertEqual(payments[2].value, rest)

    def testCreateOutPayments(self):
        if self.method_type in (MoneyPM, GiftCertificatePM):
            return

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
        if self.method_type in (MoneyPM, GiftCertificatePM):
            return

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
        group = sale.addFacet(IPaymentGroup,
                              connection=self.trans)
        method = self.method_type.selectOne(connection=self.trans)
        desc = method.describe_payment(group)
        self.failUnless(isinstance(desc, unicode))
        self.failUnless(self.method_type.description in desc)

        self.assertRaises(AssertionError, method.describe_payment, group, 0)
        self.assertRaises(AssertionError, method.describe_payment, group, 1, 0)
        self.assertRaises(AssertionError, method.describe_payment, group, 2, 1)
        desc = method.describe_payment(group, 123, 456)
        self.failUnless('123' in desc, desc)
        self.failUnless('456' in desc, desc)
        self.failUnless('123/456' in desc, desc)

    def testGetByEnum(self):
        self.assertEqual(APaymentMethod.get_by_enum(self.trans,
                                                    self.enum),
                         self.method_type.selectOne(connection=self.trans))


    def testMaxInPaymnets(self):
        method = self.method_type.selectOne(connection=self.trans)
        max = method.get_max_installments_number()
        self.assertRaises(ValueError, self.createInPayments, max + 1)

    def testMaxOutPaymnets(self):
        method = self.method_type.selectOne(connection=self.trans)
        max = method.get_max_installments_number()
        self.createOutPayments(max + 1)

    def testBank(self):
        method = self.method_type.selectOne(connection=self.trans)
        group = IPaymentGroup(self.create_purchase_order())
        payment = method.create_outpayment(group, Decimal(10))
        self.failIf(payment.get_adapted().bank)

    def testSelectable(self):
        method = self.method_type.selectOne(connection=self.trans)
        method.selectable()
        
class TestAPaymentMethod(DomainTest, _TestPaymentMethod):
    method_type = CheckPM
    enum = PaymentMethodType.CHECK

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

class TestMoneyPM(DomainTest, _TestPaymentMethodsBase):
    method_type = MoneyPM
    enum = PaymentMethodType.MONEY

class TestCheckPM(DomainTest, _TestPaymentMethodsBase):
    method_type = CheckPM
    enum = PaymentMethodType.CHECK

    def testCheckDataCreated(self):
        payment = self.createInPayment()
        method = self.method_type.selectOne(connection=self.trans)
        check_data = method.get_check_data_by_payment(payment.get_adapted())
        self.failUnless(check_data)

    def testBank(self):
        method = self.method_type.selectOne(connection=self.trans)
        group = IPaymentGroup(self.create_purchase_order())
        payment = method.create_outpayment(group, Decimal(10))
        self.failUnless(payment.get_adapted().bank)

class TestBillPM(DomainTest, _TestPaymentMethodsBase):
    method_type = BillPM
    enum = PaymentMethodType.BILL

class TestFinancePM(DomainTest, _TestPaymentMethodsBase):
    method_type = FinancePM
    enum = PaymentMethodType.FINANCIAL

class TestGiftCertificatePM(DomainTest, _TestPaymentMethodsBase):
    method_type = GiftCertificatePM
    enum = PaymentMethodType.GIFT_CERTIFICATE

class TestPaymentMethodDetails(DomainTest):

    def testGetActiveMethodDetails(self):
        provider = self.create_credit_provider()
        method_details = PaymentMethodDetails.get_active_method_details(
            provider=provider, conn=self.trans)
        self.failIf(method_details)
        payment_method_details = self.create_payment_method_details(provider)
        method_details = PaymentMethodDetails.get_active_method_details(
            provider=provider, conn=self.trans)
        self.failUnless(method_details)
        payment_method_details.is_active = False
        method_details = PaymentMethodDetails.get_active_method_details(
            provider=provider, conn=self.trans)
        self.failIf(method_details)


class TestCardInstallmentSettings(DomainTest):

        def testCalculatePaymentDueDate(self):
            # default settings: payment_day = closing_day = 15
            settings = self.create_card_installment_settings()
            today = datetime.datetime.today()
            # Reset day and month here, so we can avoid the bound cases
            # of 'today' attributes
            start_due_dates = [today.replace(day=14, month=3),
                               today.replace(day=15, month=3),
                               today.replace(day=16, month=3)]
            for date in start_due_dates:
                due_date = settings.calculate_payment_duedate(date)
                if date.day > settings.closing_day:
                    self.assertEqual(due_date.day, settings.payment_day)
                    self.assertEqual(due_date.month, date.month + 1)
                else:
                    self.assertEqual(due_date.day, settings.payment_day)
                    self.assertEqual(due_date.month, date.month)
