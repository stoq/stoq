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


from stoqlib.gui.editors.purchaseeditor import PurchaseItemEditor
from stoqlib.gui.test.uitestutils import GUITest


class TestPurchaseItemEditor(GUITest):
    def test_show(self):
        item = self.create_purchase_order_item()
        editor = PurchaseItemEditor(self.store, item)
        editor.order.set_label("12345")

        # quantity=8, price=125
        self.assertEqual(editor.total.read(), 1000)
        editor.quantity.update(10)
        self.assertEqual(editor.total.read(), 1250)
        editor.cost.update(150)
        self.assertEqual(editor.total.read(), 1500)

        self.check_editor(editor, 'editor-purchaseitem-show')
