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

import mock
from stoqlib.gui.dialogs.paymentflowhistorydialog import PaymentFlowHistoryDialog
from stoqlib.gui.test.uitestutils import GUITest


class TestPaymentFlowHistoryDialog(GUITest):
    @mock.patch('stoqlib.gui.dialogs.paymentflowhistorydialog.print_report')
    def test_create(self, print_report):
        dialog = PaymentFlowHistoryDialog(self.store)
        self.check_dialog(dialog, 'dialog-payment-flow-history')

    @mock.patch('stoqlib.gui.dialogs.paymentflowhistorydialog.info')
    def test_no_payments(self, info):
        dialog = PaymentFlowHistoryDialog(self.store)
        self.click(dialog.ok_button)
        info.assert_called_once_with('No payment history found.')

    @mock.patch('stoqlib.gui.dialogs.paymentflowhistorydialog.print_report')
    def test_with_payments(self, info):
        payment = self.create_payment()
        dialog = PaymentFlowHistoryDialog(self.store)
        self.click(dialog.ok_button)
        self.assertEquals(info.call_count, 1)

        args, kwargs = info.call_args
        results = kwargs['payment_histories']

        self.assertEquals(len(results), 1)

        divergent_payments = results[0].get_divergent_payments()
        self.assertEquals(divergent_payments.count(), 1)
        self.assertEquals(divergent_payments[0], payment)
