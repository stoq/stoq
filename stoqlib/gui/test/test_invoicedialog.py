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
import gtk
import mock

from stoqlib.domain.invoice import InvoiceLayout
from stoqlib.gui.dialogs.invoicedialog import InvoiceLayoutDialog
from stoqlib.gui.test.uitestutils import GUITest


class TestInvoiceLayoutListSlave(GUITest):
    def test_show(self):
        InvoiceLayout(description=u'Test Invoice', width=500, height=500)

        dialog = InvoiceLayoutDialog(store=self.store)
        self.check_dialog(dialog, 'invoice-layout-dialog-show')

    def test_delete_model(self):
        InvoiceLayout(store=self.store, description=u"Standard Invoice",
                      width=500, height=500)

        dialog = InvoiceLayoutDialog(store=self.store, reuse_store=True)

        item = dialog.list_slave.listcontainer.list[0]
        dialog.list_slave.listcontainer.list.select(item)

        with mock.patch('kiwi.ui.listdialog.yesno') as yesno:
            yesno.side_effect = lambda *x, **y: gtk.RESPONSE_OK
            self.click(dialog.list_slave.listcontainer.remove_button)

            yesno.assert_called_with('Do you want to remove Standard Invoice ?',
                                     buttons=(
                                         ('gtk-cancel', gtk.RESPONSE_CANCEL),
                                         ('gtk-remove', gtk.RESPONSE_OK)),
                                     default=gtk.RESPONSE_OK, parent=None)
