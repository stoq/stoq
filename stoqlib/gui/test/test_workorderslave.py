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

import contextlib
import decimal
import gtk
import mock

from stoqlib.api import api
from stoqlib.gui.slaves.workorderslave import (_WorkOrderItemEditor,
                                               _WorkOrderItemSlave)
from stoqlib.gui.test.uitestutils import GUITest


class TestWorkOrderItemEditor(GUITest):
    def test_show(self):
        workorder = self.create_workorder(description=u'Test equipment')
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
        with mock.patch.object(storable, 'get_balance_for_branch') as gbfb:
            gbfb.return_value = 0
            editor.quantity.update(20)
            # Called 2 times:
            # on_quantity__content_changed() - Is necessary check if the quantity
            # is valid to avoid update the quantity_reserved widget.
            # on_quantity__validate()
            self.assertEqual(gbfb.call_count, 2)
            self.assertInvalid(editor, ['quantity'])

        # Item without stock control.
        product2 = self.create_product()
        item2 = workorder.add_sellable(product2.sellable, quantity=2)
        editor = _WorkOrderItemEditor(self.store, model=item2)
        self.check_editor(editor, 'editor-workorderitem-without-storable-show')

    def test_show_with_sale(self):
        workorder = self.create_workorder(description=u'Test equipment')
        workorder.sale = self.create_sale()
        workorder.client = self.create_client()
        workorder.client.category = self.create_client_category()

        product = self.create_product(stock=10)

        item = workorder.add_sellable(product.sellable)
        editor = _WorkOrderItemEditor(self.store, model=item)
        self.check_editor(editor, 'editor-workorderitem-with-sale-show')

    def test_on_confirm(self):
        workorder = self.create_workorder(description=u'Test equipment')
        workorder.client = self.create_client()
        workorder.client.category = self.create_client_category()

        # Nothing made
        product = self.create_product(stock=10)
        item = workorder.add_sellable(product.sellable, quantity=1)
        item.reserve(1)
        editor = _WorkOrderItemEditor(self.store, model=item)
        with contextlib.nested(
                mock.patch.object(item, 'return_to_stock'),
                mock.patch.object(item, 'reserve')) as (return_to_stock,
                                                        reserve):
            editor.on_confirm()
            self.assertEqual(reserve.call_count, 0)
            self.assertEqual(return_to_stock.call_count, 0)

        # Reserving more quantity
        product = self.create_product(stock=10)
        item = workorder.add_sellable(product.sellable, quantity=10)
        item.reserve(2)
        editor = _WorkOrderItemEditor(self.store, model=item)
        editor.quantity.update(8)
        with contextlib.nested(
                mock.patch.object(item, 'return_to_stock'),
                mock.patch.object(item, 'reserve')) as (return_to_stock,
                                                        reserve):
            editor.on_confirm()
            reserve.assert_called_once_with(6)
            self.assertEqual(return_to_stock.call_count, 0)

        # Returning some quantity to stock
        product = self.create_product(stock=10)
        item = workorder.add_sellable(product.sellable, quantity=10)
        item.reserve(6)
        editor = _WorkOrderItemEditor(self.store, model=item)
        editor.quantity.update(4)
        with contextlib.nested(
                mock.patch.object(item, 'return_to_stock'),
                mock.patch.object(item, 'reserve')) as (return_to_stock,
                                                        reserve):
            editor.on_confirm()
            self.assertEqual(reserve.call_count, 0)
            return_to_stock.assert_called_once_with(2)


class TestWorkOrderItemSlave(GUITest):
    def test_show(self):
        workorder = self.create_workorder(description=u'Test equipment')
        workorder.client = self.create_client()
        editor = _WorkOrderItemSlave(store=self.store, parent=None,
                                     model=workorder)
        self.check_slave(editor, 'slave-workorderitem-show')

    def test_show_with_sale(self):
        workorder = self.create_workorder(description=u'Test equipment')
        workorder.sale = self.create_sale()
        workorder.client = self.create_client()
        editor = _WorkOrderItemSlave(store=self.store, parent=None,
                                     model=workorder)
        self.check_slave(editor, 'slave-workorderitem-with-sale-show')

    def test_remove(self):
        workorder = self.create_workorder(description=u'Test equipment')
        workorder.client = self.create_client()
        editor = _WorkOrderItemSlave(store=self.store, parent=None,
                                     model=workorder)
        self.assertEqual(len(editor.slave.klist), 0)

        product = self.create_product(branch=workorder.branch, stock=10)
        sellable = product.sellable
        sellable.barcode = u'666333999'
        storable = product.storable

        editor.barcode.set_text(u'666333999')
        self.activate(editor.barcode)
        editor.quantity.update(6)
        self.click(editor.add_sellable_button)

        # Make sure that the sellable (and only it) was added to the list
        self.assertEqual(len(editor.slave.klist), 1)
        self.assertEqual(sellable, editor.slave.klist[0].sellable)

        editor.slave.klist.select(editor.slave.klist[0])
        with mock.patch('stoqlib.gui.base.lists.yesno') as yesno:
            yesno.return_value = True
            self.click(editor.slave.delete_button)
            yesno.assert_called_once_with(
                'Delete this item?', gtk.RESPONSE_NO, 'Delete item', 'Keep it')

        self.assertEqual(len(editor.slave.klist), 0)
        self.assertEqual(
            storable.get_balance_for_branch(workorder.branch), 10)
