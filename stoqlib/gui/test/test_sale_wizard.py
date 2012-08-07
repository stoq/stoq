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

from stoqlib.gui.uitestutils import GUITest
from stoqlib.gui.wizards.salewizard import ConfirmSaleWizard


class TestConfirmSaleWizard(GUITest):
    def testStepSalesPerson(self):
        sale = self.create_sale()
        self.add_product(sale)
        wizard = ConfirmSaleWizard(self.trans, sale)
        step = wizard.get_current_step()

        self.check_wizard(wizard, 'wizard-sale-step-sales-person',
                          ignores=[str(step.salesperson.get_selected())])

    def testStepPaymentMethodCheck(self):
        sale = self.create_sale()
        self.add_product(sale)
        wizard = ConfirmSaleWizard(self.trans, sale)
        step = wizard.get_current_step()
        step.pm_slave.select_method('check')
        self.assertTrue(wizard.next_button.props.sensitive)
        wizard.next_button.clicked()
        self.check_wizard(wizard, 'wizard-sale-step-payment-method-check',
                          ignores=[repr(datetime.date.today())])

    def testStepPaymentMethodBill(self):
        sale = self.create_sale()
        self.add_product(sale)
        wizard = ConfirmSaleWizard(self.trans, sale)
        step = wizard.get_current_step()
        step.pm_slave.select_method('bill')
        self.assertTrue(wizard.next_button.props.sensitive)
        wizard.next_button.clicked()
        self.check_wizard(wizard, 'wizard-sale-step-payment-method-bill',
                          ignores=[repr(datetime.date.today())])

    def testStepPaymentMethodCard(self):
        sale = self.create_sale()
        self.add_product(sale)
        wizard = ConfirmSaleWizard(self.trans, sale)
        step = wizard.get_current_step()
        step.pm_slave.select_method('card')
        self.assertTrue(wizard.next_button.props.sensitive)
        wizard.next_button.clicked()
        self.check_wizard(wizard, 'wizard-sale-step-payment-method-card',
                          ignores=[repr(datetime.date.today())])

    def testStepPaymentMethodDeposit(self):
        sale = self.create_sale()
        self.add_product(sale)
        wizard = ConfirmSaleWizard(self.trans, sale)
        step = wizard.get_current_step()
        step.pm_slave.select_method('deposit')
        self.assertTrue(wizard.next_button.props.sensitive)
        wizard.next_button.clicked()
        self.check_wizard(wizard, 'wizard-sale-step-payment-method-deposit',
                          ignores=[repr(datetime.date.today())])

    def testStepPaymentMethodStoreCredit(self):
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
                          ignores=[repr(datetime.date.today())])
