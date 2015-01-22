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

import gtk

import mock

from stoq.gui.pos import TemporarySaleItem

from stoqlib.domain.sellable import Sellable
from stoqlib.domain.views import ProductFullStockView
from stoqlib.gui.editors.producteditor import ProductEditor
from stoqlib.gui.search.sellablesearch import (SellableSearch,
                                               PurchaseSellableSearch,
                                               SaleSellableSearch)
from stoqlib.gui.wizards.productwizard import ProductCreateWizard
from stoqlib.gui.test.uitestutils import GUITest


class TestSellableSearch(GUITest):
    def _show_search(self):
        search = SellableSearch(self.store)
        search.search.refresh()
        #search.results.select(search.results[0])
        return search

    def test_search(self):
        search = self._show_search()

        self.check_search(search, 'sellable-no-filter')

        search.set_searchbar_search_string('cal')
        search.search.refresh()
        self.check_search(search, 'sellable-string-filter')


class TestSaleSellableSearch(GUITest):
    @mock.patch('stoqlib.gui.search.sellablesearch.SellableSearch.set_message')
    def test_create(self, set_message):
        sellable = self.create_sellable()
        self.create_storable(product=sellable.product)
        sale_item = TemporarySaleItem(sellable=sellable, quantity=1)

        search = SaleSellableSearch(self.store,
                                    sale_items=[sale_item], quantity=1)

        self.assertRaises(TypeError, SaleSellableSearch, self.store,
                          sale_items=[sale_item],
                          selection_mode=gtk.SELECTION_MULTIPLE)
        self.assertRaises(TypeError, SaleSellableSearch, self.store,
                          sale_items=[sale_item], quantity=None)

        search = SaleSellableSearch(self.store)
        search.search.refresh()
        self.check_search(search, 'sale-sellable-no-filter')

        search = SaleSellableSearch(self.store, info_message='test')
        set_message.assert_called_once_with('test')

        search = SaleSellableSearch(self.store, search_str='cal')
        self.check_search(search, 'sale-sellable-string-filter')


class TestPurchaseSellableSearch(GUITest):
    @mock.patch('stoqlib.gui.search.searcheditor.api.new_store')
    @mock.patch('stoqlib.gui.search.searcheditor.run_dialog')
    def test_run_editor(self, run_dialog, new_store):
        run_dialog.return_value = None
        new_store.return_value = self.store
        query = Sellable.get_unblocked_sellables_query(self.store)
        dialog = PurchaseSellableSearch(store=self.store,
                                        search_spec=ProductFullStockView,
                                        search_query=query)
        dialog.search.refresh()
        dialog.results.select(dialog.results[0])
        product = dialog.results[0].product

        with mock.patch.object(self.store, 'commit'):
            with mock.patch.object(self.store, 'close'):
                self.click(dialog._toolbar.edit_button)
                run_dialog.assert_called_once_with(ProductEditor, dialog,
                                                   self.store, product,
                                                   visual_mode=False)

    @mock.patch('stoqlib.gui.search.searcheditor.api.new_store')
    @mock.patch('stoqlib.gui.wizards.productwizard.run_dialog')
    def test_run_wizard(self, run_dialog, new_store):
        run_dialog.return_value = None
        new_store.return_value = self.store
        query = Sellable.get_unblocked_sellables_query(self.store)
        dialog = PurchaseSellableSearch(store=self.store,
                                        search_spec=ProductFullStockView,
                                        search_query=query)

        with mock.patch.object(self.store, 'commit'):
            with mock.patch.object(self.store, 'close'):
                self.click(dialog._toolbar.new_button)
                run_dialog.assert_called_once_with(ProductCreateWizard, dialog,
                                                   self.store)
