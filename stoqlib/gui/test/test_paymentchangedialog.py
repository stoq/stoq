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
import mock

from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.sale import Sale
from stoqlib.gui.uitestutils import GUITest
from stoqlib.gui.dialogs.paymentchangedialog import (PaymentDueDateChangeDialog,
                                                     PaymentStatusChangeDialog)


class TestPaymentChangeDialog(GUITest):
    @mock.patch('stoqlib.gui.dialogs.paymentchangedialog.warning')
    def testChangeDueDateSale(self, warning):
        sale = self.create_sale()
        sale.client = self.create_client()
        sale.identifier = 9123
        payment = self.add_payments(sale, date=datetime.date(2001, 1, 1))[0]
        editor = PaymentDueDateChangeDialog(self.trans, payment, sale)
        self.check_editor(editor, 'editor-payment-change-due-date-sale')

        today = datetime.date.today()
        yesterday = today - relativedelta(days=1)

        # By default, we cannot set a due date to the past
        editor.due_date.update(yesterday)
        self.assertNotSensitive(editor.main_dialog, ['ok_button'])

        # Now we should be able to confirm the dialog
        editor.due_date.update(today)
        self.assertSensitive(editor.main_dialog, ['ok_button'])

        # Ok button is enabled, but should show a warning
        self.click(editor.main_dialog.ok_button)
        warning.assert_called_once_with('You can not change the due date '
                                        'without a reason!')
        warning.reset_mock()

        editor.change_reason.update('Just because')
        self.click(editor.main_dialog.ok_button)
        self.assertEquals(warning.call_count, 0)

        self.assertEquals(payment.due_date.date(), today)

    @mock.patch('stoqlib.gui.dialogs.paymentchangedialog.warning')
    def testChangeStatusPaidSale(self, warning):
        sale = self.create_sale()
        self.add_product(sale, price=10)
        sale.identifier = 9124
        sale.status = Sale.STATUS_PAID
        payment = self.add_payments(sale)[0]
        payment.set_pending()
        payment.pay()
        editor = PaymentStatusChangeDialog(self.trans, payment,
                                           Payment.STATUS_PENDING, sale)
        self.check_editor(editor, 'editor-payment-change-status-sale')

        # Ok button is enabled, but should show a warning
        self.click(editor.main_dialog.ok_button)
        warning.assert_called_once_with(
            'You can not change the payment status without a reason!')
        warning.reset_mock()

        self.assertEquals(payment.status, Payment.STATUS_PAID)
        editor.change_reason.update('Just because')
        self.click(editor.main_dialog.ok_button)
        self.assertEquals(warning.call_count, 0)

        self.assertEquals(payment.status, Payment.STATUS_PENDING)

    @mock.patch('stoqlib.gui.dialogs.paymentchangedialog.warning')
    def testChangeStatusCancelPurchase(self, warning):
        product = self.create_product()
        order = self.create_purchase_order()
        order.identifier = 9129
        order.add_item(product.sellable, 10)

        payment = self.add_payments(order)[0]
        payment.set_pending()
        payment.pay()
        editor = PaymentStatusChangeDialog(self.trans, payment,
                                           Payment.STATUS_CANCELLED, order)
        self.check_editor(editor, 'editor-payment-change-status-purchase')

        # Ok button is enabled, but should show a warning
        self.click(editor.main_dialog.ok_button)
        warning.assert_called_once_with(
            'You can not change the payment status without a reason!')
        warning.reset_mock()

        self.assertEquals(payment.status, Payment.STATUS_PAID)
        editor.change_reason.update('Just because')
        self.click(editor.main_dialog.ok_button)
        self.assertEquals(warning.call_count, 0)

        self.assertEquals(payment.status, Payment.STATUS_CANCELLED)

    def testChangeDueDateLonelyOutPayment(self):
        payment = self.create_payment(Payment.TYPE_OUT)
        payment.group = self.create_payment_group()
        payment.group.recipient = self.create_person()

        payment.description = 'Payment Description'
        editor = PaymentDueDateChangeDialog(self.trans, payment)
        self.check_editor(editor, 'editor-payment-change-due-date-lonely-out')

    def testChangeDueDateLonelyInPayment(self):
        payment = self.create_payment(Payment.TYPE_IN)
        payment.group = self.create_payment_group()
        payment.group.payer = self.create_person()

        payment.description = 'Payment Description'
        editor = PaymentDueDateChangeDialog(self.trans, payment)
        self.check_editor(editor, 'editor-payment-change-due-date-lonely-in')
