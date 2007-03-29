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

from stoqlib.domain.interfaces import IPaymentGroup
from stoqlib.domain.payment.methods import (BillPM, CheckPM, FinancePM,
                                            MoneyPM, GiftCertificatePM)
from stoqlib.domain.payment.payment import (Payment,
                                            PaymentAdaptToInPayment)
from stoqlib.domain.test.domaintest import DomainTest

class _TestPaymentMethodBase:
    def testCreateInPayment(self):
        sale = self.create_sale()
        group = sale.addFacet(IPaymentGroup,
                              connection=self.trans)

        method = self.method.selectOne(connection=self.trans)
        payment = method.create_inpayment(group, Decimal(100))
        self.failUnless(isinstance(payment, PaymentAdaptToInPayment))
        payment = payment.get_adapted()
        self.failUnless(isinstance(payment, Payment))
        self.assertEqual(payment.value, Decimal(100))

    def testCreateOutPayment(self):
        sale = self.create_sale()
        group = sale.addFacet(IPaymentGroup,
                              connection=self.trans)

        method = self.method.selectOne(connection=self.trans)
        payment = method.create_inpayment(group, Decimal(100))
        self.failUnless(isinstance(payment, PaymentAdaptToInPayment))
        payment = payment.get_adapted()
        self.failUnless(isinstance(payment, Payment))
        self.assertEqual(payment.value, Decimal(100))

    def testCreateInPayments(self):
        if self.method in (MoneyPM, GiftCertificatePM):
            return

        sale = self.create_sale()
        group = sale.addFacet(IPaymentGroup,
                              connection=self.trans)

        d = datetime.datetime.today()
        method = self.method.selectOne(connection=self.trans)
        payments = method.create_inpayments(group, Decimal(100),
                                            [d, d, d])
        payments = [p.get_adapted() for p in payments]

        athird = (Decimal(100) / Decimal(3)).quantize(Decimal("10e-2"))
        rest = (Decimal(100) - (athird * 2)).quantize(Decimal("10e-2"))
        self.assertEqual(len(payments), 3)
        self.assertEqual(payments[0].value, athird)
        self.assertEqual(payments[1].value, athird)
        self.assertEqual(payments[2].value, rest)

    def testCreateOutPayments(self):
        if self.method in (MoneyPM, GiftCertificatePM):
            return

        # FIXME: serious abuse here, should create a PurchaseOrder
        sale = self.create_sale()
        group = sale.addFacet(IPaymentGroup,
                              connection=self.trans)

        d = datetime.datetime.today()
        method = self.method.selectOne(connection=self.trans)
        payments = method.create_outpayments(group, Decimal(100),
                                             [d, d, d])
        payments = [p.get_adapted() for p in payments]

        athird = (Decimal(100) / Decimal(3)).quantize(Decimal("10e-2"))
        rest = (Decimal(100) - (athird * 2)).quantize(Decimal("10e-2"))
        self.assertEqual(len(payments), 3)
        self.assertEqual(payments[0].value, athird)
        self.assertEqual(payments[1].value, athird)
        self.assertEqual(payments[2].value, rest)

class TestMoneyPM(DomainTest, _TestPaymentMethodBase):
    method = MoneyPM

    # Money supports only 1 installment

    def testCreateInPayments(self):
        pass

    def testCreateOutPayments(self):
        pass

class TestCheckPM(DomainTest, _TestPaymentMethodBase):
    method = CheckPM

class TestBillPM(DomainTest, _TestPaymentMethodBase):
    method = BillPM

class TestFinancePM(DomainTest, _TestPaymentMethodBase):
    method = FinancePM

class TestGiftCertificatePM(DomainTest, _TestPaymentMethodBase):
    method = GiftCertificatePM
