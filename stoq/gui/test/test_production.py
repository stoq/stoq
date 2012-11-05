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

from stoqlib.gui.dialogs.productiondetails import ProductionDetailsDialog
from stoqlib.gui.dialogs.productionquotedialog import ProductionQuoteDialog
from stoqlib.gui.dialogs.startproduction import StartProductionDialog
from stoqlib.gui.search.productionsearch import (ProductionProductSearch,
                                                 ProductionItemsSearch,
                                                 ProductionHistorySearch)
from stoqlib.gui.search.servicesearch import ServiceSearch
from stoqlib.gui.wizards.productionwizard import ProductionWizard

from stoq.gui.production import ProductionApp
from stoq.gui.test.baseguitest import BaseGUITest


class TestProduction(BaseGUITest):
    @mock.patch('stoq.gui.production.ProductionApp.run_dialog')
    @mock.patch('stoq.gui.production.api.new_transaction')
    def _check_run_dialog(self, action, dialog, other_args, other_kwargs,
                          new_transaction, run_dialog):
        new_transaction.return_value = self.trans

        with mock.patch.object(self.trans, 'commit'):
            with mock.patch.object(self.trans, 'close'):
                self.activate(action)
                expected_args = [dialog, self.trans]
                if other_args:
                    expected_args.extend(other_args)
                run_dialog.assert_called_once_with(*expected_args, **other_kwargs)

    def testInitial(self):
        app = self.create_app(ProductionApp, 'production')
        self.check_app(app, 'production')

    def testSelect(self):
        self.create_production_order()
        app = self.create_app(ProductionApp, 'production')
        results = app.main_window.results
        results.select(results[0])

    def test_run_dialogs(self):
        self.create_production_order()
        app = self.create_app(ProductionApp, 'production')
        results = app.main_window.results
        results.select(results[0])

        self._check_run_dialog(app.main_window.EditProduction,
                               ProductionWizard, [results[0]], {})
        results.select(results[0])
        self._check_run_dialog(app.main_window.StartProduction,
                               StartProductionDialog, [results[0]], {})
        results.select(results[0])
        self._check_run_dialog(app.main_window.ProductionDetails,
                               ProductionDetailsDialog, [results[0]], {})
        self._check_run_dialog(app.main_window.ProductionPurchaseQuote,
                               ProductionQuoteDialog, [], {})
        self._check_run_dialog(app.main_window.SearchProduct,
                               ProductionProductSearch, [], {})
        self._check_run_dialog(app.main_window.SearchService,
                               ServiceSearch, [], {'hide_price_column': True})
        self._check_run_dialog(app.main_window.SearchProductionHistory,
                               ProductionHistorySearch, [], {})
        self._check_run_dialog(app.main_window.SearchProductionItem,
                               ProductionItemsSearch, [], {})
