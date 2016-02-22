# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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

__tests__ = 'stoqlib/domain/payment/operation.py'

import mock
from stoqdrivers.enum import PaymentMethodType

from stoqlib.domain.account import Account
from stoqlib.domain.payment.card import CreditCardData
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.operation import (BillPaymentOperation,
                                              CardPaymentOperation,
                                              CheckPaymentOperation,
                                              CreditPaymentOperation,
                                              DepositPaymentOperation,
                                              InvalidPaymentOperation,
                                              MoneyPaymentOperation,
                                              MultiplePaymentOperation,
                                              OnlinePaymentOperation,
                                              StoreCreditPaymentOperation,
                                              TradePaymentOperation)
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.reporting.boleto import BillReport
from stoqlib.reporting.booklet import BookletReport


class _TestOperation(DomainTest):
    method_name = None

    def test_pay_on_sale_confirm(self):
        self.assertFalse(self.operation.pay_on_sale_confirm())

    def test_payment_create(self):
        payment = self.create_payment()
        self.operation.payment_create(payment)

    def test_payment_delete(self):
        payment = self.create_payment()
        self.operation.payment_create(payment)
        self.operation.payment_delete(payment)

    def test_create_transaction(self):
        self.operation.create_transaction()

    def test_selectable(self):
        method = PaymentMethod.get_by_name(self.store, self.method_name)
        self.operation.selectable(method)

    def test_creatable(self):
        method = PaymentMethod.get_by_name(self.store, self.method_name)
        self.operation.creatable(method, Payment.TYPE_IN, True)
        self.operation.creatable(method, Payment.TYPE_IN, False)
        self.operation.creatable(method, Payment.TYPE_OUT, True)
        self.operation.creatable(method, Payment.TYPE_OUT, False)

    def test_get_constant(self):
        payment = self.create_payment()
        self.operation.payment_create(payment)
        self.assertEquals(self.operation.get_constant(payment),
                          PaymentMethodType.MONEY)

    def test_can_cancel(self):
        payment = self.create_payment()
        self.operation.can_cancel(payment)

    def test_can_change_due_date(self):
        payment = self.create_payment()
        self.operation.can_change_due_date(payment)

    def test_can_pay(self):
        payment = self.create_payment()
        self.operation.can_pay(payment)

    def test_can_set_not_paid(self):
        payment = self.create_payment()
        self.operation.can_set_not_paid(payment)

    def test_can_print(self):
        payment = self.create_payment()
        self.assertFalse(self.operation.can_print(payment))

    def test_print_(self):
        payment = self.create_payment()
        self.assertFalse(self.operation.print_([payment]))
        self.assertFalse(self.operation.print_([]))

    def test_require_person(self):
        self.operation.require_person(Payment.TYPE_IN)
        self.operation.require_person(Payment.TYPE_OUT)


class TestBillPaymentOperation(_TestOperation):
    method_name = u'bill'
    operation = BillPaymentOperation()

    def test_get_constant(self):
        payment = self.create_payment()
        self.assertEquals(self.operation.get_constant(payment),
                          PaymentMethodType.BILL)

    def test_can_print(self):
        payment = self.create_payment()
        self.assertFalse(self.operation.can_print(payment))

        payment.status = Payment.STATUS_PENDING
        self.assertTrue(self.operation.can_print(payment))

    @mock.patch('stoqlib.reporting.boleto.warning')
    def test_print_(self, warning):
        self.assertEquals(self.operation.print_([]), BillReport)

        method = PaymentMethod.get_by_name(self.store, self.method_name)
        payment = self.create_payment(method=method)
        self.assertEquals(self.operation.print_([payment]), None)
        account = self.create_account()
        account.account_type = Account.TYPE_BANK
        account.bank = self.create_bank_account()
        payment.method.destination_account = account

        self.assertEquals(self.operation.print_([payment]), BillReport)


class TestCardPaymentOperation(_TestOperation):
    method_name = u'card'
    operation = CardPaymentOperation()

    def test_payment_delete(self):
        method = PaymentMethod.get_by_name(self.store, self.method_name)

        payment = self.create_payment(method=method)
        credit_card_data = payment.method.operation.payment_create(payment=payment)

        total = self.store.find(CreditCardData,
                                payment=credit_card_data.payment).count()
        self.assertEquals(total, 1)

        payment.delete()
        total = self.store.find(CreditCardData,
                                payment=credit_card_data.payment).count()

        self.assertEquals(total, 0)

    def test_get_constant(self):
        payment = self.create_payment()
        self.operation.payment_create(payment)
        self.assertEquals(self.operation.get_constant(payment),
                          PaymentMethodType.CREDIT_CARD)


class TestCheckPaymentOperation(_TestOperation):
    method_name = u'check'
    operation = CheckPaymentOperation()

    def test_get_constant(self):
        payment = self.create_payment()
        self.assertEquals(self.operation.get_constant(payment),
                          PaymentMethodType.CHECK)


class TestCreditPaymentOperation(_TestOperation):
    method_name = u'credit'
    operation = CreditPaymentOperation()

    def test_pay_on_sale_confirm(self):
        self.assertTrue(self.operation.pay_on_sale_confirm())


class TestDepositPaymentOperation(_TestOperation):
    method_name = u'deposit'
    operation = DepositPaymentOperation()


class TestInvalidPaymentOperation(_TestOperation):
    method_name = u'invalid'
    operation = InvalidPaymentOperation()


class TestMoneyPaymentOperation(_TestOperation):
    method_name = u'money'
    operation = MoneyPaymentOperation()

    def test_pay_on_sale_confirm(self):
        self.assertTrue(self.operation.pay_on_sale_confirm())


class TestMultiplePaymentOperation(_TestOperation):
    method_name = u'multiple'
    operation = MultiplePaymentOperation()

    def test_get_constant(self):
        payment = self.create_payment()
        self.assertEquals(self.operation.get_constant(payment),
                          PaymentMethodType.MULTIPLE)


class TestOnlinePaymentOperation(_TestOperation):
    method_name = u'online'
    operation = OnlinePaymentOperation()


class TestStoreCreditPaymentOperation(_TestOperation):
    method_name = u'store_credit'
    operation = StoreCreditPaymentOperation()

    def test_can_print(self):
        payment = self.create_payment()
        self.assertFalse(self.operation.can_print(payment))

        payment = self.create_payment()
        payment.group.payer = self.create_person()
        self.assertFalse(self.operation.can_print(payment))

        payment.status = Payment.STATUS_PENDING
        self.assertTrue(self.operation.can_print(payment))

    def test_require_person(self):
        self.assertTrue(self.operation.require_person(Payment.TYPE_IN))
        self.assertFalse(self.operation.require_person(Payment.TYPE_OUT))

    def test_print_(self):
        payment = self.create_payment()
        self.assertEquals(self.operation.print_([payment]), BookletReport)


class TestTradePaymentOperation(_TestOperation):
    method_name = u'trade'
    operation = TradePaymentOperation()
