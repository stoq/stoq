# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011 Async Open Source <http://www.async.com.br>
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

from stoqlib.domain.account import (Account, AccountTransaction,
                                    AccountTransactionView)
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.domain.interfaces import IDescribable
from stoqlib.exceptions import PaymentError
from stoqlib.lib.parameters import sysparam


class TestAccount(DomainTest):

    def testAccount(self):
        account = self.create_account()
        self.failUnless(account)

    def testAccountGetByStation(self):
        station = self.create_station()
        account = Account.get_by_station(self.trans, station)
        self.failIf(account)
        account = self.create_account()
        account.station = station

        account = Account.get_by_station(self.trans, station)
        self.failUnless(account)

        self.assertRaises(TypeError, Account.get_by_station,
                          self.trans, None)
        self.assertRaises(TypeError, Account.get_by_station,
                          self.trans, object())

    def testAccountLongDescription(self):
        a1 = self.create_account()
        a1.description = "first"
        a2 = self.create_account()
        a2.description = "second"
        a2.parent = a1
        a3 = self.create_account()
        a3.description = "third"
        a3.parent = a2

        self.assertEquals(a1.long_description, 'first')
        self.assertEquals(a2.long_description, 'first:second')
        self.assertEquals(a3.long_description, 'first:second:third')

    def testAccountTransactions(self):
        account = self.create_account()
        self.failIf(account.transactions)

        transaction = self.create_account_transaction(account)

        self.failUnless(account.transactions)
        self.failUnless(transaction in account.transactions)

        a2 = self.create_account()
        t2 = self.create_account_transaction(a2)

        self.failIf(t2 in account.transactions)

        t2.source_account = account
        t2.sync()

        self.failUnless(t2 in account.transactions)

    def testAccountCanRemove(self):
        account = self.create_account()
        self.failUnless(account.can_remove())

        self.failIf(sysparam(self.trans).TILLS_ACCOUNT.can_remove())
        self.failIf(sysparam(self.trans).IMBALANCE_ACCOUNT.can_remove())
        self.failIf(sysparam(self.trans).BANKS_ACCOUNT.can_remove())

        station = self.create_station()
        account.station = station

        self.failIf(account.can_remove())

        account.station = None

        self.failUnless(account.can_remove())

        a2 = self.create_account()

        self.failUnless(account.can_remove())

        a2.parent = account

        self.failIf(account.can_remove())

    def testAccountRemove(self):
        a1 = self.create_account()
        a2 = self.create_account()

        imbalance_account = sysparam(self.trans).IMBALANCE_ACCOUNT

        t1 = self.create_account_transaction(a1)
        t1.source_account = a2
        t1.sync()

        t2 = self.create_account_transaction(a2)
        t2.source_account = a1
        t2.sync()

        a1.station = self.create_station()
        self.assertRaises(TypeError, a1.remove)
        a1.station = None

        a1.remove(self.trans)

        self.assertEquals(t1.account, imbalance_account)
        self.assertEquals(t2.source_account, imbalance_account)

    def testHasChildAccounts(self):
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

    def testGetTypeLabel(self):
        a = self.create_account()
        a.account_type = Account.TYPE_CASH
        self.assertEquals(a.get_type_label(True), "Spend")
        self.assertEquals(a.get_type_label(False), "Receive")

        a.account_type = Account.TYPE_BANK
        self.assertEquals(a.get_type_label(True), "Withdrawal")
        self.assertEquals(a.get_type_label(False), "Deposit")


class TestAccountTransaction(DomainTest):

    def testGetOtherAccount(self):
        a1 = self.create_account()
        a2 = self.create_account()

        t1 = self.create_account_transaction(a1)
        t2 = self.create_account_transaction(a2)

        t1.source_account = a2
        t2.source_account = a1

        t1.sync()
        t2.sync()

        self.assertEquals(t1.get_other_account(a1), a2)
        self.assertEquals(t1.get_other_account(a2), a1)

        self.assertEquals(t2.get_other_account(a1), a2)
        self.assertEquals(t2.get_other_account(a2), a1)

    def testSetOtherAccount(self):
        a1 = self.create_account()
        a2 = self.create_account()

        t1 = self.create_account_transaction(a1)
        t1.source_account = a2
        t1.sync()

        t2 = self.create_account_transaction(a2)
        t2.source_account = a1
        t2.sync()

        t1.set_other_account(a1, a2)
        t1.syncUpdate()
        self.assertEquals(t1.account, a1)
        self.assertEquals(t1.source_account, a2)
        t1.set_other_account(a2, a2)
        t1.syncUpdate()
        self.assertEquals(t1.account, a2)
        self.assertEquals(t1.source_account, a2)

        t2.set_other_account(a1, a2)
        t2.syncUpdate()
        self.assertEquals(t2.account, a2)
        self.assertEquals(t2.source_account, a1)
        t2.set_other_account(a2, a2)
        t2.syncUpdate()
        self.assertEquals(t2.account, a2)
        self.assertEquals(t2.source_account, a2)

    def testCreateFromPayment(self):
        sale = self.create_sale()
        self.add_product(sale)
        payment = self.add_payments(sale, method_type='check').payment
        sale.order()
        sale.confirm()
        account = self.create_account()
        payment.method.destination_account = account
        self.assertRaises(PaymentError,
                          AccountTransaction.create_from_payment, payment)
        payment.pay()
        transaction = AccountTransaction.create_from_payment(payment)

        imbalance_account = sysparam(self.trans).IMBALANCE_ACCOUNT
        self.assertEquals(transaction.source_account, imbalance_account)
        self.assertEquals(transaction.account, account)
        self.assertEquals(transaction.payment, payment)


class TestAccountTransactionView(DomainTest):
    def testGetForAccount(self):
        a = self.create_account()
        t = self.create_account_transaction(a)
        t.value = 100
        t.source_account = a
        t.sync()
        views = AccountTransactionView.get_for_account(a, self.trans)
        self.assertEquals(views.count(), 1)
        v1 = views[0]
        self.assertEquals(v1.value, t.value)
        self.assertEquals(v1.code, t.code)
        self.assertEquals(v1.description, t.description)
        self.assertEquals(v1.date, t.date)

    def testGetAccountDescription(self):
        a1 = self.create_account()
        a1.description = "Source Account"
        a2 = self.create_account()
        a2.description = "Account"

        t = self.create_account_transaction(a1)
        t.value = 100
        t.source_account = a1
        t.account = a2
        t.sync()

        views = AccountTransactionView.get_for_account(a1, self.trans)
        self.assertEquals(views[0].get_account_description(a1), "Account")
        self.assertEquals(views[0].get_account_description(a2), "Source Account")

    def testGetValue(self):
        a1 = self.create_account()
        a1.description = "Source Account"
        a2 = self.create_account()
        a2.description = "Account"

        t = self.create_account_transaction(a1)
        t.value = 100
        t.source_account = a1
        t.account = a2
        t.sync()

        views = AccountTransactionView.get_for_account(a1, self.trans)
        self.assertEquals(views[0].get_value(a1), -100)
        self.assertEquals(views[0].get_value(a2), 100)

    def testTransaction(self):
        a = self.create_account()
        t = self.create_account_transaction(a)

        views = AccountTransactionView.get_for_account(a, self.trans)
        self.assertEquals(views[0].transaction, t)
