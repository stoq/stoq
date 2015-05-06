# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2015 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##

import mock

from stoqlib.gui.search.gridsearch import (GridGroupSearch,
                                           GridAttributeSearch)
from stoqlib.gui.test.uitestutils import GUITest


class TestAttributeGroupSearch(GUITest):
    def test_create(self):
        search = GridGroupSearch(self.store)
        search.search.refresh()
        self.check_search(search, 'grid-group')


class TestAttributeSearch(GUITest):
    def test_create(self):
        search = GridAttributeSearch(self.store)
        search.search.refresh()
        self.check_search(search, 'grid-attribute')

    @mock.patch('stoqlib.gui.search.gridsearch.warning')
    def test_create_without_group(self, warning):
        search = GridAttributeSearch(self.store)

        self.click(search._toolbar.new_button)
        warning.asser_called_once_with("You need to register an atribute group"
                                       " first.")

    @mock.patch('stoqlib.gui.search.searcheditor.run_dialog')
    def test_create_with_group(self, run_dialog):
        search = GridAttributeSearch(self.store)
        self.create_attribute_group()

        self.click(search._toolbar.new_button)
        self.assertEquals(run_dialog.call_count, 1)
