# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import mock
from stoqlib.gui.uitestutils import GUITest
from stoqlib.gui.dialogs.productcountingdialog import ProductCountingDialog


class TestProductCountingDialog(GUITest):
    @mock.patch('stoqlib.gui.dialogs.productcountingdialog.api.new_transaction')
    def test_confirm(self, new_transaction):
        # We need to use the current transaction in the test, since the test
        # object is only in this transaction
        new_transaction.return_value = self.trans

        inventory = self.create_inventory()
        inventory_item = self.create_inventory_item(inventory=inventory)
        inventory_item.product.sellable.description = 'item'

        dialog = ProductCountingDialog(self.trans, inventory)
        self.check_dialog(dialog, 'product-counting-dialog-show')

        treeview = dialog.slave.listcontainer.list.get_treeview()
        treeview.set_cursor(0)
        rows, column = treeview.get_cursor()

        dialog.slave.listcontainer.list.emit('cell-edited', None, None)

        # Dont commit the transaction
        with mock.patch.object(self.trans, 'commit') as commit:
            # Also dont close it, since tearDown will do it.
            with mock.patch.object(self.trans, 'close') as close:
                self.click(dialog.main_dialog.ok_button)
                self.assertEquals(commit.call_count, 1)
                self.assertEquals(close.call_count, 1)

        self.check_dialog(dialog, 'product-counting-dialog-confirm',
                          [dialog.retval, inventory_item])
