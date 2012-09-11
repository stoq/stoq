# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2007 Async Open Source <http://www.async.com.br>
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

from kiwi.currency import currency

from stoqlib.domain.payment.comment import PaymentComment
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib.dateutils import INTERVALTYPE_MONTH


class TestPayment(DomainTest):
    def test_new(self):
        payment = Payment(value=currency(10), due_date=datetime.datetime.now(),
                          branch=self.create_branch(),
                          method=None,
                          group=None,
                          till=None,
                          category=None,
                          payment_type=Payment.TYPE_OUT,
                          connection=self.trans)
        self.failUnless(payment.status == Payment.STATUS_PREVIEW)

    def _get_relative_day(self, days):
        return datetime.datetime.today() + datetime.timedelta(days)

    def testGetPenalty(self):
        method = PaymentMethod.get_by_name(self.trans, 'check')
        payment = Payment(value=currency(100),
                          branch=self.create_branch(),
                          due_date=datetime.datetime.now(),
                          open_date=datetime.datetime.now(),
                          method=method,
                          group=None,
                          till=None,
                          category=None,
                          payment_type=Payment.TYPE_OUT,
                          connection=self.trans)

        for day, expected_value in [(0, 0),
                                    (-1, 0),
                                    (-30, 0),
                                    (30, 0)]:
            payment.due_date = self._get_relative_day(day)
            self.assertEqual(payment.get_penalty(), currency(expected_value))

        method.daily_penalty = Decimal(1)

        for day, expected_value in [(0, 0),
                                    (-1, 1),
                                    (-30, 30),
                                    (30, 0)]:
            payment.due_date = self._get_relative_day(day)
            self.assertEqual(payment.get_penalty(), currency(expected_value))

        due_date = self._get_relative_day(-15)
        paid_date = self._get_relative_day(-5)
        payment.due_date = payment.open_date = due_date
        method.daily_penalty = Decimal(2)
        self.assertEqual(payment.get_penalty(paid_date.date()), currency(20))
        self.assertEqual(payment.get_penalty(due_date.date()), currency(0))

        for day in (18, -18):
            paid_date = self._get_relative_day(day)
            self.assertRaises(ValueError, payment.get_penalty, paid_date.date())

    def testGetInterest(self):
        method = PaymentMethod.get_by_name(self.trans, 'check')
        payment = Payment(value=currency(100),
                          branch=self.create_branch(),
                          due_date=datetime.datetime.now(),
                          method=method,
                          group=None,
                          till=None,
                          category=None,
                          payment_type=Payment.TYPE_OUT,
                          connection=self.trans)

        for day, expected_value in [(0, 0),
                                    (-1, 0),
                                    (-30, 0),
                                    (30, 0)]:
            payment.due_date = self._get_relative_day(day)
            self.assertEqual(payment.get_interest(), currency(expected_value))

        method.interest = Decimal(20)

        for day, expected_value in [(0, 0),
                                    (-1, 20),
                                    (-30, 20),
                                    (30, 0)]:
            payment.due_date = self._get_relative_day(day)
            self.assertEqual(payment.get_interest(), currency(expected_value))

        due_date = self._get_relative_day(-15)
        paid_date = self._get_relative_day(-5)
        payment.due_date = payment.open_date = due_date
        self.assertEqual(payment.get_interest(paid_date.date()), currency(20))
        self.assertEqual(payment.get_interest(due_date.date()), currency(0))

        for day in (18, -18):
            paid_date = self._get_relative_day(day)
            self.assertRaises(ValueError, payment.get_interest, paid_date.date())

    def testIsPaid(self):
        method = PaymentMethod.get_by_name(self.trans, 'check')
        payment = Payment(value=currency(100),
                          branch=self.create_branch(),
                          due_date=datetime.datetime.now(),
                          method=method,
                          group=None,
                          till=None,
                          category=None,
                          payment_type=Payment.TYPE_OUT,
                          connection=self.trans)
        self.failIf(payment.is_paid())
        payment.set_pending()
        self.failIf(payment.is_paid())
        payment.pay()
        self.failUnless(payment.is_paid())

    def testIsCancelled(self):
        method = PaymentMethod.get_by_name(self.trans, 'check')
        payment = Payment(value=currency(100),
                          branch=self.create_branch(),
                          due_date=datetime.datetime.now(),
                          method=method,
                          group=None,
                          till=None,
                          category=None,
                          payment_type=Payment.TYPE_OUT,
                          connection=self.trans)
        self.failIf(payment.is_cancelled())
        payment.set_pending()
        self.failIf(payment.is_cancelled())
        payment.pay()
        self.failIf(payment.is_cancelled())
        payment.cancel()
        self.failUnless(payment.is_cancelled())

    def testGetPaidDateString(self):
        method = PaymentMethod.get_by_name(self.trans, 'check')
        payment = Payment(value=currency(100),
                          branch=self.create_branch(),
                          due_date=datetime.datetime.now(),
                          method=method,
                          group=None,
                          till=None,
                          category=None,
                          payment_type=Payment.TYPE_OUT,
                          connection=self.trans)
        today = datetime.datetime.today().strftime('%x')
        self.failIf(payment.get_paid_date_string() == today)
        payment.set_pending()
        payment.pay()
        self.failUnless(payment.get_paid_date_string() == today)

    def testGetOpenDateString(self):
        method = PaymentMethod.get_by_name(self.trans, 'check')
        payment = Payment(value=currency(100),
                          branch=self.create_branch(),
                          due_date=datetime.datetime.now(),
                          method=method,
                          group=None,
                          till=None,
                          category=None,
                          payment_type=Payment.TYPE_OUT,
                          connection=self.trans)
        self.assertNotEqual(payment.get_open_date_string(), "")

    def testGetDaysLate(self):
        method = PaymentMethod.get_by_name(self.trans, 'check')
        open_date = due_date = self._get_relative_day(-4)
        payment = Payment(value=currency(100),
                          branch=self.create_branch(),
                          due_date=due_date,
                          open_date=open_date,
                          method=method,
                          group=None,
                          till=None,
                          category=None,
                          payment_type=Payment.TYPE_OUT,
                          connection=self.trans)
        payment.set_pending()
        self.assertEqual(payment.get_days_late(), 4)
        payment.pay()
        self.assertEqual(payment.get_days_late(), 0)

    def testCancel(self):
        method = PaymentMethod.get_by_name(self.trans, 'check')
        payment = Payment(value=currency(100),
                          branch=self.create_branch(),
                          due_date=datetime.datetime.now(),
                          method=method,
                          group=None,
                          till=None,
                          category=None,
                          payment_type=Payment.TYPE_OUT,
                          connection=self.trans)
        payment.set_pending()
        payment.pay()
        payment.cancel()
        self.assertEqual(payment.status, Payment.STATUS_CANCELLED)

    def testCreateRepeatedMonth(self):
        p = self.create_payment()
        p.description = 'Rent'
        p.category = self.create_payment_category()
        payments = Payment.create_repeated(self.trans, p,
                                           INTERVALTYPE_MONTH,
                                           datetime.date(2012, 1, 1),
                                           datetime.date(2012, 12, 31))
        self.assertEquals(len(payments), 11)
        self.assertEquals(p.due_date, datetime.datetime(2012, 1, 1))
        self.assertEquals(p.description, '1/12 Rent')

        self.assertEquals(payments[0].due_date, datetime.datetime(2012, 2, 1))
        self.assertEquals(payments[1].due_date, datetime.datetime(2012, 3, 1))
        self.assertEquals(payments[10].due_date, datetime.datetime(2012, 12, 1))

        self.assertEquals(payments[0].description, '2/12 Rent')
        self.assertEquals(payments[10].description, '12/12 Rent')


class TestPaymentComment(DomainTest):
    def test_comment(self):
        payment = self.create_payment(Payment.TYPE_OUT)
        self.assertEqual(payment.comments_number, 0)
        user = self.create_user()
        comment = PaymentComment(author=user, payment=payment, comment='',
                                 connection=self.trans)
        self.assertEqual(payment.comments_number, 1)
        self.assertEqual(payment.comments[0], comment)
