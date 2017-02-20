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

import datetime
from decimal import Decimal
import mock
import gtk
import pango

from stoqlib.domain.sellable import Sellable, SellableCategory
from stoqlib.gui.dialogs.masseditordialog import (MultiplyOperation,
                                                  AddOperation, DivideOperation,
                                                  SetValueOperation,
                                                  SetObjectValueOperation,
                                                  SetDateValueOperation,
                                                  ReplaceOperation,
                                                  MassEditorSearch,
                                                  ReferenceField,
                                                  AccessorField, DecimalEditor)
from stoqlib.gui.test.uitestutils import GUITest


class TestOperations(GUITest):

    def test_set_field(self):
        price_field = AccessorField('Test', None, 'base_price', Decimal)
        cost_field = AccessorField('Test', None, 'cost', Decimal)
        operation = MultiplyOperation(self.store, price_field, [])
        self.assertEqual(operation._field, price_field)
        operation.set_field(cost_field)
        self.assertEqual(operation._field, cost_field)

    def test_multiply(self):
        sellable = self.create_sellable()
        sellable.cost = 100
        sellable.base_price = 1

        price_field = AccessorField('Test', None, 'base_price', Decimal)
        cost_field = AccessorField('Test', None, 'cost', Decimal)
        operation = MultiplyOperation(self.store, price_field, [cost_field])
        operation.combo.select(cost_field)
        operation.entry.set_text('3')

        self.assertEqual(price_field.get_new_value(sellable), 1)
        operation.apply_operation(sellable)
        self.assertEqual(price_field.get_new_value(sellable), 300)

        # An invalid value should not change the object
        operation.entry.set_text('foo')
        operation.apply_operation(sellable)
        self.assertEqual(price_field.get_new_value(sellable), 300)

    def test_add(self):
        sellable = self.create_sellable()
        sellable.cost = 100
        sellable.base_price = 1

        price_field = AccessorField('Test', None, 'base_price', Decimal)
        cost_field = AccessorField('Test', None, 'cost', Decimal)
        operation = AddOperation(self.store, price_field, [cost_field])
        operation.combo.select(cost_field)
        operation.entry.set_text('3')

        self.assertEqual(price_field.get_new_value(sellable), 1)
        operation.apply_operation(sellable)
        self.assertEqual(price_field.get_new_value(sellable), 103)

        # An invalid value should not change the object
        operation.entry.set_text('foo')
        operation.apply_operation(sellable)
        self.assertEqual(price_field.get_new_value(sellable), 103)

    def test_divide(self):
        sellable = self.create_sellable()
        sellable.cost = 100
        sellable.base_price = 1

        price_field = AccessorField('Test', None, 'base_price', Decimal)
        cost_field = AccessorField('Test', None, 'cost', Decimal)
        operation = DivideOperation(self.store, price_field, [cost_field])
        operation.combo.select(cost_field)
        operation.entry.set_text('4')

        self.assertEqual(price_field.get_new_value(sellable), 1)
        operation.apply_operation(sellable)
        self.assertEqual(price_field.get_new_value(sellable), 25)

        # An invalid value should not change the object
        operation.entry.set_text('foo')
        operation.apply_operation(sellable)
        self.assertEqual(price_field.get_new_value(sellable), 25)

    def test_set(self):
        sellable = self.create_sellable()
        sellable.cost = 100
        sellable.base_price = 1

        price_field = AccessorField('Test', None, 'base_price', Decimal)
        operation = SetValueOperation(self.store, price_field, [])
        operation.entry.set_text('4')

        self.assertEqual(price_field.get_new_value(sellable), 1)
        operation.apply_operation(sellable)
        self.assertEqual(price_field.get_new_value(sellable), 4)

        # An invalid value should not change the object
        operation.entry.set_text('foo')
        operation.apply_operation(sellable)
        self.assertEqual(price_field.get_new_value(sellable), 4)

    def test_set_object(self):
        sellable = self.create_sellable()
        old_category = self.create_sellable_category()
        new_category = self.create_sellable_category()
        sellable.category = old_category

        field = ReferenceField('Test', None, 'category', SellableCategory,
                               'description')
        operation = SetObjectValueOperation(self.store, field, [])
        operation.combo.select(new_category)

        self.assertEqual(field.get_new_value(sellable), old_category)
        operation.apply_operation(sellable)
        self.assertEqual(field.get_new_value(sellable), new_category)

    def test_set_date(self):
        sellable = self.create_sellable()
        old_date = datetime.date(2016, 1, 1)
        new_date = datetime.date(2015, 2, 2)
        sellable.on_sale_start_date = old_date

        field = AccessorField('Test', None, 'on_sale_start_date', datetime.date)
        operation = SetDateValueOperation(self.store, field, [])
        operation.entry.update(new_date)

        self.assertEqual(field.get_new_value(sellable).date(), old_date)
        operation.apply_operation(sellable)
        self.assertEqual(field.get_new_value(sellable), new_date)

    def test_replace(self):
        sellable = self.create_sellable()
        sellable.description = u'foo bar foo Foo'

        field = AccessorField('Test', None, 'description', Decimal)
        operation = ReplaceOperation(self.store, field, [])
        operation.one_entry.set_text('foo')
        operation.other_entry.set_text('XXX')

        self.assertEqual(field.get_new_value(sellable), u'foo bar foo Foo')
        operation.apply_operation(sellable)
        self.assertEqual(field.get_new_value(sellable), u'XXX bar XXX Foo')


class TestEditors(GUITest):

    def test_set_field(self):
        price_field = AccessorField('Test', None, 'base_price', Decimal)
        cost_field = AccessorField('Test', None, 'cost', Decimal)
        editor = DecimalEditor(self.store, price_field, [cost_field, price_field])

        self.assertEqual(editor._oper._field, price_field)
        editor.set_field(cost_field)
        self.assertEqual(editor._oper._field, cost_field)

    def test_change_operation(self):
        price_field = AccessorField('Test', None, 'base_price', Decimal)
        cost_field = AccessorField('Test', None, 'cost', Decimal)
        editor = DecimalEditor(self.store, price_field, [cost_field, price_field])

        self.assertEqual(type(editor._oper), SetValueOperation)
        editor.operations_combo.select(AddOperation)
        self.assertEqual(type(editor._oper), AddOperation)


class TestAccessorField(GUITest):
    def test_methods(self):
        sellable = self.create_sellable(price=10)
        field = AccessorField('Test', None, 'base_price', Decimal)

        # The value is still 10
        self.assertEqual(field.get_value(sellable), 10)
        self.assertEqual(field.get_new_value(sellable), 10)
        self.assertFalse(field.is_changed(sellable))

        # Setting it to 10 again should not change anything
        field.set_new_value(sellable, 10)
        self.assertFalse(field.is_changed(sellable))

        # Lets update it to 15
        field.set_new_value(sellable, 15)

        # The current value of the object is still 10, but the new value is 15
        self.assertEqual(sellable.price, 10)
        self.assertEqual(field.get_value(sellable), 10)
        self.assertEqual(field.get_new_value(sellable), 15)
        self.assertTrue(field.is_changed(sellable))

        # Now lest save the value.
        field.save_value(sellable)
        self.assertEqual(sellable.price, 15)

    def test_accessor(self):
        sellable = self.create_sellable(price=10)
        sellable.product.ncm = u'123'
        field = AccessorField('Test', 'product', 'ncm', unicode)

        self.assertEqual(field.get_value(sellable), '123')
        field.set_new_value(sellable, u'456')
        field.save_value(sellable)

        self.assertEqual(sellable.product.ncm, '456')


class TestMassEditor(GUITest):

    def _create_search(self, fields, data):

        class FooEditor(MassEditorSearch):
            search_spec = Sellable

            def get_fields(self, store):
                return fields

            def get_items(self, store):
                return data

        editor = FooEditor(self.store)
        return editor

    def test_get_fields(self):
        field = AccessorField('Test', None, 'base_price', Decimal)
        sellable = self.create_sellable(price=10)
        search = self._create_search([field], [sellable])
        self.assertEqual(search.get_fields(self.store), [field])

    def test_cell_data_func(self):
        field = AccessorField('Test', None, 'base_price', Decimal)
        sellable = self.create_sellable(price=10)
        search = self._create_search([field], [sellable])
        col = search.columns[0]

        # Note that below we are testing the properties of the renderer, and not
        # really the value returned
        renderer = gtk.CellRendererText()
        search._on_cell_data_func(col, renderer, sellable, '10')
        self.assertFalse(renderer.get_property('weight-set'))

        field.set_new_value(sellable, 15)
        search._on_cell_data_func(col, renderer, sellable, '10')
        self.assertTrue(renderer.get_property('weight-set'))
        self.assertEqual(renderer.get_property('weight'), pango.WEIGHT_BOLD)

    def test_change_editor(self):
        price_field = AccessorField('Test', None, 'base_price', Decimal)
        cost_field = AccessorField('Test', None, 'cost', Decimal)
        sellable = self.create_sellable(price=10)
        search = self._create_search([price_field, cost_field], [sellable])

        search.mass_editor.field_combo.select(price_field)
        field_editor = search.mass_editor._editor
        # Changing the field that has the same datatype should not change the
        # editor
        search.mass_editor.field_combo.select(cost_field)
        self.assertEqual(search.mass_editor._editor, field_editor)

    def test_format_func(self):
        sellable = self.create_sellable(price=10)
        sellable.code = u'123'
        sellable.category = self.create_sellable_category(u'Categoria')

        field = AccessorField('Test', None, 'code', unicode)
        self.assertEqual(field.format_func(sellable), '123')
        sellable.code = None
        self.assertEqual(field.format_func(sellable), '')

        field = ReferenceField('Test', None, 'category', SellableCategory,
                               'description')
        self.assertEqual(field.format_func(sellable), 'Categoria')
        sellable.category = None
        self.assertEqual(field.format_func(sellable), '')

    @mock.patch('stoqlib.gui.dialogs.masseditordialog.yesno')
    @mock.patch('stoqlib.gui.dialogs.masseditordialog.warning')
    def test_confirm_invalid(self, warning, yesno):
        price_field = AccessorField('Test', None, 'base_price', Decimal)
        desc_field = AccessorField('Test', None, 'description', unicode)
        sellable = self.create_sellable(price=10)
        search = self._create_search([price_field, desc_field], [sellable])

        sellable.non_existing_attr = -20
        column = search.results.get_columns()[0]
        search.results.emit('cell-edited', sellable, column)

        # Force cell editing of unicode column that needs special treatment
        column = search.results.get_columns()[1]
        search.results.emit('cell-edited', sellable, column)

        # Dialog should still be open
        yesno.return_value = False
        self.click(search.ok_button)

        yesno.return_value = True
        self.click(search.ok_button)

        args, kwargs = warning.call_args
        self.assertEqual(args[0],
                         'There was an error saving one of the values')

    @mock.patch('stoqlib.gui.dialogs.masseditordialog.yesno')
    @mock.patch('stoqlib.gui.dialogs.masseditordialog.warning')
    def test_confirm_not_changed(self, warning, yesno):
        price_field = AccessorField('Test', None, 'base_price', Decimal)
        sellable = self.create_sellable(price=10)
        search = self._create_search([price_field], [sellable])

        self.click(search.ok_button)
        self.assertEquals(yesno.call_count, 0)
        self.assertEquals(warning.call_count, 0)
