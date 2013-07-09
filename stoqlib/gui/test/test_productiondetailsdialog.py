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

from stoqlib.api import api
from stoqlib.domain.production import ProductionMaterial
from stoqlib.gui.dialogs.productiondetails import ProductionDetailsDialog
from stoqlib.gui.editors.productioneditor import (ProductionItemProducedEditor,
                                                  ProductionMaterialLostEditor,
                                                  ProductionMaterialAllocateEditor)
from stoqlib.gui.test.uitestutils import GUITest


class TestProductionDetailsDialog(GUITest):
    def _create_order(self):
        # Create production order
        order = self.create_production_order()
        order.identifier = 75423

        # Create product and components (1 of each)
        product = self.create_product(stock=0)
        product.sellable.description = u'Composed product'
        self.create_storable(product)

        component1 = self.create_product(stock=20, branch=order.branch)
        component1.sellable.description = u'Component 1'
        self.create_product_component(product=product, component=component1)
        component2 = self.create_product(stock=30, branch=order.branch)
        component2.sellable.description = u'Component 2'
        self.create_product_component(product=product, component=component2)

        # Add the products we want to produce:
        order.add_item(product.sellable, quantity=10)

        # And create the material we will need.
        # TODO: This should be in domain.
        ProductionMaterial(store=self.store, order=order,
                           product=component1, needed=10)
        ProductionMaterial(store=self.store, order=order,
                           product=component2, needed=10)

        return order

    def _create_quality_tests(self, order):
        from stoqlib.domain.product import ProductQualityTest
        product = order.get_items()[0].product
        ProductQualityTest(store=self.store, product=product,
                           test_type=ProductQualityTest.TYPE_BOOLEAN,
                           description=u'Boolean test',
                           success_value=u'True')
        ProductQualityTest(store=self.store, product=product,
                           test_type=ProductQualityTest.TYPE_DECIMAL,
                           description=u'Decimal test',
                           success_value=u'2 - 3')

    @mock.patch('stoqlib.gui.dialogs.productiondetails.run_dialog')
    def test_without_quality_test(self, run_dialog):
        order = self._create_order()
        order.start_production()
        editor = ProductionDetailsDialog(self.store, order)
        self.check_editor(editor, 'dialog-production-details-create')

        # Test producing one item
        self.assertNotSensitive(editor, ['produce_button'])
        production_item = editor.production_items[0]
        editor.production_items.select(production_item)

        with mock.patch.object(self.store, 'commit'):
            self.click(editor.produce_button)
            run_dialog.assert_called_once_with(ProductionItemProducedEditor,
                                               editor, self.store,
                                               production_item)
            # This is what the editor above would have done:
            production_item.produce(1, api.get_current_user(self.store), [])
            self.check_editor(editor, 'dialog-production-details-produced')

        run_dialog.reset_mock()

        self.assertNotSensitive(editor, ['lost_button', 'allocate_button'])
        material = editor.materials[0]
        editor.materials.select(material)
        self.assertSensitive(editor, ['lost_button', 'allocate_button'])

        # Test losing one production material
        with mock.patch.object(self.store, 'commit'):
            self.click(editor.lost_button)
            run_dialog.assert_called_once_with(ProductionMaterialLostEditor,
                                               editor, self.store,
                                               material)
            # This is what the editor above would have done:
            material.add_lost(1)
            self.check_editor(editor, 'dialog-production-details-lost')

        editor.materials.select(material)
        run_dialog.reset_mock()
        with mock.patch.object(self.store, 'commit'):
            self.click(editor.allocate_button)
            run_dialog.assert_called_once_with(ProductionMaterialAllocateEditor,
                                               editor, self.store,
                                               material)
            # This is what the editor above would have done:
            material.allocate(1)
            self.check_editor(editor, 'dialog-production-details-allocated')

    @mock.patch('stoqlib.gui.dialogs.productiondetails.run_dialog')
    def test_with_quality_test(self, run_dialog):
        order = self._create_order()
        self._create_quality_tests(order)
        order.start_production()
        editor = ProductionDetailsDialog(self.store, order)
        self.check_editor(editor, 'dialog-production-details-quality-create')

        # Test producing one item
        self.assertNotSensitive(editor, ['produce_button'])
        production_item = editor.production_items[0]
        editor.production_items.select(production_item)

        with mock.patch.object(self.store, 'commit'):
            # This is what the editor above would have done:
            production_item.produce(1, api.get_current_user(self.store), [1])
            self.click(editor.produce_button)
        run_dialog.assert_called_once_with(ProductionItemProducedEditor,
                                           editor, self.store,
                                           production_item)
        self.check_editor(editor, 'dialog-production-details-quality-produced')

        produced_item = editor.produced_items[0]
        editor.produced_items.select(produced_item)
        editor.quality_slave.apply()
