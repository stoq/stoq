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


import mock

from stoqlib.domain.workorder import WorkOrder
from stoqlib.gui.editors.workordereditor import WorkOrderEditor
from stoqlib.gui.search.workordersearch import WorkOrderFinishedSearch
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.lib.dateutils import localdate


class TestWorkOrderFinishedSearch(GUITest):
    def _show_search(self):
        search = WorkOrderFinishedSearch(self.store)
        search.search.refresh()
        return search

    @mock.patch('stoqlib.domain.workorder.localnow')
    def _create_domain(self, localnow):
        self.clean_domain([WorkOrder])
        localnow.return_value = localdate(2014, 1, 1)
        work_order = self.create_workorder()
        work_order.open_date = localdate(2014, 1, 1)
        work_order.identifier = 123
        work_order.approve()
        work_order.work()
        work_order.add_sellable(self.create_sellable(), quantity=1)
        work_order.finish()

    def test_search(self):
        self._create_domain()
        search = self._show_search()
        self.check_search(search, 'work-order-finished')

    def test_confirm(self):
        self._create_domain()
        search = self._show_search()
        search.search.refresh()

        search.results.select(search.results[0])
        work_order = self.store.get(WorkOrder, search.results[0].id)

        # Try confirm without reserved items.
        for item in work_order.get_items():
            item.quantity_decreased = 0
        with mock.patch('stoqlib.gui.search.workordersearch.warning') as warning:
            search.confirm()
            warning.assert_called_once_with("You need to reserve all items to "
                                            "close that work order.")
            self.assertFalse(search.retval)
        # With all items reserved.
        for item in work_order.get_items():
            item.reserve(item.quantity)
        search.confirm()
        self.assertTrue(search.retval)

    def test_details(self):
        self._create_domain()
        search = self._show_search()
        search.search.refresh()
        self.assertSensitive(search._details_slave, ['details_button'])

        # Try show details without a selected work order.
        self.assertFalse(self.click(search._details_slave.details_button))
        # With work order selected.
        search.results.select(search.results[0])
        work_order = self.store.get(WorkOrder, search.results[0].id)
        with mock.patch('stoqlib.gui.search.workordersearch.run_dialog') as run_dialog:
            self.click(search._details_slave.details_button)
            run_dialog.assert_called_once_with(WorkOrderEditor, search, self.store,
                                               model=work_order, visual_mode=True)
