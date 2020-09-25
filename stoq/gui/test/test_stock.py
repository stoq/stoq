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

from stoqlib.database.runtime import StoqlibStore, get_current_branch
from stoqlib.domain.transfer import TransferOrder
from stoq.lib.gui.dialogs.initialstockdialog import InitialStockDialog
from stoq.lib.gui.dialogs.productstockdetails import ProductStockHistoryDialog
from stoq.lib.gui.editors.producteditor import ProductStockEditor
from stoq.lib.gui.search.loansearch import LoanItemSearch, LoanSearch
from stoq.lib.gui.search.receivingsearch import PurchaseReceivingSearch
from stoq.lib.gui.search.productsearch import (ProductSearchQuantity,
                                               ProductStockSearch,
                                               ProductClosedStockSearch)
from stoq.lib.gui.search.purchasesearch import PurchasedItemsSearch
from stoq.lib.gui.search.transfersearch import TransferOrderSearch, TransferItemSearch
from stoq.lib.gui.search.stockdecreasesearch import StockDecreaseSearch
from stoq.lib.gui.search.returnedsalesearch import PendingReturnedSaleSearch, ReturnedItemSearch
from stoq.lib.gui.wizards.loanwizard import NewLoanWizard, CloseLoanWizard
from stoq.lib.gui.wizards.receivingwizard import ReceivingOrderWizard
from stoq.lib.gui.wizards.stockdecreasewizard import StockDecreaseWizard
from stoq.lib.gui.wizards.stocktransferwizard import StockTransferWizard

from stoq.gui.stock import StockApp
from stoq.gui.test.baseguitest import BaseGUITest


class TestStock(BaseGUITest):
    def _check_run_dialog(self, action, dialog, other_args):
        with contextlib.nested(
                mock.patch.object(self.store, 'commit'),
                mock.patch.object(self.store, 'close'),
                mock.patch('stoq.gui.stock.StockApp.run_dialog'),
                mock.patch('stoq.gui.stock.api.new_store')) as ctx:
            new_store = ctx[3]
            new_store.return_value = self.store

            self.activate(action)

            run_dialog = ctx[2]
            self.assertEqual(run_dialog.call_count, 1)
            args, kwargs = run_dialog.call_args
            self.assertEqual(args[0], dialog)
            self.assertEqual(args[1], self.store)

            if not other_args or len(other_args) != len(args[2:]):
                return

            for arg in args[2:]:
                for other_arg in other_args:
                    self.assertEqual(arg, other_arg)

    def test_initial(self):
        app = self.create_app(StockApp, u'stock')
        self.check_app(app, u'stock')

    def test_message_bars_with_inventory(self):
        self.create_inventory()
        app = self.create_app(StockApp, u'stock')
        self.assertIsNone(app.transfers_bar)
        self.assertIsNone(app.returned_bar)

    def test_message_bars_without_inventory(self):
        self.create_pending_returned_sale()
        branch = get_current_branch(self.store)
        transfer = self.create_transfer_order(dest_branch=branch)
        transfer.status = TransferOrder.STATUS_SENT
        app = self.create_app(StockApp, u'stock')
        self.assertIsNotNone(app.returned_bar)
        self.assertIsNotNone(app.transfers_bar)

    def test_select(self):
        app = self.create_app(StockApp, u'stock')
        results = app.results
        results.select(results[1])

    @mock.patch('stoq.gui.stock.StockApp.run_dialog')
    def test_product_stock_history(self, run_dialog):
        app = self.create_app(StockApp, u'stock')

        results = app.results
        results.select(results[0])

        self.activate(app.ProductStockHistory)
        self.assertEqual(run_dialog.call_count, 1)
        args, kwargs = run_dialog.call_args
        dialog, store, sellable = args
        self.assertEqual(dialog, ProductStockHistoryDialog)
        self.assertTrue(isinstance(store, StoqlibStore))
        self.assertEqual(sellable, results[0].sellable)

    def test_actions(self):
        app = self.create_app(StockApp, u'stock')

        results = app.results
        results.select(results[0])

        self._check_run_dialog(app.EditProduct,
                               ProductStockEditor, [results[0].product])
        self._check_run_dialog(app.NewStockDecrease,
                               StockDecreaseWizard, [])
        self._check_run_dialog(app.StockInitial,
                               InitialStockDialog, [])
        self._check_run_dialog(app.LoanNew,
                               NewLoanWizard, [])
        self._check_run_dialog(app.LoanClose,
                               CloseLoanWizard, [])
        self._check_run_dialog(app.LoanSearch,
                               LoanSearch, [])
        self._check_run_dialog(app.LoanSearchItems,
                               LoanItemSearch, [])
        self._check_run_dialog(app.SearchPurchaseReceiving,
                               PurchaseReceivingSearch, [])
        self._check_run_dialog(app.SearchTransfer,
                               TransferOrderSearch, [])
        self._check_run_dialog(app.SearchTransferItems,
                               TransferItemSearch, [])
        self._check_run_dialog(app.SearchPurchasedStockItems,
                               PurchasedItemsSearch, [])
        self._check_run_dialog(app.SearchStockItems,
                               ProductStockSearch, [])
        self._check_run_dialog(app.SearchClosedStockItems,
                               ProductClosedStockSearch, [])
        self._check_run_dialog(app.SearchProductHistory,
                               ProductSearchQuantity, [])
        self._check_run_dialog(app.SearchStockDecrease,
                               StockDecreaseSearch, [])
        self._check_run_dialog(app.NewTransfer,
                               StockTransferWizard, [])
        self._check_run_dialog(app.SearchPendingReturnedSales,
                               PendingReturnedSaleSearch, [])
        self._check_run_dialog(app.SearchReturnedItems,
                               ReturnedItemSearch, [])
        self._check_run_dialog(app.NewReceiving,
                               ReceivingOrderWizard, [])
