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

from stoqlib.domain.person import ClientCategory
from stoqlib.domain.sellable import ClientCategoryPrice
from stoqlib.gui.uitestutils import GUITest
from stoqlib.gui.editors.clientcategoryeditor import ClientCategoryEditor
from stoqlib.gui.dialogs.clientcategorydialog import ClientCategoryDialog
from stoqlib.lib.translation import stoqlib_gettext as _


class TestClientCategoryDialog(GUITest):
    def testShow(self):
        dialog = ClientCategoryDialog(self.trans)
        self.check_dialog(dialog, 'dialog-clientcategory-show')

    @mock.patch('stoqlib.gui.base.lists.run_dialog')
    def testAdd(self, run_dialog):
        dialog = ClientCategoryDialog(self.trans)
        # user canceled the dialog
        run_dialog.return_value = None
        self.click(dialog.list_slave.listcontainer.add_button)
        self.assertEquals(run_dialog.call_count, 1)

    @mock.patch('stoqlib.gui.base.lists.run_dialog')
    def testRemove(self, run_dialog):
        category = ClientCategory(name='foo', connection=self.trans)
        client = self.create_client()
        client.category = category

        total_categoryes = ClientCategory.select(connection=self.trans).count()
        self.assertEquals(total_categoryes, 1)

        dialog = ClientCategoryDialog(self.trans)
        dialog.list_slave.set_reuse_transaction(self.trans)
        dialog.list_slave.listcontainer.list.select(category)

        with mock.patch.object(dialog.list_slave.listcontainer,
                               'default_remove') as default_remove:
            default_remove.return_value = True
            self.click(dialog.list_slave.listcontainer.remove_button)

        total_categoryes = ClientCategory.select(connection=self.trans).count()
        self.assertEquals(total_categoryes, 0)
        self.assertEquals(client.category, None)

    @mock.patch('stoqlib.gui.dialogs.clientcategorydialog.warning')
    def testRemoveWithProduct(self, warning):
        category = ClientCategory(name='foo', connection=self.trans)
        ClientCategoryPrice(category=category,
                            sellable=self.create_sellable(),
                            connection=self.trans)
        dialog = ClientCategoryDialog(self.trans)
        dialog.list_slave.set_reuse_transaction(self.trans)
        dialog.list_slave.listcontainer.list.select(category)

        with mock.patch.object(dialog.list_slave.listcontainer,
                               'default_remove') as default_remove:
            default_remove.return_value = True
            self.click(dialog.list_slave.listcontainer.remove_button)
            msg = _("%s cannot be deleted, because is used in one or more "
                    "products.") % category.name
            warning.assert_called_once_with(msg)


class TestClientCategoryEditor(GUITest):
    def testCreate(self):
        editor = ClientCategoryEditor(self.trans)
        self.check_editor(editor, 'editor-clientcategory-create')
