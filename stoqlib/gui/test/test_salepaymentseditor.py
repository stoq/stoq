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


from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment
from stoqlib.gui.editors.paymentseditor import SalePaymentsEditor
from stoqlib.gui.test.uitestutils import GUITest


class TestSalePaymentsEditor(GUITest):
    def test_show(self):
        client = self.create_client()
        sale = self.create_sale(client=client)
        editor = SalePaymentsEditor(self.store, sale)
        self.check_editor(editor, 'editor-salepayments-show')

    def test_pay_with_credit(self):
        client = self.create_client()
        sale = self.create_sale(client=client)
        sale.identifier = 1234
        sellable = self.create_sellable(price=10)
        sale.add_sellable(sellable)

        # Create credit to the client.
        method = PaymentMethod.get_by_name(self.store, u'credit')
        group = self.create_payment_group(payer=client.person)
        payment = self.create_payment(value=20, method=method, group=group)
        payment.set_pending()
        payment.pay()
        self.assertEquals(client.credit_account_balance, 20)

        editor = SalePaymentsEditor(self.store, sale)
        # Select credit method.
        for radio in editor.slave.methods_box.get_children():
            if radio.get_label() == 'Credit ($20.00)':
                radio.set_active(True)
                break
        # Add credit payment.
        editor.slave.value.update(10)
        self.assertSensitive(editor.slave, ['add_button'])
        self.click(editor.slave.add_button)
        editor.confirm()
        self.assertEquals(client.credit_account_balance, 10)
        for payment in sale.payments:
            self.assertEquals(payment.status, Payment.STATUS_PAID)

        # Test remove payment.
        self.assertNotSensitive(editor.slave, ['remove_button'])
        editor = SalePaymentsEditor(self.store, sale)
        payments = editor.slave.payments
        payments.select(payments[0])
        self.assertSensitive(editor.slave, ['remove_button'])
        self.click(editor.slave.remove_button)
        editor.confirm()
        for payment in sale.payments:
            self.assertEquals(payment.status, Payment.STATUS_CANCELLED)
