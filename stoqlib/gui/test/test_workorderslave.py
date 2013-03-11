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

import mock

from stoqlib.gui.uitestutils import GUITest
from stoqlib.gui.slaves.workorderslave import _WorkOrderItemEditor


class TestWorkOrderItemEditor(GUITest):
    def testShow(self):
        workorder = self.create_workorder(equipment=u'Test equipment')
        workorder.client = self.create_client()
        workorder.client.category = self.create_client_category()

        product = self.create_product(stock=10)
        sellable = product.sellable
        storable = product.storable

        item = workorder.add_sellable(sellable)
        editor = _WorkOrderItemEditor(self.store, model=item)
        self.check_editor(editor, 'editor-workorderitem-show')

        self.assertValid(editor, ['price'])
        editor.price.update(0)
        self.assertInvalid(editor, ['price'])
        editor.price.update(-1)
        self.assertInvalid(editor, ['price'])
        with mock.patch.object(sellable, 'is_valid_price') as ivp:
            ivp.return_value = False
            editor.price.update(1)
            ivp.assert_called_once_with(1, workorder.client.category)
            self.assertInvalid(editor, ['price'])

        self.assertValid(editor, ['quantity'])
        editor.quantity.update(0)
        self.assertInvalid(editor, ['quantity'])
        with mock.patch.object(storable, 'get_balance_for_branch') as gbfb:
            gbfb.return_value = False
            editor.quantity.update(20)
            gbfb.assert_called_once_with(workorder.branch)
            self.assertInvalid(editor, ['quantity'])
        with mock.patch.object(sellable, 'is_valid_quantity') as ivq:
            ivq.return_value = False
            editor.quantity.update(5)
            ivq.assert_called_once_with(5)
            self.assertInvalid(editor, ['quantity'])
