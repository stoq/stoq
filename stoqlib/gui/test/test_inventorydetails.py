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

__tests__ = 'stoqlib/gui/dialogs/inventorydetails.py'

import unittest

from stoqlib.database.runtime import get_current_branch
from stoqlib.gui.dialogs.inventorydetails import InventoryDetailsDialog
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.lib.dateutils import localdate


class TestInventoryDetails(GUITest):

    def _create_inventory(self):
        today = localdate(2010, 12, 1)

        # new sale
        inventory = self.create_inventory(branch=get_current_branch(self.store))
        inventory.identifier = 123
        inventory.open_date = today

        self.create_inventory_item(inventory)
        return inventory

    def test_show(self):
        model = self._create_inventory()
        dialog = InventoryDetailsDialog(self.store, model)
        self.check_editor(dialog, 'dialog-inventory-details')


if __name__ == '__main__':
    from stoqlib.api import api
    c = api.prepare_test()
    unittest.main()
