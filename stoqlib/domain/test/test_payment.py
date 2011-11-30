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

from kiwi.datatypes import currency

from stoqlib.domain.interfaces import IInPayment, IOutPayment
from stoqlib.domain.payment.comment import PaymentComment
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment, PaymentFlowHistory
from stoqlib.domain.test.domaintest import DomainTest


class TestPayment(DomainTest):
    def test_new(self):
        payment = Payment(value=currency(10), due_date=datetime.datetime.now(),
                          method=None,
                          group=None,
                          till=None,
                          category=None,
                          connection=self.trans)
        self.failUnless(payment.status == Payment.STATUS_PREVIEW)

    def _get_relative_day(self, days):
        return datetime.datetime.today() + datetime.timedelta(days)

    def testGetPenalty(self):
        method = PaymentMethod.get_by_name(self.trans, 'check')
        payment = Payment(value=currency(100),
                          due_date=datetime.datetime.now(),
                          open_date=datetime.datetime.now(),
                          method=method,
                          group=None,
                          till=None,
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
        self.assertEqual(payment.get_penalty(paid_date.date()), currency(20))
        self.assertEqual(payment.get_penalty(due_date.date()), currency(0))

        for day in (18, -18):
            paid_date = self._get_relative_day(day)
            self.assertRaises(ValueError, payment.get_penalty, paid_date.date())

    def testGetInterest(self):
        method = PaymentMethod.get_by_name(self.trans, 'check')
        payment = Payment(value=currency(100),
                          due_date=datetime.datetime.now(),
                          method=method,
                          group=None,
                          till=None,
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
        self.assertEqual(payment.get_interest(paid_date.date()), currency(20))
        self.assertEqual(payment.get_interest(due_date.date()), currency(0))

        for day in (18, -18):
            paid_date = self._get_relative_day(day)
            self.assertRaises(ValueError, payment.get_interest, paid_date.date())

    def testIsPaid(self):
        method = PaymentMethod.get_by_name(self.trans, 'check')
        payment = Payment(value=currency(100),
                          due_date=datetime.datetime.now(),
                          method=method,
                          group=None,
                          till=None,
                          category=None,
                          connection=self.trans)
        self.failIf(payment.is_paid())
        payment.set_pending()
        self.failIf(payment.is_paid())
        payment.pay()
        self.failUnless(payment.is_paid())

    def testIsCancelled(self):
        method = PaymentMethod.get_by_name(self.trans, 'check')
        payment = Payment(value=currency(100),
                          due_date=datetime.datetime.now(),
                          method=method,
                          group=None,
                          till=None,
                          category=None,
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
                          due_date=datetime.datetime.now(),
                          method=method,
                          group=None,
                          till=None,
                          category=None,
                          connection=self.trans)
        today = datetime.datetime.today().strftime('%x')
        self.failIf(payment.get_paid_date_string() == today)
        payment.set_pending()
        payment.pay()
        self.failUnless(payment.get_paid_date_string() == today)

    def testGetOpenDateString(self):
        method = PaymentMethod.get_by_name(self.trans, 'check')
        payment = Payment(value=currency(100),
                          due_date=datetime.datetime.now(),
                          open_date=None,
                          method=method,
                          group=None,
                          till=None,
                          category=None,
                          connection=self.trans)
        self.assertEqual(payment.get_open_date_string(), "")
        payment.open_date = datetime.datetime.now()
        self.assertNotEqual(payment.get_open_date_string(), "")

    def testGetDaysLate(self):
        method = PaymentMethod.get_by_name(self.trans, 'check')
        open_date = due_date = self._get_relative_day(-4)
        payment = Payment(value=currency(100),
                          due_date=due_date,
                          open_date=open_date,
                          method=method,
                          group=None,
                          till=None,
                          category=None,
                          connection=self.trans)
        payment.set_pending()
        self.assertEqual(payment.get_days_late(), 4)
        payment.pay()
        self.assertEqual(payment.get_days_late(), 0)

    def testCancel(self):
        method = PaymentMethod.get_by_name(self.trans, 'check')
        payment = Payment(value=currency(100),
                          due_date=datetime.datetime.now(),
                          method=method,
                          group=None,
                          till=None,
                          category=None,
                          connection=self.trans)
        payment.set_pending()
        payment.pay()
        payment.cancel()
        self.assertEqual(payment.status, Payment.STATUS_CANCELLED)


class TestPaymentFlowHistory(DomainTest):

    def testGetOrCreateFlowHistory(self):
        today = datetime.datetime.today()
        history = PaymentFlowHistory.get_or_create_flow_history(self.trans,
                                                                today)
        history2 = PaymentFlowHistory.get_or_create_flow_history(self.trans,
                                                                 today)
        self.failIf(history is not history2)

    def testGetLastDay(self):
        today = datetime.datetime.today()
        yesterday = today + datetime.timedelta(days=-1)
        tomorrow = today + datetime.timedelta(days=+1)

        today_history = PaymentFlowHistory.get_or_create_flow_history(
            self.trans, today)
        yesterday_history = PaymentFlowHistory.get_or_create_flow_history(
            self.trans, yesterday)
        PaymentFlowHistory.get_or_create_flow_history(self.trans, tomorrow)

        self.failUnless(PaymentFlowHistory.get_last_day(self.trans, today) is
                        yesterday_history)
        self.failUnless(PaymentFlowHistory.get_last_day(self.trans) is
                        yesterday_history)
        self.failUnless(PaymentFlowHistory.get_last_day(self.trans, tomorrow) is
                        today_history)

    def testGetLastDayRealBalance(self):
        today = datetime.datetime.today()
        yesterday = today + datetime.timedelta(days=-1)
        tomorrow = today + datetime.timedelta(days=+1)

        today_history = PaymentFlowHistory.get_or_create_flow_history(
            self.trans, today)
        yesterday_history = PaymentFlowHistory.get_or_create_flow_history(
            self.trans, yesterday)
        tomorrow_history = PaymentFlowHistory.get_or_create_flow_history(
            self.trans, tomorrow)

        self.assertEqual(today_history.get_last_day_real_balance(),
                         yesterday_history.balance_real)
        self.assertEqual(tomorrow_history.get_last_day_real_balance(),
                         today_history.balance_real)
        # FIXME: this is 436, why?
        #self.assertEqual(yesterday_history.get_last_day_real_balance(),
        #                 Decimal(0))

    def testGetDivergentPayments(self):
        today = datetime.datetime.today()
        history = PaymentFlowHistory.get_or_create_flow_history(
            self.trans, today)
        self.failIf(history.get_divergent_payments())

        payment = self.create_payment()
        payment.value = Decimal(100)
        payment.due_date = today
        payment.addFacet(IInPayment, connection=self.trans)
        payment.set_pending()

        # not received
        self.failUnless(payment in history.get_divergent_payments())
        payment.pay()
        # For some reason, the test fails if we do not set paid_date.
        payment.paid_date = today
        self.failIf(payment in history.get_divergent_payments())

        payment2 = self.create_payment()
        payment2.value = Decimal(10)
        payment2.due_date = today
        payment2.addFacet(IOutPayment, connection=self.trans)
        payment2.set_pending()

        # not paid
        self.failUnless(payment2 in history.get_divergent_payments())
        payment2.pay()
        payment2.paid_date = today
        self.failIf(payment2 in history.get_divergent_payments())
        # should be empty now
        self.failIf(history.get_divergent_payments())

        payment3 = self.create_payment()
        payment3.value = Decimal(30)
        payment3.due_date = today
        payment3.addFacet(IInPayment, connection=self.trans)
        payment3.set_pending()
        payment3.interest = Decimal(1)
        payment3.pay()
        payment3.paid_date = today
        # paid value is different
        self.failUnless(payment3 in history.get_divergent_payments())

        payment4 = self.create_payment()
        payment4.value = Decimal(40)
        payment4.due_date = today + datetime.timedelta(days=-1)
        payment4.addFacet(IOutPayment, connection=self.trans)
        payment4.set_pending()
        payment4.pay()
        payment4.paid_date = today
        # not expected to be received today
        self.failUnless(payment4 in history.get_divergent_payments())

    def testAddPayment(self):
        today = datetime.datetime.today()
        history = PaymentFlowHistory.get_or_create_flow_history(
            self.trans, today)
        old_to_receive = history.to_receive

        payment = self.create_payment()
        payment.value = Decimal(100)
        payment.due_date = today
        payment.addFacet(IInPayment, connection=self.trans)
        payment.set_pending()

        self.assertEqual(old_to_receive + Decimal(100), history.to_receive)

        old_to_pay = history.to_pay
        payment2 = self.create_payment()
        payment2.value = Decimal(10)
        payment2.due_date = today
        payment2.addFacet(IOutPayment, connection=self.trans)
        payment2.set_pending()
        self.assertEqual(old_to_pay + Decimal(10), history.to_pay)

    def testRemovePayment(self):
        today = datetime.datetime.today()
        history = PaymentFlowHistory.get_or_create_flow_history(
            self.trans, today)
        old_to_receive = history.to_receive

        payment = self.create_payment()
        payment.value = Decimal(100)
        payment.due_date = today
        payment.addFacet(IInPayment, connection=self.trans)
        payment.set_pending()

        self.assertEqual(old_to_receive + Decimal(100), history.to_receive)
        payment.cancel()
        self.assertEqual(old_to_receive, history.to_receive)

        old_to_pay = history.to_pay
        payment2 = self.create_payment()
        payment2.value = Decimal(10)
        payment2.due_date = today
        payment2.addFacet(IOutPayment, connection=self.trans)
        payment2.set_pending()

        self.assertEqual(old_to_pay + Decimal(10), history.to_pay)
        payment2.cancel()
        self.assertEqual(old_to_pay, history.to_pay)

    def testAddPaidPayment(self):
        today = datetime.datetime.today()
        history = PaymentFlowHistory.get_or_create_flow_history(
            self.trans, today)
        old_received = history.received

        payment = self.create_payment()
        payment.value = Decimal(100)
        payment.due_date = today
        payment.addFacet(IInPayment, connection=self.trans)
        payment.set_pending()
        payment.pay()

        self.assertEqual(old_received + Decimal(100), history.received)

        old_paid = history.paid
        payment2 = self.create_payment()
        payment2.value = Decimal(10)
        payment2.due_date = today
        payment2.addFacet(IOutPayment, connection=self.trans)
        payment2.set_pending()
        payment2.pay()
        self.assertEqual(old_paid + Decimal(10), history.paid)

    def testRemovePaidPayment(self):
        today = datetime.datetime.today()
        history = PaymentFlowHistory.get_or_create_flow_history(
            self.trans, today)
        old_received = history.received

        payment = self.create_payment()
        payment.value = Decimal(100)
        payment.due_date = today
        payment.addFacet(IInPayment, connection=self.trans)
        payment.set_pending()
        payment.pay()

        self.assertEqual(old_received + Decimal(100), history.received)
        payment.cancel()
        self.assertEqual(old_received, history.received)

        old_paid = history.paid
        payment2 = self.create_payment()
        payment2.value = Decimal(10)
        payment2.due_date = today
        payment2.addFacet(IOutPayment, connection=self.trans)
        payment2.set_pending()
        payment2.pay()

        self.assertEqual(old_paid + Decimal(10), history.paid)
        payment2.cancel()
        self.assertEqual(old_paid, history.paid)


class TestPaymentComment(DomainTest):
    def test_comment(self):
        payment = self.create_payment()
        self.assertEqual(payment.comments_number, 0)
        user = self.create_user()
        comment = PaymentComment(author=user, payment=payment, comment='',
                                connection=self.trans)
        self.assertEqual(payment.comments_number, 1)
        self.assertEqual(payment.comments[0], comment)
