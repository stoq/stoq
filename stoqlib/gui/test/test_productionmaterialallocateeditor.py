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


from stoqlib.database.runtime import get_current_branch
from stoqlib.gui.uitestutils import GUITest
from stoqlib.gui.editors.productioneditor import ProductionMaterialAllocateEditor


class TestProductionMaterialAllocateEditor(GUITest):
    def testShow(self):
        material = self.create_production_material()
        editor = ProductionMaterialAllocateEditor(self.store, material)
        editor.order_number.set_label("12345")
        self.check_editor(editor, 'editor-productionmaterialallocate-show')

    def testAllocate(self):
        branch = get_current_branch(self.store)
        material = self.create_production_material()
        material.product.storable.increase_stock(5, branch, 0, 0)
        editor = ProductionMaterialAllocateEditor(self.store, material)

        allocated = material.allocated

        editor.quantity.update(3)
        self.click(editor.main_dialog.ok_button)

        self.assertEquals(material.allocated, allocated + 3)
