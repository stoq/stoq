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

from stoqlib.domain.fiscal import FiscalBookEntry
from stoqlib.gui.search.fiscalsearch import (CfopSearch,
                                             FiscalBookEntrySearch)
from stoqlib.gui.uitestutils import GUITest
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class TestFiscalBookSearch(GUITest):
    def _show_search(self):
        search = FiscalBookEntrySearch(self.trans)
        search.search.refresh()
        search.results.select(search.results[0])
        return search

    def testShow(self):
        for i in FiscalBookEntry.select(connection=self.trans):
            i.date = datetime.date.today()

        search = self._show_search()
        self.check_search(search, 'fiscal-book-icms-filter')

        search.entry_type.set_state(1)
        search.search.refresh()
        self.check_search(search, 'fiscal-book-ipi-filter')

        search.entry_type.set_state(2)
        search.search.refresh()
        self.check_search(search, 'fiscal-book-iss-filter')

        search.entry_type.set_state(0)
        search.branch_filter.set_state(2)
        search.search.refresh()
        self.check_search(search, 'fiscal-book-branch-filter')

    @mock.patch('stoqlib.gui.search.fiscalsearch.SpreadSheetExporter.export')
    @mock.patch('stoqlib.gui.search.fiscalsearch.run_dialog')
    def testButtons(self, run_dialog, export):
        search = self._show_search()

        self.assertSensitive(search, ['edit_button'])
        self.click(search.edit_button)
        self.assertEquals(run_dialog.call_count, 1)

        self.assertSensitive(search, ['csv_button'])
        self.click(search.csv_button)
        export.assert_called_once_with(object_list=search.results,
                                       name=_('Fiscal book'),
                                       filename_prefix=_('fiscal-book'))


class TestCfopSearch(GUITest):
    def testShow(self):
        search = CfopSearch(self.trans)
        search.search.refresh()
        self.check_search(search, 'cfop-show')
