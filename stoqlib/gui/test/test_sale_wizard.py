# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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
from dateutil.relativedelta import relativedelta

import gtk
import mock

from kiwi.currency import currency

from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment
from stoqlib.enums import LatePaymentPolicy

from stoqlib.gui.uitestutils import GUITest
from stoqlib.gui.wizards.salewizard import ConfirmSaleWizard
from stoqlib.lib.parameters import sysparam
from stoqlib.reporting.booklet import BookletReport


class TestConfirmSaleWizard(GUITest):
    def testCreate(self):
        sale = self.create_sale()
        self.add_product(sale)
        wizard = ConfirmSaleWizard(self.trans, sale)

        self.click(wizard.next_button)

        models = self.collect_sale_models(sale)

        self.check_wizard(wizard, 'wizard-sale-done-sold',
                          models=models)

        self.assertEquals(sale.payments[0].method.method_name, 'money')

    def testStepPaymentMethodCheck(self):
        sale = self.create_sale()
        sale.identifier = 12345
        self.add_product(sale)
        wizard = ConfirmSaleWizard(self.trans, sale)
        step = wizard.get_current_step()
        step.pm_slave.select_method('check')
        self.click(wizard.next_button)
        self.check_wizard(wizard, 'wizard-sale-step-payment-method-check')

        self.click(wizard.next_button)

        self.assertEquals(sale.payments[0].method.method_name, 'check')

    # FIXME: add a test with a configured bank account
    @mock.patch('stoqlib.reporting.boleto.warning')
    def testStepPaymentMethodBill(self, warning):
        sale = self.create_sale()
        sale.identifier = 12345
        self.add_product(sale)
        wizard = ConfirmSaleWizard(self.trans, sale)
        step = wizard.get_current_step()
        step.pm_slave.select_method('bill')
        self.click(wizard.next_button)
        self.check_wizard(wizard, 'wizard-sale-step-payment-method-bill')

        self.click(wizard.next_button)

        self.assertEquals(sale.payments[0].method.method_name, 'bill')

        warning.assert_called_once_with(
            'Could not print Bill Report', description=(
            "Account 'Imbalance' must be a bank account.\n"
            "You need to configure the bill payment method in "
            "the admin application and try again"))

    def testStepPaymentMethodCard(self):
        sale = self.create_sale()
        sale.identifier = 12345
        self.add_product(sale)
        wizard = ConfirmSaleWizard(self.trans, sale)
        step = wizard.get_current_step()
        step.pm_slave.select_method('card')
        self.click(wizard.next_button)
        self.check_wizard(wizard, 'wizard-sale-step-payment-method-card')

        self.assertSensitive(wizard, ['next_button'])

        # FIXME: verify card payments
        #self.click(wizard.next_button)
        #self.assertEquals(sale.payments[0].method.method_name, 'card')

    def testStepPaymentMethodDeposit(self):
        sale = self.create_sale()
        sale.identifier = 12345
        self.add_product(sale)
        wizard = ConfirmSaleWizard(self.trans, sale)
        step = wizard.get_current_step()
        step.pm_slave.select_method('deposit')
        self.click(wizard.next_button)
        self.check_wizard(wizard, 'wizard-sale-step-payment-method-deposit')

        self.click(wizard.next_button)

        self.assertEquals(sale.payments[0].method.method_name, 'deposit')

    @mock.patch('stoqlib.gui.wizards.salewizard.yesno')
    def testStepPaymentMethodStoreCredit(self, yesno):
        yesno.return_value = False

        sale = self.create_sale()
        sale.identifier = 12345
        self.add_product(sale)
        sale.client = self.create_client()
        sale.client.credit_limit = 1000
        wizard = ConfirmSaleWizard(self.trans, sale)
        step = wizard.get_current_step()
        step.pm_slave.select_method('store_credit')
        self.click(wizard.next_button)
        self.check_wizard(wizard, 'wizard-sale-step-payment-method-store-credit')

    def testSaleToClientWithoutCredit(self):
        sale = self.create_sale()
        sale.identifier = 12345
        self.add_product(sale)
        sale.client = self.create_client()
        wizard = ConfirmSaleWizard(self.trans, sale)
        step = wizard.get_current_step()
        step.pm_slave.select_method('store_credit')
        self.assertEquals(
            str(step.client.emit('validate', sale.client)),
            'Client Client does not have enough credit left to purchase.')

    @mock.patch('stoqlib.gui.wizards.salewizard.print_report')
    @mock.patch('stoqlib.gui.wizards.salewizard.yesno')
    def testSaleToClientWithLatePayments(self, yesno, print_report):
        #: this parameter allows a client to buy even if he has late payments
        sysparam(self.trans).update_parameter('LATE_PAYMENTS_POLICY',
                                str(int(LatePaymentPolicy.ALLOW_SALES)))

        sale = self.create_sale()
        sale.identifier = 12345
        self.add_product(sale)
        sale.client = self.create_client()
        wizard = ConfirmSaleWizard(self.trans, sale)
        step = wizard.get_current_step()

        money_method = PaymentMethod.get_by_name(self.trans, 'money')
        today = datetime.date.today()

        sale.client.credit_limit = currency('90000000000')
        step.pm_slave.select_method('money')

        # checks if a client can buy normally
        self.assertTrue(wizard.next_button.props.sensitive)

        # checks if a client with late payments can buy
        payment = self.create_payment(Payment.TYPE_IN,
                                      today - relativedelta(days=1),
                                      method=money_method)
        payment.status = Payment.STATUS_PENDING
        payment.group = self.create_payment_group()
        payment.group.payer = sale.client.person

        step.pm_slave.select_method('bill')
        self.assertTrue(wizard.next_button.props.sensitive)

        step.pm_slave.select_method('store_credit')
        self.assertTrue(wizard.next_button.props.sensitive)

        #: this parameter disallows a client with late payments to buy with
        #: store credit
        sysparam(self.trans).update_parameter('LATE_PAYMENTS_POLICY',
                               str(int(LatePaymentPolicy.DISALLOW_STORE_CREDIT)))

        #checks if a client can buy normally
        payment.due_date = today
        self.assertEquals(step.client.emit('validate', sale.client), None)
        self.assertTrue(wizard.next_button.props.sensitive)

        #checks if a client with late payments can buy with money method
        step.pm_slave.select_method('money')
        payment.due_date = today - relativedelta(days=3)
        self.assertEquals(step.client.emit('validate', sale.client), None)
        self.assertTrue(wizard.next_button.props.sensitive)

        #checks if a client with late payments can buy with store credit
        step.pm_slave.select_method('store_credit')
        self.assertEquals(
            str(step.client.emit('validate', sale.client)),
            'It is not possible to sell with store credit for clients with '
            'late payments.')
        #self.assertFalse(wizard.next_button.props.sensitive)
        step.client.validate(force=True)
        # FIXME: This is not updating correcly
        #self.assertNotSensitive(wizard, ['next_button'])

        #: this parameter disallows a client with late payments to buy with
        #: store credit
        sysparam(self.trans).update_parameter('LATE_PAYMENTS_POLICY',
                               str(int(LatePaymentPolicy.DISALLOW_SALES)))

        #checks if a client can buy normally
        payment.due_date = today
        self.assertEquals(step.client.emit('validate', sale.client), None)

        #checks if a client with late payments can buy
        payment.due_date = today - relativedelta(days=3)

        step.pm_slave.select_method('store_credit')
        self.assertEquals(
            str(step.client.emit('validate', sale.client)),
            'It is not possible to sell for clients with late payments.')

        step.pm_slave.select_method('check')
        self.assertEquals(
            str(step.client.emit('validate', sale.client)),
            'It is not possible to sell for clients with late payments.')

        step.pm_slave.select_method('store_credit')
        sysparam(self.trans).update_parameter('LATE_PAYMENTS_POLICY',
                                str(int(LatePaymentPolicy.ALLOW_SALES)))

        sale.client.credit_limit = currency("9000")
        # Force validation since we changed the credit limit.
        step.client.validate(force=True)

        self.click(wizard.next_button)

        # finish wizard
        self.click(wizard.next_button)

        self.assertEquals(sale.payments[0].method.method_name, 'store_credit')

        yesno.assert_called_once_with(
            'Do you want to print the booklets for this sale?',
            gtk.RESPONSE_YES, 'Print booklets', "Don't print")

        print_report.assert_called_once_with(BookletReport,
                    list(sale.group.get_payments_by_method_name('store_credit')))
