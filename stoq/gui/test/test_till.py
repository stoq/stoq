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

import decimal

import mock

from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.sale import Sale
from stoqlib.gui.dialogs.saledetails import SaleDetailsDialog
from stoqlib.gui.editors.tilleditor import CashInEditor
from stoqlib.gui.search.personsearch import ClientSearch
from stoqlib.gui.search.salesearch import (SaleWithToolbarSearch,
                                           SoldItemsByBranchSearch)
from stoqlib.gui.search.tillsearch import TillFiscalOperationsSearch

from stoq.gui.till import TillApp
from stoq.gui.test.baseguitest import BaseGUITest


class TestTill(BaseGUITest):
    @mock.patch('stoq.gui.till.TillApp.run_dialog')
    def _check_run_dialog(self, action, dialog, run_dialog):
        with mock.patch.object(self.store, 'commit'):
            with mock.patch.object(self.store, 'close'):
                self.activate(action)
                self.assertEquals(run_dialog.call_count, 1)
                args, kwargs = run_dialog.call_args
                called_dialog, store = args
                self.assertEquals(called_dialog, dialog)
                self.assertEquals(store, self.store)

    def testInitial(self):
        app = self.create_app(TillApp, u'till')
        self.check_app(app, u'till')

    def testSelect(self):
        sale = self.create_sale(branch=get_current_branch(self.store))
        self.add_product(sale)
        sale.status = Sale.STATUS_CONFIRMED

        app = self.create_app(TillApp, u'till')
        results = app.main_window.results
        results.select(results[0])

    @mock.patch('stoqlib.gui.fiscalprinter.FiscalCoupon.confirm')
    @mock.patch('stoq.gui.till.api.new_store')
    def test_confirm_order(self, new_store, confirm):
        new_store.return_value = self.store

        sale = self.create_sale(branch=get_current_branch(self.store))
        self.add_product(sale)
        sale.status = Sale.STATUS_ORDERED

        app = self.create_app(TillApp, u'till')

        app.main_window.status_filter.select(Sale.STATUS_ORDERED)

        results = app.main_window.results
        results.select(results[0])

        with mock.patch.object(self.store, 'commit'):
            with mock.patch.object(self.store, 'close'):
                self.activate(app.main_window.Confirm)
                confirm.assert_called_once_with(
                    sale, self.store,
                    subtotal=decimal.Decimal("10.00"))

    @mock.patch('stoq.gui.till.api.new_store')
    def test_run_search_dialogs(self, new_store):
        new_store.return_value = self.store

        app = self.create_app(TillApp, u'till')

        self._check_run_dialog(app.main_window.SearchClient, ClientSearch)
        self._check_run_dialog(app.main_window.SearchSale,
                               SaleWithToolbarSearch)
        self._check_run_dialog(app.main_window.SearchSoldItemsByBranch,
                               SoldItemsByBranchSearch)
        self._check_run_dialog(app.main_window.SearchFiscalTillOperations,
                               TillFiscalOperationsSearch)

    @mock.patch('stoq.gui.till.run_dialog')
    def test_run_details_dialog(self, run_dialog):
        sale = self.create_sale(branch=get_current_branch(self.store))
        self.add_product(sale)
        sale.status = Sale.STATUS_ORDERED

        app = self.create_app(TillApp, u'till')
        results = app.main_window.results
        results.select(results[0])

        self.activate(app.main_window.Details)
        self.assertEquals(run_dialog.call_count, 1)
        args, kwargs = run_dialog.call_args
        dialog, _app, store, sale_view = args
        self.assertEquals(dialog, SaleDetailsDialog)
        self.assertEquals(_app, app.main_window)
        self.assertTrue(store is not None)
        self.assertEquals(sale_view, results[0])

    @mock.patch('stoq.gui.till.run_dialog')
    @mock.patch('stoqlib.api.new_store')
    def test_run_add_cash_dialog(self, new_store, run_dialog):
        new_store.return_value = self.store

        app = self.create_app(TillApp, u'till')

        with mock.patch.object(self.store, 'commit'):
            with mock.patch.object(self.store, 'close'):
                app.main_window.TillAddCash.set_sensitive(True)
                self.activate(app.main_window.TillAddCash)
                run_dialog.assert_called_once_with(CashInEditor,
                                                   app.main_window, self.store)

    @mock.patch('stoq.gui.till.return_sale')
    @mock.patch('stoqlib.api.new_store')
    def test_return_sale(self, new_store, return_sale):
        new_store.return_value = self.store

        sale = self.create_sale(branch=get_current_branch(self.store))
        self.add_product(sale)
        sale.status = Sale.STATUS_ORDERED

        app = self.create_app(TillApp, u'till')

        results = app.main_window.results
        results.select(results[0])

        with mock.patch.object(self.store, 'commit'):
            with mock.patch.object(self.store, 'close'):
                self.activate(app.main_window.Return)
                return_sale.assert_called_once_with(app.main_window.get_toplevel(),
                                                    results[0], self.store)
