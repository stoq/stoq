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

from kiwi.currency import currency

from stoqlib.domain.payment.payment import Payment
from stoqlib.gui.editors.crediteditor import CreditEditor
from stoqlib.gui.uitestutils import GUITest


class TestCreditEditor(GUITest):
    def testCreditEditor(self):
        client = self.create_client()
        editor = CreditEditor(self.store, client)

        self.assertNotSensitive(editor.main_dialog, ['ok_button'])

        editor.description.set_text('Desc')
        editor.value.set_text('4.23')
        self.assertSensitive(editor.main_dialog, ['ok_button'])

        editor.value.set_text('-3.78')
        payment = editor._create_payment()

        self.assertEquals(payment.value, currency(3.78))
        self.assertEquals(payment.payment_type, Payment.TYPE_IN)

    def testCreditEditorCancel(self):
        client = self.create_client()
        editor = CreditEditor(self.store, client)

        editor.description.set_text('Desc')
        editor.value.set_text('-4.23')
        editor.cancel()

        self.assertEquals(editor.client.credit_account_balance, currency(0.00))
