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

import gtk
import mock

from stoqlib.gui.uitestutils import GUITest
from stoqlib.gui.wizards.salewizard import ConfirmSaleWizard


class TestConfirmSaleWizard(GUITest):
    def testCreate(self):
        sale = self.create_sale()
        self.add_product(sale)
        wizard = ConfirmSaleWizard(self.trans, sale)

        self.assertSensitive(wizard, ['next_button'])
        wizard.next_button.clicked()

        models = [sale, sale.group]
        models.extend(sale.payments)

        p = list(sale.payments)[0]
        p.description = p.description.rsplit(' ', 1)[0]

        for item in sale.get_items():
            models.extend(list(item.sellable.product_storable.get_stock_items()))

        self.check_wizard(wizard, 'wizard-sale-done-sold',
                          models=models)

        self.assertEquals(sale.payments[0].method.method_name, 'money')

    def testStepPaymentMethodCheck(self):
        sale = self.create_sale()
        self.add_product(sale)
        wizard = ConfirmSaleWizard(self.trans, sale)
        step = wizard.get_current_step()
        step.pm_slave.select_method('check')
        self.assertTrue(wizard.next_button.props.sensitive)
        wizard.next_button.clicked()
        self.check_wizard(wizard, 'wizard-sale-step-payment-method-check',
                          ignores=['%05d' % (sale.id, )])

        self.assertSensitive(wizard, ['next_button'])
        wizard.next_button.clicked()

        self.assertEquals(sale.payments[0].method.method_name, 'check')

    # FIXME: add a test with a configured bank account
    @mock.patch('stoqlib.reporting.boleto.warning')
    def testStepPaymentMethodBill(self, warning):
        sale = self.create_sale()
        self.add_product(sale)
        wizard = ConfirmSaleWizard(self.trans, sale)
        step = wizard.get_current_step()
        step.pm_slave.select_method('bill')
        self.assertTrue(wizard.next_button.props.sensitive)
        wizard.next_button.clicked()
        self.check_wizard(wizard, 'wizard-sale-step-payment-method-bill',
                          ignores=['%05d' % (sale.id, )])

        self.assertSensitive(wizard, ['next_button'])

        wizard.next_button.clicked()
        self.assertEquals(sale.payments[0].method.method_name, 'bill')

        warning.assert_called_once_with(
            'Could not print Bill Report', description=(
            "Account 'Imbalance' must be a bank account.\n"
            "You need to configure the bill payment method in "
            "the admin application and try again"))

    def testStepPaymentMethodCard(self):
        sale = self.create_sale()
        self.add_product(sale)
        wizard = ConfirmSaleWizard(self.trans, sale)
        step = wizard.get_current_step()
        step.pm_slave.select_method('card')
        self.assertTrue(wizard.next_button.props.sensitive)
        wizard.next_button.clicked()
        self.check_wizard(wizard, 'wizard-sale-step-payment-method-card',
                          ignores=['%05d' % (sale.id, )])

        self.assertSensitive(wizard, ['next_button'])

        # FIXME: verify card payments
        #wizard.next_button.clicked()
        #self.assertEquals(sale.payments[0].method.method_name, 'card')

    def testStepPaymentMethodDeposit(self):
        sale = self.create_sale()
        self.add_product(sale)
        wizard = ConfirmSaleWizard(self.trans, sale)
        step = wizard.get_current_step()
        step.pm_slave.select_method('deposit')
        self.assertTrue(wizard.next_button.props.sensitive)
        wizard.next_button.clicked()
        self.check_wizard(wizard, 'wizard-sale-step-payment-method-deposit',
                          ignores=['%05d' % (sale.id, )])

        self.assertSensitive(wizard, ['next_button'])
        wizard.next_button.clicked()

        self.assertEquals(sale.payments[0].method.method_name, 'deposit')

    @mock.patch('stoqlib.gui.wizards.salewizard.yesno')
    def testStepPaymentMethodStoreCredit(self, yesno):
        yesno.return_value = False

        sale = self.create_sale()
        self.add_product(sale)
        sale.client = self.create_client()
        sale.client.credit_limit = 1000
        wizard = ConfirmSaleWizard(self.trans, sale)
        step = wizard.get_current_step()
        step.pm_slave.select_method('store_credit')
        self.assertTrue(wizard.next_button.props.sensitive)
        wizard.next_button.clicked()
        self.check_wizard(wizard, 'wizard-sale-step-payment-method-store-credit',
                          ignores=['%05d' % (sale.id, )])

        self.assertSensitive(wizard, ['next_button'])
        wizard.next_button.clicked()

        self.assertEquals(sale.payments[0].method.method_name, 'store_credit')

        yesno.assert_called_once_with(
            'Do you want to print the booklets for this sale?',
            gtk.RESPONSE_YES, 'Print booklets', "Don't print")
