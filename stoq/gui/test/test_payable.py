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

import contextlib

import mock
from stoqlib.api import api
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.lib.dateutils import localdate
from stoqlib.gui.dialogs.paymentcommentsdialog import PaymentCommentsDialog
from stoqlib.gui.dialogs.paymentchangedialog import PaymentDueDateChangeDialog
from stoqlib.gui.editors.paymenteditor import OutPaymentEditor
from stoqlib.gui.editors.paymentseditor import PurchasePaymentsEditor
from stoqlib.gui.search.paymentsearch import OutPaymentBillCheckSearch
from stoqlib.gui.slaves.paymentconfirmslave import PurchasePaymentConfirmSlave
from stoqlib.reporting.paymentsreceipt import OutPaymentReceipt

from stoq.gui.payable import PayableApp
from stoq.gui.test.baseguitest import BaseGUITest


class TestPayable(BaseGUITest):
    def _check_run_dialog(self, app, action, dialog, other_args):
        with contextlib.nested(
                mock.patch('stoq.gui.payable.run_dialog'),
                mock.patch('stoq.gui.payable.api.new_store'),
                mock.patch.object(self.store, 'commit'),
                mock.patch.object(self.store, 'close')) as ctx:
            new_store = ctx[1]
            new_store.return_value = self.store

            self.activate(action)

            run_dialog = ctx[0]
            self.assertEqual(run_dialog.call_count, 1)
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
        branch = api.get_current_branch(self.store)
        order = self.create_purchase_order(branch=branch)
        order.identifier = 12345
        order.status = PurchaseOrder.ORDER_PENDING
        order.add_item(self.create_sellable(), 1)
        payment = self.add_payments(order, method_type=u'money')[0]
        payment.open_date = payment.due_date = localdate(2012, 1, 1)
        order.confirm()
        payment.identifier = 67890
        order.close()
        return order, payment

    def test_initial(self):
        app = self.create_app(PayableApp, u'payable')
        self.check_app(app, u'payable')

    def test_select(self):
        purchase, payment = self.create_purchase_payment()
        app = self.create_app(PayableApp, u'payable')
        olist = app.results
        olist.select(olist[1])
        self.check_app(app, u'payable-selected')

    @mock.patch('stoq.gui.payable.run_dialog')
    def test_pay(self, run_dialog):
        purchase, payment = self.create_purchase_payment()

        app = self.create_app(PayableApp, u'payable')
        olist = app.results
        olist.select(olist[1])

        with mock.patch('stoq.gui.payable.api', new=self.fake.api):
            self.activate(app.Pay)

        run_dialog.assert_called_once_with(
            PurchasePaymentConfirmSlave, app,
            self.store.readonly, payments=[payment])

    @mock.patch('stoq.gui.payable.run_dialog')
    def test_edit(self, run_dialog):
        purchase, payment = self.create_purchase_payment()

        app = self.create_app(PayableApp, u'payable')
        olist = app.results
        olist.select(olist[1])

        with mock.patch('stoq.gui.payable.api', new=self.fake.api):
            self.activate(app.Edit)

        run_dialog.assert_called_once_with(
            PurchasePaymentsEditor, app,
            self.store.readonly, purchase)

    @mock.patch('stoq.gui.accounts.run_dialog')
    def test_change_due_date_dialog(self, run_dialog):
        purchase, payment = self.create_purchase_payment()

        app = self.create_app(PayableApp, u'payable')
        olist = app.results
        olist.select(olist[1])

        with mock.patch('stoq.gui.accounts.api', new=self.fake.api):
            self.activate(app.ChangeDueDate)

        run_dialog.assert_called_once_with(
            PaymentDueDateChangeDialog, app,
            self.store.readonly, payment, purchase)

    @mock.patch('stoq.gui.accounts.run_dialog')
    def test_details(self, run_dialog):
        purchase, payment = self.create_purchase_payment()

        app = self.create_app(PayableApp, u'payable')
        olist = app.results
        olist.select(olist[1])

        with mock.patch('stoq.gui.accounts.api', new=self.fake.api):
            self.activate(app.Details)

        run_dialog.assert_called_once_with(
            OutPaymentEditor, app,
            self.store.readonly, payment)

    @mock.patch('stoq.gui.accounts.run_dialog')
    def test_comments(self, run_dialog):
        purchase, payment = self.create_purchase_payment()

        app = self.create_app(PayableApp, u'payable')
        olist = app.results
        olist.select(olist[1])

        with mock.patch('stoq.gui.accounts.api', new=self.fake.api):
            self.activate(app.Comments)

        run_dialog.assert_called_once_with(
            PaymentCommentsDialog, app,
            self.store.readonly, payment)

    def test_can_edit(self):
        purchase, payment = self.create_purchase_payment()
        purchase.status = PurchaseOrder.ORDER_CANCELLED

        app = self.create_app(PayableApp, u'payable')
        olist = app.results
        self.assertFalse(app._can_edit([olist[-1]]))

    def test_can_pay(self):
        sale, payment1 = self.create_purchase_payment()
        payment2 = self.add_payments(sale, method_type=u'bill')[0]
        payment2.identifier = 67891

        app = self.create_app(PayableApp, u'payable')

        olist = app.results
        payments = list(olist)[-2:]

        for payment in payments:
            payment.status = Payment.STATUS_PENDING
        self.assertTrue(app._can_pay(payments))

    @mock.patch('stoq.gui.payable.print_report')
    @mock.patch('stoq.gui.payable.localtoday')
    def test_print_receipt(self, localtoday_, print_report):
        today_ = localdate(2012, 1, 1)
        localtoday_.return_value = today_
        purchase, payment = self.create_purchase_payment()
        payment.pay()

        app = self.create_app(PayableApp, u'payable')
        olist = app.results
        olist.select(olist[-1])

        self.activate(app.PrintReceipt)
        print_report.assert_called_once_with(OutPaymentReceipt, payment=payment,
                                             order=purchase, date=today_.date())

    @mock.patch('stoq.gui.payable.PayableApp.change_status')
    def test_cancel_payment(self, change_status):
        payment = self.create_payment()
        payment.status = Payment.STATUS_PENDING
        payment.payment_type = Payment.TYPE_OUT

        app = self.create_app(PayableApp, u'payable')
        olist = app.results
        olist.select(olist[-1])

        self.activate(app.CancelPayment)
        change_status.assert_called_once_with(olist[-1], None,
                                              Payment.STATUS_CANCELLED)

    @mock.patch('stoq.gui.payable.PayableApp.change_status')
    def test_set_not_paid(self, change_status):
        purchase, payment = self.create_purchase_payment()
        payment.pay()

        app = self.create_app(PayableApp, u'payable')
        olist = app.results
        olist.select(olist[-1])

        self.activate(app.SetNotPaid)
        change_status.assert_called_once_with(olist[-1], purchase,
                                              Payment.STATUS_PENDING)

    @mock.patch('stoq.gui.payable.PayableApp.change_due_date')
    def test_change_due_date(self, change_due_date):
        purchase, payment = self.create_purchase_payment()

        app = self.create_app(PayableApp, u'payable')
        olist = app.results
        olist.select(olist[-1])

        self.activate(app.ChangeDueDate)
        change_due_date.assert_called_once_with(olist[-1], purchase)

    def test_run_search(self):
        app = self.create_app(PayableApp, u'payable')
        self._check_run_dialog(app, app.BillCheckSearch,
                               OutPaymentBillCheckSearch, [])
