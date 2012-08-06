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

from stoqlib.domain.payment.category import PaymentCategory
from stoqlib.domain.payment.payment import Payment
from stoqlib.gui.editors.paymenteditor import (InPaymentEditor,
                                               OutPaymentEditor,
                                               INTERVALTYPE_ONCE)
from stoqlib.gui.uitestutils import GUITest
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.defaults import INTERVALTYPE_WEEK

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

    def testCreateCategory(self):
        category = PaymentCategory(connection=self.trans,
                                   name='TestCategory',
                                   category_type=PaymentCategory.TYPE_RECEIVABLE)
        editor = InPaymentEditor(self.trans, category=category.name)

        self.check_editor(editor, 'editor-in-payment-create-with-category',
                          ignores=[repr(category)])

    def testEndDateSensitivity(self):
        editor = InPaymentEditor(self.trans)
        self.assertNotSensitive(editor, ['end_date'])
        editor.repeat.update(INTERVALTYPE_WEEK)
        self.assertSensitive(editor, ['end_date'])
        editor.repeat.update(INTERVALTYPE_ONCE)
        self.assertNotSensitive(editor, ['end_date'])

    def testShow(self):
        payment = self.create_payment(payment_type=Payment.TYPE_OUT)
        payment.due_date = datetime.date(2012, 1, 1)
        payment.group = self.create_payment_group()
        editor = OutPaymentEditor(self.trans, payment)

        self.check_editor(editor, 'editor-out-payment-show')

        payment = self.create_payment(payment_type=Payment.TYPE_IN)
        payment.due_date = datetime.date(2012, 1, 1)
        payment.group = self.create_payment_group()
        editor = InPaymentEditor(self.trans, payment)

        self.check_editor(editor, 'editor-in-payment-show')

    def testShowFromSale(self):
        sale = self.create_sale()
        self.add_payments(sale, method_type='money')

        p = sale.payments[0]
        p.due_date = datetime.date(2012, 1, 1)
        editor = InPaymentEditor(self.trans, p)
        self.check_editor(editor, 'editor-in-payment-show-sale',
                          ignores=[p.group.get_description()])

    def testShowFromPurchase(self):
        purchase = self.create_purchase_order()
        self.add_payments(purchase, method_type='money')

        p = purchase.payments[0]
        p.due_date = datetime.date(2012, 1, 1)
        editor = OutPaymentEditor(self.trans, p)
        self.check_editor(editor, 'editor-out-payment-show-purchase',
                          ignores=[p.group.get_description()])


if __name__ == '__main__':
    from stoqlib.api import api
    c = api.prepare_test()
    unittest.main()
