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
import decimal
from datetime import datetime

import mock
from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.sale import Sale
from stoqlib.domain.till import Till
from stoqlib.gui.dialogs.saledetails import SaleDetailsDialog
from stoqlib.gui.editors.paymentseditor import SalePaymentsEditor
from stoqlib.gui.editors.tilleditor import CashInEditor
from stoqlib.gui.search.personsearch import ClientSearch
from stoqlib.gui.search.salesearch import (SaleWithToolbarSearch,
                                           SoldItemsByBranchSearch)
from stoqlib.gui.search.tillsearch import TillFiscalOperationsSearch
from stoqlib.lib.dateutils import localtoday

from stoq.gui.till import TillApp
from stoq.gui.test.baseguitest import BaseGUITest


class TestTill(BaseGUITest):
    def _check_run_dialog(self, action, dialog):
        with contextlib.nested(
                mock.patch('stoq.gui.till.TillApp.run_dialog'),
                mock.patch.object(self.store, 'commit'),
                mock.patch.object(self.store, 'close')) as ctx:
            self.activate(action)
            run_dialog = ctx[0]
            self.assertEquals(run_dialog.call_count, 1)
            args, kwargs = run_dialog.call_args
            called_dialog, store = args
            self.assertEquals(called_dialog, dialog)
            self.assertEquals(store, self.store)

    def test_initial_with_open_till(self):
        till = self.create_till()
        till.opening_date = localtoday()
        till.status = Till.STATUS_OPEN
        app = self.create_app(TillApp, u'till')
        self.check_app(app, u'till-opened-till')

    def test_initial_with_closed_till(self):
        app = self.create_app(TillApp, u'till')
        self.check_app(app, u'till-closed-till')

    @mock.patch('stoqlib.gui.fiscalprinter.api.new_store')
    @mock.patch('stoqlib.gui.fiscalprinter.yesno')
    @mock.patch('stoqlib.gui.fiscalprinter.run_dialog')
    def test_initial_with_blocked_till(self, yesno, new_store, run_dialog):
        till = self.create_till()
        till.opening_date = datetime(2015, 1, 2)
        till.status = Till.STATUS_OPEN

        new_store.return_value = self.store
        yesno.return_value = False
        app = self.create_app(TillApp, u'till')
        self.check_app(app, u'till-blocked-till')

    def test_select(self):
        sale = self.create_sale(branch=get_current_branch(self.store))
        self.add_product(sale)
        sale.status = Sale.STATUS_CONFIRMED

        app = self.create_app(TillApp, u'till')
        app.status_filter.select(Sale.STATUS_CONFIRMED)
        results = app.results
        results.select(results[0])

    @mock.patch('stoq.gui.till.run_dialog')
    def test_confirm_order(self, run_dialog):
        with contextlib.nested(
                mock.patch('stoqlib.gui.fiscalprinter.FiscalCoupon.confirm'),
                mock.patch('stoq.gui.till.api.new_store'),
                mock.patch.object(self.store, 'commit'),
                mock.patch.object(self.store, 'close')) as ctx:
            new_store = ctx[1]
            new_store.return_value = self.store

            sale = self.create_sale(branch=get_current_branch(self.store))
            self.add_product(sale)
            sale.status = Sale.STATUS_ORDERED

            app = self.create_app(TillApp, u'till')

            app.status_filter.select(Sale.STATUS_ORDERED)

            results = app.results
            results.select(results[0])

            self.activate(app.Confirm)

            confirm = ctx[0]
            confirm.assert_called_once_with(
                sale, self.store,
                subtotal=decimal.Decimal("10.00"))

            # Confirm a pre sale.
            wo_sale = self.create_sale(branch=get_current_branch(self.store))
            wo_sale.status = Sale.STATUS_QUOTE
            wo_sale.add_sellable(self.create_sellable())

            workorder = self.create_workorder()
            workorder.sale = wo_sale

            app.status_filter.select(Sale.STATUS_QUOTE)
            results.select(results[0])
            self.activate(app.Confirm)
            run_dialog.assert_called_once_with(SalePaymentsEditor, app,
                                               self.store, wo_sale)
            self.assertEquals(sale.status, Sale.STATUS_ORDERED)

    @mock.patch('stoq.gui.till.api.new_store')
    def test_run_search_dialogs(self, new_store):
        new_store.return_value = self.store

        app = self.create_app(TillApp, u'till')

        self._check_run_dialog(app.SearchClient, ClientSearch)
        self._check_run_dialog(app.SearchSale,
                               SaleWithToolbarSearch)
        self._check_run_dialog(app.SearchSoldItemsByBranch,
                               SoldItemsByBranchSearch)
        self._check_run_dialog(app.SearchFiscalTillOperations,
                               TillFiscalOperationsSearch)

    @mock.patch('stoq.gui.till.run_dialog')
    def test_run_details_dialog(self, run_dialog):
        sale = self.create_sale(branch=get_current_branch(self.store))
        self.add_product(sale)
        sale.status = Sale.STATUS_ORDERED

        app = self.create_app(TillApp, u'till')
        app.status_filter.select(Sale.STATUS_ORDERED)
        results = app.results
        results.select(results[0])

        self.activate(app.Details)
        self.assertEquals(run_dialog.call_count, 1)
        args, kwargs = run_dialog.call_args
        dialog, _app, store, sale_view = args
        self.assertEquals(dialog, SaleDetailsDialog)
        self.assertEquals(_app, app)
        self.assertTrue(store is not None)
        self.assertEquals(sale_view, results[0])

    @mock.patch('stoq.gui.till.run_dialog')
    @mock.patch('stoqlib.api.new_store')
    def test_run_add_cash_dialog(self, new_store, run_dialog):
        new_store.return_value = self.store

        app = self.create_app(TillApp, u'till')

        with mock.patch.object(self.store, 'commit'):
            with mock.patch.object(self.store, 'close'):
                app.TillAddCash.set_sensitive(True)
                self.activate(app.TillAddCash)
                run_dialog.assert_called_once_with(CashInEditor,
                                                   app, self.store)

    @mock.patch('stoq.gui.till.return_sale')
    @mock.patch('stoqlib.api.new_store')
    def test_return_sale(self, new_store, return_sale):
        new_store.return_value = self.store

        with self.sysparam(ALLOW_CANCEL_CONFIRMED_SALES=True):
            sale = self.create_sale(branch=get_current_branch(self.store))
            self.add_product(sale)
            sale.status = Sale.STATUS_ORDERED

            app = self.create_app(TillApp, u'till')
            app.status_filter.select(Sale.STATUS_ORDERED)

            results = app.results
            results.select(results[0])

            with mock.patch.object(self.store, 'commit'):
                with mock.patch.object(self.store, 'close'):
                    self.activate(app.Return)
                    return_sale.assert_called_once_with(app.get_toplevel(),
                                                        results[0].sale, self.store)
