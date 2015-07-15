# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2015 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import mock

from stoqlib.gui.dialogs.returnedsaledialog import ReturnedSaleDialog
from stoqlib.gui.search.returnedsalesearch import (ReturnedSaleSearch,
                                                   PendingReturnedSaleSearch,
                                                   ReturnedItemSearch)
from stoqlib.gui.test.uitestutils import GUITest


class TestReturnedSaleSearch(GUITest):
    def test_create(self):
        search = ReturnedSaleSearch(self.store)
        self.check_search(search, 'returned-sale-search')
        self.assertNotSensitive(search._details_slave, ['details_button'])
        search.search.refresh()

    @mock.patch('stoqlib.gui.search.returnedsalesearch.run_dialog')
    def test_show_details(self, run_dialog):
        sale = self.create_sale()
        product = self.create_product(stock=2)
        client = self.create_client()
        sale = self.create_sale(client=client)
        sale.add_sellable(sellable=product.sellable)

        self.create_returned_sale(sale)
        search = ReturnedSaleSearch(self.store)
        search.search.refresh()
        search.results.double_click(0)
        self.assertEquals(run_dialog.call_count, 1)
        run_dialog.assert_called_once_with(ReturnedSaleDialog, search, self.store,
                                           search.results[0])

        run_dialog.reset_mock()
        search.results.select(search.results[0])
        self.assertSensitive(search._details_slave, ['details_button'])
        self.click(search._details_slave.details_button)
        self.assertEquals(run_dialog.call_count, 1)
        run_dialog.assert_called_once_with(ReturnedSaleDialog, search, self.store,
                                           search.results[0])


class TestPendingReturnedSaleSearch(GUITest):
    def test_create(self):
        search = PendingReturnedSaleSearch(self.store)
        search.search.refresh()
        self.check_search(search, 'pending-returned-sale-search')

    @mock.patch('stoqlib.gui.search.returnedsalesearch.run_dialog')
    def test_show_details(self, run_dialog):
        sale = self.create_sale()
        product = self.create_product(stock=2)
        client = self.create_client()
        sale = self.create_sale(client=client)
        sale.add_sellable(sellable=product.sellable)
        self.create_returned_sale(sale)

        search = PendingReturnedSaleSearch(self.store)
        search.search.refresh()
        # Testing double click
        search.results.double_click(0)
        self.assertEquals(run_dialog.call_count, 1)
        run_dialog.assert_called_once_with(ReturnedSaleDialog, search,
                                           self.store, search.results[0])

        # Testing pressing the button
        run_dialog.reset_mock()
        search.results.select(search.results[0])
        self.assertSensitive(search._details_slave, ['details_button'])
        self.click(search._details_slave.details_button)
        run_dialog.assert_called_once_with(ReturnedSaleDialog, search,
                                           self.store, search.results[0])


class TestReturnedItemSearch(GUITest):
    def test_create(self):
        search = ReturnedItemSearch(self.store)
        search.search.refresh()
        self.check_search(search, 'returned-item-search')

    @mock.patch('stoqlib.gui.search.returnedsalesearch.run_dialog')
    def test_show_details(self, run_dialog):
        sale = self.create_sale()
        product = self.create_product(stock=2)
        client = self.create_client()
        sale = self.create_sale(client=client)
        sale.add_sellable(sellable=product.sellable)

        self.create_returned_sale(sale)
        search = ReturnedItemSearch(self.store)
        search.search.refresh()
        search.results.double_click(0)
        self.assertEquals(run_dialog.call_count, 1)
        run_dialog.assert_called_once_with(ReturnedSaleDialog, search, self.store,
                                           search.results[0])

        # Testing click on details button
        run_dialog.reset_mock()
        search.results.select(search.results[0])
        self.assertSensitive(search._details_slave, ['details_button'])
        self.click(search._details_slave.details_button)
        self.assertEquals(run_dialog.call_count, 1)
        run_dialog.assert_called_once_with(ReturnedSaleDialog, search, self.store,
                                           search.results[0])
