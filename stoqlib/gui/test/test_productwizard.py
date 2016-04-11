# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

#
# Copyright (C) 2015 Async Open Source <http://www.async.com.br>
# All rights reserved
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., or visit: http://www.gnu.org/.
#
# Author(s): Stoq Team <stoq-devel@async.com.br>
#

__tests__ = 'stoqlib.gui.wizards.productwizard'

import contextlib
import mock

from stoqlib.database.runtime import StoqlibStore
from stoqlib.domain.product import Product
from stoqlib.gui.editors.producteditor import (ProductPackageComponentEditor,
                                               TemporaryProductComponent)
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.gui.wizards.productwizard import ProductCreateWizard


class TestProducCreateWizard(GUITest):

    def test_create_inactive_group(self):
        inactive_group = self.create_attribute_group()
        inactive_group.is_active = False
        wizard = ProductCreateWizard(self.store)
        type_step = wizard.get_current_step()
        type_step.grid.set_active(True)
        self.click(wizard.next_button)
        attribute_step = wizard.get_current_step()

        groups = attribute_step.slave.attribute_group
        for combo_model in groups.get_model_items():
            # The inactive group should not be shown on combo
            self.assertNotEquals(combo_model, inactive_group.description)

    @mock.patch('stoqlib.gui.wizards.productwizard.warning')
    def test_create_without_attribute(self, warning):
        attribute_group = self.create_attribute_group()

        wizard = ProductCreateWizard(self.store)
        type_step = wizard.get_current_step()
        type_step.grid.set_active(True)
        self.click(wizard.next_button)

        attribute_step = wizard.get_current_step()
        self.click(wizard.next_button)
        # Testing without selecting a group
        warning.assert_called_once_with("You should select an attribute first")
        # Checking that we are in the same step after the warning
        self.assertEquals(wizard.get_current_step(), attribute_step)

        warning.reset_mock()
        # Selecting a group but it doesnt have a GridAttribute
        attribute_step.slave.attribute_group.select_item_by_data(attribute_group)
        self.click(wizard.next_button)
        warning.assert_called_once_with("You should select an attribute first")

    def test_create_inactive_attribute(self):
        attribute_group = self.create_attribute_group()
        attribute = self.create_grid_attribute(attribute_group=attribute_group)
        attribute.is_active = False

        wizard = ProductCreateWizard(self.store)
        type_step = wizard.get_current_step()
        type_step.grid.set_active(True)
        self.click(wizard.next_button)

        attribute_step = wizard.get_current_step()
        attribute_step.slave.attribute_group.select_item_by_data(attribute_group)
        # Inactive attributes should not be shown
        self.assertEquals(attribute_step.slave._widgets, {})

    @mock.patch('stoqlib.gui.wizards.productwizard.warning')
    def test_create_with_attribute_not_selected(self, warning):
        attribute_group = self.create_attribute_group()
        self.create_grid_attribute(attribute_group=attribute_group)

        wizard = ProductCreateWizard(self.store)
        type_step = wizard.get_current_step()
        type_step.grid.set_active(True)
        self.click(wizard.next_button)

        attribute_step = wizard.get_current_step()
        self.click(wizard.next_button)
        warning.reset_mock()
        # Selecting a group with a GridAttribute
        attribute_step.slave.attribute_group.select_item_by_data(attribute_group)
        self.click(wizard.next_button)
        warning.assert_called_once_with("You should select an attribute first")

    @mock.patch('stoqlib.gui.wizards.productwizard.warning')
    def test_create_with_attribute_without_option(self, warning):
        attribute_group = self.create_attribute_group()
        self.create_grid_attribute(attribute_group=attribute_group)

        wizard = ProductCreateWizard(self.store)
        type_step = wizard.get_current_step()
        type_step.grid.set_active(True)
        self.click(wizard.next_button)

        attribute_step = wizard.get_current_step()
        self.click(wizard.next_button)
        warning.reset_mock()
        # Selecting a group with a GridAttribute
        attribute_step.slave.attribute_group.select_item_by_data(attribute_group)
        self.click(wizard.next_button)
        warning.assert_called_once_with("You should select an attribute first")

        warning.reset_mock()
        # At this point we dont have any attribute_option for grid_attribute
        for i in attribute_step.slave._widgets.keys():
            self.assertEquals(i.get_sensitive(), False)
        self.click(wizard.next_button)
        warning.assert_called_once_with("You should select an attribute first")

    def test_create_with_inactive_option(self):
        attribute_group = self.create_attribute_group()
        attribute = self.create_grid_attribute(attribute_group=attribute_group)
        option = self.create_attribute_option(grid_attribute=attribute)
        option.is_active = False

        wizard = ProductCreateWizard(self.store)
        type_step = wizard.get_current_step()
        type_step.grid.set_active(True)
        self.click(wizard.next_button)

        attribute_step = wizard.get_current_step()
        attribute_step.slave.attribute_group.select_item_by_data(attribute_group)
        for check_box in attribute_step.slave._widgets.keys():
            self.assertEquals(check_box.get_sensitive(), False)

    @mock.patch('stoqlib.gui.slaves.productslave.warning')
    def test_create_grid_product(self, warning):
        attribute_group = self.create_attribute_group()
        grid_attribute = self.create_grid_attribute(attribute_group=attribute_group,
                                                    description=u'attr 1')
        grid_attribute2 = self.create_grid_attribute(attribute_group=attribute_group,
                                                     description=u'attr 2')
        self.create_attribute_option(grid_attribute=grid_attribute,
                                     description=u'option for attr 1',
                                     order=1)
        self.create_attribute_option(grid_attribute=grid_attribute2,
                                     description=u'option for attr 2',
                                     order=2)

        # Creating the wizard
        wizard = ProductCreateWizard(self.store)
        type_step = wizard.get_current_step()
        type_step.grid.set_active(True)
        self.click(wizard.next_button)

        # ProductAttributeEditorStep
        attribute_step = wizard.get_current_step()
        # Testing simulating combo selection change to cover everything
        attribute_step.slave.attribute_group.select(attribute_group)
        attribute_step.slave.attribute_group.select(None)
        # Selecting the attribute_group on the combo
        attribute_step.slave.attribute_group.select(attribute_group)
        # Set to active all grid_attributes for that group
        for attribute in attribute_step.slave._widgets.keys():
            self.assertEquals(attribute.get_sensitive(), True)
            attribute.set_active(True)
        self.click(wizard.next_button)

        # ProductEditorStep
        editor_step = wizard.get_current_step()
        # Getting ProductGridSlave
        grid_slave = editor_step.slave.get_slave('Grid')
        self.assertEquals(grid_slave.add_product_button.get_sensitive(), False)

        # Trying add a child without description
        for combo in grid_slave._widgets.values():
            # Position 0 (zero) is empty
            combo.select_item_by_position(1)
        self.assertEquals(grid_slave.add_product_button.get_sensitive(), True)
        self.click(grid_slave.add_product_button)
        warning.assert_called_once_with('You should fill the description first')

        # Filling the description and try again
        editor_step.slave.description.update('grid test')
        self.assertEquals(grid_slave.add_product_button.get_sensitive(), True)
        self.click(grid_slave.add_product_button)
        # Testing the sensitivity right after adding a child
        self.assertEquals(grid_slave.add_product_button.get_sensitive(), False)

        # One combo not filled with an valid option
        combo = grid_slave._widgets.values()[0]
        # Position 0 (zero) is empty
        combo.select_item_by_position(0)
        self.assertEquals(grid_slave.add_product_button.get_sensitive(), False)

        # Trying add a child with exactly the same attribute_option
        for combo in grid_slave._widgets.values():
            combo.select_item_by_position(1)
        self.assertEquals(grid_slave.add_product_button.get_sensitive(), False)

    @mock.patch('stoqlib.gui.slaves.productslave.run_dialog')
    def test_create_package_product(self, run_dialog):
        wizard = ProductCreateWizard(self.store)
        type_step = wizard.get_current_step()
        type_step.package.set_active(True)
        self.click(wizard.next_button)

        # ProductEditor step
        editor_step = wizard.get_current_step()
        # Checking that the slave is attached
        self.assertEquals(hasattr(editor_step.slave, 'package_slave'), True)

        # Package slave
        package_slave = editor_step.slave.get_slave('Pack content')
        self.assertNotSensitive(package_slave, ['add_button', 'remove_button',
                                                'edit_button'])

        package_slave.component_combo.select_item_by_position(0)
        selected = package_slave.component_combo.get_selected()
        temp = TemporaryProductComponent(package_slave.store,
                                         product=package_slave._product,
                                         component=selected,
                                         price=10)
        # After select a component add button will be sensitive
        self.assertSensitive(package_slave, ['add_button'])
        # And the other remain not sensitive
        self.assertNotSensitive(package_slave, ['remove_button', 'edit_button'])
        run_dialog.return_value = temp
        self.click(package_slave.add_button)

        args, kwargs = run_dialog.call_args
        self.assertEquals(args[0], ProductPackageComponentEditor)
        self.assertTrue(isinstance(args[2], StoqlibStore))
        self.assertTrue(isinstance(args[3], TemporaryProductComponent))
        self.assertTrue(hasattr(args[3], 'product'))
        self.assertTrue(hasattr(args[3], 'component'))
        self.assertTrue(hasattr(args[3], 'quantity'))
        self.assertTrue(hasattr(args[3], 'design_reference'))
        self.assertTrue(hasattr(args[3], 'price'))

    @mock.patch('stoqlib.gui.wizards.productwizard.yesno')
    def test_create_product_alike(self, yesno):
        attribute_group = self.create_attribute_group()
        grid_attribute = self.create_grid_attribute(attribute_group=attribute_group,
                                                    description=u'attr 1')
        grid_attribute2 = self.create_grid_attribute(attribute_group=attribute_group,
                                                     description=u'attr 2')
        self.create_attribute_option(grid_attribute=grid_attribute,
                                     description=u'option for attr 1',
                                     order=1)
        self.create_attribute_option(grid_attribute=grid_attribute2,
                                     description=u'option for attr 2',
                                     order=2)

        grid_product = self.create_product(storable=True, is_grid=True)
        self.create_product_attribute(product=grid_product, attribute=grid_attribute)

        # We need the mocked yesno to return different values each time it
        # is called inside of run_wizard bellow
        values = [True, False]

        def fake_yes_no(*args, **kwargs):
            return values.pop(0)

        with contextlib.nested(
                mock.patch('stoqlib.gui.wizards.productwizard.run_dialog'),
                mock.patch('stoqlib.gui.wizards.productwizard.api.new_store'),
                mock.patch.object(self.store, 'commit'),
                mock.patch.object(self.store, 'close')
        ) as (run_dialog, new_store, commit, close):
            new_store.return_value = self.store
            run_dialog.return_value = grid_product
            yesno.side_effect = fake_yes_no
            ProductCreateWizard.run_wizard(None)
        # This is the second call to yesno()
        args, kwargs = run_dialog.call_args_list[1]
        self.assertEquals(kwargs['product_type'], Product.TYPE_GRID)
        self.assertEquals(kwargs['template'], grid_product)
