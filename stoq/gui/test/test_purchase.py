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

from stoqlib.api import api

from stoq.gui.purchase import PurchaseApp
from stoq.gui.test.baseguitest import BaseGUITest
from stoqlib.domain.purchase import PurchaseItem, PurchaseOrder, PurchaseOrderView
from stoqlib.domain.receiving import (ReceivingOrderItem, ReceivingOrder,
                                      PurchaseReceivingMap)
from stoqlib.gui.dialogs.purchasedetails import PurchaseDetailsDialog
from stoqlib.gui.search.searchresultview import SearchResultListView
from stoqlib.gui.wizards.consignmentwizard import ConsignmentWizard
from stoqlib.gui.wizards.productwizard import ProductCreateWizard
from stoqlib.gui.wizards.purchasefinishwizard import PurchaseFinishWizard
from stoqlib.gui.wizards.purchasequotewizard import QuotePurchaseWizard
from stoqlib.gui.wizards.purchasewizard import PurchaseWizard
from stoqlib.reporting.purchase import PurchaseReport


class TestPurchase(BaseGUITest):

    def create_app(self, *args, **kwargs):
        app = BaseGUITest.create_app(self, *args, **kwargs)
        app.branch_filter.combo.select_item_by_data(None)
        return app

    def test_initial(self):
        app = self.create_app(PurchaseApp, u'purchase')
        for purchase in app.results:
            purchase.open_date = datetime.datetime(2012, 1, 1)
        self.check_app(app, u'purchase')

    def test_select(self):
        self.create_purchase_order()
        app = self.create_app(PurchaseApp, u'purchase')
        results = app.results
        results.select(results[0])

    @mock.patch('stoq.gui.purchase.PurchaseApp.run_dialog')
    def test_edit_quote_order(self, run_dialog):
        api.sysparam.set_bool(self.store, 'SMART_LIST_LOADING', False)
        purchase = self.create_purchase_order()

        app = self.create_app(PurchaseApp, u'purchase')
        for purchase in app.results:
            purchase.open_date = datetime.datetime(2012, 1, 1)
        olist = app.results
        olist.select(olist[0])

        with mock.patch('stoq.gui.purchase.api', new=self.fake.api):
            self.fake.set_retval(purchase)
            self.activate(app.NewQuote)

            self.assertEquals(run_dialog.call_count, 1)
            args, kwargs = run_dialog.call_args
            wizard, store, edit_mode = args
            self.assertEquals(wizard, QuotePurchaseWizard)
            self.assertTrue(store is not None)
            self.assertEquals(edit_mode, None)

    @mock.patch('stoq.gui.purchase.PurchaseApp.print_report')
    def test_print_report(self, print_report):
        api.sysparam.set_bool(self.store, 'SMART_LIST_LOADING', False)
        app = self.create_app(PurchaseApp, u'purchase')

        self.activate(app.window.Print)
        self.assertEquals(print_report.call_count, 1)

        args, kwargs = print_report.call_args
        report, results, views = args
        self.assertEquals(report, PurchaseReport)
        self.assertTrue(isinstance(results, SearchResultListView))
        for view in views:
            self.assertTrue(isinstance(view, PurchaseOrderView))

    @mock.patch('stoq.gui.purchase.PurchaseApp.select_result')
    @mock.patch('stoq.gui.purchase.PurchaseApp.run_dialog')
    @mock.patch('stoq.gui.purchase.api.new_store')
    def test_new_quote_order(self, new_store, run_dialog, select_result):
        new_store.return_value = self.store

        self.clean_domain([ReceivingOrderItem, PurchaseReceivingMap,
                           ReceivingOrder, PurchaseItem, PurchaseOrder])

        quotation = self.create_quotation()
        quotation.purchase.add_item(self.create_sellable(), 2)
        quotation.purchase.status = PurchaseOrder.ORDER_PENDING

        api.sysparam.set_bool(self.store, 'SMART_LIST_LOADING', False)
        app = self.create_app(PurchaseApp, u'purchase')

        olist = app.results
        olist.select(olist[0])
        self.store.retval = olist[0]

        with mock.patch.object(self.store, 'close'):
            with mock.patch.object(self.store, 'commit'):
                self.activate(app.Edit)
                run_dialog.assert_called_once_with(PurchaseWizard,
                                                   self.store,
                                                   quotation.purchase, False)
                select_result.assert_called_once_with(olist[0])

    @mock.patch('stoq.gui.purchase.PurchaseApp.run_dialog')
    def test_details_dialog(self, run_dialog):
        self.clean_domain([ReceivingOrderItem, PurchaseReceivingMap,
                           ReceivingOrder, PurchaseItem, PurchaseOrder])

        purchase = self.create_purchase_order()
        purchase.add_item(self.create_sellable(), 2)

        api.sysparam.set_bool(self.store, 'SMART_LIST_LOADING', False)
        app = self.create_app(PurchaseApp, u'purchase')

        olist = app.results
        olist.select(olist[0])
        olist.double_click(0)

        self.assertEquals(run_dialog.call_count, 1)
        args, kwargs = run_dialog.call_args
        dialog, store = args

        self.assertEquals(dialog, PurchaseDetailsDialog)
        self.assertTrue(store is not None)
        self.assertEquals(kwargs[u'model'], purchase)

    @mock.patch('stoq.gui.purchase.yesno')
    @mock.patch('stoq.gui.purchase.api.new_store')
    def test_confirm_order(self, new_store, yesno):
        new_store.return_value = self.store
        yesno.return_value = True

        self.clean_domain([ReceivingOrderItem, PurchaseReceivingMap,
                           ReceivingOrder, PurchaseItem, PurchaseOrder])

        purchase = self.create_purchase_order()
        purchase.add_item(self.create_sellable(), 2)
        purchase.status = PurchaseOrder.ORDER_PENDING

        api.sysparam.set_bool(self.store, 'SMART_LIST_LOADING', False)
        app = self.create_app(PurchaseApp, u'purchase')

        olist = app.results
        olist.select(olist[0])

        with mock.patch.object(self.store, 'close'):
            with mock.patch.object(self.store, 'commit'):
                self.activate(app.Confirm)
                yesno.assert_called_once_with(u'The selected order will be '
                                              u'marked as sent.',
                                              gtk.RESPONSE_YES,
                                              u"Confirm order", u"Don't confirm")
                self.assertEquals(purchase.status, PurchaseOrder.ORDER_CONFIRMED)

    @mock.patch('stoq.gui.purchase.PurchaseApp.run_dialog')
    @mock.patch('stoq.gui.purchase.api.new_store')
    def test_finish_order(self, new_store, run_dialog):
        new_store.return_value = self.store
        self.clean_domain([ReceivingOrderItem, PurchaseReceivingMap,
                           ReceivingOrder, PurchaseItem, PurchaseOrder])

        purchase = self.create_purchase_order()
        purchase.add_item(self.create_sellable(), 2)
        purchase.get_items()[0].quantity_received = 2
        purchase.status = PurchaseOrder.ORDER_CONFIRMED
        purchase.received_quantity = 2

        api.sysparam.set_bool(self.store, 'SMART_LIST_LOADING', False)
        app = self.create_app(PurchaseApp, u'purchase')

        olist = app.results
        olist.select(olist[0])

        with mock.patch.object(self.store, 'close'):
            with mock.patch.object(self.store, 'commit'):
                self.activate(app.Finish)
                run_dialog.assert_called_once_with(PurchaseFinishWizard,
                                                   self.store, purchase)

    @mock.patch('stoq.gui.purchase.yesno')
    @mock.patch('stoq.gui.purchase.api.new_store')
    def test_cancel_order(self, new_store, yesno):
        new_store.return_value = self.store
        yesno.return_value = True

        self.clean_domain([ReceivingOrderItem, PurchaseReceivingMap,
                           ReceivingOrder, PurchaseItem, PurchaseOrder])

        purchase = self.create_purchase_order()
        purchase.add_item(self.create_sellable(), 2)
        purchase.status = PurchaseOrder.ORDER_PENDING

        api.sysparam.set_bool(self.store, 'SMART_LIST_LOADING', False)
        app = self.create_app(PurchaseApp, u'purchase')

        olist = app.results
        olist.select(olist[0])

        with mock.patch.object(self.store, 'close'):
            with mock.patch.object(self.store, 'commit'):
                self.activate(app.Cancel)
                yesno.assert_called_once_with(u'The selected order will be '
                                              u'cancelled.', gtk.RESPONSE_YES,
                                              u"Cancel order", u"Don't cancel")
                self.assertEquals(purchase.status, PurchaseOrder.ORDER_CANCELLED)

    @mock.patch('stoqlib.gui.wizards.productwizard.run_dialog')
    @mock.patch('stoqlib.gui.wizards.productwizard.api.new_store')
    def test_new_product(self, new_store, run_dialog):
        run_dialog.return_value = False
        new_store.return_value = self.store

        self.clean_domain([ReceivingOrderItem, PurchaseReceivingMap,
                           ReceivingOrder, PurchaseItem, PurchaseOrder])

        purchase = self.create_purchase_order()
        purchase.add_item(self.create_sellable(), 2)
        purchase.status = PurchaseOrder.ORDER_PENDING

        api.sysparam.set_bool(self.store, 'SMART_LIST_LOADING', False)
        app = self.create_app(PurchaseApp, u'purchase')

        olist = app.results
        olist.select(olist[0])

        with mock.patch.object(self.store, 'close'):
            with mock.patch.object(self.store, 'commit'):
                self.activate(app.NewProduct)
                run_dialog.assert_called_once_with(ProductCreateWizard,
                                                   app, self.store)

    @mock.patch('stoq.gui.purchase.PurchaseApp.run_dialog')
    def test_new_consignment(self, run_dialog):
        api.sysparam.set_bool(self.store, 'SMART_LIST_LOADING', False)
        purchase = self.create_purchase_order()

        app = self.create_app(PurchaseApp, u'purchase')
        for purchase in app.results:
            purchase.open_date = datetime.datetime(2012, 1, 1)
        olist = app.results
        olist.select(olist[0])

        with mock.patch('stoq.gui.purchase.api', new=self.fake.api):
            self.fake.set_retval(purchase)
            self.activate(app.NewConsignment)

            self.assertEquals(run_dialog.call_count, 1)
            args, kwargs = run_dialog.call_args
            wizard, store = args
            self.assertEquals(wizard, ConsignmentWizard)
            self.assertTrue(store is not None)
            self.assertEquals(kwargs[u'model'], None)
