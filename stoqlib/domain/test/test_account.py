# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011-2013 Async Open Source <http://www.async.com.br>
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

__tests__ = 'stoqlib/domain/account.py'

import datetime
from storm.exceptions import OrderLoopError

from stoqlib.domain.account import (Account, AccountTransaction,
                                    AccountTransactionView,
                                    BillOption)
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.domain.interfaces import IDescribable
from stoqlib.exceptions import PaymentError
from stoqlib.lib.parameters import sysparam


class TestAccount(DomainTest):

    def test_account(self):
        account = self.create_account()
        self.failUnless(account)

    def test_account_get_by_station(self):
        station = self.create_station()
        account = Account.get_by_station(self.store, station)
        self.failIf(account)
        account = self.create_account()
        account.station = station

        account = Account.get_by_station(self.store, station)
        self.failUnless(account)

        self.assertRaises(TypeError, Account.get_by_station,
                          self.store, None)
        self.assertRaises(TypeError, Account.get_by_station,
                          self.store, object())

    def test_account_long_description(self):
        a1 = self.create_account()
        a1.description = u"first"
        a2 = self.create_account()
        a2.description = u"second"
        a2.parent = a1
        a3 = self.create_account()
        a3.description = u"third"
        a3.parent = a2

        # Testing Loop error
        with self.assertRaises(OrderLoopError):
            a1.parent = a2
            self.assertEquals(a1.long_description, u'first')

        a1.parent = None
        self.assertEquals(a1.long_description, u'first')
        self.assertEquals(a2.long_description, u'first:second')
        self.assertEquals(a3.long_description, u'first:second:third')

    def test_account_transactions(self):
        account = self.create_account()
        self.assertTrue(account.transactions.is_empty())

        transaction = self.create_account_transaction(account)

        self.assertFalse(account.transactions.is_empty())
        self.failUnless(transaction in account.transactions)

        a2 = self.create_account()
        t2 = self.create_account_transaction(a2)

        self.failIf(t2 in account.transactions)

        t2.source_account = account
        self.store.flush()

        self.failUnless(t2 in account.transactions)

    def test_account_can_remove(self):
        account = self.create_account()
        self.failUnless(account.can_remove())

        self.failIf(sysparam.get_object(self.store, 'TILLS_ACCOUNT').can_remove())
        self.failIf(sysparam.get_object(self.store, 'IMBALANCE_ACCOUNT').can_remove())
        self.failIf(sysparam.get_object(self.store, 'BANKS_ACCOUNT').can_remove())

        station = self.create_station()
        account.station = station

        self.failIf(account.can_remove())

        account.station = None

        self.failUnless(account.can_remove())

        a2 = self.create_account()

        self.failUnless(account.can_remove())

        a2.parent = account

        self.failIf(account.can_remove())

    def test_account_remove(self):
        a1 = self.create_account()
        a2 = self.create_account()

        imbalance_account = sysparam.get_object(self.store, 'IMBALANCE_ACCOUNT')

        t1 = self.create_account_transaction(a1)
        t1.source_account = a2
        self.store.flush()

        t2 = self.create_account_transaction(a2)
        t2.source_account = a1
        self.store.flush()

        a2.parent = a1
        with self.assertRaises(TypeError):
            a1.remove(self.store)
        a2.parent = None

        a1.station = self.create_station()
        self.assertRaises(TypeError, a1.remove)
        a1.station = None

        a1.remove(self.store)

        self.assertEquals(t1.account, imbalance_account)
        self.assertEquals(t2.source_account, imbalance_account)

    def test_account_remove_with_bank_account(self):
        account = self.create_account()
        bank = self.create_bank_account(account=account)
        BillOption(option=u'foo',
                   value=u'bar',
                   bank_account=bank,
                   store=self.store)
        account.remove(self.store)

    def test_has_child_accounts(self):
        a1 = self.create_account()
        a2 = self.create_account()

        self.failIf(a1.has_child_accounts())
        self.failIf(a2.has_child_accounts())

        a2.parent = a1

        self.failUnless(a1.has_child_accounts())
        self.failIf(a2.has_child_accounts())

    def testIDescribable(self):
        a1 = self.create_account()
        self.assertEquals(a1.long_description, IDescribable(a1).get_description())

    def test_get_type_label(self):
        a = self.create_account()
        a.account_type = Account.TYPE_CASH
        self.assertEquals(a.get_type_label(True), u"Spend")
        self.assertEquals(a.get_type_label(False), u"Receive")

        a.account_type = Account.TYPE_BANK
        self.assertEquals(a.get_type_label(True), u"Withdrawal")
        self.assertEquals(a.get_type_label(False), u"Deposit")

    def test_get_children_for(self):
        a1 = self.create_account()
        self.assertTrue(Account.get_children_for(self.store, a1).is_empty())

        a2 = self.create_account()
        a2.parent = a1
        self.assertEquals(Account.get_children_for(self.store, a1).one(), a2)

        a3 = self.create_account()
        self.assertEquals(Account.get_children_for(self.store, a1).one(), a2)
        a3.parent = a1
        self.assertEquals(
            set(Account.get_children_for(self.store, a1)),
            set([a2, a3]))

    def test_get_total_for_interval(self):
        a = self.create_account()
        start = datetime.datetime(2010, 1, 1)
        end = datetime.datetime(2010, 12, 31)
        self.assertEquals(a.get_total_for_interval(start, end), 0)

        transaction = self.create_account_transaction(a)
        self.assertEquals(
            a.get_total_for_interval(start, end), 0)
        transaction.date = datetime.datetime(2010, 6, 1)
        transaction.value = 100

        self.assertEquals(
            a.get_total_for_interval(start, end), 100)

        transaction = self.create_account_transaction(a)
        transaction.date = datetime.datetime(2010, 12, 31)
        transaction.value = 100

        self.assertEquals(
            a.get_total_for_interval(start, end), 200)

        transaction = self.create_account_transaction(a)
        transaction.date = datetime.datetime(2009, 1, 1)
        transaction.value = 100

        transaction = self.create_account_transaction(a)
        transaction.date = datetime.datetime(2012, 1, 1)
        transaction.value = 100

        self.assertEquals(
            a.get_total_for_interval(start, end), 200)

    def test_get_total_for_interval_error(self):
        a = self.create_account()
        good = datetime.datetime(2010, 1, 1)
        bad = 'bad type'
        self.assertRaises(TypeError, a.get_total_for_interval, good, bad)
        self.assertRaises(TypeError, a.get_total_for_interval, bad, good)

    def test_matches(self):
        a1 = self.create_account()
        a2 = self.create_account()
        a2.parent = a1
        accounts = list(self.store.find(Account))
        for account in accounts:
            if a1.matches(account.id):
                result1 = True
            if a2.matches(account.id):
                result2 = True
        self.assertTrue(result1)
        self.assertTrue(result2)
        a3 = self.create_account()
        result3 = a1.matches(a3.id)
        self.assertFalse(result3)


class TestAccountTransaction(DomainTest):

    def test_create_reverse(self):
        source_account = self.create_account()
        at = self.create_account_transaction(account=source_account, value=10)
        transactions = list(self.store.find(AccountTransaction, account=source_account))
        self.assertEquals(len(transactions), 1)
        original_transaction = transactions[0]
        self.assertEquals(original_transaction.operation_type, AccountTransaction.TYPE_OUT)

        at.create_reverse()
        reversed_transactions = list(self.store.find(AccountTransaction,
                                                     source_account=source_account))
        self.assertEquals(len(reversed_transactions), 1)
        reversed_transaction = reversed_transactions[0]
        self.assertEquals(reversed_transaction.operation_type, AccountTransaction.TYPE_IN)

    def test_get_inverted_operation(self):
        # IN -> OUT
        operation_type = AccountTransaction.TYPE_IN
        inverted_type = AccountTransaction.get_inverted_operation_type(operation_type)
        self.assertEquals(inverted_type, AccountTransaction.TYPE_OUT)
        # OUT -> IN
        operation_type = AccountTransaction.TYPE_OUT
        inverted_type = AccountTransaction.get_inverted_operation_type(operation_type)
        self.assertEquals(inverted_type, AccountTransaction.TYPE_IN)

    def test_invert_transaction_type(self):
        account1 = self.create_account()
        account2 = self.create_account()
        transaction = self.create_account_transaction(account=account2, source=account1,
                                                      incoming=True)

        transaction.invert_transaction_type()
        self.assertEquals(transaction.source_account, account2)
        self.assertEquals(transaction.account, account1)
        self.assertEquals(transaction.operation_type, AccountTransaction.TYPE_OUT)

    def test_get_other_account(self):
        a1 = self.create_account()
        a2 = self.create_account()

        t1 = self.create_account_transaction(account=a1, source=a2)
        t2 = self.create_account_transaction(account=a2, source=a1)

        self.assertEquals(t1.get_other_account(a1), a2)
        self.assertEquals(t1.get_other_account(a2), a1)

        self.assertEquals(t2.get_other_account(a1), a2)
        self.assertEquals(t2.get_other_account(a2), a1)

        a3 = self.create_account()
        with self.assertRaises(AssertionError):
            t1.get_other_account(account=a3)

    def test_set_other_account(self):
        a1 = self.create_account()
        a2 = self.create_account()

        t1 = self.create_account_transaction(account=a1, source=a2)

        t2 = self.create_account_transaction(account=a2, source=a1)

        t1.set_other_account(a1, a2)
        self.store.flush()
        self.assertEquals(t1.account, a1)
        self.assertEquals(t1.source_account, a2)
        t1.set_other_account(a2, a2)
        self.store.flush()
        self.assertEquals(t1.account, a2)
        self.assertEquals(t1.source_account, a2)

        t2.set_other_account(a1, a2)
        self.store.flush()
        self.assertEquals(t2.account, a2)
        self.assertEquals(t2.source_account, a1)
        t2.set_other_account(a2, a2)
        self.store.flush()
        self.assertEquals(t2.account, a2)
        self.assertEquals(t2.source_account, a2)

        a3 = self.create_account()
        with self.assertRaises(AssertionError):
            t1.set_other_account(a3, a1)
            t2.set_other_account(a3, a2)

    def test_create_from_payment(self):
        sale = self.create_sale()
        self.add_product(sale)
        payment = self.add_payments(sale, method_type=u'check')[0]
        sale.order()
        sale.confirm()
        account = self.create_account()
        payment.method.destination_account = account
        with self.assertRaisesRegexp(PaymentError, "Payment needs to be paid"):
            AccountTransaction.create_from_payment(payment)
        payment.pay()
        transaction = AccountTransaction.create_from_payment(payment)

        imbalance_account = sysparam.get_object(self.store, 'IMBALANCE_ACCOUNT')
        self.assertEquals(transaction.source_account, imbalance_account)
        self.assertEquals(transaction.account, account)
        self.assertEquals(transaction.payment, payment)
        self.assertEquals(transaction.operation_type, AccountTransaction.TYPE_IN)

        # Payment from purchase.
        purchase = self.create_purchase_order()
        purchase.status = PurchaseOrder.ORDER_PENDING
        purchase.add_item(self.create_sellable(), 1)
        payment = self.add_payments(purchase, method_type=u'money')[0]
        purchase.confirm()
        account = self.create_account()
        payment.method.destination_account = account
        with self.assertRaisesRegexp(PaymentError, "Payment needs to be paid"):
            AccountTransaction.create_from_payment(payment)

        payment.pay()
        transaction = AccountTransaction.create_from_payment(payment)
        imbalance_account = sysparam.get_object(self.store, 'IMBALANCE_ACCOUNT')
        self.assertEquals(transaction.source_account, account)
        self.assertEquals(transaction.account, imbalance_account)
        self.assertEquals(transaction.payment, payment)
        self.assertEquals(transaction.operation_type, AccountTransaction.TYPE_OUT)


class TestAccountTransactionView(DomainTest):
    def test_get_for_account(self):
        a = self.create_account()
        t = self.create_account_transaction(a)
        t.value = 100
        t.source_account = a
        self.store.flush()
        views = AccountTransactionView.get_for_account(a, self.store)
        self.assertEquals(views.count(), 1)
        v1 = views[0]
        self.assertEquals(v1.value, t.value)
        self.assertEquals(v1.code, t.code)
        self.assertEquals(v1.description, t.description)
        self.assertEquals(v1.date.replace(tzinfo=None), t.date)

    def test_get_account_description(self):
        a1 = self.create_account()
        a1.description = u"Source Account"
        a2 = self.create_account()
        a2.description = u"Account"
        a3 = self.create_account()
        t = self.create_account_transaction(a1)
        t.value = 100
        t.source_account = a1
        t.account = a2
        self.store.flush()
        self.store.autoreload(t)
        views = AccountTransactionView.get_for_account(a1, self.store)
        self.assertEquals(views[0].get_account_description(a1), u"Account")
        self.assertEquals(views[0].get_account_description(a2), u"Source Account")
        with self.assertRaises(AssertionError):
            views[0].get_account_description(a3)

    def test_get_value(self):
        a1 = self.create_account()
        a1.description = u"Source Account"
        a2 = self.create_account()
        a2.description = u"Account"

        transaction = self.create_account_transaction(a1, incoming=True)
        transaction.value = 100
        transaction.source_account = a1
        transaction.account = a2
        self.store.flush()

        views = AccountTransactionView.get_for_account(a1, self.store)
        self.assertEquals(views[0].get_value(a1), -100)
        self.assertEquals(views[0].get_value(a2), 100)

        # Source account equal to destination account
        transaction.account = a1
        views = AccountTransactionView.get_for_account(a1, self.store)
        self.assertEquals(views[0].get_value(a1), 100)
        transaction.operation_type = AccountTransaction.TYPE_OUT
        views = AccountTransactionView.get_for_account(a1, self.store)
        self.assertEquals(views[0].get_value(a1), -100)

    def test_transaction(self):
        a = self.create_account()
        t = self.create_account_transaction(a)

        views = AccountTransactionView.get_for_account(a, self.store)
        self.assertEquals(views[0].transaction, t)
