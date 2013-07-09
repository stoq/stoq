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

from stoqlib.domain.payment.category import PaymentCategory
from stoqlib.gui.editors.paymentcategoryeditor import PaymentCategoryEditor
from stoqlib.gui.test.uitestutils import GUITest


class TestPaymentCategoryEditor(GUITest):
    def test_create(self):
        editor = PaymentCategoryEditor(self.store)
        self.check_editor(editor, 'editor-paymentcategory-create')

    def test_show(self):
        payment_category = self.create_payment_category()
        editor = PaymentCategoryEditor(self.store, model=payment_category)
        self.check_editor(editor, 'editor-paymentcategory-show')

    def test_confirm(self):
        payment = self.create_payment()
        payment_category = self.create_payment_category()
        payment.category = payment_category
        editor = PaymentCategoryEditor(self.store, model=payment_category)

        # Change the category type so validate_confirm will ask the
        # user to remove this category from payments
        editor.category_type.select(PaymentCategory.TYPE_RECEIVABLE)

        with mock.patch('stoqlib.gui.editors.paymentcategoryeditor.yesno') as yesno:
            yesno.return_value = False
            self.click(editor.main_dialog.ok_button)
            yesno.assert_called_once_with(
                "Changing the payment type will remove "
                "this category from 1 payments. Are you sure?",
                gtk.RESPONSE_NO, "Change", "Don't change")
            self.assertEqual(payment.category, payment_category)

            yesno.reset_mock()

            yesno.return_value = True
            self.click(editor.main_dialog.ok_button)
            yesno.assert_called_once_with(
                "Changing the payment type will remove "
                "this category from 1 payments. Are you sure?",
                gtk.RESPONSE_NO, "Change", "Don't change")
            self.assertEqual(payment.category, None)
