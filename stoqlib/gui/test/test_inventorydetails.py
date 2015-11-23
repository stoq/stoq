# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013-2014 Async Open Source <http://www.async.com.br>
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

__tests__ = 'stoqlib/gui/dialogs/inventorydetails.py'

import unittest

import mock

from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.inventory import InventoryItemsView
from stoqlib.gui.dialogs.inventorydetails import InventoryDetailsDialog
from stoqlib.gui.editors.noteeditor import NoteEditor
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.lib.dateutils import localdate
from stoqlib.reporting.inventory import InventoryReport


class TestInventoryDetails(GUITest):

    def _create_inventory(self):
        today = localdate(2010, 12, 1)

        # new sale
        inventory = self.create_inventory(branch=get_current_branch(self.store))
        inventory.identifier = 123
        inventory.open_date = today

        self.create_inventory_item(inventory)
        return inventory

    def test_show(self):
        inventory = self._create_inventory()
        dialog = InventoryDetailsDialog(self.store, inventory)
        self.check_editor(dialog, 'dialog-inventory-details')
        self.assertNotSensitive(dialog, ['info_button'])

    @mock.patch('stoqlib.gui.dialogs.inventorydetails.print_report')
    def test_on_print_button__clicked_with_adjusted_item(self, print_report):
        inventory = self._create_inventory()
        item = self.create_inventory_item(inventory)
        item.recorded_quantity = 10
        item.actual_quantity = 5
        dialog = InventoryDetailsDialog(self.store, inventory)

        self.assertSensitive(dialog, ['print_button'])
        items = list(dialog._get_report_items())
        self.click(dialog.print_button)
        print_report.assert_called_once_with(InventoryReport,
                                             dialog.items_list, items)

    @mock.patch('stoqlib.gui.dialogs.inventorydetails.run_dialog')
    def test_on_items_list__double_click_without_reason(self, run_dialog):
        inventory = self._create_inventory()
        item = self.create_inventory_item(inventory)

        dialog = InventoryDetailsDialog(self.store, inventory)
        dialog.items_list.emit('double-click', item)
        self.assertEquals(run_dialog.call_count, 0)

    @mock.patch('stoqlib.gui.dialogs.inventorydetails.run_dialog')
    def test_on_items_list__double_click_with_reason(self, run_dialog):
        inventory = self._create_inventory()
        item = self.create_inventory_item(inventory)
        item.reason = u'Reason test'

        dialog = InventoryDetailsDialog(self.store, inventory)
        dialog.items_list.emit('double-click', item)
        run_dialog.assert_called_once_with(NoteEditor, dialog, self.store,
                                           item, 'reason', title='Reason',
                                           label_text='Adjust reason',
                                           visual_mode=True)

    @mock.patch('stoqlib.gui.dialogs.inventorydetails.run_dialog')
    def test_on_info_button__clicked_without_reason(self, run_dialog):
        inventory = self._create_inventory()
        dialog = InventoryDetailsDialog(self.store, inventory)

        dialog.items_list.select(dialog.items_list[0])
        self.assertNotSensitive(dialog, ['info_button'])

    @mock.patch('stoqlib.gui.dialogs.inventorydetails.run_dialog')
    def test_on_info_button__clicked_with_reason(self, run_dialog):
        inventory = self._create_inventory()
        item = self.create_inventory_item(inventory)
        item.reason = u'Reason test'
        item_view = self.store.find(InventoryItemsView, id=item.id).one()
        dialog = InventoryDetailsDialog(self.store, inventory)

        dialog.items_list.select(item_view)
        self.assertSensitive(dialog, ['info_button'])
        self.click(dialog.info_button)
        run_dialog.assert_called_once_with(NoteEditor, dialog, self.store,
                                           item_view, 'reason', title='Reason',
                                           label_text='Adjust reason',
                                           visual_mode=True)

    @mock.patch('stoqlib.gui.dialogs.purchasedetails.SpreadSheetExporter.export')
    def test_export_spread_sheet(self, export):
        inventory = self._create_inventory()
        self.create_inventory_item(inventory)
        dialog = InventoryDetailsDialog(self.store, inventory)

        self.assertEquals(export.call_count, 0)
        self.click(dialog.export_button)
        self.assertEquals(export.call_count, 1)


if __name__ == '__main__':
    from stoqlib.api import api
    c = api.prepare_test()
    unittest.main()
