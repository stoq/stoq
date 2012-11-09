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

from stoqlib.gui.dialogs.stockdecreasedialog import StockDecreaseDetailsDialog
from stoqlib.gui.search.stockdecreasesearch import StockDecreaseSearch
from stoqlib.gui.uitestutils import GUITest
from stoqlib.reporting.stockdecreasereceipt import StockDecreaseReceipt


class TestStockDecreaseSearch(GUITest):
    def _show_search(self):
        search = StockDecreaseSearch(self.trans)
        search.search.refresh()
        search.results.select(search.results[0])
        return search

    def _create_domain(self):
        dec = self.create_stock_decrease(reason='Defective product')
        dec.identifier = 54287
        dec.confirm_date = datetime.datetime(2012, 1, 1)

        dec = self.create_stock_decrease(reason='Item was stolen')
        dec.identifier = 74268
        dec.confirm_date = datetime.datetime(2012, 2, 2)

    def testSearch(self):
        self._create_domain()
        search = self._show_search()

        self.check_search(search, 'stock-decrease-no-filter')

        search.set_searchbar_search_string('def')
        search.search.refresh()
        self.check_search(search, 'stock-decrease-string-filter')

    @mock.patch('stoqlib.gui.search.stockdecreasesearch.run_dialog')
    @mock.patch('stoqlib.gui.search.stockdecreasesearch.print_report')
    def testButtons(self, print_report, run_dialog):
        self._create_domain()
        search = self._show_search()

        search.search.refresh()
        self.assertNotSensitive(search._details_slave, ['print_button'])
        search.results.select(search.results[0])
        self.assertSensitive(search._details_slave, ['print_button'])
        self.click(search._details_slave.print_button)
        print_report.assert_called_once_with(StockDecreaseReceipt,
                                             search.results[0])

        search.search.refresh()
        self.assertNotSensitive(search._details_slave, ['details_button'])
        search.results.select(search.results[0])
        self.assertSensitive(search._details_slave, ['details_button'])
        self.click(search._details_slave.details_button)
        run_dialog.assert_called_once_with(StockDecreaseDetailsDialog,
                                           search, self.trans,
                                           search.results[0])

        run_dialog.reset_mock()
        search.results.emit('row_activated', search.results[0])
        run_dialog.assert_called_once_with(StockDecreaseDetailsDialog,
                                           search, self.trans,
                                           search.results[0])
