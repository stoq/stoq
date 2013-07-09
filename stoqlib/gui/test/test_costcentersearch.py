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

import mock

from stoqlib.gui.dialogs.costcenterdialog import CostCenterDialog
from stoqlib.gui.search.costcentersearch import CostCenterSearch
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class TestCostCenterSearch(GUITest):
    def test_show(self):
        self.create_cost_center()
        search = CostCenterSearch(self.store)
        search.search.refresh()
        self.check_search(search, 'cost-center-show')

    @mock.patch('stoqlib.gui.search.costcentersearch.run_dialog')
    def test_details(self, run_dialog):
        cost_center = self.create_cost_center()
        search = CostCenterSearch(self.store)
        search.search.refresh()
        search.results.select(cost_center)
        self.click(search._details_slave.details_button)
        run_dialog.assert_called_once_with(CostCenterDialog, search,
                                           self.store, cost_center)
