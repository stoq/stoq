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

from stoqlib.domain.payment.payment import Payment
from stoqlib.gui.editors.paymentseditor import SalePaymentsEditor
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.lib.dateutils import localdate
from stoqlib.lib.translation import stoqlib_gettext

# FIXME: We should not translate anything on tests
_ = stoqlib_gettext


class TestPaymentEditor(GUITest):
    def _create_sale(self):
        date = localdate(2001, 1, 1).date()
        sale = self.create_sale()
        sale.identifier = 9431
        sellable = self.create_sellable(price=10)
        sale.add_sellable(sellable, quantity=5)
        self.add_payments(sale, method_type=u'check', date=date)

        return sale

    def test_sale_editor_show(self):
        sale = self._create_sale()
        editor = SalePaymentsEditor(self.store, sale)
        self.check_editor(editor, 'editor-payment-installments')

    def test_sale_editor_remove_preview_payment(self):
        sale = self._create_sale()
        editor = SalePaymentsEditor(self.store, sale)

        payment = sale.payments[0]
        editor.slave.payments.select(payment)

        # Removing a PREVIEW payment will remove it from the list
        self.assertEquals(payment.status, Payment.STATUS_PREVIEW)
        self.click(editor.slave.remove_button)
        self.assertEquals(len(editor.slave.payments), 0)

    def test_sale_editor_remove_pending_payment(self):
        sale = self._create_sale()
        editor = SalePaymentsEditor(self.store, sale)

        payment = sale.payments[0]
        payment.status = Payment.STATUS_PENDING
        editor.slave.payments.select(payment)

        # Removing an already confirmed payment will just cancel it
        self.assertEquals(payment.status, Payment.STATUS_PENDING)
        self.click(editor.slave.remove_button)
        self.assertEquals(len(editor.slave.payments), 1)
        self.assertEquals(payment.status, Payment.STATUS_CANCELLED)

    def test_sale_editor_confirmed_sale(self):
        sale = self._create_sale()
        sale.order()
        sale.confirm()
        editor = SalePaymentsEditor(self.store, sale)
        payments = editor.slave.payments
        payments.select(payments[0])

        # Before removing the payment, the dialog should be confirmable
        self.assertSensitive(editor.main_dialog, ['ok_button'])
        self.click(editor.slave.remove_button)

        # But we cannot confirm after removing it.
        self.assertNotSensitive(editor.main_dialog, ['ok_button'])

        # Lets add another payment
        self.click(editor.slave.add_button)
        self.assertSensitive(editor.main_dialog, ['ok_button'])

        # There should be one preview payment
        for payment in payments:
            if payment.status == payment.STATUS_PREVIEW:
                break
        assert payment.status == payment.STATUS_PREVIEW

        # Confirming the dialog should change the new payment to pending
        editor.confirm()
        assert payment.status == payment.STATUS_PENDING
