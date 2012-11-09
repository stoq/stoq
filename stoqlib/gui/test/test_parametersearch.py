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

from stoqlib.gui.search.parametersearch import ParameterSearch
from stoqlib.gui.uitestutils import GUITest


class TestParameterSearch(GUITest):
    def testSearch(self):
        search = ParameterSearch(self.trans)

        self.check_search(search, 'parameter-no-filter')

        search.entry.activate()
        self.check_search(search, 'parameter-no-filter')

        search.entry.update('account')
        search.entry.activate()
        self.check_search(search, 'parameter-string-filter')

        self.click(search.show_all_button)
        self.check_search(search, 'parameter-no-filter')

    @mock.patch('stoqlib.gui.search.parametersearch.run_dialog')
    def testEdit(self, run_dialog):
        search = ParameterSearch(self.trans)

        self.assertNotSensitive(search, ['edit_button'])

        search.results.select(search.results[0])
        self.click(search.edit_button)
        self.assertEquals(run_dialog.call_count, 1)

        search.on_results__double_click(list(search.results),
                                        search.results[0])
        self.assertEquals(run_dialog.call_count, 2)
