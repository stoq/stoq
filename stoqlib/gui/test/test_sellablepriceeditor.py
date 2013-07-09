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

from decimal import Decimal

from stoqlib.gui.editors.sellableeditor import SellablePriceEditor
from stoqlib.gui.test.uitestutils import GUITest


class TestSellablePriceEditor(GUITest):
    def test_show(self):
        sellable = self.create_sellable()
        editor = SellablePriceEditor(self.store, sellable)
        self.check_editor(editor, 'editor-sellablepriceeditor-show')

    def test_editing(self):
        sellable = self.create_sellable()

        # With this values, the markup is 38.2636..., but when the editor is
        # created, the markup will be rounded to 38.26, what will make the price
        # go to 21.49943, and that will change the markup again, and this loop
        # will go on until the rounded values of price and markup are stable.
        sellable.cost = Decimal('15.55')
        sellable.price = Decimal('21.50')

        # Creating the editor should not change the price to 21.50
        editor = SellablePriceEditor(self.store, sellable)
        self.assertEqual(sellable.price, Decimal('21.50'))
        self.assertEqual(editor.markup.read(), Decimal('38.26'))

        # Updating the price should make the markup be updated, but the price
        # should not be changed again
        editor.price.update('21.49')
        self.assertEqual(editor.markup.read(), Decimal('38.20'))
        self.assertEqual(sellable.price, Decimal('21.49'))

        # Setting the markup to 38.24% should change the price to $21.49632, that
        # when rounded, will be $21.50. But $21.50 is 38.26% of $15.55. But the
        # markup widget should still have 38.24%
        editor.markup.update(Decimal('38.24'))
        self.assertEqual(sellable.price, Decimal('21.50'))
        self.assertEqual(editor.markup.read(), Decimal('38.24'))
