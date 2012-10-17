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

from stoqlib.gui.search.stockdecreasesearch import StockDecreaseSearch
from stoqlib.gui.uitestutils import GUITest


class TestStockDecreaseSearch(GUITest):
    def testSearch(self):
        defective = self.create_stock_decrease(reason='Defective product')
        stolen = self.create_stock_decrease(reason='Item was stolen')

        defective.identifier = 54287
        defective.confirm_date = datetime.datetime(2012, 1, 1)

        stolen.identifier = 74268
        stolen.confirm_date = datetime.datetime(2012, 1, 1)

        search = StockDecreaseSearch(self.trans)

        search.search.refresh()
        self.check_search(search, 'stock-decrease-no-filter')

        search.search.search._primary_filter.entry.set_text('def')
        search.search.refresh()
        self.check_search(search, 'stock-decrease-reason-filter')
