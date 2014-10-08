# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007-2008 Async Open Source <http://www.async.com.br>
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

__tests__ = 'stoqlib/domain/payment/method.py'

import datetime
from decimal import Decimal

from stoqlib.database.runtime import get_current_station
from stoqlib.domain.payment.method import PaymentMethod, _
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.domain.till import Till
from stoqlib.exceptions import TillError, PaymentMethodError, DatabaseInconsistency
from stoqlib.lib.dateutils import localnow, localtoday
from stoqlib.lib.defaults import quantize


class _TestPaymentMethod:
    def createInPayment(self):
        sale = self.create_sale()
        method = PaymentMethod.get_by_name(self.store, self.method_type)
        return method.create_payment(Payment.TYPE_IN, sale.group,
                                     sale.branch, Decimal(100))

    def createOutPayment(self):
        purchase = self.create_purchase_order()
        method = PaymentMethod.get_by_name(self.store, self.method_type)
        return method.create_payment(Payment.TYPE_OUT, purchase.group,
                                     purchase.branch, Decimal(100))

    def createInPayments(self, no=3):
        sale = self.create_sale()
        d = localnow()
        method = PaymentMethod.get_by_name(self.store, self.method_type)
        payments = method.create_payments(Payment.TYPE_IN, sale.group,
                                          sale.branch, Decimal(100),
                                          [d] * no)
        return payments

    def createOutPayments(self, no=3):
        purchase = self.create_purchase_order()
        d = localnow()
        method = PaymentMethod.get_by_name(self.store, self.method_type)
        payments = method.create_payments(Payment.TYPE_OUT, purchase.group,
                                          purchase.branch, Decimal(100),
                                          [d] * no)
        return payments

    def createPayment(self, payment_type):
        if payment_type == Payment.TYPE_OUT:
            order = self.create_purchase_order()
        elif payment_type == Payment.TYPE_IN:
            order = self.create_sale()
        else:
            order = None

        value = Decimal(100)
        method = PaymentMethod.get_by_name(self.store, self.method_type)
        return method.create_payment(payment_type, order.group, order.branch, value)

    def createPayments(self, payment_type, no=3):
        if payment_type == Payment.TYPE_OUT:
            order = self.create_purchase_order()
        elif payment_type == Payment.TYPE_IN:
            order = self.create_sale()
        else:
            order = None

        value = Decimal(100)
        due_dates = [localnow()] * no
        method = PaymentMethod.get_by_name(self.store, self.method_type)
        return method.create_payments(payment_type, order.group, order.branch, value, due_dates)


class _TestPaymentMethodsBase(_TestPaymentMethod):
    def test_create_in_payment(self):
        payment = self.createInPayment()
        self.failUnless(isinstance(payment, Payment))
        self.assertEqual(payment.value, Decimal(100))

    def test_create_out_payment(self):
        payment = self.createOutPayment()
        self.failUnless(isinstance(payment, Payment))
        self.assertEqual(payment.value, Decimal(100))

    def test_create_in_payments(self):
        payments = self.createInPayments()
        athird = quantize(Decimal(100) / Decimal(3))
        rest = quantize(Decimal(100) - (athird * 2))
        self.assertEqual(len(payments), 3)
        self.assertEqual(payments[0].value, athird)
        self.assertEqual(payments[1].value, athird)
        self.assertEqual(payments[2].value, rest)

    def test_create_out_payments(self):
        payments = self.createOutPayments()
        athird = quantize(Decimal(100) / Decimal(3))
        rest = quantize(Decimal(100) - (athird * 2))
        self.assertEqual(len(payments), 3)
        self.assertEqual(payments[0].value, athird)
        self.assertEqual(payments[1].value, athird)
        self.assertEqual(payments[2].value, rest)

    def test_create_payment(self):
        payment = self.createPayment(Payment.TYPE_IN)
        self.failUnless(isinstance(payment, Payment))
        self.assertEqual(payment.value, Decimal(100))

        payment = self.createPayment(Payment.TYPE_OUT)
        self.failUnless(isinstance(payment, Payment))
        self.assertEqual(payment.value, Decimal(100))

    def test_create_payments(self):
        payments = self.createPayments(Payment.TYPE_IN)
        self.assertEqual(len(payments), 3)
        athird = quantize(Decimal(100) / Decimal(3))
        rest = quantize(Decimal(100) - (athird * 2))
        self.assertEqual(payments[0].value, athird)
        self.assertEqual(payments[1].value, athird)
        self.assertEqual(payments[2].value, rest)

        payments = self.createPayments(Payment.TYPE_OUT)
        self.assertEqual(len(payments), 3)
        athird = quantize(Decimal(100) / Decimal(3))
        rest = quantize(Decimal(100) - (athird * 2))
        self.assertEqual(payments[0].value, athird)
        self.assertEqual(payments[1].value, athird)
        self.assertEqual(payments[2].value, rest)

    def test_describe_payment(self):
        sale = self.create_sale()
        method = PaymentMethod.get_by_name(self.store, self.method_type)
        desc = method.describe_payment(sale.group)
        self.failUnless(isinstance(desc, unicode))
        self.failUnless(method.description in desc)

        self.assertRaises(AssertionError, method.describe_payment, sale.group, 0)
        self.assertRaises(AssertionError, method.describe_payment, sale.group, 1, 0)
        self.assertRaises(AssertionError, method.describe_payment, sale.group, 2, 1)
        desc = method.describe_payment(sale.group, 123, 456)
        self.failUnless(u'123' in desc, desc)
        self.failUnless(u'456' in desc, desc)
        self.failUnless(u'123/456' in desc, desc)

    def test_max_in_paymnets(self):
        method = PaymentMethod.get_by_name(self.store, self.method_type)
        max = method.max_installments
        self.assertRaises(ValueError, self.createInPayments, max + 1)

    def test_max_out_paymnets(self):
        method = PaymentMethod.get_by_name(self.store, self.method_type)
        self.createOutPayments(method.max_installments + 1)

    def test_selectable(self):
        method = PaymentMethod.get_by_name(self.store, self.method_type)
        method.selectable()


class TestPaymentMethod(DomainTest, _TestPaymentMethod):
    method_type = u'check'

    def test_activate(self):
        acc = self.create_account()
        method = PaymentMethod(method_name=u'Test', destination_account=acc)
        with self.assertRaises(AssertionError) as error:
            method.activate()
        self.assertEquals(str(error.exception), 'This provider is already '
                                                'active')
        method.is_active = False
        self.assertIsNone(method.activate())

    def test_inactivate(self):
        acc = self.create_account()
        method = PaymentMethod(method_name=u'Test', destination_account=acc)
        self.assertIsNone(method.inactivate())
        method.is_active = False
        with self.assertRaises(AssertionError) as error:
            method.inactivate()
        self.assertEquals(str(error.exception), 'This provider is already '
                                                'inactive')

    def test_get_status_string(self):
        acc = self.create_account()
        method = PaymentMethod(method_name=u'Test', destination_account=acc)
        self.assertEquals(method.get_status_string(), u'Active')
        method.inactivate()
        self.assertEquals(method.get_status_string(), u'Inactive')

    def _createUnclosedTill(self):
        till = Till(station=get_current_station(self.store),
                    store=self.store)
        till.open_till()
        yesterday = localtoday() - datetime.timedelta(1)
        till.opening_date = yesterday

    def test_create_payment(self):
        acc = self.create_account()
        branch = self.create_branch()
        method = PaymentMethod(method_name=u'Test', destination_account=acc)
        group = self.create_payment_group()
        self.create_payment(payment_type=Payment.TYPE_IN, date=None,
                            value=100, method=method, branch=branch,
                            group=group)
        with self.assertRaisesRegexp(
                PaymentMethodError,
                ('You can not create more inpayments for this payment '
                 'group since the maximum allowed for this payment '
                 'method is 1')):
            method.create_payment(payment_type=Payment.TYPE_IN, payment_group=group,
                                  branch=branch, value=100, due_date=None,
                                  description=None, base_value=None,
                                  payment_number=None)

        self.create_payment(payment_type=Payment.TYPE_IN, date=None,
                            value=100, method=method, branch=branch,
                            group=group)
        with self.assertRaises(DatabaseInconsistency):
            method.create_payment(payment_type=Payment.TYPE_IN, payment_group=group,
                                  branch=branch, value=100, due_date=None,
                                  description=None, base_value=None,
                                  payment_number=None)

    def test_create_payments_without_installments(self):
        acc = self.create_account()
        branch = self.create_branch()
        method = PaymentMethod(method_name=u'Test', destination_account=acc)
        group = self.create_payment_group()
        with self.assertRaises(ValueError) as error:
            method.create_payments(payment_type=Payment.TYPE_IN, group=group,
                                   branch=branch, value=Decimal(100),
                                   due_dates=[])
        self.assertEquals(str(error.exception), _('Need at least one '
                                                  'installment'))

    def test_create_out_payment_un_closed_till(self):
        self._createUnclosedTill()
        payment = self.createOutPayment()
        self.failUnless(isinstance(payment, Payment))

    def test_create_out_payments_un_closed_till(self):
        # Test for bug 3270
        self._createUnclosedTill()
        self.createOutPayments()

    def test_create_in_payment_un_closed_till(self):
        self._createUnclosedTill()
        self.assertRaises(TillError, self.createInPayment)

    def test_create_in_payments_un_closed_till(self):
        self._createUnclosedTill()
        self.assertRaises(TillError, self.createInPayments)

    def test_create_payment_un_closed_till(self):
        self._createUnclosedTill()
        self.assertRaises(TillError, self.createPayment,
                          Payment.TYPE_IN)

        self.createPayment(Payment.TYPE_OUT)

    def test_create_payments_un_closed_till(self):
        self._createUnclosedTill()
        self.assertRaises(TillError, self.createPayments,
                          Payment.TYPE_IN)

        self.createPayments(Payment.TYPE_OUT)

    def test_get_active_methods(self):
        methods = PaymentMethod.get_active_methods(self.store)
        self.assertTrue(methods)
        self.assertEquals(len(methods), 10)
        self.assertEquals(methods[0].method_name, u'bill')
        self.assertEquals(methods[1].method_name, u'card')
        self.assertEquals(methods[2].method_name, u'check')
        self.assertEquals(methods[3].method_name, u'credit')
        self.assertEquals(methods[4].method_name, u'deposit')
        self.assertEquals(methods[5].method_name, u'money')
        self.assertEquals(methods[6].method_name, u'multiple')
        self.assertEquals(methods[7].method_name, u'online')
        self.assertEquals(methods[8].method_name, u'store_credit')
        self.assertEquals(methods[9].method_name, u'trade')

    def test_get_creditable_methods(self):
        # Incoming payments
        methods = PaymentMethod.get_creatable_methods(
            self.store, Payment.TYPE_IN, separate=False)
        self.assertTrue(methods)
        self.assertEquals(len(methods), 8)
        self.assertEquals(methods[0].method_name, u'bill')
        self.assertEquals(methods[1].method_name, u'card')
        self.assertEquals(methods[2].method_name, u'check')
        self.assertEquals(methods[3].method_name, u'credit')
        self.assertEquals(methods[4].method_name, u'deposit')
        self.assertEquals(methods[5].method_name, u'money')
        self.assertEquals(methods[6].method_name, u'multiple')
        self.assertEquals(methods[7].method_name, u'store_credit')

        methods = PaymentMethod.get_creatable_methods(
            self.store, Payment.TYPE_OUT, separate=False)
        self.assertTrue(methods)
        self.assertEquals(len(methods), 4)
        self.assertEquals(methods[0].method_name, u'bill')
        self.assertEquals(methods[1].method_name, u'check')
        self.assertEquals(methods[2].method_name, u'deposit')
        self.assertEquals(methods[3].method_name, u'money')

    def test_get_creditable_methods_separate(self):
        methods = PaymentMethod.get_creatable_methods(
            self.store, Payment.TYPE_IN, separate=True)
        self.assertTrue(methods)
        self.assertEquals(len(methods), 7)
        self.assertEquals(methods[0].method_name, u'bill')
        self.assertEquals(methods[1].method_name, u'card')
        self.assertEquals(methods[2].method_name, u'check')
        self.assertEquals(methods[3].method_name, u'credit')
        self.assertEquals(methods[4].method_name, u'deposit')
        self.assertEquals(methods[5].method_name, u'money')
        self.assertEquals(methods[6].method_name, u'store_credit')

        methods = PaymentMethod.get_creatable_methods(
            self.store, Payment.TYPE_OUT, separate=True)
        self.assertTrue(methods)
        self.assertEquals(len(methods), 4)
        self.assertEquals(methods[0].method_name, u'bill')
        self.assertEquals(methods[1].method_name, u'check')
        self.assertEquals(methods[2].method_name, u'deposit')
        self.assertEquals(methods[3].method_name, u'money')

    def test_get_editable_methods(self):
        methods = PaymentMethod.get_editable_methods(self.store)
        self.assertTrue(methods)
        self.assertEquals(len(methods), 8)
        self.assertEquals(methods[0].method_name, u'bill')
        self.assertEquals(methods[1].method_name, u'card')
        self.assertEquals(methods[2].method_name, u'check')
        self.assertEquals(methods[3].method_name, u'credit')
        self.assertEquals(methods[4].method_name, u'deposit')
        self.assertEquals(methods[5].method_name, u'money')
        self.assertEquals(methods[6].method_name, u'multiple')
        self.assertEquals(methods[7].method_name, u'store_credit')

        methods_names = [m.method_name for m in methods]
        self.assertFalse(u'online' in methods_names)
        self.assertFalse(u'trade' in methods_names)

    def test_get_by_account(self):
        account = self.create_account()
        methods = PaymentMethod.get_by_account(self.store, account)
        self.assertTrue(methods.is_empty())
        PaymentMethod(store=self.store,
                      method_name=u'test',
                      destination_account=account)
        methods = PaymentMethod.get_by_account(self.store, account)
        self.assertFalse(methods.is_empty())


class TestMoney(DomainTest, _TestPaymentMethodsBase):
    method_type = u'money'

    def test_create_in_payments(self):
        pass

    def test_create_out_payments(self):
        pass

    def test_create_payments(self):
        pass


class TestCheck(DomainTest, _TestPaymentMethodsBase):
    method_type = u'check'

    def test_check_data_created(self):
        payment = self.createInPayment()
        method = PaymentMethod.get_by_name(self.store, self.method_type)
        check_data = method.operation.get_check_data_by_payment(payment)
        self.failUnless(check_data)

    def test_bank(self):
        sale = self.create_sale()
        method = PaymentMethod.get_by_name(self.store, self.method_type)
        payment = method.create_payment(Payment.TYPE_OUT, sale.group, sale.branch, Decimal(10))
        check_data = method.operation.get_check_data_by_payment(payment)
        check_data.bank_account.bank_number = 123
        self.assertEquals(payment.bank_account_number, 123)


class TestBill(DomainTest, _TestPaymentMethodsBase):
    method_type = u'bill'


class TestCard(DomainTest, _TestPaymentMethodsBase):
    method_type = u'card'

    def test_card_data(self):
        payment = self.createInPayment()
        method = PaymentMethod.get_by_name(self.store, self.method_type)
        card_data = method.operation.get_card_data_by_payment(payment)
        self.failUnless(card_data)


class TestDeposit(DomainTest, _TestPaymentMethodsBase):
    method_type = u'deposit'
