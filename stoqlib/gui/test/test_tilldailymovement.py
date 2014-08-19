# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2014 Async Open Source <http://www.async.com.br>
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

from stoqlib.api import api
from stoqlib.gui.dialogs.tilldailymovement import TillDailyMovementDialog
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.reporting.till import TillDailyMovementReport


class TestTillHistory(GUITest):
    def test_show(self):
        dialog = TillDailyMovementDialog(self.store)
        method = self.get_payment_method(u'credit')
        payment = self.create_payment(value=100, method=method,
                                      date=datetime.datetime.now())
        payment.identifier = 9941
        payment.set_pending()
        payment.pay()
        self.click(dialog.search_button)
        self.check_dialog(dialog, 'till-dailymovement-dialog-show')

    def test_show_synchronized(self):
        with self.sysparam(SYNCHRONIZED_MODE=True):
            dialog = TillDailyMovementDialog(self.store)
            self.check_dialog(dialog, 'till-dailymovement-dialog-show-sync')

    @mock.patch('stoqlib.gui.dialogs.tilldailymovement.print_report')
    def test_print(self, print_report):
        dialog = TillDailyMovementDialog(self.store)

        # Before doing any search, the print button should not be sensitive
        self.assertFalse(dialog.print_button.get_sensitive())

        # After clicking the button, the print dialog should be sensitive
        self.click(dialog.search_button)
        self.assertTrue(dialog.print_button.get_sensitive())

        self.click(dialog.print_button)

        date = dialog.get_daterange()
        print_report.assert_called_once_with(TillDailyMovementReport,
                                             self.store,
                                             api.get_current_branch(self.store),
                                             date, dialog)
