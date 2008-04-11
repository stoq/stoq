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
## Author(s):     Henrique Romano <henrique@async.com.br>
##                Johan Dahlin <jdahlin@async.com.br>
##

import datetime
from decimal import Decimal

from kiwi.datatypes import currency

from stoqlib.domain.payment.methods import CheckPM
from stoqlib.domain.payment.payment import Payment

from stoqlib.domain.test.domaintest import DomainTest

class TestPayment(DomainTest):
    def test_new(self):
        payment = Payment(value=currency(10), due_date=datetime.datetime.now(),
                          method=None,
                          group=None,
                          till=None,
                          destination=None,
                          category=None,
                          connection=self.trans)
        self.failUnless(payment.status == Payment.STATUS_PREVIEW)

    def _get_relative_day(self, days):
        return datetime.date.today() + datetime.timedelta(days)

    def testGetPenalty(self):
        method = CheckPM.selectOne(connection=self.trans)
        payment = Payment(value=currency(100),
                          due_date=datetime.datetime.now(),
                          open_date=datetime.datetime.now(),
                          method=method,
                          group=None,
                          till=None,
                          destination=None,
                          category=None,
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
        self.assertEqual(payment.get_penalty(paid_date), currency(20))
        self.assertEqual(payment.get_penalty(due_date), currency(0))

        for day in (18, -18):
            paid_date = self._get_relative_day(day)
            self.assertRaises(ValueError, payment.get_penalty, paid_date)

    def testGetInterest(self):
        method = CheckPM.selectOne(connection=self.trans)
        payment = Payment(value=currency(100),
                          due_date=datetime.datetime.now(),
                          method=method,
                          group=None,
                          till=None,
                          destination=None,
                          category=None,
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
        self.assertEqual(payment.get_interest(paid_date), currency(20))
        self.assertEqual(payment.get_interest(due_date), currency(0))

        for day in (18, -18):
            paid_date = self._get_relative_day(day)
            self.assertRaises(ValueError, payment.get_interest, paid_date)

    def testIsPaid(self):
        method = CheckPM.selectOne(connection=self.trans)
        payment = Payment(value=currency(100),
                          due_date=datetime.datetime.now(),
                          method=method,
                          group=None,
                          till=None,
                          destination=None,
                          category=None,
                          connection=self.trans)
        self.failIf(payment.is_paid())
        payment.set_pending()
        self.failIf(payment.is_paid())
        payment.pay()
        self.failUnless(payment.is_paid())

    def testGetPaidDateString(self):
        method = CheckPM.selectOne(connection=self.trans)
        payment = Payment(value=currency(100),
                          due_date=datetime.datetime.now(),
                          method=method,
                          group=None,
                          till=None,
                          destination=None,
                          category=None,
                          connection=self.trans)
        today = datetime.date.today().strftime('%x')
        self.failIf(payment.get_paid_date_string() == today)
        payment.set_pending()
        payment.pay()
        self.failUnless(payment.get_paid_date_string() == today)

    def testGetOpenDateString(self):
        method = CheckPM.selectOne(connection=self.trans)
        payment = Payment(value=currency(100),
                          due_date=datetime.datetime.now(),
                          open_date=None,
                          method=method,
                          group=None,
                          till=None,
                          destination=None,
                          category=None,
                          connection=self.trans)
        self.assertEqual(payment.get_open_date_string(), "")
        payment.open_date = datetime.datetime.now()
        self.assertNotEqual(payment.get_open_date_string(), "")

    def testGetDaysLate(self):
        method = CheckPM.selectOne(connection=self.trans)
        open_date = due_date = self._get_relative_day(-4)
        payment = Payment(value=currency(100),
                          due_date=due_date,
                          open_date=open_date,
                          method=method,
                          group=None,
                          till=None,
                          destination=None,
                          category=None,
                          connection=self.trans)
        payment.set_pending()
        self.assertEqual(payment.get_days_late(), 4)
        payment.pay()
        self.assertEqual(payment.get_days_late(), 0)

    def testCancel(self):
        method = CheckPM.selectOne(connection=self.trans)
        payment = Payment(value=currency(100),
                          due_date=datetime.datetime.now(),
                          method=method,
                          group=None,
                          till=None,
                          destination=None,
                          category=None,
                          connection=self.trans)
        payment.set_pending()
        payment.pay()
        payment.cancel()
        self.assertEqual(payment.status, Payment.STATUS_CANCELLED)
