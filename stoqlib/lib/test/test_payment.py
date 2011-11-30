# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008 Async Open Source <http://www.async.com.br>
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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Test for stoqlib/lib/payment.py module. """

import datetime
from decimal import Decimal

from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib.defaults import (INTERVALTYPE_YEAR, INTERVALTYPE_MONTH,
                                  INTERVALTYPE_WEEK, INTERVALTYPE_DAY)
from stoqlib.lib.payment import (generate_payments_due_dates,
                                 generate_payments_values)


class TestPaymentFunctions(DomainTest):
    """"A class for testing the functions on lib/payment.py
    """

    def testGeneratePaymentsDueDates(self):
        # Test 1
        due_date = datetime.date(year=2010, month=4, day=1)
        due_dates = generate_payments_due_dates(5, due_date, 1,
                                                INTERVALTYPE_MONTH)
        expected = [datetime.date(2010, 4, 1),
                    datetime.date(2010, 5, 1),
                    datetime.date(2010, 6, 1),
                    datetime.date(2010, 7, 1),
                    datetime.date(2010, 8, 1)]
        self.assertEqual(due_dates, expected)
        self.assertEqual(len(due_dates), 5)
        self.assertEqual(due_dates[0], due_date)
        for t in due_dates[1:]:
            self.failUnless(t > due_date)

        # Test 2
        due_date = datetime.date(year=2010, month=1, day=31)
        due_dates = generate_payments_due_dates(10, due_date, 2,
                                                INTERVALTYPE_WEEK)
        expected = [datetime.date(2010, 1, 31),
                    datetime.date(2010, 2, 14),
                    datetime.date(2010, 2, 28),
                    datetime.date(2010, 3, 14),
                    datetime.date(2010, 3, 28),
                    datetime.date(2010, 4, 11),
                    datetime.date(2010, 4, 25),
                    datetime.date(2010, 5, 9),
                    datetime.date(2010, 5, 23),
                    datetime.date(2010, 6, 6)]
        self.assertEqual(due_dates, expected)
        self.assertEqual(len(due_dates), 10)
        self.assertEqual(due_dates[0], due_date)
        for t in due_dates[1:]:
            self.failUnless(t > due_date)

        # Test 3
        due_date = due_date = datetime.date(year=2011, month=3, day=14)
        due_dates = generate_payments_due_dates(3, due_date, 10,
                                                INTERVALTYPE_DAY)
        expected = [datetime.date(2011, 3, 14),
                    datetime.date(2011, 3, 24),
                    datetime.date(2011, 4, 3)]
        self.assertEqual(due_dates, expected)
        self.assertEqual(len(due_dates), 3)
        self.assertEqual(due_dates[0], due_date)
        for t in due_dates[1:]:
            self.failUnless(t > due_date)

        # Test 4
        due_date = due_date = datetime.date(year=2012, month=12, day=31)
        due_dates = generate_payments_due_dates(4, due_date, 2,
                                                INTERVALTYPE_YEAR)
        expected = [datetime.date(2012, 12, 31),
                    datetime.date(2014, 12, 31),
                    datetime.date(2016, 12, 31),
                    datetime.date(2018, 12, 31)]
        self.assertEqual(due_dates, expected)
        self.assertEqual(len(due_dates), 4)
        self.assertEqual(due_dates[0], due_date)
        for t in due_dates[1:]:
            self.failUnless(t > due_date)

        # Test 5
        due_date = due_date = datetime.date(year=2010, month=1, day=1)
        self.assertRaises(AssertionError, generate_payments_due_dates, 0,
                          due_date, 1, INTERVALTYPE_YEAR)

    def testGeneratePaymentsValues(self):
        # Test 1
        values = generate_payments_values(Decimal(101), 3)
        expected = [Decimal('33.67'), Decimal('33.67'), Decimal('33.66')]
        self.assertEqual(values, expected)
        self.assertEqual(len(values), 3)

        self.assertEqual(sum(values), Decimal(101))

        # Test 2
        values = generate_payments_values(Decimal('10.5'), 5,
                                             Decimal('1'))
        expected = [Decimal('2.12'), Decimal('2.12'), Decimal('2.12'),
                    Decimal('2.12'), Decimal('2.12')]
        self.assertEqual(values, expected)
        self.assertEqual(len(values), 5)

        self.assertEqual(sum(values), (Decimal('10.5') + Decimal('0.10')))

        # Test 3
        self.assertRaises(AssertionError, generate_payments_values,
                          Decimal('2'), 0)
