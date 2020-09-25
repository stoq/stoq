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
from gi.repository import Gtk

from kiwi import ValueUnset
from stoqlib.api import api
from stoq.lib.gui.dialogs.initialstockdialog import InitialStockDialog
from stoq.lib.gui.test.uitestutils import GUITest
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class TestInitialStockDialog(GUITest):
    def test_show(self):
        storable = self.create_storable()
        storable.product.sellable.cost = 15
        storable.product.sellable.code = u'100'
        storable.product.sellable.barcode = u'0000000'
        storable.product.sellable.description = u'desc'

        dialog = InitialStockDialog(self.store)
        self.check_dialog(dialog, 'initial-stock-dialog-show')

    @mock.patch('stoq.lib.gui.editors.baseeditor.yesno')
    def test_cancel(self, yesno):
        self.create_storable()
        with self.sysparam(SYNCHRONIZED_MODE=True):
            dialog = InitialStockDialog(self.store)
            dialog.storables[0].initial_stock = 4
            self.click(dialog.main_dialog.cancel_button)

        msg = 'If you cancel this dialog all changes will be lost. Are you sure?'
        yesno.assert_called_once_with(msg, Gtk.ResponseType.NO, 'Cancel',
                                      "Don't cancel")

    def test_save(self):
        storable = self.create_storable()
        storable.product.sellable.cost = 17
        storable.product.sellable.code = u'100'
        storable.product.sellable.barcode = u'0000000'
        storable.product.sellable.description = u'desc'
        branch = api.get_current_branch(self.store)

        stock_item = storable.get_stock_item(branch, None)
        self.assertEqual(stock_item, None)

        dialog = InitialStockDialog(self.store)
        dialog.storables[0].initial_stock = 123
        self.click(dialog.main_dialog.ok_button)

        self.assertEqual(123, storable.get_balance_for_branch(branch))

        stock_item = storable.get_stock_item(branch, None)
        self.assertEqual(stock_item.stock_cost, 17)

    def test_edit(self):
        self.create_storable()
        self.create_storable()

        dialog = InitialStockDialog(self.store)

        treeview = dialog.slave.listcontainer.list.get_treeview()
        treeview.set_cursor(0)
        rows, column = treeview.get_cursor()

        item = dialog.slave.listcontainer.list[0]

        dialog.slave.listcontainer.list.emit('cell-edited', item, 'initial_stock')

        self.assertNotEqual((rows, column), treeview.get_cursor())

    def test_format_qty(self):
        dialog = InitialStockDialog(self.store)
        self.assertEqual(dialog._format_qty(10), 10)
        self.assertEqual(dialog._format_qty(ValueUnset), None)
