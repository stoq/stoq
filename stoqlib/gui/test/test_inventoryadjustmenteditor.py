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

from stoqlib.gui.editors.inventoryadjustmenteditor import (InventoryAdjustmentEditor,
                                                           InventoryItemAdjustmentEditor)
from stoqlib.gui.test.uitestutils import GUITest


class TestProductAdjustmentDialog(GUITest):
    def test_show(self):
        inventory = self.create_inventory()
        inventory.invoice_number = 4123
        item = self.create_inventory_item(inventory, 5)
        item.actual_quantity = 10
        dialog = InventoryAdjustmentEditor(self.store, inventory)
        self.check_editor(dialog, 'dialog-product-adjustment')

    @mock.patch('stoqlib.gui.editors.inventoryadjustmenteditor.run_dialog')
    def test_adjust(self, run_dialog):
        inventory = self.create_inventory()
        item = self.create_inventory_item(inventory, 5)
        item.actual_quantity = 10

        dialog = InventoryAdjustmentEditor(self.store, inventory)
        self.assertNotSensitive(dialog, ['adjust_button'])

        dialog.invoice_number.update(123)
        dialog.inventory_items.select(item)
        # _run_adjustment_dialog commits the store. Avoid that as it will
        # break other tests
        confirm = 'stoqlib.database.runtime.StoqlibStore.confirm'
        with mock.patch(confirm):
            self.click(dialog.adjust_button)

        self.assertEquals(run_dialog.call_count, 1)

    def test_adjust_all(self):
        inventory = self.create_inventory()
        item = self.create_inventory_item(inventory, 5)
        item.counted_quantity = 10

        dialog = InventoryAdjustmentEditor(self.store, inventory)
        dialog.invoice_number.update(123)
        self.assertEquals(item.actual_quantity, None)
        self.click(dialog.adjust_all_button)
        self.assertEquals(item.actual_quantity, 10)
        self.assertEquals(item.reason, 'Automatic adjustment')


class TestAdjustmentDialog(GUITest):

    def test_show(self):
        item = self.create_inventory_item()
        item.recorded_quantity = 10
        item.counted_quantity = 20
        dialog = InventoryItemAdjustmentEditor(self.store, item, 41234)
        self.check_editor(dialog, 'dialog-product-adjustment-item')

        dialog.reason.update('just because')
        self.click(dialog.main_dialog.ok_button)
