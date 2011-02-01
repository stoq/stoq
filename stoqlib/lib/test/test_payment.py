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
##  Author(s):   Thiago Bellini              <hackedbellini@async.com.br>
##
""" Test for stoqlib/lib/payment.py module. """

import datetime
from decimal import Decimal

from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib.defaults import (INTERVALTYPE_MONTH, INTERVALTYPE_WEEK)
from stoqlib.lib.payment import (generate_payments_due_dates,
                                 generate_payments_values)



class TestPaymentFunctions(DomainTest):
    """"A class for testing the functions on lib/payment.py
    """

    def testGeneratePaymentsDueDates(self):
        due_date = datetime.date(year=2010, month=4, day=1)
        _test1 = (generate_payments_due_dates(5, due_date, 1,
                                              INTERVALTYPE_MONTH) ==
                  [datetime.date(2010, 4, 1),
                   datetime.date(2010, 5, 1),
                   datetime.date(2010, 6, 1),
                   datetime.date(2010, 7, 1),
                   datetime.date(2010, 8, 1)])
        due_date = datetime.date(year=2010, month=1, day=31)
        _test2 = (generate_payments_due_dates(10, due_date, 2,
                                              INTERVALTYPE_WEEK) ==
                  [datetime.date(2010, 1, 31),
                   datetime.date(2010, 2, 14),
                   datetime.date(2010, 2, 28),
                   datetime.date(2010, 3, 14),
                   datetime.date(2010, 3, 28),
                   datetime.date(2010, 4, 11),
                   datetime.date(2010, 4, 25),
                   datetime.date(2010, 5, 9),
                   datetime.date(2010, 5, 23),
                   datetime.date(2010, 6, 6)])

        self.failUnless(_test1)
        self.failUnless(_test2)

    def testGeneratePaymentsValues(self):
        _test1 = (generate_payments_values(Decimal(101), 3) ==
                  [Decimal('33.67'),
                   Decimal('33.67'),
                   Decimal('33.66')])
        _test2 = (generate_payments_values(Decimal('10.5'), 5,
                                           Decimal('1')) ==
                  [Decimal('2.12'),
                   Decimal('2.12'),
                   Decimal('2.12'),
                   Decimal('2.12'),
                   Decimal('2.12')])

        self.failUnless(_test1)
        self.failUnless(_test2)
