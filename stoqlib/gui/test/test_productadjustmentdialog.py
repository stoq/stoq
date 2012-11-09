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
from stoqlib.gui.uitestutils import GUITest
from stoqlib.gui.dialogs.productadjustmentdialog import (ProductsAdjustmentDialog,
                                                         AdjustmentDialog)


class TestProductAdjustmentDialog(GUITest):
    def testShow(self):
        inventory = self.create_inventory()
        inventory.invoice_number = 4123
        item = self.create_inventory_item(inventory, 5)
        item.actual_quantity = 10
        dialog = ProductsAdjustmentDialog(self.trans, inventory)
        self.check_editor(dialog, 'dialog-product-adjustment')

    @mock.patch('stoqlib.gui.dialogs.productadjustmentdialog.run_dialog')
    def testAdjust(self, run_dialog):
        inventory = self.create_inventory()
        item = self.create_inventory_item(inventory, 5)
        item.actual_quantity = 10

        dialog = ProductsAdjustmentDialog(self.trans, inventory)
        self.assertNotSensitive(dialog, ['adjust_button'])

        dialog.invoice_number.update(123)
        dialog.inventory_items.select(item)
        # _run_adjustment_dialog commits the transaction. Avoid that as it will
        # break other tests
        finish = 'stoqlib.gui.dialogs.productadjustmentdialog.api.finish_transaction'
        with mock.patch(finish):
            self.click(dialog.adjust_button)

        self.assertEquals(run_dialog.call_count, 1)


class TestAdjustmentDialog(GUITest):

    @mock.patch('stoqlib.gui.dialogs.productadjustmentdialog.warning')
    def testShow(self, warning):
        cfop = self.create_cfop_data()
        item = self.create_inventory_item()
        item.actual_quantity = 10
        dialog = AdjustmentDialog(self.trans, item, 41234)
        self.check_editor(dialog, 'dialog-product-adjustment-item')

        self.click(dialog.main_dialog.ok_button)
        warning.assert_called_once_with(
            'You can not adjust a product without a cfop!')

        warning.reset_mock()
        dialog.cfop_combo.select(cfop)
        self.click(dialog.main_dialog.ok_button)
        warning.assert_called_once_with(
            'You can not adjust a product without a reason!')

        dialog.reason.update('just because')
        warning.reset_mock()
        self.click(dialog.main_dialog.ok_button)
        self.assertEquals(warning.call_count, 0)
