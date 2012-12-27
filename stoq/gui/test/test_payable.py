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
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.gui.dialogs.paymentcommentsdialog import PaymentCommentsDialog
from stoqlib.gui.dialogs.paymentchangedialog import PaymentDueDateChangeDialog
from stoqlib.gui.editors.paymenteditor import OutPaymentEditor
from stoqlib.gui.editors.paymentseditor import PurchasePaymentsEditor
from stoqlib.gui.search.paymentsearch import OutPaymentBillCheckSearch
from stoqlib.gui.slaves.installmentslave import PurchaseInstallmentConfirmationSlave
from stoqlib.reporting.paymentsreceipt import OutPaymentReceipt

from stoq.gui.payable import PayableApp
from stoq.gui.test.baseguitest import BaseGUITest


class TestPayable(BaseGUITest):
    @mock.patch('stoq.gui.payable.run_dialog')
    @mock.patch('stoq.gui.payable.api.new_store')
    def _check_run_dialog(self, app, action, dialog, other_args,
                          new_store, run_dialog):
        new_store.return_value = self.store

        with mock.patch.object(self.store, 'commit'):
            with mock.patch.object(self.store, 'close'):
                self.activate(action)
                run_dialog.assert_called_once()
                args, kwargs = run_dialog.call_args
                self.assertEquals(args[0], dialog)
                self.assertEquals(args[1], app)
                self.assertEquals(args[2], self.store)

                if not other_args or len(other_args) != len(args[2:]):
                    return

                for arg in args[2:]:
                    for other_arg in other_args:
                        self.assertEquals(arg, other_arg)

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
            self.store.readonly, payments=[payment])

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
            self.store.readonly, purchase)

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
            self.store.readonly, payment, purchase)

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
            self.store.readonly, payment)

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
            self.store.readonly, payment)

    def test_can_edit(self):
        purchase, payment = self.create_purchase_payment()
        purchase.status = PurchaseOrder.ORDER_CANCELLED

        app = self.create_app(PayableApp, 'payable')
        olist = app.main_window.results
        self.assertFalse(app.main_window._can_edit([olist[-1]]))

    def test_can_pay(self):
        sale, payment1 = self.create_purchase_payment()
        payment2 = self.add_payments(sale, method_type='bill')[0]
        payment2.identifier = 67891

        app = self.create_app(PayableApp, 'receivable')

        olist = app.main_window.results
        payments = list(olist)[-2:]

        for payment in payments:
            payment.status = Payment.STATUS_PENDING
        self.assertTrue(app.main_window._can_pay(payments))

    @mock.patch('stoq.gui.payable.print_report')
    def test_print_receipt(self, print_report):
        purchase, payment = self.create_purchase_payment()
        payment.pay()

        app = self.create_app(PayableApp, 'payable')
        olist = app.main_window.results
        olist.select(olist[-1])

        self.activate(app.main_window.PrintReceipt)
        print_report.assert_called_once_with(OutPaymentReceipt, payment=payment,
                                             order=purchase, date=datetime.date.today())

    @mock.patch('stoq.gui.payable.PayableApp.change_status')
    def test_cancel_payment(self, change_status):
        payment = self.create_payment()
        payment.status = Payment.STATUS_PENDING
        payment.payment_type = Payment.TYPE_OUT

        app = self.create_app(PayableApp, 'payable')
        olist = app.main_window.results
        olist.select(olist[-1])

        self.activate(app.main_window.CancelPayment)
        change_status.assert_called_once_with(olist[-1], None,
                                              Payment.STATUS_CANCELLED)

    @mock.patch('stoq.gui.payable.PayableApp.change_status')
    def test_set_not_paid(self, change_status):
        purchase, payment = self.create_purchase_payment()
        payment.pay()

        app = self.create_app(PayableApp, 'payable')
        olist = app.main_window.results
        olist.select(olist[-1])

        self.activate(app.main_window.SetNotPaid)
        change_status.assert_called_once_with(olist[-1], purchase,
                                              Payment.STATUS_PENDING)

    @mock.patch('stoq.gui.payable.PayableApp.change_due_date')
    def test_change_due_date(self, change_due_date):
        purchase, payment = self.create_purchase_payment()

        app = self.create_app(PayableApp, 'payable')
        olist = app.main_window.results
        olist.select(olist[-1])

        self.activate(app.main_window.ChangeDueDate)
        change_due_date.assert_called_once_with(olist[-1], purchase)

    def test_run_search(self):
        app = self.create_app(PayableApp, 'payable')
        self._check_run_dialog(app.main_window, app.main_window.BillCheckSearch,
                               OutPaymentBillCheckSearch, [])
