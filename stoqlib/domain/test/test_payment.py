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
                          method=None, group=None, till=None,
                          destination=None, connection=self.trans)
        self.failUnless(payment.status == Payment.STATUS_PREVIEW)

    def _get_relative_day(self, days):
        return datetime.datetime.today() + datetime.timedelta(days)

    def testGetPenalty(self):
        method = CheckPM.selectOne(connection=self.trans)
        payment = Payment(value=currency(100),
                          due_date=datetime.datetime.now(),
                          method=method,
                          group=None,
                          till=None,
                          destination=None,
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

    def testGetInterest(self):
        method = CheckPM.selectOne(connection=self.trans)
        payment = Payment(value=currency(100),
                          due_date=datetime.datetime.now(),
                          method=method,
                          group=None,
                          till=None,
                          destination=None,
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

