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

from stoqlib.gui.search.creditcheckhistorysearch import CreditCheckHistorySearch
from stoqlib.gui.test.uitestutils import GUITest


class TestCreditCheckHistorySearch(GUITest):
    def test_show(self):
        user = self.create_user()
        credit_check1 = self.create_credit_check_history(user)
        credit_check1.identifier = u'1'

        user2 = self.create_user(username=u'username2')
        client = self.create_client()
        client.person.name = u'Client2'
        credit_check2 = self.create_credit_check_history(user2, client)
        credit_check2.identifier = u'2'

        credit_check3 = self.create_credit_check_history(user2, client)
        credit_check3.identifier = u'3'

        # displaying all
        dialog = CreditCheckHistorySearch(self.store)
        self.click(dialog.search.search_button)

        self.check_dialog(dialog, 'credit-check-history-search-show-all')

        # displaying a single client
        dialog = CreditCheckHistorySearch(self.store, client)
        self.click(dialog.search.search_button)

        self.check_dialog(dialog, 'credit-check-history-search-show-single')

    @mock.patch('stoqlib.gui.search.creditcheckhistorysearch.run_dialog')
    def test_edit(self, run_dialog):
        credit_check = self.create_credit_check_history()

        dialog = CreditCheckHistorySearch(self.store, reuse_store=True)
        self.click(dialog.search.search_button)

        dialog.results.double_click(0)

        run_dialog.assert_called_once_with(dialog.editor_class, dialog,
                                           self.store, credit_check, None,
                                           visual_mode=True)

    @mock.patch('stoqlib.gui.search.creditcheckhistorysearch.run_dialog')
    def test_new(self, run_dialog):
        dialog = CreditCheckHistorySearch(self.store)
        self.click(dialog._toolbar.new_button)

        self.assertEquals(run_dialog.call_count, 1)
