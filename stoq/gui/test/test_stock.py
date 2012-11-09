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

import mock

from stoqlib.database.runtime import StoqlibTransaction
from stoqlib.domain.sellable import Sellable
from stoqlib.gui.dialogs.initialstockdialog import InitialStockDialog
from stoqlib.gui.dialogs.productstockdetails import ProductStockHistoryDialog
from stoqlib.gui.editors.producteditor import ProductStockEditor
from stoqlib.gui.search.loansearch import LoanItemSearch, LoanSearch
from stoqlib.gui.search.receivingsearch import PurchaseReceivingSearch
from stoqlib.gui.search.productsearch import (ProductSearchQuantity,
                                              ProductStockSearch,
                                              ProductClosedStockSearch)
from stoqlib.gui.search.purchasesearch import PurchasedItemsSearch
from stoqlib.gui.search.transfersearch import TransferOrderSearch
from stoqlib.gui.search.stockdecreasesearch import StockDecreaseSearch
from stoqlib.gui.wizards.loanwizard import NewLoanWizard, CloseLoanWizard
from stoqlib.gui.wizards.receivingwizard import ReceivingOrderWizard
from stoqlib.gui.wizards.stockdecreasewizard import StockDecreaseWizard
from stoqlib.gui.wizards.stocktransferwizard import StockTransferWizard

from stoq.gui.stock import StockApp
from stoq.gui.test.baseguitest import BaseGUITest


class TestStock(BaseGUITest):
    @mock.patch('stoq.gui.stock.StockApp.run_dialog')
    @mock.patch('stoq.gui.stock.api.new_transaction')
    def _check_run_dialog(self, action, dialog, other_args, new_transaction,
                          run_dialog):
        new_transaction.return_value = self.trans

        with mock.patch.object(self.trans, 'commit'):
            with mock.patch.object(self.trans, 'close'):
                self.activate(action)
                self.assertEquals(run_dialog.call_count, 1)
                args, kwargs = run_dialog.call_args
                self.assertEquals(args[0], dialog)
                self.assertEquals(args[1], self.trans)

                if not other_args or len(other_args) != len(args[2:]):
                    return

                for arg in args[2:]:
                    for other_arg in other_args:
                        self.assertEquals(arg, other_arg)

    def testInitial(self):
        app = self.create_app(StockApp, 'stock')
        self.check_app(app, 'stock')

    def testSelect(self):
        app = self.create_app(StockApp, 'stock')
        results = app.main_window.results
        results.select(results[1])

    @mock.patch('stoq.gui.stock.StockApp.run_dialog')
    def test_product_stock_history(self, run_dialog):
        app = self.create_app(StockApp, 'stock')

        results = app.main_window.results
        results.select(results[0])

        self.activate(app.main_window.ProductStockHistory)
        self.assertEquals(run_dialog.call_count, 1)
        args, kwargs = run_dialog.call_args
        dialog, trans, sellable = args
        self.assertEquals(dialog, ProductStockHistoryDialog)
        self.assertTrue(isinstance(trans, StoqlibTransaction))
        self.assertEquals(sellable, Sellable.get(results[0].id,
                                                 connection=self.trans))

    def test_actions(self):
        app = self.create_app(StockApp, 'stock')

        results = app.main_window.results
        results.select(results[0])

        self._check_run_dialog(app.main_window.EditProduct,
                               ProductStockEditor, [results[0].product])
        self._check_run_dialog(app.main_window.NewStockDecrease,
                               StockDecreaseWizard, [])
        branch = app.main_window.branch_filter.get_state().value
        self._check_run_dialog(app.main_window.StockInitial,
                               InitialStockDialog, [branch])
        self._check_run_dialog(app.main_window.LoanNew,
                               NewLoanWizard, [])
        self._check_run_dialog(app.main_window.LoanClose,
                               CloseLoanWizard, [])
        self._check_run_dialog(app.main_window.LoanSearch,
                               LoanSearch, [])
        self._check_run_dialog(app.main_window.LoanSearchItems,
                               LoanItemSearch, [])
        self._check_run_dialog(app.main_window.SearchPurchaseReceiving,
                               PurchaseReceivingSearch, [])
        self._check_run_dialog(app.main_window.SearchTransfer,
                               TransferOrderSearch, [])
        self._check_run_dialog(app.main_window.SearchPurchasedStockItems,
                               PurchasedItemsSearch, [])
        self._check_run_dialog(app.main_window.SearchStockItems,
                               ProductStockSearch, [])
        self._check_run_dialog(app.main_window.SearchClosedStockItems,
                               ProductClosedStockSearch, [])
        self._check_run_dialog(app.main_window.SearchProductHistory,
                               ProductSearchQuantity, [])
        self._check_run_dialog(app.main_window.SearchStockDecrease,
                               StockDecreaseSearch, [])
        self._check_run_dialog(app.main_window.NewTransfer,
                               StockTransferWizard, [])
        self._check_run_dialog(app.main_window.NewReceiving,
                               ReceivingOrderWizard, [])
