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
from stoqlib.domain.account import Account
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.gui.dialogs.paymentchangedialog import PaymentDueDateChangeDialog
from stoqlib.gui.dialogs.paymentcommentsdialog import PaymentCommentsDialog
from stoqlib.gui.editors.paymenteditor import InPaymentEditor
from stoqlib.gui.editors.paymentseditor import SalePaymentsEditor
from stoqlib.gui.wizards.renegotiationwizard import PaymentRenegotiationWizard
from stoqlib.reporting.boleto import BillReport

from stoq.gui.receivable import ReceivableApp
from stoq.gui.test.baseguitest import BaseGUITest


class TestReceivable(BaseGUITest):
    def setUp(self):
        BaseGUITest.setUp(self)

    def testInitial(self):
        app = self.create_app(ReceivableApp, 'receivable')
        self.check_app(app, 'receivable')

    def create_receivable_sale(self):
        sale = self.create_sale()
        sale.identifier = 12345
        self.add_product(sale)
        sale.order()
        payment = self.add_payments(sale, method_type='bill')[0]
        payment.identifier = 67890
        sale.confirm()
        payment.due_date = datetime.datetime(2012, 1, 1)
        #payment.paid_date = datetime.datetime(2012, 2, 2)
        return sale, payment

    def testSelect(self):
        sale, payment = self.create_receivable_sale()
        app = self.create_app(ReceivableApp, 'receivable')
        olist = app.main_window.results
        olist.select(olist[1])
        self.check_app(app, 'receivable-selected')

    @mock.patch('stoq.gui.receivable.run_dialog')
    def testReceive(self, run_dialog):
        sale, payment = self.create_receivable_sale()

        app = self.create_app(ReceivableApp, 'receivable')
        olist = app.main_window.results
        olist.select(olist[3])
        assert olist[3].payment == payment

        with mock.patch('stoq.gui.receivable.api', new=self.fake.api):
            self.activate(app.main_window.Receive)

    @mock.patch('stoq.gui.receivable.run_dialog')
    def testEdit(self, run_dialog):
        sale, payment = self.create_receivable_sale()

        app = self.create_app(ReceivableApp, 'receivable')
        olist = app.main_window.results
        olist.select(olist[3])

        with mock.patch('stoq.gui.receivable.api', new=self.fake.api):
            self.activate(app.main_window.Edit)

        run_dialog.assert_called_once_with(
            SalePaymentsEditor, app.main_window,
            self.trans.readonly, sale)

    @mock.patch('stoq.gui.accounts.run_dialog')
    def testChangeDueDate(self, run_dialog):
        sale, payment = self.create_receivable_sale()

        app = self.create_app(ReceivableApp, 'receivable')
        olist = app.main_window.results
        olist.select(olist[3])

        with mock.patch('stoq.gui.accounts.api', new=self.fake.api):
            self.activate(app.main_window.ChangeDueDate)

        run_dialog.assert_called_once_with(
            PaymentDueDateChangeDialog, app.main_window,
            self.trans.readonly, payment, sale)

    @mock.patch('stoq.gui.accounts.run_dialog')
    def testDetails(self, run_dialog):
        sale, payment = self.create_receivable_sale()

        app = self.create_app(ReceivableApp, 'receivable')
        olist = app.main_window.results
        olist.select(olist[3])

        with mock.patch('stoq.gui.accounts.api', new=self.fake.api):
            self.activate(app.main_window.Details)

        run_dialog.assert_called_once_with(
            InPaymentEditor, app.main_window,
            self.trans.readonly, payment)

    @mock.patch('stoq.gui.accounts.run_dialog')
    def testComments(self, run_dialog):
        sale, payment = self.create_receivable_sale()

        app = self.create_app(ReceivableApp, 'receivable')
        olist = app.main_window.results
        olist.select(olist[3])

        with mock.patch('stoq.gui.accounts.api', new=self.fake.api):
            self.activate(app.main_window.Comments)
        run_dialog.assert_called_once_with(
            PaymentCommentsDialog, app.main_window,
            self.trans.readonly, payment)

    @mock.patch('stoq.gui.receivable.run_dialog')
    def testRenegotiate(self, run_dialog):
        sale, payment = self.create_receivable_sale()
        sale.client = self.create_client()

        app = self.create_app(ReceivableApp, 'receivable')
        olist = app.main_window.results
        olist.select(olist[3])

        with mock.patch('stoq.gui.receivable.api', new=self.fake.api):
            self.activate(app.main_window.Renegotiate)

        run_dialog.assert_called_once_with(
            PaymentRenegotiationWizard, app.main_window,
            self.trans.readonly, [payment.group])

    @mock.patch('stoq.gui.receivable.print_report')
    def testPrintDocument(self, print_report):
        sale, payment = self.create_receivable_sale()
        sale.client = self.create_client()

        app = self.create_app(ReceivableApp, 'receivable')
        olist = app.main_window.results
        olist.select(olist[3])

        method = PaymentMethod.get_by_name(self.trans, 'bill')
        account = Account.selectOneBy(description=u'Banco do Brasil',
                                      connection=self.trans)
        method.destination_account = account

        with mock.patch('stoq.gui.receivable.api', new=self.fake.api):
            self.activate(app.main_window.PrintDocument)

        print_report.assert_called_once_with(BillReport, [payment])
