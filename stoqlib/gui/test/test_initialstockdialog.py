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
import gtk

from stoqlib.api import api
from stoqlib.gui.dialogs.initialstockdialog import InitialStockDialog
from stoqlib.gui.uitestutils import GUITest
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class TestInitialStockDialog(GUITest):
    def test_show(self):
        storable = self.create_storable()
        storable.product.sellable.code = '100'
        storable.product.sellable.barcode = '0000000'
        storable.product.sellable.description = 'desc'

        dialog = InitialStockDialog(self.trans)
        self.check_dialog(dialog, 'initial-stock-dialog-show')

    @mock.patch('stoqlib.gui.dialogs.initialstockdialog.yesno')
    def test_cancel(self, yesno):
        self.create_storable()

        dialog = InitialStockDialog(self.trans)
        self.click(dialog.main_dialog.cancel_button)

        yesno.assert_called_once_with(_('Save data before close the dialog ?'),
                                      gtk.RESPONSE_NO, _('Save data'),
                                      _("Don't save"))

    def test_save(self):
        storable = self.create_storable()
        storable.product.sellable.code = '100'
        storable.product.sellable.barcode = '0000000'
        storable.product.sellable.description = 'desc'

        dialog = InitialStockDialog(self.trans)
        dialog._storables[0].initial_stock = 123
        self.click(dialog.main_dialog.ok_button)

        branch = api.get_current_branch(self.trans)
        self.assertEquals(123, storable.get_balance_for_branch(branch))

    def test_edit(self):
        self.create_storable()
        self.create_storable()

        dialog = InitialStockDialog(self.trans)

        treeview = dialog.slave.listcontainer.list.get_treeview()
        treeview.set_cursor(0)
        rows, column = treeview.get_cursor()

        item = dialog.slave.listcontainer.list[0]

        dialog.slave.listcontainer.list.emit('cell-edited', item, 'initial_stock')

        self.assertNotEquals((rows, column), treeview.get_cursor())
