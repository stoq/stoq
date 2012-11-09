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

from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.product import Storable
from stoqlib.gui.uitestutils import GUITest
from stoqlib.gui.editors.producteditor import (ProductEditor,
                                               ProductionProductEditor)
from stoqlib.gui.slaves.productslave import ProductComponentSlave


class TestProductEditor(GUITest):
    def testCreate(self):
        editor = ProductEditor(self.trans)
        editor.code.update("12345")
        self.check_editor(editor, 'editor-product-create')

    def testShow(self):
        product = self.create_product()
        editor = ProductEditor(self.trans, product)
        editor.code.update("12345")
        self.check_editor(editor, 'editor-product-show')

    def testVisualMode(self):
        product = self.create_product()
        editor = ProductEditor(self.trans, product, visual_mode=True)
        editor.code.update("12412")
        self.assertNotSensitive(editor, ['add_category', 'sale_price_button'])
        self.check_editor(editor, 'editor-product-visual-mode')


class TestProductProductionEditor(GUITest):
    def testCreate(self):
        editor = ProductionProductEditor(self.trans)
        editor.code.update("12345")
        self.check_editor(editor, 'editor-product-prod-create')

    def testShow(self):
        component = self.create_product_component()
        component.component.sellable.code = '4567'
        editor = ProductionProductEditor(
            self.trans, component.product)
        editor.code.update("12345")
        self.check_editor(editor, 'editor-product-prod-show')

    def test_confirm(self):
        component = self.create_product_component()
        component.component.sellable.code = '4567'
        component.product.sellable.code = '6789'
        editor = ProductionProductEditor(self.trans, component.product)

        self.click(editor.main_dialog.ok_button)
        self.check_editor(editor, 'editor-product-prod-confirm',
                          [editor.retval])

    @mock.patch('stoqlib.gui.slaves.productslave.run_dialog')
    def testEditComponent(self, run_dialog):
        run_dialog.return_value = None
        component = self.create_product_component()
        component.component.sellable.code = '4567'
        branch = get_current_branch(self.trans)
        Storable(product=component.product, connection=self.trans)
        component.product.storable.increase_stock(1, branch, unit_cost=10)

        editor = ProductionProductEditor(self.trans, component.product)
        editor.code.update("12345")
        compslave = editor.component_slave
        compslave.component_combo.select_item_by_data(component.component)
        self.click(compslave.add_button)

        self.assertEquals(run_dialog.call_count, 1)

        self.check_editor(editor, 'editor-product-prod-edit')

    @mock.patch('stoqlib.gui.slaves.productslave.info')
    def testEditComponentEditComposed(self, info):
        component = self.create_product_component()
        component.component.sellable.code = '4567'
        branch = get_current_branch(self.trans)
        Storable(product=component.component, connection=self.trans)
        component.component.storable.increase_stock(1, branch, unit_cost=10)

        editor = ProductionProductEditor(self.trans, component.component)
        editor.code.update("12345")
        compslave = editor.component_slave
        compslave.component_combo.select_item_by_data(component.product)
        self.click(compslave.add_button)

        info.assert_called_once_with(
            'You can not add this product as component, '
            'since Description is composed by Description')


class TestProductComponentSlave(GUITest):
    def testShow(self):
        component = self.create_product_component()
        slave = ProductComponentSlave(self.trans, component.product)
        self.check_slave(slave, 'slave-production-component-show')
