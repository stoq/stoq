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
import unittest
from decimal import Decimal

import mock
from stoqlib.domain.payment.category import PaymentCategory
from stoqlib.domain.payment.payment import Payment
from stoqlib.gui.dialogs.purchasedetails import PurchaseDetailsDialog
from stoqlib.gui.editors.paymenteditor import (_ONCE, InPaymentEditor,
                                               OutPaymentEditor,
                                               LonelyPaymentDetailsDialog)
from stoqlib.gui.uitestutils import GUITest
from stoqlib.lib.dateutils import INTERVALTYPE_WEEK
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class TestPaymentEditor(GUITest):
    def testCreate(self):
        editor = InPaymentEditor(self.trans)

        # Model
        self.assertTrue(isinstance(editor.model, Payment))
        # FIXME: In the long run this should be moved into the domain,
        #        Like Domain.create_empty() or so
        self.assertEquals(editor.model.payment_type, Payment.TYPE_IN)
        self.assertEquals(editor.model.method.method_name, 'money')
        self.assertEquals(editor.model.description, '')
        self.assertEquals(editor.model.status, Payment.STATUS_PENDING)
        self.assertEquals(editor.model.value, 0)
        self.assertEquals(editor.model.category, None)
        self.check_editor(editor, 'editor-in-payment-create')

    def testConfirm(self):
        editor = OutPaymentEditor(self.trans)
        self.assertFalse(editor.validate_confirm())
        editor.description.update('Payment name')
        self.assertFalse(editor.validate_confirm())

        editor.value.update(100)
        self.assertFalse(editor.validate_confirm())

        editor.due_date.update(datetime.date(2015, 1, 1))
        self.assertTrue(editor.validate_confirm())

        editor.repeat.update(INTERVALTYPE_WEEK)
        self.assertFalse(editor.validate_confirm())

        editor.end_date.update(datetime.date(2014, 1, 10))
        self.assertFalse(editor.validate_confirm())

        editor.end_date.update(datetime.date(2015, 1, 10))
        self.assertTrue(editor.validate_confirm())

        editor.main_dialog.confirm()

        model = editor.retval
        self.check_editor(editor, 'editor-payment-confirm',
                          [model.group] + list(model.group.payments))

    def testCreateCategory(self):
        category = PaymentCategory(connection=self.trans,
                                   name='TestCategory',
                                   category_type=PaymentCategory.TYPE_RECEIVABLE)
        editor = InPaymentEditor(self.trans, category=category.name)

        self.check_editor(editor, 'editor-in-payment-create-with-category')

    def testEndDateSensitivity(self):
        editor = InPaymentEditor(self.trans)
        self.assertNotSensitive(editor, ['end_date'])
        editor.repeat.update(INTERVALTYPE_WEEK)
        self.assertSensitive(editor, ['end_date'])
        editor.repeat.update(-1)
        self.assertNotSensitive(editor, ['end_date'])

    def test_repeat_validation(self):
        editor = InPaymentEditor(self.trans)
        editor.description.update('desc')
        editor.value.update(Decimal('10'))
        editor.due_date.update(datetime.date.today())

        editor.repeat.update(INTERVALTYPE_WEEK)
        self.assertNotSensitive(editor.main_dialog, ['ok_button'])

        editor.repeat.update(_ONCE)
        self.assertSensitive(editor.main_dialog, ['ok_button'])

    def testValueValidation(self):
        editor = InPaymentEditor(self.trans)
        self.assertEquals(str(editor.value.emit('validate', None)),
                          "The value must be greater than zero.")

        self.assertEquals(str(editor.value.emit('validate', -1)),
                          "The value must be greater than zero.")
        self.assertFalse(editor.value.emit('validate', 10))

    def testShowOut(self):
        payment = self.create_payment(payment_type=Payment.TYPE_OUT)
        payment.group = self.create_payment_group()
        editor = OutPaymentEditor(self.trans, payment)

        self.check_editor(editor, 'editor-out-payment-show')

    def testShowIn(self):
        payment = self.create_payment(payment_type=Payment.TYPE_IN)
        payment.group = self.create_payment_group()
        editor = InPaymentEditor(self.trans, payment)

        self.check_editor(editor, 'editor-in-payment-show')

    def testShowFromSale(self):
        sale = self.create_sale()
        sale.identifier = 12345
        self.add_payments(sale, method_type='money')

        p = sale.payments[0]

        editor = InPaymentEditor(self.trans, p)
        self.check_editor(editor, 'editor-in-payment-show-sale')

        self.assertTrue(editor.model.group.sale)

    def testShowFromPurchase(self):
        purchase = self.create_purchase_order()
        purchase.identifier = 12345
        self.add_payments(purchase, method_type='money')

        p = purchase.payments[0]
        editor = OutPaymentEditor(self.trans, p)
        self.check_editor(editor, 'editor-out-payment-show-purchase')

    @mock.patch('stoqlib.gui.editors.paymenteditor.run_dialog')
    def testShowLonelyDialogOut(self, run_dialog):
        payment = self.create_payment(payment_type=Payment.TYPE_OUT)
        payment.group = self.create_payment_group()
        editor = OutPaymentEditor(self.trans, payment)

        self.click(editor.details_button)
        run_dialog.assert_called_once_with(LonelyPaymentDetailsDialog, editor,
                                           editor.conn, editor.model)

    @mock.patch('stoqlib.gui.editors.paymenteditor.run_dialog')
    def testShowLonelyDialogIn(self, run_dialog):
        payment = self.create_payment(payment_type=Payment.TYPE_IN)
        payment.group = self.create_payment_group()
        editor = InPaymentEditor(self.trans, payment)

        self.click(editor.details_button)
        run_dialog.assert_called_once_with(LonelyPaymentDetailsDialog, editor,
                                           editor.conn, editor.model)

    @mock.patch('stoqlib.gui.editors.paymenteditor.run_dialog')
    def testShowPurchaseDialog(self, run_dialog):
        purchase = self.create_purchase_order()
        self.add_payments(purchase, method_type='money')

        p = purchase.payments[0]
        editor = OutPaymentEditor(self.trans, p)

        self.click(editor.details_button)
        run_dialog.assert_called_once_with(PurchaseDetailsDialog, editor,
                                           editor.conn, purchase)

    @mock.patch('stoqlib.gui.editors.paymenteditor.run_dialog')
    def testShowSaleDialog(self, run_dialog):
        sale = self.create_sale()
        self.add_product(sale)
        sale.order()
        self.add_payments(sale, method_type='money')
        sale.confirm()

        p = sale.payments[0]

        editor = InPaymentEditor(self.trans, p)

        self.click(editor.details_button)
        # FIXME: for Viewable comparision in Storm"
        #from stoqlib.domain.sale import SaleView
        #from stoqlib.gui.dialogs.saledetails import SaleDetailsDialog
        #sale_view = SaleView.get(editor.model.group.sale.id, connection=self.trans)
        #run_dialog.assert_called_once_with(SaleDetailsDialog, editor,
        #                                   editor.conn, sale_view)
        self.assertEquals(run_dialog.call_count, 1)


if __name__ == '__main__':
    from stoqlib.api import api
    c = api.prepare_test()
    unittest.main()
