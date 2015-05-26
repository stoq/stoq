# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012-2015 Async Open Source <http://www.async.com.br>
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


from stoqlib.gui.editors.producteditor import ProductManufacturerEditor
from stoqlib.gui.test.uitestutils import GUITest


class TestProductManufacturerEditor(GUITest):
    def test_create(self):
        editor = ProductManufacturerEditor(self.store)
        self.check_editor(editor, 'editor-productmanufacturer-create')

    def test_validate_code(self):
        self.create_product_manufacturer(name=u'name', code=u'code')
        editor = ProductManufacturerEditor(self.store)
        editor.code.update(u'code')
        # This cannot register 2 manufacturer with the same code
        self.assertInvalid(editor, ['code'])
        # This code should be ok
        editor.code.update(u'code2')
        self.assertValid(editor, ['code'])
