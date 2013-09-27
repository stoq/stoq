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

from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment
from stoqlib.gui.slaves.paymentmethodslave import SelectPaymentMethodSlave
from stoqlib.gui.test.uitestutils import GUITest

__tests__ = 'stoqlib/gui/slaves/paymentmethodslave.py'


class TestSelectPaymentMethodSlave(GUITest):
    def test_init(self):
        with self.assertRaisesRegexp(ValueError, "payment_type must be set"):
            SelectPaymentMethodSlave(payment_type=None)

    def test_init_default_method(self):
        check_method = self.store.find(PaymentMethod,
                                       method_name=u'check').one()
        multiple_method = self.store.find(PaymentMethod,
                                          method_name=u'multiple').one()
        money_method = self.store.find(PaymentMethod,
                                       method_name=u'money').one()

        # Check should be selected here since it was passed as default ethod
        slave = SelectPaymentMethodSlave(store=self.store,
                                         payment_type=Payment.TYPE_IN,
                                         default_method=u'check')
        self.assertEqual(slave.get_selected_method(), check_method)

        with self.sysparam(DEFAULT_PAYMENT_METHOD=multiple_method):
            # Even with multiple as default, the constructor default
            # should overwrite it
            slave = SelectPaymentMethodSlave(store=self.store,
                                             payment_type=Payment.TYPE_IN,
                                             default_method=u'check')
            self.assertEqual(slave.get_selected_method(), check_method)

            # Making check inactive should make the DEFAULT_PAYMENT_METHOD
            # the default one on the slave
            check_method.is_active = False
            slave = SelectPaymentMethodSlave(store=self.store,
                                             payment_type=Payment.TYPE_IN,
                                             default_method=u'check')
            self.assertEqual(slave.get_selected_method(), multiple_method)

            # Making check and the DEFAULT_PAYMENT_METHOD inactive,
            # the default should fallback to money
            multiple_method.is_active = False
            slave = SelectPaymentMethodSlave(store=self.store,
                                             payment_type=Payment.TYPE_IN,
                                             default_method=u'check')
            self.assertEqual(slave.get_selected_method(), money_method)

    def test_created_methods(self):
        # Payment.TYPE_IN
        slave = SelectPaymentMethodSlave(store=self.store,
                                         payment_type=Payment.TYPE_IN)
        methods = ['bill', 'card', 'check', 'credit', 'deposit',
                   'money', 'multiple', 'store_credit']
        self.assertEqual(set(slave._widgets.keys()), set(methods))

        for method in methods:
            widget = slave._widgets.get(method)
            self.assertTrue(widget.get_visible())

        # Payment.TYPE_OUT
        slave = SelectPaymentMethodSlave(store=self.store,
                                         payment_type=Payment.TYPE_OUT)
        methods = ['bill', 'check', 'deposit', 'money']
        self.assertEqual(set(slave._widgets.keys()), set(methods))

        for method in methods:
            widget = slave._widgets.get(method)
            self.assertTrue(widget.get_visible())

        # Only 1 method available
        for method in self.store.find(PaymentMethod,
                                      PaymentMethod.method_name != u'money'):
            method.is_active = False
        slave = SelectPaymentMethodSlave(store=self.store,
                                         payment_type=Payment.TYPE_IN)
        self.assertEqual(set(slave._widgets.keys()), set([u'money']))
        self.assertEqual(slave.get_selected_method().method_name, u'money')

    def test_default_method(self):
        method = self.store.find(PaymentMethod, method_name=u'multiple').one()
        with self.sysparam(DEFAULT_PAYMENT_METHOD=method):
            slave = SelectPaymentMethodSlave(store=self.store,
                                             payment_type=Payment.TYPE_IN)
            self.assertEqual(
                slave.get_selected_method().method_name, u'multiple')

            # If the default method is not created (setting is_active to False
            # does the trick), it should fallback to money
            method.is_active = False
            slave = SelectPaymentMethodSlave(store=self.store,
                                             payment_type=Payment.TYPE_IN)
            self.assertEqual(
                slave.get_selected_method().method_name, u'money')

    def test_method_set_visible(self):
        inactive = self.store.find(PaymentMethod, method_name=u'bill').one()
        inactive.is_active = False

        slave = SelectPaymentMethodSlave(store=self.store,
                                         payment_type=Payment.TYPE_IN,
                                         default_method=u'check')
        self.assertEqual(
            slave.get_selected_method().method_name, u'check')

        slave.method_set_visible(u'check', False)
        self.assertFalse(slave._widgets[u'check'].get_visible())
        self.assertEqual(
            slave.get_selected_method().method_name, u'money')

        # Test when the widget is not there
        slave.method_set_visible(u'bill', True)

    def test_method_set_sensitive(self):
        inactive = self.store.find(PaymentMethod, method_name=u'bill').one()
        inactive.is_active = False

        slave = SelectPaymentMethodSlave(store=self.store,
                                         payment_type=Payment.TYPE_IN,
                                         default_method=u'check')
        self.assertEqual(
            slave.get_selected_method().method_name, u'check')

        slave.method_set_sensitive(u'check', False)
        self.assertFalse(slave._widgets[u'check'].get_sensitive())
        self.assertEqual(
            slave.get_selected_method().method_name, u'money')

        # Test when the widget is not there
        slave.method_set_sensitive(u'bill', True)

    def test_set_client_none(self):
        slave = SelectPaymentMethodSlave(store=self.store,
                                         payment_type=Payment.TYPE_IN)

        slave.set_client(None, 100)
        self.check_slave(slave, 'slave-select-payment-method-client-none')

    def test_set_client_without_credit_and_store_credit(self):
        slave = SelectPaymentMethodSlave(store=self.store,
                                         payment_type=Payment.TYPE_IN)
        client = self.create_client()

        slave.set_client(client, 100)
        self.check_slave(
            slave,
            'slave-select-payment-method-client-without-credit-and-store-credit')

    def test_set_client_with_some_store_credit(self):
        slave = SelectPaymentMethodSlave(store=self.store,
                                         payment_type=Payment.TYPE_IN)
        client = self.create_client()
        client.credit_limit = 10

        slave.set_client(client, 100)
        self.check_slave(
            slave,
            'slave-select-payment-method-client-with-some-store-credit')

    def test_set_client_with_enough_store_credit(self):
        slave = SelectPaymentMethodSlave(store=self.store,
                                         payment_type=Payment.TYPE_IN)
        client = self.create_client()
        client.credit_limit = 100

        slave.set_client(client, 100)
        self.check_slave(
            slave,
            'slave-select-payment-method-client-with-enough-store-credit')

    def test_set_client_with_some_credit(self):
        slave = SelectPaymentMethodSlave(store=self.store,
                                         payment_type=Payment.TYPE_IN)
        client = self.create_client()
        method = self.store.find(PaymentMethod, method_name=u'credit').one()
        payment = self.create_payment(payment_type=Payment.TYPE_OUT,
                                      value=10, method=method)
        payment.group.payer = client.person
        payment.set_pending()
        payment.pay()

        slave.set_client(client, 100)
        self.check_slave(
            slave,
            'slave-select-payment-method-client-with-some-credit')

    def test_set_client_with_enough_credit(self):
        slave = SelectPaymentMethodSlave(store=self.store,
                                         payment_type=Payment.TYPE_IN)
        client = self.create_client()
        method = self.store.find(PaymentMethod, method_name=u'credit').one()
        payment = self.create_payment(payment_type=Payment.TYPE_OUT,
                                      value=100, method=method)
        payment.group.payer = client.person
        payment.set_pending()
        payment.pay()

        slave.set_client(client, 100)
        self.check_slave(
            slave,
            'slave-select-payment-method-client-with-enough-credit')
