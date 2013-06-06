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

import decimal
import gtk
import mock

from stoqlib.api import api
from stoqlib.gui.slaves.workorderslave import (_WorkOrderItemEditor,
                                               _WorkOrderItemSlave)
from stoqlib.gui.test.uitestutils import GUITest


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
            ivp.return_value = {
                'is_valid': False,
                'min_price': decimal.Decimal('10.00'),
                'max_discount': decimal.Decimal('0.00'),
            }
            editor.price.update(1)
            ivp.assert_called_once_with(1, workorder.client.category,
                                        api.get_current_user(self.store))
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


class TestWorkOrderItemSlave(GUITest):
    def testRemove(self):
        workorder = self.create_workorder(equipment=u'Test equipment')
        workorder.client = self.create_client()
        editor = _WorkOrderItemSlave(store=self.store, model=workorder)
        self.assertEqual(len(editor.slave.klist), 0)

        product = self.create_product(branch=workorder.branch, stock=10)
        sellable = product.sellable
        sellable.barcode = u'666333999'
        storable = product.storable

        # Test synchronizing stoq (like if the user confirmed the wizard, came
        # back and removed the item) and not synchronizing (like if he added
        # and removed the item).
        # sync_stock is called on WorkOrderEditor at on_confirm
        for sync_stock in [True, False]:
            editor.barcode.set_text(u'666333999')
            self.activate(editor.barcode)
            editor.quantity.update(6)
            self.click(editor.add_sellable_button)

            # Make sure that the sellable (and only it) was added to the list
            self.assertEqual(len(editor.slave.klist), 1)
            self.assertEqual(sellable, editor.slave.klist[0].sellable)

            if sync_stock:
                # This is done on the WorkOrderEditor when closing it
                # Mimicing the behaviour
                workorder.sync_stock()
                self.assertEqual(
                    storable.get_balance_for_branch(workorder.branch), 4)

            editor.slave.klist.select(editor.slave.klist[0])
            with mock.patch('stoqlib.gui.base.lists.yesno') as yesno:
                yesno.return_value = True
                self.click(editor.slave.delete_button)
                yesno.assert_called_once_with(
                    'Delete this item?', gtk.RESPONSE_NO, 'Delete item', 'Keep it')

            self.assertEqual(len(editor.slave.klist), 0)
            self.assertEqual(
                storable.get_balance_for_branch(workorder.branch), 10)
