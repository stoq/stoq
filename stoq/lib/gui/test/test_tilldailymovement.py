# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2014 Async Open Source <http://www.async.com.br>
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
import mock

from stoqlib.api import api
from stoq.lib.gui.dialogs.tilldailymovement import TillDailyMovementDialog
from stoq.lib.gui.test.uitestutils import GUITest
from stoqlib.reporting.till import TillDailyMovementReport


class TestTillHistory(GUITest):
    def test_show(self):
        dialog = TillDailyMovementDialog(self.store)

        # Creating a sale to which a bill payment is attached.
        sale = self.create_sale(client=self.create_client(name=u'Fulano de Tal'))
        sale.identifier = 1234
        self.add_product(sale)
        self.add_payments(sale, method_type=u'bill')
        sale.order(self.current_user)
        sale.confirm(self.current_user)
        sale.group.pay()

        # Creating a purchase order to which a money payment is attached.
        purchase = self.create_purchase_order(branch=sale.branch)
        purchase.identifier = 4321
        self.create_purchase_order_item(order=purchase)
        payment = self.add_payments(purchase, method_type=u'money')[0]
        payment.identifier = 43210
        purchase.status = purchase.ORDER_PENDING
        purchase.confirm(self.current_user)
        purchase.group.pay()

        # We create two payments whose dates are corresponding to the day of the test,
        # s.t. the search returns both of them.
        payment = self.create_payment(value=100, method=self.get_payment_method(u'credit'),
                                      date=datetime.datetime.now())
        payment.identifier = 9941
        payment.set_pending()
        payment.pay()

        payment = self.create_payment(value=300, method=self.get_payment_method(u'money'),
                                      date=datetime.datetime.now())
        payment.identifier = 9942
        payment.set_pending()
        payment.pay()

        # The search should fetch the two payments created above as well as the sale's
        # and the purchase order's respective payment.
        self.click(dialog.search_button)
        self.check_dialog(dialog, 'till-dailymovement-dialog-show')

    def test_show_with_check_payments(self):
        dialog = TillDailyMovementDialog(self.store)

        # Sale with check
        sale = self.create_sale()
        sale.identifier = 1234
        self.add_product(sale)
        payments = self.add_payments(sale, method_type=u'check', installments=2)
        sale.order(self.current_user)
        sale.confirm(self.current_user)
        sale.group.pay()
        # Set the check data
        number = 0
        for payment in payments:
            number += 1
            payment.payment_number = str(number)
            bank = payment.check_data.bank_account
            bank.bank_number = 1
            bank.bank_branch = u'1234-23'
            bank.bank_account = u'12345-23'

        # New sale to use blank values in check data
        sale = self.create_sale()
        sale.identifier = 7894
        self.add_product(sale)
        payments = self.add_payments(sale, method_type=u'check', installments=3)
        sale.order(self.current_user)
        sale.confirm(self.current_user)
        sale.group.pay()
        # Set some blank values
        number = 0
        for payment in payments:
            number += 1
            payment.payment_number = str(number)
            bank = payment.check_data.bank_account
            bank.bank_number = None
            bank.bank_branch = u'4561-12'
            bank.bank_account = u'45678-89'
        # Remove the payment_number of the second installment
        payments[1].payment_number = u""

        self.click(dialog.search_button)
        self.check_dialog(dialog, 'till-dailymovement-dialog-check-payments')

    def test_show_synchronized(self):
        with self.sysparam(SYNCHRONIZED_MODE=True):
            dialog = TillDailyMovementDialog(self.store)
            self.check_dialog(dialog, 'till-dailymovement-dialog-show-sync')

    @mock.patch('stoq.lib.gui.dialogs.tilldailymovement.print_report')
    def test_print(self, print_report):
        dialog = TillDailyMovementDialog(self.store)

        # Before doing any search, the print button should not be sensitive
        self.assertFalse(dialog.print_button.get_sensitive())

        # After clicking the button, the print dialog should be sensitive
        self.click(dialog.search_button)
        self.assertTrue(dialog.print_button.get_sensitive())

        self.click(dialog.print_button)

        date = dialog.get_daterange()
        print_report.assert_called_once_with(TillDailyMovementReport,
                                             self.store,
                                             api.get_current_branch(self.store),
                                             date, dialog)
