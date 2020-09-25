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

from stoqlib.database.runtime import get_current_user, get_current_branch
from stoq.lib.gui.editors.producteditor import ProductSupplierEditor
from stoq.lib.gui.test.uitestutils import GUITest


class TestProductSupplierEditor(GUITest):
    def test_show(self):
        product = self.create_product(with_supplier=True)
        supplier_info = product.get_main_supplier_info()
        editor = ProductSupplierEditor(self.store, supplier_info)
        self.check_editor(editor, 'editor-productsupplier-show')

    def test_branch_combo_items(self):
        branch = get_current_branch(self.store)
        user = get_current_user(self.store)
        product = self.create_product(with_supplier=True)
        supplier_info = product.get_main_supplier_info()
        with mock.patch.object(user.profile, 'check_app_permission') as is_admin:
            # Admin user can set the supplier for any branch
            is_admin.side_effect = [True, False]
            editor = ProductSupplierEditor(self.store, supplier_info)
            self.assertEqual(len(editor.branch_combo.get_model_items()), 2)
            # Regular user can only set to the current branch
            editor = ProductSupplierEditor(self.store, supplier_info)
            items = list(editor.branch_combo.get_model_items().values())
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0], branch)

    def test_branch_combo_sensitivity(self):
        branch = get_current_branch(self.store)
        # Create product with supplier info for all branches
        supplier = self.create_supplier()
        product = self.create_product()
        supplier_info = self.create_product_supplier_info(
            product=product, supplier=supplier, branch=branch)

        # We are editing another product supplier info, and since there is NOT
        # another one for all branches, it's optional to set a branch
        new_supplier_info = self.create_product_supplier_info(
            product=product, supplier=supplier)
        editor = ProductSupplierEditor(self.store, new_supplier_info)
        self.assertNotSensitive(editor, ['branch_combo'])
        self.assertSensitive(editor, ['branch_checkbutton'])
        self.assertFalse(editor.branch_checkbutton.get_active())

        # Remove branch from original supplier info. Now it's generic/default
        supplier_info.branch = None
        # We are editing another product supplier info, and since there is
        # already another one for all branches, it's mandatory to set a specific
        # branch now
        editor = ProductSupplierEditor(self.store, new_supplier_info)
        self.assertSensitive(editor, ['branch_combo'])
        self.assertNotSensitive(editor, ['branch_checkbutton'])
        self.assertTrue(editor.branch_checkbutton.get_active())
