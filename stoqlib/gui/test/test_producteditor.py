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
from storm.expr import Update

from decimal import Decimal
from stoqlib.domain.sellable import SellableCategory, Sellable
from stoqlib.domain.commission import CommissionSource
from stoqlib.database.runtime import get_current_branch
from stoqlib.gui.editors.producteditor import (ProductEditor,
                                               ProductionProductEditor)
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.gui.slaves.productslave import ProductComponentSlave
from stoqlib.lib.parameters import sysparam


# TODO: Test product editor for products without storable
class TestProductEditor(GUITest):
    def tearDown(self):
        sysparam.set_int(self.store, 'COST_PRECISION_DIGITS', 2)
        GUITest.tearDown(self)

    def test_create(self):
        editor = ProductEditor(self.store)
        editor.code.update("12345")
        self.check_editor(editor, 'editor-product-create')

    def test_create_without_category(self):
        # Removing data from SellableCategory, so we can test the validation of
        # category_combo update when there is no category.
        self.store.execute(Update({Sellable.category_id: None}, table=Sellable))
        self.clean_domain([CommissionSource, SellableCategory])

        editor = ProductEditor(self.store)
        editor.code.update("12345")
        self.assertNotSensitive(editor, ['category_combo'])
        self.check_editor(editor, 'editor-product-create-no-category')

    def test_show(self):
        product = self.create_product(storable=True)
        editor = ProductEditor(self.store, product)
        editor.code.update("12345")
        self.check_editor(editor, 'editor-product-show')

    def test_visual_mode(self):
        product = self.create_product(storable=True)
        editor = ProductEditor(self.store, product, visual_mode=True)
        editor.code.update("12412")
        self.assertNotSensitive(editor, ['add_category', 'sale_price_button'])
        self.check_editor(editor, 'editor-product-visual-mode')

    def test_cost_precision_digits(self):
        # Set a number of digts greated than 2
        sysparam.set_int(self.store, 'COST_PRECISION_DIGITS', 5)

        product = self.create_product(storable=True)
        product.sellable.cost = Decimal('1.23456')
        editor = ProductEditor(self.store, product)
        editor.code.update("12345")
        # We expect the editor to show the correct value
        self.check_editor(editor, 'editor-product-cost-precision-digits')


class TestProductProductionEditor(GUITest):
    def test_create(self):
        editor = ProductionProductEditor(self.store)
        editor.code.update("12345")
        self.check_editor(editor, 'editor-product-prod-create')

    def test_show(self):
        component = self.create_product_component(storable=True)
        component.component.sellable.code = u'4567'
        editor = ProductionProductEditor(
            self.store, component.product)
        editor.code.update("12345")
        self.check_editor(editor, 'editor-product-prod-show')

    def test_confirm(self):
        component = self.create_product_component(storable=True)
        component.component.sellable.code = u'4567'
        component.product.sellable.code = u'6789'
        editor = ProductionProductEditor(self.store, component.product)

        self.click(editor.main_dialog.ok_button)
        self.check_editor(editor, 'editor-product-prod-confirm',
                          [editor.retval])

    @mock.patch('stoqlib.gui.slaves.productslave.run_dialog')
    def test_edit_component(self, run_dialog):
        run_dialog.return_value = None
        component = self.create_product_component()
        component.component.sellable.code = u'4567'
        branch = get_current_branch(self.store)
        self.create_storable(component.product, branch=branch, stock=1,
                             unit_cost=10)

        editor = ProductionProductEditor(self.store, component.product)
        editor.code.update("12345")
        compslave = editor.component_slave
        compslave.component_combo.select_item_by_data(component.component)
        self.click(compslave.add_button)

        self.assertEquals(run_dialog.call_count, 1)

        self.check_editor(editor, 'editor-product-prod-edit')

    @mock.patch('stoqlib.gui.slaves.productslave.info')
    def test_edit_component_edit_composed(self, info):
        component = self.create_product_component()
        component.component.sellable.code = u'4567'
        branch = get_current_branch(self.store)
        self.create_storable(component.component, branch=branch, stock=1,
                             unit_cost=10)

        editor = ProductionProductEditor(self.store, component.component)
        editor.code.update("12345")
        compslave = editor.component_slave
        compslave.component_combo.select_item_by_data(component.product)
        self.click(compslave.add_button)

        info.assert_called_once_with(
            'You can not add this product as component, '
            'since Description is composed by Description')


class TestProductComponentSlave(GUITest):
    def test_show(self):
        component = self.create_product_component()
        slave = ProductComponentSlave(self.store, component.product)
        self.check_slave(slave, 'slave-production-component-show')
