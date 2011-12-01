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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" This module test all class in stoq/domain/station.py """

import datetime
from decimal import Decimal

from kiwi.datatypes import currency

from stoqlib.exceptions import TillError
from stoqlib.database.runtime import get_current_station
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.till import Till, TillEntry
from stoqlib.domain.test.domaintest import DomainTest


class TestTill(DomainTest):

    def _create_inpayment(self):
        sale = self.create_sale()
        sellable = self.create_sellable()
        sale.add_sellable(sellable, price=10)
        method = PaymentMethod.get_by_name(self.trans, 'bill')
        payment = method.create_inpayment(sale.group, Decimal(10))
        return payment.get_adapted()

    def _create_outpayment(self):
        purchase = self.create_purchase_order()
        sellable = self.create_sellable()
        purchase.add_item(sellable, 1)
        method = PaymentMethod.get_by_name(self.trans, 'bill')
        payment = method.create_outpayment(purchase.group, Decimal(10))
        return payment.get_adapted()

    def testGetCurrentTillOpen(self):
        self.assertEqual(Till.get_current(self.trans), None)

        station = get_current_station(self.trans)
        till = Till(connection=self.trans, station=station)

        self.assertEqual(Till.get_current(self.trans), None)
        till.open_till()
        self.assertEqual(Till.get_current(self.trans), till)
        self.assertEqual(till.opening_date.date(), datetime.date.today())
        self.assertEqual(till.status, Till.STATUS_OPEN)

        self.assertRaises(TillError, till.open_till)

    def testGetCurrentTillClose(self):
        station = get_current_station(self.trans)
        self.assertEqual(Till.get_current(self.trans), None)
        till = Till(connection=self.trans, station=station)
        till.open_till()

        self.assertEqual(Till.get_current(self.trans), till)
        till.close_till()
        self.assertEqual(Till.get_current(self.trans), None)

    def testTillOpenOnce(self):
        station = get_current_station(self.trans)
        till = Till(connection=self.trans, station=station)

        till.open_till()
        till.close_till()

        self.assertRaises(TillError, till.open_till)

    def testTillClose(self):
        station = self.create_station()
        till = Till(connection=self.trans, station=station)
        till.open_till()
        self.assertEqual(till.status, Till.STATUS_OPEN)
        till.close_till()
        self.assertEqual(till.status, Till.STATUS_CLOSED)
        self.assertRaises(TillError, till.close_till)

    def testTillCloseMoreThanBalance(self):
        station = self.create_station()
        till = Till(connection=self.trans, station=station)
        till.open_till()
        till.add_debit_entry(currency(20), u"")
        self.assertRaises(ValueError, till.close_till)

    def testGetBalance(self):
        till = Till(connection=self.trans,
                    station=self.create_station())
        till.open_till()

        old = till.get_balance()
        till.add_credit_entry(currency(10), u"")
        self.assertEqual(till.get_balance(), old + 10)
        till.add_debit_entry(currency(5), u"")
        self.assertEqual(till.get_balance(), old + 5)

    def testGetCashAmount(self):
        till = Till(connection=self.trans,
                    station=self.create_station())
        till.open_till()

        old = till.get_cash_amount()
        # money operations
        till.add_credit_entry(currency(10), u"")
        self.assertEqual(till.get_cash_amount(), old + 10)
        till.add_debit_entry(currency(5), u"")
        self.assertEqual(till.get_cash_amount(), old + 5)
        # non-money operations
        payment1 = self._create_inpayment()
        till.add_entry(payment1)
        self.assertEqual(till.get_cash_amount(), old + 5)
        payment2 = self._create_outpayment()
        till.add_entry(payment2)
        self.assertEqual(till.get_cash_amount(), old + 5)
        # money payment method operation
        payment = self.create_payment()
        payment.due_date = till.opening_date
        payment.till = till
        payment.set_pending()
        TillEntry(description='test', value=payment.value, till=till,
                  payment=payment, connection=self.trans)
        payment.pay()
        self.assertEqual(till.get_cash_amount(), old + 5 + payment.value)

    def testGetCreditsTotal(self):
        till = Till(connection=self.trans,
                    station=self.create_station())
        till.open_till()

        old = till.get_credits_total()
        till.add_credit_entry(currency(10), u"")
        self.assertEqual(till.get_credits_total(), old + 10)
        # This should not affect the credit
        till.add_debit_entry(currency(5), u"")
        self.assertEqual(till.get_credits_total(), old + 10)

    def testGetDebitsTotal(self):
        till = Till(connection=self.trans,
                    station=self.create_station())
        till.open_till()

        old = till.get_debits_total()
        till.add_debit_entry(currency(10), u"")
        self.assertEqual(till.get_debits_total(), old - 10)
        # This should not affect the debit
        till.add_credit_entry(currency(5), u"")
        self.assertEqual(till.get_debits_total(), old - 10)

    def testTillOpenYesterday(self):
        yesterday = datetime.datetime.today() - datetime.timedelta(1)

        # Open a till, set the opening_date to yesterday
        till = Till(station=get_current_station(self.trans),
                    connection=self.trans)
        till.open_till()
        till.opening_date = yesterday

        self.assertRaises(TillError, Till.get_current, self.trans)
        # This is used to close a till
        self.assertEqual(Till.get_last_opened(self.trans), till)

        till.close_till()

        self.assertEqual(Till.get_current(self.trans), None)

    def testTillOpenPreviouslyNotClosed(self):
        yesterday = datetime.datetime.today() - datetime.timedelta(1)

        # Open a till, set the opening_date to yesterday
        till = Till(station=get_current_station(self.trans),
                    connection=self.trans)
        till.open_till()
        till.opening_date = yesterday
        till.close_till()
        till.closing_date = None

        self.assertRaises(TillError, till.open_till)

    def testTillOpenPreviouslyOpened(self):
        yesterday = datetime.datetime.today() - datetime.timedelta(1)

        # Open a till, set the opening_date to yesterday
        till = Till(station=get_current_station(self.trans),
                    connection=self.trans)
        till.open_till()
        till.opening_date = yesterday
        till.add_credit_entry(currency(10), u"")
        till.close_till()
        till.closing_date = yesterday

        new_till = Till(station=get_current_station(self.trans),
                        connection=self.trans)
        self.failUnless(new_till._get_last_closed_till())
        new_till.open_till()
        self.assertEquals(new_till.initial_cash_amount,
                          till.final_cash_amount)

    def testTillOpenOtherStation(self):
        till = Till(station=self.create_station(),
                    connection=self.trans)
        till.open_till()

        till = Till(station=get_current_station(self.trans),
                    connection=self.trans)
        till.open_till()

        self.assertEqual(Till.get_last_opened(self.trans), till)

    def testNeedsClosing(self):
        till = Till(station=self.create_station(),
                    connection=self.trans)
        self.failIf(till.needs_closing())
        till.open_till()
        self.failIf(till.needs_closing())
        till.opening_date = datetime.datetime.today() - datetime.timedelta(1)
        self.failUnless(till.needs_closing())
        till.close_till()
        self.failIf(till.needs_closing())

    def testAddEntryInPayment(self):
        till = Till(connection=self.trans,
                    station=self.create_station())
        till.open_till()

        payment = self._create_inpayment()
        self.assertEqual(till.get_balance(), 0)
        till.add_entry(payment)
        self.assertEqual(till.get_balance(), 10)

    def testAddEntryOutPayment(self):
        till = Till(connection=self.trans,
                    station=self.create_station())
        till.open_till()

        payment = self._create_outpayment()
        self.assertEqual(till.get_balance(), 0)
        till.add_entry(payment)
        self.assertEqual(till.get_balance(), -10)

    def testAddCreditEntry(self):
        till = Till(connection=self.trans,
                    station=self.create_station())
        till.open_till()

        self.assertEqual(till.get_balance(), 0)
        till.add_credit_entry(10)
        self.assertEqual(till.get_balance(), 10)

    def testAddDebitEntry(self):
        till = Till(connection=self.trans,
                    station=self.create_station())
        till.open_till()

        self.assertEqual(till.get_balance(), 0)
        till.add_debit_entry(10)
        self.assertEqual(till.get_balance(), -10)

    def testGetLast(self):
        till = Till(connection=self.trans,
                    station=get_current_station(self.trans))
        till.open_till()
        self.assertEquals(Till.get_last(self.trans), till)

    def testGetLastClosed(self):
        till = Till(connection=self.trans,
                    station=get_current_station(self.trans))
        till.open_till()
        till.close_till()
        self.assertEquals(Till.get_last_closed(self.trans), till)
