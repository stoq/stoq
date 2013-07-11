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


from stoqlib.gui.editors.producteditor import ProductSupplierEditor
from stoqlib.gui.test.uitestutils import GUITest


class TestProductSupplierEditor(GUITest):
    def test_show(self):
        product = self.create_product(with_supplier=True)
        supplier_info = product.get_main_supplier_info()
        editor = ProductSupplierEditor(self.store, supplier_info)
        self.check_editor(editor, 'editor-productsupplier-show')
