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
from stoqlib.domain.fiscal import FiscalBookEntry
from stoqlib.gui.search.fiscalsearch import (CfopSearch,
                                             FiscalBookEntrySearch)
from stoqlib.gui.uitestutils import GUITest


class TestFiscalBookSearch(GUITest):
    def testShow(self):
        for i in FiscalBookEntry.select(connection=self.trans):
            i.date = datetime.date.today()

        search = FiscalBookEntrySearch(self.trans)
        search.search.refresh()
        search.results.sort_by_attribute('id')
        self.check_search(search, 'search-fiscal-book-show')


class TestCfopSearch(GUITest):
    def testShow(self):
        search = CfopSearch(self.trans)
        search.search.refresh()
        self.check_search(search, 'search-cfop-show')
