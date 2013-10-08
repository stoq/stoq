# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012-2013 Async Open Source <http://www.async.com.br>
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

from stoqlib.domain.loan import LoanItem
from stoqlib.gui.editors.loanitemeditor import LoanItemEditor
from stoqlib.gui.test.uitestutils import GUITest


class TestLoanItemEditor(GUITest):
    def test_show(self):
        loan_item = self.create_loan_item()
        editor = LoanItemEditor(self.store, loan_item)
        editor.sale.set_label("12345")

        # quantity=1, price=10
        self.assertEqual(editor.total.read(), 10)
        editor.quantity.update(2)
        self.assertEqual(editor.total.read(), 20)
        editor.price.update(15)
        self.assertEqual(editor.total.read(), 30)

        self.check_editor(editor, 'editor-loanitem-show')

    def test_quantity_validate(self):
        # The storable is created with 10 of quantity
        loan_item = self.create_loan_item()
        editor = LoanItemEditor(self.store, loan_item)

        editor.quantity.update(10)
        self.assertValid(editor, ['quantity'])
        editor.quantity.update(11)
        self.assertInvalid(editor, ['quantity'])
        editor.quantity.update(2)
        self.assertValid(editor, ['quantity'])

        # Create an item with 8 of quantity, so the item we are testing should
        # only be able to loan 2 or less of quantity (10 available in the
        # stock minus 8 already loaned in this new item)
        LoanItem(store=self.store, loan=loan_item.loan,
                 sellable=loan_item.sellable, price=10, quantity=8)

        editor.quantity.update(3)
        self.assertInvalid(editor, ['quantity'])
        editor.quantity.update(2)
        self.assertValid(editor, ['quantity'])

    def test_has_stock(self):
        # The storable is created with 10 of quantity
        loan_item = self.create_loan_item()
        editor = LoanItemEditor(self.store, loan_item)

        # Check if have exactly the same quantity on stock
        result = editor._has_stock(10)
        self.assertTrue(result)

        # Check if have one more product than the quantity on stock
        result = editor._has_stock(11)
        self.assertFalse(result)

        # Check if have one product less than the quantity on stock
        result = editor._has_stock(9)
        self.assertTrue(result)
