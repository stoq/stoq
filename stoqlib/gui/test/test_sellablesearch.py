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

from stoqlib.gui.search.sellablesearch import SellableSearch
from stoqlib.gui.uitestutils import GUITest


class TestCallsSearch(GUITest):
    def _show_search(self):
        search = SellableSearch(self.trans)
        search.search.refresh()
        search.results.select(search.results[0])
        return search

    def testSearch(self):
        search = self._show_search()

        self.check_search(search, 'sellable-no-filter')

        search.set_searchbar_search_string('cal')
        search.search.refresh()
        self.check_search(search, 'sellable-string-filter')

    @mock.patch('stoqlib.gui.search.sellablesearch.SellableSearch.set_message')
    def testCreate(self, set_message):
        sellable = self.create_sellable()
        self.create_storable(product=sellable.product)
        sale_item = TemporarySaleItem(sellable=sellable, quantity=1)

        search = SellableSearch(self.trans, sale_items=[sale_item], quantity=1)

        self.assertRaises(TypeError, SellableSearch, self.trans,
                          sale_items=[sale_item],
                          selection_mode=gtk.SELECTION_MULTIPLE)
        self.assertRaises(TypeError, SellableSearch, self.trans,
                          sale_items=[sale_item], quantity=None)

        search = SellableSearch(self.trans, info_message='test')
        set_message.assert_called_once_with('test')

        search = SellableSearch(self.trans, search_str='cal')
        self.check_search(search, 'sellable-string-filter')
