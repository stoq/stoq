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

from stoqlib.api import api
from stoqlib.domain.fiscal import FiscalBookEntry
from stoqlib.gui.search.fiscalsearch import (CfopSearch,
                                             FiscalBookEntrySearch,
                                             FiscalBookEntryType)
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.lib.dateutils import localtoday
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class TestFiscalBookSearch(GUITest):
    def _show_search(self):
        search = FiscalBookEntrySearch(self.store)
        search.search.refresh()
        search.results.select(search.results[0])
        return search

    def test_show(self):
        entries = []
        for entry in self.store.find(FiscalBookEntry).order_by(FiscalBookEntry.date):
            entry.date = localtoday().date()
            entries.append(entry)
        search = self._show_search()
        self.check_search(search, 'fiscal-book-icms-filter')

        search.entry_type.set_state(FiscalBookEntryType.IPI)
        search.search.refresh()
        self.check_search(search, 'fiscal-book-ipi-filter')

        search.entry_type.set_state(FiscalBookEntryType.ISS)
        search.search.refresh()
        self.check_search(search, 'fiscal-book-iss-filter')

        search.entry_type.set_state(FiscalBookEntryType.ICMS)
        search.branch_filter.set_state(api.get_current_branch(self.store).id)
        search.search.refresh()
        self.check_search(search, 'fiscal-book-branch-filter')

    @mock.patch('stoqlib.gui.search.fiscalsearch.run_dialog')
    def test_buttons(self, run_dialog):
        search = self._show_search()

        self.assertSensitive(search, ['edit_button'])
        self.click(search.edit_button)
        self.assertEquals(run_dialog.call_count, 1)


class TestCfopSearch(GUITest):
    def test_show(self):
        search = CfopSearch(self.store)
        search.search.refresh()
        self.check_search(search, 'cfop-show')
