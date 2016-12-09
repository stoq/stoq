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

from stoqlib.gui.dialogs.masseditordialog import MultiplyOperation
from stoqlib.gui.dialogs.sellabledialog import SellableMassEditorDialog
from stoqlib.gui.test.uitestutils import GUITest


class TestSellablePriceDialog(GUITest):

    @mock.patch('stoqlib.gui.dialogs.masseditordialog.yesno')
    @mock.patch('stoqlib.gui.dialogs.masseditordialog.ProgressDialog.show')
    def test_create(self, show, yesno):
        sellable = self.create_sellable()
        sellable.code = u'123'
        sellable.cost = 10
        category1 = self.create_client_category(u'cat1')
        category2 = self.create_client_category(u'cat2')
        p1 = self.create_client_category_price(sellable=sellable,
                                               category=category1)
        p2 = self.create_client_category_price(sellable=sellable,
                                               category=category2)

        search = SellableMassEditorDialog(self.store)
        search.search.refresh()
        self.check_search(search, 'sellable-price-create')

        cost_field = [f for f in search._fields if f.label == 'Cost'][0]

        # Select the field corresponding to category1
        field = [f for f in search._fields
                 if getattr(f, 'category', None) == category1][0]
        search.mass_editor.field_combo.select(field)
        # Now, select the multiply operation
        search.mass_editor._editor.operations_combo.select(MultiplyOperation)
        # multiply by cost field
        search.mass_editor._editor._oper.combo.select(cost_field)
        search.mass_editor._editor._oper.entry.set_text('1.1')  # 10%
        self.click(search.mass_editor.apply_button)

        # Now, select the second category
        field = [f for f in search._fields
                 if getattr(f, 'category', None) == category2][0]
        search.mass_editor.field_combo.select(field)
        search.mass_editor._editor._oper.combo.select(cost_field)
        search.mass_editor._editor._oper.entry.set_text('1.5')  # 10%
        self.click(search.mass_editor.apply_button)

        yesno.return_value = True
        self.click(search.ok_button)

        self.assertEquals(p1.price, 11)
        self.assertEquals(p2.price, 15)

    def test_cancel(self):
        editor = SellableMassEditorDialog(self.store)
        self.click(editor.cancel_button)
