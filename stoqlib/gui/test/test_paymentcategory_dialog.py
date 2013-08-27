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

from stoqlib.gui.dialogs.paymentcategorydialog import PaymentCategoryDialog
from stoqlib.gui.test.uitestutils import GUITest


class TestPaymentCategoryDialog(GUITest):
    def test_show(self):
        self.create_payment_category()
        dialog = PaymentCategoryDialog(self.store)

        self.check_dialog(dialog, 'payment-category-show')

    @mock.patch('kiwi.ui.listdialog.yesno')
    def test_delete(self, yesno):
        category = self.create_payment_category()
        dialog = PaymentCategoryDialog(self.store, reuse_store=True)

        dialog.list_slave.listcontainer.list.select(category)

        yesno.return_value = gtk.RESPONSE_OK
        self.click(dialog.list_slave.listcontainer.remove_button)

        yesno.assert_called_once_with('Do you want to remove category ?',
                                      buttons=((gtk.STOCK_CANCEL,
                                                gtk.RESPONSE_CANCEL),
                                               (gtk.STOCK_REMOVE,
                                                gtk.RESPONSE_OK)),
                                      default=gtk.RESPONSE_OK,
                                      parent=None)

        self.check_dialog(dialog, 'payment-category-delete')

    @mock.patch('stoqlib.gui.dialogs.paymentcategorydialog.'
                'PaymentCategoryListSlave.run_editor')
    def test_edit(self, run_editor):
        category = self.create_payment_category()
        dialog = PaymentCategoryDialog(self.store, reuse_store=True)

        dialog.list_slave.listcontainer.list.select(category)

        self.click(dialog.list_slave.listcontainer.edit_button)
        run_editor.assert_called_once_with(self.store, category)
