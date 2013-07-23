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

__tests__ = 'stoqlib/gui/editors/discounteditor.py'

import decimal

from stoqlib.gui.editors.discounteditor import DiscountEditor
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class TestDiscountEditor(GUITest):
    def test_confirm(self):
        user = self.create_user()
        user.profile.max_discount = decimal.Decimal('50')

        sellable = self.create_sellable(price=100, product=True)
        sellable.barcode = u'123'

        sale = self.create_sale()
        sale_item1 = sale.add_sellable(self.create_sellable(), price=100)
        sale_item1.base_price = 100
        sale_item2 = sale.add_sellable(self.create_sellable(), price=200)
        sale_item2.base_price = 200

        # 10% of discount
        editor = DiscountEditor(self.store, sale, user=user)
        editor.discount.update(u'10%')
        self.click(editor.main_dialog.ok_button)
        self.assertEqual(sale_item1.price, 90)
        self.assertEqual(sale_item2.price, 180)

        # 75 of discount (25%)
        editor = DiscountEditor(self.store, sale, user=user)
        editor.discount.update(u'75')
        self.click(editor.main_dialog.ok_button)
        self.assertEqual(sale_item1.price, 75)
        self.assertEqual(sale_item2.price, 150)

        # 10.5% of discount (with . and ,)
        editor = DiscountEditor(self.store, sale, user=user)
        editor.discount.update(u'10.5%')
        self.click(editor.main_dialog.ok_button)
        self.assertEqual(sale_item1.price, 89.5)
        self.assertEqual(sale_item2.price, 179)
        editor = DiscountEditor(self.store, sale, user=user)
        editor.discount.update(u'10,5%')
        self.click(editor.main_dialog.ok_button)
        self.assertEqual(sale_item1.price, 89.5)
        self.assertEqual(sale_item2.price, 179)
