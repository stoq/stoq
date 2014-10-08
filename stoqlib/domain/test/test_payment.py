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

__tests__ = 'stoqlib/domain/payment/payment.py'

import datetime
from decimal import Decimal
import mock

from kiwi.currency import currency
from storm.expr import Or

from stoqlib.domain.account import AccountTransaction
from stoqlib.domain.commission import Commission, CommissionView
from stoqlib.domain.event import Event
from stoqlib.domain.payment.comment import PaymentComment
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment, PaymentChangeHistory
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib.dateutils import (INTERVALTYPE_MONTH, localdate,
                                   localdatetime, localnow, localtoday)
from stoqlib.exceptions import DatabaseInconsistency, StoqlibError


class TestPayment(DomainTest):
    def test_get_status_string_without_status(self):
        payment = self.create_payment()
        payment.status = 9
        with self.assertRaises(DatabaseInconsistency):
            self.status = payment.status_str

    def test_new(self):
        with self.assertRaises(TypeError):
            Payment(due_date=localnow(),
                    branch=self.create_branch(),
                    payment_type=Payment.TYPE_OUT,
                    store=self.store)

        payment = Payment(value=currency(10), due_date=localnow(),
                          branch=self.create_branch(),
                          method=None,
                          group=None,
                          category=None,
                          payment_type=Payment.TYPE_OUT,
                          store=self.store)
        self.failUnless(payment.status == Payment.STATUS_PREVIEW)

    def test_installment_number(self):
        payment = self.create_payment()
        self.assertEquals(payment.installment_number, 1)

    def _get_relative_day(self, days):
        return localtoday() + datetime.timedelta(days)

    def test_get_penalty(self):
        method = PaymentMethod.get_by_name(self.store, u'check')
        payment = Payment(value=currency(100),
                          branch=self.create_branch(),
                          due_date=localnow(),
                          method=method,
                          group=None,
                          category=None,
                          payment_type=Payment.TYPE_OUT,
                          store=self.store)

        for day, expected_value in [(0, 0),
                                    (-1, 0),
                                    (-30, 0),
                                    (30, 0)]:
            payment.due_date = self._get_relative_day(day)
            self.assertEqual(payment.get_penalty(), currency(expected_value))

        method.penalty = Decimal(20)

        for day, expected_value in [(0, 0),
                                    (-1, 20),
                                    (-30, 20),
                                    (30, 0)]:
            payment.due_date = self._get_relative_day(day)
            self.assertEqual(payment.get_penalty(), currency(expected_value))

        due_date = self._get_relative_day(-15)
        paid_date = self._get_relative_day(-5)
        payment.due_date = payment.open_date = due_date
        self.assertEqual(payment.get_penalty(paid_date.date()), currency(20))
        self.assertEqual(payment.get_penalty(due_date.date()), currency(0))

        for day in (18, -18):
            paid_date = self._get_relative_day(day)
            self.assertRaises(ValueError, payment.get_penalty, paid_date.date())

    def test_get_interest(self):
        method = PaymentMethod.get_by_name(self.store, u'check')
        payment = Payment(value=currency(100),
                          branch=self.create_branch(),
                          due_date=localnow(),
                          open_date=localnow(),
                          method=method,
                          group=None,
                          category=None,
                          payment_type=Payment.TYPE_OUT,
                          store=self.store)

        for day, expected_value in [(0, 0),
                                    (-1, 0),
                                    (-30, 0),
                                    (30, 0)]:
            payment.due_date = self._get_relative_day(day)
            self.assertEqual(payment.get_interest(), currency(expected_value))

        method.daily_interest = Decimal(1)

        for day, expected_value in [(0, 0),
                                    (-1, 1),
                                    (-30, 30),
                                    (30, 0)]:
            payment.due_date = self._get_relative_day(day)
            self.assertEqual(payment.get_interest(), currency(expected_value))

        due_date = self._get_relative_day(-15)
        paid_date = self._get_relative_day(-5)
        payment.due_date = payment.open_date = due_date
        method.daily_interest = Decimal(2)
        self.assertEqual(payment.get_interest(paid_date.date()), currency(20))
        self.assertEqual(payment.get_interest(due_date.date()), currency(0))

        for day in (18, -18):
            paid_date = self._get_relative_day(day)
            self.assertRaises(ValueError, payment.get_interest, paid_date.date())

    def test_has_commission(self):
        item = self.create_sale_item()
        self.add_payments(item.sale, method_type=u'check', installments=2)

        for p in item.sale.payments:
            self.assertFalse(p.has_commission())
            commission = Commission(store=self.store,
                                    payment=p,
                                    sale=item.sale)
            self.assertTrue(p.has_commission())
            p.value = Decimal(2)
            commission = self.store.find(CommissionView, payment_id=p.id).one()
            self.assertEquals(commission.quantity_sold, Decimal(1))
            commission.sale_status = item.sale.STATUS_RETURNED
            self.assertEquals(commission.quantity_sold, Decimal(0))

    @mock.patch('stoqlib.domain.payment.payment.Event.log')
    def test_pay(self, log):
        payment = self.create_payment(value=Decimal(101))
        with self.assertRaises(ValueError):
            payment.pay()
        payment.status = Payment.STATUS_PENDING
        payment.pay(paid_value=Decimal(102))
        expected = (u'Money payment with value original value 101.00 was paid'
                    u' with value 102.00')
        log.assert_called_with(self.store, Event.TYPE_PAYMENT, expected)

    def test_is_paid(self):
        method = PaymentMethod.get_by_name(self.store, u'check')
        payment = Payment(value=currency(100),
                          branch=self.create_branch(),
                          due_date=localnow(),
                          method=method,
                          group=None,
                          category=None,
                          payment_type=Payment.TYPE_OUT,
                          store=self.store)
        self.failIf(payment.is_paid())
        payment.set_pending()
        self.failIf(payment.is_paid())
        payment.pay()
        self.failUnless(payment.is_paid())

    def test_is_cancelled(self):
        method = PaymentMethod.get_by_name(self.store, u'check')
        payment = Payment(value=currency(100),
                          branch=self.create_branch(),
                          due_date=localnow(),
                          method=method,
                          group=None,
                          category=None,
                          payment_type=Payment.TYPE_OUT,
                          store=self.store)
        self.failIf(payment.is_cancelled())
        payment.set_pending()
        self.failIf(payment.is_cancelled())
        payment.pay()
        self.failIf(payment.is_cancelled())
        payment.cancel()
        self.failUnless(payment.is_cancelled())
        with self.assertRaises(StoqlibError):
            payment.status = Payment.STATUS_CANCELLED
            payment.cancel()

    def test_get_paid_date_string(self):
        method = PaymentMethod.get_by_name(self.store, u'check')
        payment = Payment(value=currency(100),
                          branch=self.create_branch(),
                          due_date=localnow(),
                          method=method,
                          group=None,
                          category=None,
                          payment_type=Payment.TYPE_OUT,
                          store=self.store)
        today = localnow().strftime(u'%x')
        self.failIf(payment.get_paid_date_string() == today)
        payment.set_pending()
        payment.pay()
        self.failUnless(payment.get_paid_date_string() == today)

    def test_get_open_date_string(self):
        method = PaymentMethod.get_by_name(self.store, u'check')
        payment = Payment(value=currency(100),
                          branch=self.create_branch(),
                          due_date=localnow(),
                          method=method,
                          group=None,
                          category=None,
                          payment_type=Payment.TYPE_OUT,
                          store=self.store)
        self.assertNotEqual(payment.get_open_date_string(), u"")
        payment.open_date = None
        self.assertEquals(payment.get_open_date_string(), u"")

    def test_is_separate_payment_with_renegotiation(self):
        payment = self.create_payment()
        self.create_payment_renegotiation(group=payment.group)
        self.assertFalse(payment.is_separate_payment())

    def test_get_days_late(self):
        method = PaymentMethod.get_by_name(self.store, u'check')
        open_date = due_date = self._get_relative_day(-4)
        payment = Payment(value=currency(100),
                          branch=self.create_branch(),
                          due_date=due_date,
                          open_date=open_date,
                          method=method,
                          group=None,
                          category=None,
                          payment_type=Payment.TYPE_OUT,
                          store=self.store)
        payment.set_pending()
        self.assertEqual(payment.get_days_late(), 4)
        payment.due_date = self._get_relative_day(+4)
        self.assertFalse(payment.get_days_late())
        payment.pay()
        self.assertEqual(payment.get_days_late(), 0)

    def test_can_cancel(self):
        payment = self.create_payment()
        self.failUnless(payment.can_cancel())

        payment.set_pending()
        self.failUnless(payment.can_cancel())

        payment.pay()
        self.failUnless(payment.can_cancel())

        payment.cancel()
        self.failIf(payment.can_cancel())

    def test_cancel(self):
        method = PaymentMethod.get_by_name(self.store, u'check')
        payment = Payment(value=currency(100),
                          branch=self.create_branch(),
                          due_date=localnow(),
                          method=method,
                          group=None,
                          category=None,
                          payment_type=Payment.TYPE_OUT,
                          store=self.store)
        payment.set_pending()
        payment.pay()
        payment.cancel(change_entry=payment)
        self.assertEqual(payment.status, Payment.STATUS_CANCELLED)

    def test_change_due_date(self):
        payment = self.create_payment()
        self.assertEquals(payment.due_date, localtoday())
        payment.change_due_date(new_due_date=self._get_relative_day(-2))
        self.assertEquals(payment.due_date, self._get_relative_day(-2))
        payment.status = Payment.STATUS_PAID
        with self.assertRaises(StoqlibError):
            payment.change_due_date(new_due_date=self._get_relative_day(-1))

    def test_update_value(self):
        payment = self.create_payment()
        self.assertEquals(payment.value, 10)
        payment.update_value(Decimal(101))
        self.assertEquals(payment.value, 101)

    def test_get_payable_value(self):
        payment = self.create_payment()
        self.assertEquals(payment.get_payable_value(), 10)
        payment.status = Payment.STATUS_PAID
        payment.paid_value = 10
        self.assertEquals(payment.get_payable_value(), 10)
        payment.status = 9
        self.assertEquals(payment.get_payable_value(), 10)

    def test_create_repeated_month(self):
        p = self.create_payment()
        p.description = u'Rent'
        p.category = self.create_payment_category()
        with self.assertRaises(AssertionError):
            Payment.create_repeated(self.store, p,
                                    INTERVALTYPE_MONTH,
                                    localdate(2012, 1, 1).date(),
                                    localdate(2012, 1, 1).date())
        payments = Payment.create_repeated(self.store, p,
                                           INTERVALTYPE_MONTH,
                                           localdate(2012, 1, 1).date(),
                                           localdate(2012, 12, 31).date())
        self.assertEquals(len(payments), 11)
        self.assertEquals(p.due_date, localdatetime(2012, 1, 1))
        self.assertEquals(p.description, u'1/12 Rent')

        self.assertEquals(payments[0].due_date, localdatetime(2012, 2, 1))
        self.assertEquals(payments[1].due_date, localdatetime(2012, 3, 1))
        self.assertEquals(payments[10].due_date, localdatetime(2012, 12, 1))

        self.assertEquals(payments[0].description, u'2/12 Rent')
        self.assertEquals(payments[10].description, u'12/12 Rent')

    def test_set_not_paid(self):
        sale = self.create_sale()
        self.add_product(sale)
        payment = self.add_payments(sale, method_type=u'check')[0]
        sale.order()
        sale.confirm()

        account = self.create_account()
        payment.method.destination_account = account

        payment.pay()

        # Verify if payment is referenced on account transaction.
        transactions = self.store.find(AccountTransaction, account=account, payment=payment)
        self.assertEquals(transactions.count(), 1)
        original_transaction = list(transactions)[0]
        self.assertEquals(original_transaction.operation_type, AccountTransaction.TYPE_IN)
        self.assertEquals(original_transaction.value, payment.value)

        entry = PaymentChangeHistory(payment=payment,
                                     change_reason=u'foo',
                                     store=self.store)
        payment.set_not_paid(entry)

        # Now that the payment was reverted, there should also be a reverted operation,
        # and the payment will not be referenced in transactions anymore.
        transactions = self.store.find(AccountTransaction, account=account, payment=payment)
        self.assertEquals(transactions.count(), 0)

        new_transactions = self.store.find(AccountTransaction, source_account=account)
        self.assertEquals(new_transactions.count(), 1)
        reversed_transaction = list(new_transactions)[0]
        self.assertEquals(reversed_transaction.operation_type, AccountTransaction.TYPE_OUT)
        self.assertEquals(self.store.find(AccountTransaction, payment=payment).count(), 0)

        # Verify all transactions - The created account, will be referenced as source
        # and destination account.
        query = Or(AccountTransaction.source_account == account,
                   AccountTransaction.account == account)
        total_transactions = self.store.find(AccountTransaction, query).count()
        self.assertEquals(total_transactions, 2)
        payment.pay()
        self.assertEquals(self.store.find(AccountTransaction, payment=payment).count(), 1)
        total_transactions = self.store.find(AccountTransaction, query).count()
        self.assertEquals(total_transactions, 3)


class TestPaymentComment(DomainTest):
    def test_comment(self):
        payment = self.create_payment(Payment.TYPE_OUT)
        self.assertEqual(payment.comments_number, 0)
        user = self.create_user()
        comment = PaymentComment(author=user, payment=payment, comment=u'',
                                 store=self.store)
        self.assertEqual(payment.comments_number, 1)
        self.assertEqual(list(payment.comments)[0], comment)
