# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2015 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##

import gtk
import mock

from stoqlib.domain.product import GridOption
from stoqlib.gui.editors.grideditor import (GridGroupEditor,
                                            GridAttributeEditor,
                                            GridOptionEditor,
                                            _GridOptionsSlave)
from stoqlib.gui.test.uitestutils import GUITest


class TestGridGroupEditor(GUITest):
    def test_create(self):
        editor = GridGroupEditor(self.store)
        self.check_editor(editor, 'editor-grid-group-create')

    def test_edit_group(self):
        group = self.create_attribute_group()
        editor = GridGroupEditor(self.store, model=group)
        self.assertEquals(editor.description.read(), u'grid group 1')

    def test_description_activation(self):
        editor = GridGroupEditor(self.store)
        editor.description.update("new group")
        retval = editor.description.activate()
        self.assertEquals(retval, True)


class TestGridAttributeEditor(GUITest):
    def test_create(self):
        self.create_attribute_group()
        editor = GridAttributeEditor(self.store)
        self.check_editor(editor, 'editor-grid-attribute-create')

    def test_edit_with_inactive_group(self):
        group = self.create_attribute_group()
        model = self.create_grid_attribute(attribute_group=group)
        group.is_active = False
        editor = GridAttributeEditor(self.store, model=model)
        self.check_editor(editor, 'editor-grid-attribute-edit-inactive')

    @mock.patch('stoqlib.gui.editors.grideditor.warning')
    def test_edit_attribute(self, warning):
        group1 = self.create_attribute_group(description=u'group1')
        group2 = self.create_attribute_group(description=u'group2')
        attribute = self.create_grid_attribute(attribute_group=group1)
        editor = GridAttributeEditor(self.store, model=attribute)

        # checking the values of the widgets
        self.assertEquals(editor.description.read(), u'grid attribute 1')
        self.assertEquals(editor.group.get_selected(), group1)

        editor.group.select_item_by_data(group2)
        editor.description.update("attribute1")

        self.click(editor.main_dialog.ok_button)
        warning.assert_called_once_with("You need to add at least one option")

        GridOption(store=self.store, attribute=attribute)
        self.assertEquals(editor.group.read(), group2)
        # changing the selected group and confirming the editor
        self.click(editor.main_dialog.ok_button)


class TestGridOptionEditor(GUITest):
    def test_create(self):
        editor = GridOptionEditor(self.store)
        self.check_editor(editor, 'editor-grid-option-create')

    def test_edit_option(self):
        attribute = self.create_grid_attribute()
        option = self.create_attribute_option(grid_attribute=attribute,
                                              description=u'option')
        editor = GridOptionEditor(self.store, model=option)
        self.assertEquals(editor.description.read(), option.description)

    def test_option_order_validation(self):
        attribute = self.create_grid_attribute()
        self.create_attribute_option(grid_attribute=attribute,
                                     description=u'option',
                                     order=1)
        editor = GridOptionEditor(self.store, attribute=attribute)

        editor.option_order_spin.update(1)
        self.assertValid(editor, ['option_order_spin'])


class TestGridOptionsSlave(GUITest):
    def test_create(self):
        attribute = self.create_grid_attribute()
        slave = _GridOptionsSlave(self.store, attribute)
        self.check_slave(slave, 'slave-grid-option')

    def test_remove_button(self):
        attribute = self.create_grid_attribute()
        option1 = self.create_attribute_option(grid_attribute=attribute,
                                               description=u'option1')
        option2 = self.create_attribute_option(grid_attribute=attribute,
                                               description=u'option2',
                                               order=2)

        # creating a child product using option2
        options = []
        options.append(option2)
        grid_product = self.create_product(is_grid=True)
        grid_product.add_grid_child(options)

        # Creating the slave
        slave = _GridOptionsSlave(self.store, attribute)
        # At first remove_button should be insensitive
        self.assertNotSensitive(slave.listcontainer, ['remove_button'])

        # changing selection to a option which is not being used
        slave.listcontainer.list.select(option1)
        self.assertSensitive(slave.listcontainer, ['remove_button'])

        # changing selection to a option that is being used
        slave.listcontainer.list.select(option2)
        self.assertNotSensitive(slave.listcontainer, ['remove_button'])

    @mock.patch('kiwi.ui.listdialog.yesno')
    def test_remove_last_option(self, yesno):
        attribute = self.create_grid_attribute()
        option = self.create_attribute_option(grid_attribute=attribute,
                                              description=u'option1')

        # Creating the slave
        slave = _GridOptionsSlave(self.store, attribute)
        # At first remove_button should be insensitive
        self.assertNotSensitive(slave.listcontainer, ['remove_button'])

        # Selecting one option to remove
        slave.listcontainer.list.select(option)
        self.assertSensitive(slave.listcontainer, ['remove_button'])
        yesno.return_value = gtk.RESPONSE_OK
        self.click(slave.listcontainer.remove_button)
        self.assertEquals(len(slave.listcontainer.list), 0)

    @mock.patch('stoqlib.gui.editors.grideditor._GridOptionsSlave.run_dialog')
    def test_run_editor(self, run_dialog):
        attribute = self.create_grid_attribute()
        option = self.create_attribute_option(grid_attribute=attribute,
                                              description=u'option1')

        slave = _GridOptionsSlave(self.store, attribute)
        self.assertSensitive(slave.listcontainer, ['add_button'])
        self.click(slave.listcontainer.add_button)
        run_dialog.assert_called_once_with(GridOptionEditor, store=self.store,
                                           model=None, attribute=attribute)

        run_dialog.reset_mock()
        slave.listcontainer.list.select(option)
        self.click(slave.listcontainer.edit_button)
        run_dialog.assert_called_once_with(GridOptionEditor, store=self.store,
                                           model=option, attribute=attribute)
