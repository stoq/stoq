# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##

from decimal import Decimal

from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.sale import Sale
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.gui.wizards.renegotiationwizard import PaymentRenegotiationWizard
from stoqlib.gui.wizards.salewizard import PaymentMethodStep


class TestPaymentRenegotiationWizard(GUITest):
    def test_money(self):
        sale = self.create_sale()
        payment = self.create_payment()

        sale.status = Sale.STATUS_CONFIRMED
        payment.group = sale.group
        payment.status = Payment.STATUS_PENDING
        payment.identifier = 333

        wizard = PaymentRenegotiationWizard(self.store, [sale.group])
        self.click(wizard.next_button)

        self.check_wizard(wizard, 'wizard-renegotiation-money-payment-list-step',
                          [wizard.model, payment.group, payment, sale])

    def test_store_credit(self):
        client = self.create_client()
        sale = self.create_sale(client=client)
        group = sale.group
        payment = self.create_payment()

        client.credit_limit = Decimal('1234')
        sale.status = Sale.STATUS_CONFIRMED
        payment.group = group
        payment.status = Payment.STATUS_PENDING
        payment.identifier = 333

        wizard = PaymentRenegotiationWizard(self.store, [group])

        step = wizard.get_current_step()
        widget = step.pm_slave._widgets['store_credit']
        widget.set_active(True)
        self.check_wizard(wizard,
                          'wizard-renegotiation-store-credit-payment-list-step')

        self.click(wizard.next_button)

        step = wizard.get_current_step()
        self.assertTrue(isinstance(step, PaymentMethodStep))

    def test_store_credit_client_without_credit(self):
        client = self.create_client()
        sale = self.create_sale(client=client)
        group = sale.group
        payment = self.create_payment()

        sale.status = Sale.STATUS_CONFIRMED
        payment.group = group
        payment.status = Payment.STATUS_PENDING
        payment.identifier = 333

        wizard = PaymentRenegotiationWizard(self.store, [group])
        self.check_wizard(wizard,
                          'wizard-renegotiation-without-credit-payment-list-step')
