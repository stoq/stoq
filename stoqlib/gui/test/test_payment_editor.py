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

import unittest
from decimal import Decimal

import mock
from stoqlib.domain.account import Account
from stoqlib.domain.payment.category import PaymentCategory
from stoqlib.domain.payment.payment import Payment
from stoqlib.gui.dialogs.purchasedetails import PurchaseDetailsDialog
from stoqlib.gui.dialogs.stockdecreasedialog import StockDecreaseDetailsDialog
from stoqlib.gui.editors.paymenteditor import (_ONCE, InPaymentEditor,
                                               OutPaymentEditor,
                                               LonelyPaymentDetailsDialog)
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.lib.dateutils import INTERVALTYPE_WEEK, localdate, localtoday
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class TestPaymentEditor(GUITest):
    def test_create(self):
        editor = InPaymentEditor(self.store)

        # Model
        self.assertTrue(isinstance(editor.model, Payment))
        # FIXME: In the long run this should be moved into the domain,
        #        Like Domain.create_empty() or so
        self.assertEquals(editor.model.payment_type, Payment.TYPE_IN)
        self.assertEquals(editor.model.method.method_name, u'money')
        self.assertEquals(editor.model.description, u'')
        self.assertEquals(editor.model.status, Payment.STATUS_PENDING)
        self.assertEquals(editor.model.value, 0)
        self.assertEquals(editor.model.category, None)
        self.check_editor(editor, 'editor-in-payment-create')

    def test_edit_paid_out_payment(self):
        payment = self.create_payment()
        payment.status = Payment.STATUS_PENDING
        account = self.store.find(Account, description=u'Income').one()
        payment.pay(destination_account=account)
        editor = OutPaymentEditor(self.store, payment)
        self.check_editor(editor, 'editor-paid-out-payment-edit')

    def test_edit__paid_in_payment(self):
        payment = self.create_payment(payment_type=Payment.TYPE_IN)
        payment.status = Payment.STATUS_PENDING
        account = self.store.find(Account, description=u'Expenses').one()
        payment.pay(source_account=account)
        editor = InPaymentEditor(self.store, payment)
        self.check_editor(editor, 'editor-paid-in-payment-edit')

    def test_confirm(self):
        editor = OutPaymentEditor(self.store)
        self.assertFalse(editor.validate_confirm())
        editor.description.update('Payment name')
        self.assertFalse(editor.validate_confirm())

        editor.value.update(100)
        self.assertFalse(editor.validate_confirm())

        editor.due_date.update(localdate(2015, 1, 1).date())
        self.assertTrue(editor.validate_confirm())

        editor.repeat.update(INTERVALTYPE_WEEK)
        self.assertFalse(editor.validate_confirm())

        editor.end_date.update(localdate(2014, 1, 10).date())
        self.assertFalse(editor.validate_confirm())

        editor.end_date.update(localdate(2015, 1, 10).date())
        self.assertTrue(editor.validate_confirm())

        editor.main_dialog.confirm()

        model = editor.retval
        self.check_editor(editor, 'editor-payment-confirm',
                          [model.group] + list(model.group.payments))

    def test_create_category(self):
        category = PaymentCategory(store=self.store,
                                   name=u'TestCategory',
                                   category_type=PaymentCategory.TYPE_RECEIVABLE)
        editor = InPaymentEditor(self.store, category=category.name)

        self.check_editor(editor, 'editor-in-payment-create-with-category')

    def test_end_date_sensitivity(self):
        editor = InPaymentEditor(self.store)
        self.assertNotSensitive(editor, ['end_date'])
        editor.repeat.update(INTERVALTYPE_WEEK)
        self.assertSensitive(editor, ['end_date'])
        editor.repeat.update(-1)
        self.assertNotSensitive(editor, ['end_date'])

    def test_repeat_validation(self):
        editor = InPaymentEditor(self.store)
        editor.description.update(u'desc')
        editor.value.update(Decimal('10'))
        editor.due_date.update(localtoday().date())

        editor.repeat.update(INTERVALTYPE_WEEK)
        self.assertNotSensitive(editor.main_dialog, ['ok_button'])

        editor.repeat.update(_ONCE)
        self.assertSensitive(editor.main_dialog, ['ok_button'])

    def test_value_validation(self):
        editor = InPaymentEditor(self.store)
        self.assertEquals(unicode(editor.value.emit('validate', None)),
                          u"The value must be greater than zero.")

        self.assertEquals(unicode(editor.value.emit('validate', -1)),
                          u"The value must be greater than zero.")
        self.assertFalse(editor.value.emit('validate', 10))

    def test_show_out(self):
        payment = self.create_payment(payment_type=Payment.TYPE_OUT)
        payment.group = self.create_payment_group()
        editor = OutPaymentEditor(self.store, payment)

        self.check_editor(editor, 'editor-out-payment-show')

    def test_show_in(self):
        payment = self.create_payment(payment_type=Payment.TYPE_IN)
        payment.group = self.create_payment_group()
        editor = InPaymentEditor(self.store, payment)

        self.check_editor(editor, 'editor-in-payment-show')

    def test_show_from_sale(self):
        sale = self.create_sale()
        sale.identifier = 12345
        self.add_payments(sale, method_type=u'money')

        p = sale.payments[0]

        editor = InPaymentEditor(self.store, p)
        self.check_editor(editor, 'editor-in-payment-show-sale')

        self.assertTrue(editor.model.group.sale)

    def test_show_from_purchase(self):
        purchase = self.create_purchase_order()
        purchase.identifier = 12345
        self.add_payments(purchase, method_type=u'money')

        p = purchase.payments[0]
        editor = OutPaymentEditor(self.store, p)
        self.check_editor(editor, 'editor-out-payment-show-purchase')

    @mock.patch('stoqlib.gui.editors.paymenteditor.run_dialog')
    def test_show_lonely_dialog_out(self, run_dialog):
        payment = self.create_payment(payment_type=Payment.TYPE_OUT)
        payment.group = self.create_payment_group()
        editor = OutPaymentEditor(self.store, payment)

        self.click(editor.details_button)
        run_dialog.assert_called_once_with(LonelyPaymentDetailsDialog, editor,
                                           editor.store, editor.model)

    @mock.patch('stoqlib.gui.editors.paymenteditor.run_dialog')
    def test_show_lonely_dialog_in(self, run_dialog):
        payment = self.create_payment(payment_type=Payment.TYPE_IN)
        payment.group = self.create_payment_group()
        editor = InPaymentEditor(self.store, payment)

        self.click(editor.details_button)
        run_dialog.assert_called_once_with(LonelyPaymentDetailsDialog, editor,
                                           editor.store, editor.model)

    @mock.patch('stoqlib.gui.editors.paymenteditor.run_dialog')
    def test_show_purchase_dialog(self, run_dialog):
        purchase = self.create_purchase_order()
        self.add_payments(purchase, method_type=u'money')

        p = purchase.payments[0]
        editor = OutPaymentEditor(self.store, p)

        self.click(editor.details_button)
        run_dialog.assert_called_once_with(PurchaseDetailsDialog, editor,
                                           editor.store, purchase)

    @mock.patch('stoqlib.gui.editors.paymenteditor.run_dialog')
    def test_show_sale_dialog(self, run_dialog):
        sale = self.create_sale()
        self.add_product(sale)
        sale.order()
        self.add_payments(sale, method_type=u'money')
        sale.confirm()

        p = sale.payments[0]

        editor = InPaymentEditor(self.store, p)

        self.click(editor.details_button)
        # FIXME: for Viewable comparision in Storm"
        # from stoqlib.domain.sale import SaleView
        # from stoqlib.gui.dialogs.saledetails import SaleDetailsDialog
        # sale_view = SaleView.get(editor.model.group.sale.id, store=self.store)
        # run_dialog.assert_called_once_with(SaleDetailsDialog, editor,
        #                                   editor.store, sale_view)
        self.assertEquals(run_dialog.call_count, 1)

    @mock.patch('stoqlib.gui.editors.paymenteditor.run_dialog')
    def test_show_stock_decrease_dialog(self, run_dialog):
        group = self.create_payment_group()
        decrease = self.create_stock_decrease(group=group)
        self.create_stock_decrease_item(decrease)
        self.add_payments(decrease)
        payment = decrease.group.payments[0]

        editor = InPaymentEditor(self.store, payment)
        self.click(editor.details_button)
        run_dialog.assert_called_once_with(StockDecreaseDetailsDialog, editor,
                                           self.store, decrease)


if __name__ == '__main__':
    from stoqlib.api import api
    c = api.prepare_test()
    unittest.main()
