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

from stoqlib.lib.dateutils import localdatetime
from stoqlib.gui.editors.inventoryeditor import InventoryOpenEditor
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.domain.inventory import Inventory


class TestOpenInventoryEditor(GUITest):
    def test_create(self):
        dialog = InventoryOpenEditor(self.store)
        d = localdatetime(2010, 01, 30, 12, 33)
        dialog.open_time.set_text(d.strftime("%X"))

        self.check_editor(dialog, 'editor-inventory-open')

    def test_open_iventory(self):
        # There are no inventories open right now
        self.assertEquals(self.store.find(Inventory).count(), 0)
        dialog = InventoryOpenEditor(self.store)
        self.click(dialog.main_dialog.ok_button)

        # There should be one open inventory now
        self.assertEquals(self.store.find(Inventory).count(), 1)

    def test_category_selection(self):
        dialog = InventoryOpenEditor(self.store)

        # By default, all categories are selected, so these buttons should be
        # enabled
        self.assertSensitive(dialog.main_dialog, ['ok_button'])
        self.assertSensitive(dialog, ['unselect_all'])

        self.click(dialog.unselect_all)

        # Now there are now categories selected. We cannot confirm and unselect
        # all
        self.assertNotSensitive(dialog.main_dialog, ['ok_button'])
        self.assertNotSensitive(dialog, ['unselect_all'])

        self.click(dialog.select_all)

        # Status should be back to normal
        self.assertSensitive(dialog.main_dialog, ['ok_button'])
        self.assertSensitive(dialog, ['unselect_all'])
