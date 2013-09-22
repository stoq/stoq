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
    def _check_run_dialog(self, action, dialog, other_args, other_kwargs):
        with contextlib.nested(
                mock.patch('stoq.gui.production.ProductionApp.run_dialog'),
                mock.patch('stoq.gui.production.api.new_store'),
                mock.patch.object(self.store, 'commit'),
                mock.patch.object(self.store, 'close')) as ctx:
            new_store = ctx[1]
            new_store.return_value = self.store

            self.activate(action)
            expected_args = [dialog, self.store]
            if other_args:
                expected_args.extend(other_args)

            run_dialog = ctx[0]
            run_dialog.assert_called_once_with(*expected_args, **other_kwargs)

    def test_initial(self):
        app = self.create_app(ProductionApp, u'production')
        self.check_app(app, u'production')

    def test_select(self):
        self.create_production_order()
        app = self.create_app(ProductionApp, u'production')
        results = app.results
        results.select(results[0])

    def test_run_dialogs(self):
        self.create_production_order()
        app = self.create_app(ProductionApp, u'production')
        results = app.results
        results.select(results[0])

        self._check_run_dialog(app.EditProduction,
                               ProductionWizard, [results[0]], {})
        results.select(results[0])
        self._check_run_dialog(app.StartProduction,
                               StartProductionDialog, [results[0]], {})
        results.select(results[0])
        self._check_run_dialog(app.ProductionDetails,
                               ProductionDetailsDialog, [results[0]], {})
        self._check_run_dialog(app.ProductionPurchaseQuote,
                               ProductionQuoteDialog, [], {})
        self._check_run_dialog(app.SearchProduct,
                               ProductionProductSearch, [], {})
        self._check_run_dialog(app.SearchService,
                               ServiceSearch, [], {u'hide_price_column': True})
        self._check_run_dialog(app.SearchProductionHistory,
                               ProductionHistorySearch, [], {})
        self._check_run_dialog(app.SearchProductionItem,
                               ProductionItemsSearch, [], {})
