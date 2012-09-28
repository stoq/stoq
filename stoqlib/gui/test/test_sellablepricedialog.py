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

from stoqlib.gui.uitestutils import GUITest
from stoqlib.gui.dialogs.sellablepricedialog import SellablePriceDialog


class TestSellablePriceDialog(GUITest):
    @mock.patch('stoqlib.gui.dialogs.sellablepricedialog.ProgressDialog.show')
    def testCreate(self, show):
        sellable = self.create_sellable()
        sellable.code = '123'
        sellable.cost = 10
        category1 = self.create_client_category('cat1')
        category2 = self.create_client_category('cat2')
        p1 = self.create_client_category_price(sellable=sellable,
                                               category=category1)
        p2 = self.create_client_category_price(sellable=sellable,
                                               category=category2)

        editor = SellablePriceDialog(self.trans)
        self.check_editor(editor, 'dialog-sellable-price-create')
        editor.category.select(category1)
        editor.markup.set_text('10')
        self.click(editor.apply)

        editor.category.select(category2)
        editor.markup.set_text('50')
        self.click(editor.apply)

        self.click(editor.main_dialog.ok_button)

        self.assertEquals(p1.price, 11)
        self.assertEquals(p2.price, 15)
