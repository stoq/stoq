# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
## Author(s):   Johan Dahlin      <jdahlin@async.com.br>
##
""" This module test all class in stoq/domain/station.py """

import datetime

from kiwi.datatypes import currency

from stoqlib.exceptions import TillError
from stoqlib.database.runtime import get_current_station
from stoqlib.domain.station import BranchStation
from stoqlib.domain.till import Till

from stoqlib.domain.test.domaintest import DomainTest

class TestTill(DomainTest):
    def testGetCurrentTillOpen(self):
        self.assertEqual(Till.get_current(self.trans), None)

        station = get_current_station(self.trans)
        till = Till(connection=self.trans, station=station)

        self.assertEqual(Till.get_current(self.trans), None)
        till.open_till()
        self.assertEqual(Till.get_current(self.trans), till)

        self.assertRaises(TillError, till.open_till)

    def testTillOpenOnce(self):
        station = get_current_station(self.trans)
        till = Till(connection=self.trans, station=station)

        till.open_till()
        till.close_till()

        self.assertRaises(TillError, till.open_till)

    def testGetCurrentTillClose(self):
        station = get_current_station(self.trans)

        self.assertEqual(Till.get_current(self.trans), None)
        till = Till(connection=self.trans, station=station)
        till.open_till()

        self.assertEqual(Till.get_current(self.trans), till)
        till.close_till()
        self.assertEqual(Till.get_current(self.trans), None)

    def testGetCurrentOtherStation(self):
        # Test bug #2734
        self.assertEqual(Till.get_current(self.trans), None)

        # Create a new station in the same branch as the current one
        station = get_current_station(self.trans)
        newstation = BranchStation.create(
            self.trans, branch=station.branch, name='teststation')

        # Create a Till for the new station and open it
        till = Till(connection=self.trans, station=newstation)
        till.open_till()

        # Verify that it's set for "us" as well since
        # Till.get_current calls get_current_branch()
        self.assertEqual(Till.get_current(self.trans), till)

    def testGetCashTotal(self):
        till = Till(connection=self.trans,
                    station=get_current_station(self.trans))
        till.open_till()

        old = till.get_cash_total()
        till.create_credit(currency(10), u"")
        self.assertEqual(till.get_cash_total(), old + 10)
        till.create_debit(currency(5), u"")
        self.assertEqual(till.get_cash_total(), old + 5)


    def testGetBalance(self):
        till = Till(connection=self.trans,
                    station=get_current_station(self.trans))
        till.open_till()

        old = till.get_balance()
        till.create_credit(currency(10), u"")
        self.assertEqual(till.get_balance(), old + 10)
        till.create_debit(currency(5), u"")
        self.assertEqual(till.get_balance(), old + 5)

    def testGetCreditsTotal(self):
        till = Till(connection=self.trans,
                    station=get_current_station(self.trans))
        till.open_till()

        old = till.get_credits_total()
        till.create_credit(currency(10), u"")
        self.assertEqual(till.get_credits_total(), old + 10)
        # This should not affect the credit
        till.create_debit(currency(5), u"")
        self.assertEqual(till.get_credits_total(), old + 10)

    def testGetDebitsTotal(self):
        till = Till(connection=self.trans,
                    station=get_current_station(self.trans))
        till.open_till()

        old = till.get_debits_total()
        till.create_debit(currency(10), u"")
        self.assertEqual(till.get_debits_total(), old - 10)
        # This should not affect the debit
        till.create_credit(currency(5), u"")
        self.assertEqual(till.get_debits_total(), old - 10)

    def testTillOpenYesterday(self):
        yesterday = (datetime.datetime.today() - datetime.timedelta(1)).date()

        # Open a till, set the opening_date to yesterday
        till = Till(connection=self.trans, station=get_current_station(self.trans))
        till.open_till()
        till.opening_date = yesterday

        self.assertRaises(TillError, Till.get_current, self.trans)
        # This is used to close a till
        self.assertEqual(Till.get_last_opened(self.trans), till)

        till.close_till()

        self.assertEqual(Till.get_current(self.trans), None)


    def testPendingClosure(self):
        till = Till(connection=self.trans, station=get_current_station(self.trans))
        self.failIf(till.pending_closure())
        till.open_till()
        self.failIf(till.pending_closure())
        till.opening_date = (datetime.datetime.today() - datetime.timedelta(1)).date()
        self.failUnless(till.pending_closure())
        till.close_till()
        self.failIf(till.pending_closure())
