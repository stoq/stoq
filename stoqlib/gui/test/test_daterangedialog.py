# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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

__tests__ = 'stoqlib/gui/dialogs/daterangedialog.py'

import datetime

from stoqlib.gui.dialogs.daterangedialog import DateRangeDialog, date_range
from stoqlib.gui.test.uitestutils import GUITest


class TestDateRangeDialog(GUITest):
    def test_create(self):
        dialog = DateRangeDialog()
        self.check_dialog(dialog, 'dialog-date-range')

    def test_confirm(self):
        dialog = DateRangeDialog()
        start = end = datetime.date(2013, 1, 1)
        dialog.date_filter.set_state(start=start, end=end)
        dialog.confirm()
        self.assertEqual(dialog.retval, date_range(start=start, end=end))

        dialog = DateRangeDialog()
        start = datetime.date(2013, 1, 1)
        end = datetime.date(2013, 2, 1)
        dialog.date_filter.set_state(start=start, end=end)
        dialog.confirm()
        self.assertEqual(dialog.retval, date_range(start=start, end=end))
