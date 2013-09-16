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

from stoqlib.gui.editors.saleeditor import SaleQuoteItemEditor
from stoqlib.gui.test.uitestutils import GUITest


class TestSaleQuoteItemEditor(GUITest):
    def test_show_param_allow_higher_sale_price(self):
        sale_item = self.create_sale_item()
        editor = SaleQuoteItemEditor(self.store, sale_item)
        editor.sale.set_label('12345')

        # quantity=1, price=100
        with self.sysparam(ALLOW_HIGHER_SALE_PRICE=True):
            self.assertEqual(editor.total.read(), 100)
            editor.quantity.update(2)
            self.assertEqual(editor.total.read(), 200)
            editor.price.update(150)
            self.assertEqual(editor.total.read(), 300)

            self.check_editor(editor, 'editor-salequoteitem-show')
            module = 'stoqlib.lib.pluginmanager.PluginManager.is_active'
            with mock.patch(module) as patch:
                patch.return_value = True
                editor = SaleQuoteItemEditor(self.store, sale_item)
                editor.sale.set_label('23456')
                self.check_editor(editor, 'editor-salequoteitem-show-nfe')

    def test_show_param_no_allow_higher_sale_price(self):
        sale_item = self.create_sale_item()
        editor = SaleQuoteItemEditor(self.store, sale_item)
        editor.sale.set_label('12345')

        # quantity=1, price=100
        with self.sysparam(ALLOW_HIGHER_SALE_PRICE=False):
            self.assertEqual(editor.total.read(), 100)
            editor.quantity.update(2)
            self.assertEqual(editor.total.read(), 200)
            editor.price.update(150)
            # The price greater than 100 should be invalid.
            self.assertInvalid(editor, ['price'])
