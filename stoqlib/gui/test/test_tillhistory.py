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

from decimal import Decimal

from stoqlib.api import api
from stoqlib.domain.till import TillEntry
from stoqlib.lib.dateutils import localdate
from stoqlib.gui.dialogs.tillhistory import TillHistoryDialog
from stoqlib.gui.search.searchfilters import DateSearchFilter
from stoqlib.gui.test.uitestutils import GUITest


class TestTillHistory(GUITest):
    def test_show(self):
        dialog = TillHistoryDialog(self.store)
        self.check_dialog(dialog, 'till-history-dialog-show')

    def test_date_search(self):
        entry = TillEntry(identifier=1234,
                          description=u'desc',
                          date=localdate(2011, 01, 01).date(),
                          value=Decimal(123.0),
                          till=self.create_till(),
                          payment=None,
                          branch=api.get_current_branch(self.store),
                          store=self.store)

        dialog = TillHistoryDialog(self.store)
        dialog.date_filter.select(DateSearchFilter.Type.USER_DAY)
        dialog.date_filter.start_date.update(entry.date)
        self.click(dialog.search.search_button)
        self.check_dialog(dialog, 'till-history-dialog-custom-day')
