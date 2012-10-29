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

import mock
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.gui.dialogs.paymentcommentsdialog import PaymentCommentsDialog
from stoqlib.gui.dialogs.paymentchangedialog import PaymentDueDateChangeDialog
from stoqlib.gui.editors.paymenteditor import OutPaymentEditor
from stoqlib.gui.editors.paymentseditor import PurchasePaymentsEditor
from stoqlib.gui.slaves.installmentslave import PurchaseInstallmentConfirmationSlave

from stoq.gui.payable import PayableApp
from stoq.gui.test.baseguitest import BaseGUITest


class TestPayable(BaseGUITest):
    def setUp(self):
        BaseGUITest.setUp(self)

    def create_purchase_payment(self):
        order = self.create_purchase_order()
        order.identifier = 12345
        order.status = PurchaseOrder.ORDER_PENDING
        order.add_item(self.create_sellable(), 1)
        payment = self.add_payments(order, method_type='money')[0]
        payment.open_date = payment.due_date = datetime.date(2012, 1, 1)
        order.confirm()
        payment.identifier = 67890
        order.close()
        return order, payment

    def testInitial(self):
        app = self.create_app(PayableApp, 'payable')
        self.check_app(app, 'payable')

    def testSelect(self):
        purchase, payment = self.create_purchase_payment()
        app = self.create_app(PayableApp, 'payable')
        olist = app.main_window.results
        olist.select(olist[1])
        self.check_app(app, 'payable-selected')

    @mock.patch('stoq.gui.payable.run_dialog')
    def testPay(self, run_dialog):
        purchase, payment = self.create_purchase_payment()

        app = self.create_app(PayableApp, 'payable')
        olist = app.main_window.results
        olist.select(olist[1])

        with mock.patch('stoq.gui.payable.api', new=self.fake.api):
            self.activate(app.main_window.Pay)

        run_dialog.assert_called_once_with(
            PurchaseInstallmentConfirmationSlave, app.main_window,
            self.trans.readonly, payments=[payment])

    @mock.patch('stoq.gui.payable.run_dialog')
    def testEdit(self, run_dialog):
        purchase, payment = self.create_purchase_payment()

        app = self.create_app(PayableApp, 'payable')
        olist = app.main_window.results
        olist.select(olist[1])

        with mock.patch('stoq.gui.payable.api', new=self.fake.api):
            self.activate(app.main_window.Edit)

        run_dialog.assert_called_once_with(
            PurchasePaymentsEditor, app.main_window,
            self.trans.readonly, purchase)

    @mock.patch('stoq.gui.accounts.run_dialog')
    def testChangeDueDate(self, run_dialog):
        purchase, payment = self.create_purchase_payment()

        app = self.create_app(PayableApp, 'payable')
        olist = app.main_window.results
        olist.select(olist[1])

        with mock.patch('stoq.gui.accounts.api', new=self.fake.api):
            self.activate(app.main_window.ChangeDueDate)

        run_dialog.assert_called_once_with(
            PaymentDueDateChangeDialog, app.main_window,
            self.trans.readonly, payment, purchase)

    @mock.patch('stoq.gui.accounts.run_dialog')
    def testDetails(self, run_dialog):
        purchase, payment = self.create_purchase_payment()

        app = self.create_app(PayableApp, 'payable')
        olist = app.main_window.results
        olist.select(olist[1])

        with mock.patch('stoq.gui.accounts.api', new=self.fake.api):
            self.activate(app.main_window.Details)

        run_dialog.assert_called_once_with(
            OutPaymentEditor, app.main_window,
            self.trans.readonly, payment)

    @mock.patch('stoq.gui.accounts.run_dialog')
    def testComments(self, run_dialog):
        purchase, payment = self.create_purchase_payment()

        app = self.create_app(PayableApp, 'payable')
        olist = app.main_window.results
        olist.select(olist[1])

        with mock.patch('stoq.gui.accounts.api', new=self.fake.api):
            self.activate(app.main_window.Comments)

        run_dialog.assert_called_once_with(
            PaymentCommentsDialog, app.main_window,
            self.trans.readonly, payment)
