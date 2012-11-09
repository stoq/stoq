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
import gtk

from kiwi.ui.search import SearchResults
from stoqlib.api import api

from stoq.gui.purchase import PurchaseApp
from stoq.gui.test.baseguitest import BaseGUITest
from stoqlib.domain.purchase import PurchaseItem, PurchaseOrder, PurchaseOrderView
from stoqlib.domain.receiving import ReceivingOrderItem, ReceivingOrder
from stoqlib.gui.editors.producteditor import ProductEditor
from stoqlib.gui.dialogs.purchasedetails import PurchaseDetailsDialog
from stoqlib.gui.wizards.consignmentwizard import ConsignmentWizard
from stoqlib.gui.wizards.purchasefinishwizard import PurchaseFinishWizard
from stoqlib.gui.wizards.purchasequotewizard import QuotePurchaseWizard
from stoqlib.gui.wizards.purchasewizard import PurchaseWizard
from stoqlib.reporting.purchase import PurchaseReport


class TestPurchase(BaseGUITest):
    def testInitial(self):
        app = self.create_app(PurchaseApp, 'purchase')
        for purchase in app.main_window.results:
            purchase.open_date = datetime.datetime(2012, 1, 1)
        self.check_app(app, 'purchase')

    def testSelect(self):
        self.create_purchase_order()
        app = self.create_app(PurchaseApp, 'purchase')
        results = app.main_window.results
        results.select(results[0])

    @mock.patch('stoq.gui.purchase.PurchaseApp.run_dialog')
    def test_edit_quote_order(self, run_dialog):
        api.sysparam(self.trans).update_parameter('SMART_LIST_LOADING', '0')
        purchase = self.create_purchase_order()

        app = self.create_app(PurchaseApp, 'purchase')
        for purchase in app.main_window.results:
            purchase.open_date = datetime.datetime(2012, 1, 1)
        olist = app.main_window.results
        olist.select(olist[0])

        with mock.patch('stoq.gui.purchase.api', new=self.fake.api):
            self.fake.set_retval(purchase)
            self.activate(app.main_window.NewQuote)

            self.assertEquals(run_dialog.call_count, 1)
            args, kwargs = run_dialog.call_args
            wizard, trans, edit_mode = args
            self.assertEquals(wizard, QuotePurchaseWizard)
            self.assertTrue(trans is not None)
            self.assertEquals(edit_mode, None)

    @mock.patch('stoq.gui.purchase.PurchaseApp.print_report')
    def test_print_report(self, print_report):
        api.sysparam(self.trans).update_parameter('SMART_LIST_LOADING', '0')
        app = self.create_app(PurchaseApp, 'purchase')

        self.activate(app.launcher.Print)
        self.assertEquals(print_report.call_count, 1)

        args, kwargs = print_report.call_args
        report, results, views = args
        self.assertEquals(report, PurchaseReport)
        self.assertTrue(isinstance(results, SearchResults))
        for view in views:
            self.assertTrue(isinstance(view, PurchaseOrderView))

    @mock.patch('stoq.gui.purchase.PurchaseApp.select_result')
    @mock.patch('stoq.gui.purchase.PurchaseApp.run_dialog')
    @mock.patch('stoq.gui.purchase.api.new_transaction')
    def test_new_quote_order(self, new_transaction, run_dialog, select_result):
        new_transaction.return_value = self.trans

        self.clean_domain([ReceivingOrderItem, ReceivingOrder,
                           PurchaseItem, PurchaseOrder])

        quotation = self.create_quotation()
        quotation.purchase.add_item(self.create_sellable(), 2)
        quotation.purchase.status = PurchaseOrder.ORDER_PENDING

        api.sysparam(self.trans).update_parameter('SMART_LIST_LOADING', '0')
        app = self.create_app(PurchaseApp, 'purchase')

        olist = app.main_window.results
        olist.select(olist[0])
        self.trans.retval = olist[0]

        with mock.patch.object(self.trans, 'close'):
            with mock.patch.object(self.trans, 'commit'):
                self.activate(app.main_window.Edit)
                run_dialog.assert_called_once_with(PurchaseWizard,
                                                   self.trans,
                                                   quotation.purchase, False)
                select_result.assert_called_once_with(olist[0])

    @mock.patch('stoq.gui.purchase.PurchaseApp.run_dialog')
    def test_details_dialog(self, run_dialog):
        self.clean_domain([ReceivingOrderItem, ReceivingOrder,
                           PurchaseItem, PurchaseOrder])

        purchase = self.create_purchase_order()
        purchase.add_item(self.create_sellable(), 2)

        api.sysparam(self.trans).update_parameter('SMART_LIST_LOADING', '0')
        app = self.create_app(PurchaseApp, 'purchase')

        olist = app.main_window.results
        olist.select(olist[0])
        olist.double_click(0)

        self.assertEquals(run_dialog.call_count, 1)
        args, kwargs = run_dialog.call_args
        dialog, trans = args

        self.assertEquals(dialog, PurchaseDetailsDialog)
        self.assertTrue(trans is not None)
        self.assertEquals(kwargs['model'], purchase)

    @mock.patch('stoq.gui.purchase.yesno')
    @mock.patch('stoq.gui.purchase.api.new_transaction')
    def test_confirm_order(self, new_transaction, yesno):
        new_transaction.return_value = self.trans
        yesno.return_value = False

        self.clean_domain([ReceivingOrderItem, ReceivingOrder,
                           PurchaseItem, PurchaseOrder])

        purchase = self.create_purchase_order()
        purchase.add_item(self.create_sellable(), 2)
        purchase.status = PurchaseOrder.ORDER_PENDING

        api.sysparam(self.trans).update_parameter('SMART_LIST_LOADING', '0')
        app = self.create_app(PurchaseApp, 'purchase')

        olist = app.main_window.results
        olist.select(olist[0])

        with mock.patch.object(self.trans, 'close'):
            with mock.patch.object(self.trans, 'commit'):
                self.activate(app.main_window.Confirm)
                yesno.assert_called_once_with('The selected order will be '
                                              'marked as sent.', gtk.RESPONSE_NO,
                                              "Don't confirm", "Confirm order")
                self.assertEquals(purchase.status, PurchaseOrder.ORDER_CONFIRMED)

    @mock.patch('stoq.gui.purchase.PurchaseApp.run_dialog')
    @mock.patch('stoq.gui.purchase.api.new_transaction')
    def test_finish_order(self, new_transaction, run_dialog):
        new_transaction.return_value = self.trans
        self.clean_domain([ReceivingOrderItem, ReceivingOrder,
                           PurchaseItem, PurchaseOrder])

        purchase = self.create_purchase_order()
        purchase.add_item(self.create_sellable(), 2)
        purchase.get_items()[0].quantity_received = 2
        purchase.status = PurchaseOrder.ORDER_CONFIRMED
        purchase.received_quantity = 2

        api.sysparam(self.trans).update_parameter('SMART_LIST_LOADING', '0')
        app = self.create_app(PurchaseApp, 'purchase')

        olist = app.main_window.results
        olist.select(olist[0])

        with mock.patch.object(self.trans, 'close'):
            with mock.patch.object(self.trans, 'commit'):
                self.activate(app.main_window.Finish)
                run_dialog.assert_called_once_with(PurchaseFinishWizard,
                                                   self.trans, purchase)

    @mock.patch('stoq.gui.purchase.yesno')
    @mock.patch('stoq.gui.purchase.api.new_transaction')
    def test_cancel_order(self, new_transaction, yesno):
        new_transaction.return_value = self.trans
        yesno.return_value = False

        self.clean_domain([ReceivingOrderItem, ReceivingOrder,
                           PurchaseItem, PurchaseOrder])

        purchase = self.create_purchase_order()
        purchase.add_item(self.create_sellable(), 2)
        purchase.status = PurchaseOrder.ORDER_PENDING

        api.sysparam(self.trans).update_parameter('SMART_LIST_LOADING', '0')
        app = self.create_app(PurchaseApp, 'purchase')

        olist = app.main_window.results
        olist.select(olist[0])

        with mock.patch.object(self.trans, 'close'):
            with mock.patch.object(self.trans, 'commit'):
                self.activate(app.main_window.Cancel)
                yesno.assert_called_once_with('The selected order will be '
                                              'cancelled.', gtk.RESPONSE_NO,
                                              "Don't cancel", "Cancel order")
                self.assertEquals(purchase.status, PurchaseOrder.ORDER_CANCELLED)

    @mock.patch('stoq.gui.purchase.PurchaseApp.run_dialog')
    @mock.patch('stoq.gui.purchase.api.new_transaction')
    def test_new_product(self, new_transaction, run_dialog):
        new_transaction.return_value = self.trans

        self.clean_domain([ReceivingOrderItem, ReceivingOrder,
                           PurchaseItem, PurchaseOrder])

        purchase = self.create_purchase_order()
        purchase.add_item(self.create_sellable(), 2)
        purchase.status = PurchaseOrder.ORDER_PENDING

        api.sysparam(self.trans).update_parameter('SMART_LIST_LOADING', '0')
        app = self.create_app(PurchaseApp, 'purchase')

        olist = app.main_window.results
        olist.select(olist[0])

        with mock.patch.object(self.trans, 'close'):
            with mock.patch.object(self.trans, 'commit'):
                self.activate(app.main_window.NewProduct)
                run_dialog.assert_called_once_with(ProductEditor,
                                                   self.trans, model=None)

    @mock.patch('stoq.gui.purchase.PurchaseApp.run_dialog')
    def test_new_consignment(self, run_dialog):
        api.sysparam(self.trans).update_parameter('SMART_LIST_LOADING', '0')
        purchase = self.create_purchase_order()

        app = self.create_app(PurchaseApp, 'purchase')
        for purchase in app.main_window.results:
            purchase.open_date = datetime.datetime(2012, 1, 1)
        olist = app.main_window.results
        olist.select(olist[0])

        with mock.patch('stoq.gui.purchase.api', new=self.fake.api):
            self.fake.set_retval(purchase)
            self.activate(app.main_window.NewConsignment)

            self.assertEquals(run_dialog.call_count, 1)
            args, kwargs = run_dialog.call_args
            wizard, trans = args
            self.assertEquals(wizard, ConsignmentWizard)
            self.assertTrue(trans is not None)
            self.assertEquals(kwargs['model'], None)
