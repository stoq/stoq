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

    def testShow(self):
        search = ParameterSearch(self.trans)
        self.check_editor(search, 'search-parameter-show')

    @mock.patch('stoqlib.gui.search.parametersearch.run_dialog')
    def testEdit(self, run_dialog):
        search = ParameterSearch(self.trans)
        self.assertNotSensitive(search, ['edit_button'])
        search.results.select(search.results[0])
        self.click(search.edit_button)
        run_dialog.assert_called_once()

    def testFilter(self):
        search = ParameterSearch(self.trans)
        self.assertEquals(len(search.results), 55)

        search.entry.update('Paulista')
        search.entry.activate()
        self.assertEquals(len(search.results), 1)

        self.click(search.show_all_button)
        self.assertEquals(len(search.results), 55)
