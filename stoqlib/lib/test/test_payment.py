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

from decimal import Decimal

from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib.payment import generate_payments_values


class TestPaymentFunctions(DomainTest):
    """A class for testing the functions on lib/payment.py
    """

    def test_generate_payments_values(self):
        # Test 1
        values = generate_payments_values(Decimal(101), 3)
        expected = [Decimal('33.67'), Decimal('33.67'), Decimal('33.66')]
        self.assertEqual(values, expected)
        self.assertEqual(len(values), 3)

        self.assertEqual(sum(values), Decimal(101))

        # Test 2
        self.assertRaises(ValueError, generate_payments_values,
                          Decimal('2'), 0)
