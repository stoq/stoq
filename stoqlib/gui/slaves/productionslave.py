# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2009 Async Open Source <http://www.async.com.br>
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Slaves for production """

from decimal import Decimal

import pango
import gtk

from kiwi.python import Settable
from kiwi.ui.objectlist import Column, ColoredColumn
from kiwi.utils import gsignal

from stoqlib.database.runtime import get_current_user, get_current_branch
from stoqlib.domain.interfaces import IStorable
from stoqlib.domain.inventory import Inventory
from stoqlib.domain.product import ProductQualityTest
from stoqlib.domain.production import ProductionOrder, ProductionMaterial
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.formatters import format_quantity
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.baseeditor import BaseEditorSlave
from stoqlib.gui.editors.productioneditor import ProductionMaterialEditor

_ = stoqlib_gettext


#XXX: This is just a workaround to avoid the zillions of queries
#     when handling production items and materials.
class _TemporaryMaterial(object):
    def __init__(self, production, component, conn):
        storable = IStorable(component, None)
        if storable is not None:
            self.stock_quantity = storable.get_full_balance(production.branch)
        else:
            self.stock_quantity = Decimal(0)

        sellable = component.sellable
        self.code = sellable.code
        self.description = sellable.get_description()
        self.category_description = sellable.get_category_description()
        self.unit_description = sellable.get_unit_description()
        self.product = component
        self.needed = Decimal(0)
        self.to_purchase = Decimal(0)
        self.to_make = Decimal(0)
        self.order = production
        self._material = None
        self._conn = conn

    @property
    def material(self):
        if self._material is None:
            # At this point, the needed quantity have already been updated.
            assert self.needed > 0
            material = ProductionMaterial.selectOneBy(order=self.order,
                                                      product=self.product,
                                                      connection=self._conn)
            if material is not None:
                self._material = material
                self._material.needed = self.needed
            else:
                self._material = ProductionMaterial(
                                                needed=self.needed,
                                                to_purchase=self.to_purchase,
                                                to_make=self.to_make,
                                                order=self.order,
                                                product=self.product,
                                                connection=self._conn)
        return self._material

    def create(self):
        return self.material

    def sync(self):
        #assert self._material is not None
        self.to_purchase = self.material.to_purchase
        self.to_make = self.material.to_make

    def add_quantity(self, quantity):
        assert quantity > 0
        self.needed += quantity
        self.update_quantities()

    def update_quantities(self):
        missing_quantity = self.needed - self.stock_quantity
        if missing_quantity < 0:
            missing_quantity = Decimal(0)

        if self.product.has_components():
            self.to_make = missing_quantity
        else:
            self.to_purchase = missing_quantity

        if self._material is not None:
            self._material.needed = self.needed
            self._material.to_make = self.to_make
            self._material.to_purchase = self.to_purchase


class ProductionMaterialListSlave(BaseEditorSlave):
    gladefile = 'ProductionMaterialListSlave'
    model_type = ProductionOrder

    def __init__(self, conn, model, visual_mode=False):
        BaseEditorSlave.__init__(self, conn, model, visual_mode)
        self._setup_widgets()

    def _add_materials(self, production_item):
        self._materials_objects = []
        for product_component in production_item.get_components():
            material = self._get_or_create_material(product_component)
            quantity = product_component.quantity * production_item.quantity
            material.add_quantity(quantity)
            material.sync()

            if material not in self.materials:
                self.materials.append(material)
            else:
                self.materials.update(material)

    def _get_or_create_material(self, product_component):
        component = product_component.component
        for material in self.materials:
            if material.product is component:
                return material
        return _TemporaryMaterial(self.model, component, self.conn)

    def _edit_production_material(self):
        material = self.materials.get_selected()
        assert material is not None

        retval = run_dialog(ProductionMaterialEditor, self, self.conn,
                            material.material)
        if retval:
            material.sync()
            self.materials.update(material)

    def _setup_widgets(self):
        self.edit_button.set_sensitive(False)
        if not self.visual_mode:
            self.start_production_check.hide()

        has_open_inventory = Inventory.has_open(self.conn,
                                                get_current_branch(self.conn))
        self.start_production_check.set_sensitive(not bool(has_open_inventory))

        self.materials.set_columns(self._get_columns())
        for production_item in self.model.get_items():
            self._add_materials(production_item)

    def _get_columns(self):
        return [
            Column('code', title=_('Code'), data_type=str),
            Column('category_description', title=_('Category'),
                    data_type=str, expand=True, ellipsize=pango.ELLIPSIZE_END),
            Column('description', title=_('Description'), data_type=str,
                    expand=True, ellipsize=pango.ELLIPSIZE_END, sorted=True),
            Column('unit_description', title=_('Unit'),
                    data_type=str),
            Column('needed', title=_('Needed'), data_type=Decimal,
                    format_func=format_quantity),
            Column('stock_quantity', title=_('In Stock'), data_type=Decimal,
                    format_func=format_quantity),
            ColoredColumn('to_purchase', title=_('To Purchase'),
                          data_type=Decimal, format_func=format_quantity,
                          use_data_model=True, color='red',
                          data_func=self._colorize_to_purchase_col),
            ColoredColumn('to_make', title=_('To Make'), data_type=Decimal,
                          format_func=format_quantity, use_data_model=True,
                          color='red', data_func=self._colorize_to_make_col)]

    #XXX: Some duplication here, since the columns will never be both red.

    def _colorize_to_purchase_col(self, material):
        if material.product.has_components():
            return
        stock_qty = material.stock_quantity
        if material.to_purchase + stock_qty - material.needed < 0:
            return True
        return False

    def _colorize_to_make_col(self, material):
        if not material.product.has_components():
            return
        stock_qty = material.stock_quantity
        if material.to_make + stock_qty - material.needed < 0:
            return True
        return False

    #
    # BaseEditorSlave
    #

    def validate_confirm(self):
        for material in self.materials:
            material.create()

        # In visual mode the user can choose if we start the production now or
        # later. If not in visual mode, we start the production now.
        if self.start_production_check.get_active() or not self.visual_mode:
            self.model.start_production()
        elif self.model.status != ProductionOrder.ORDER_WAITING:
            for material in self.materials:
                if material.to_purchase > 0 or material.to_make > 0:
                    self.model.set_production_waiting()
                    break
        return True

    def reload_materials(self):
        """Reloads the material list if needed."""
        if len(self.materials) == 0:
            return

        self.materials.clear()
        # will trigger the material re-population.
        self._setup_widgets()

        for material in self.materials:
            material.update_quantities()

    #
    # Kiwi Callbacks
    #

    def on_materials__selection_changed(self, widget, material):
        self.edit_button.set_sensitive(bool(material))

    def on_materials__double_click(self, widget, material):
        self._edit_production_material()

    def on_edit_button__clicked(self, widget):
        self._edit_production_material()


class QualityTestResultSlave(BaseEditorSlave):
    model_name = _('Quality Test Result')
    model_type = Settable
    gladefile = 'QualityTestResultSlave'
    proxy_widgets = ['quality_test', 'decimal_value', 'boolean_value']

    gsignal('test-updated', object, object, object)

    def __init__(self, conn):
        self._items = []
        self._product = None
        BaseEditorSlave.__init__(self, conn=conn, model=None)

    @property
    def test_type(self):
        if self.model.quality_test:
            return self.model.quality_test.test_type
        return None

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)
        self.quality_vbox.set_sensitive(False)

    def _setup_widgets(self):
        self.sizegroup1.add_widget(self.decimal_value)
        self.sizegroup1.add_widget(self.boolean_value)
        self.decimal_value.set_visible(False)
        self.boolean_value.prefill([(_('True'), True), (_('False'), False)])

    def create_model(self, conn):
        return Settable(quality_test=None,
                        decimal_value=Decimal(0),
                        boolean_value=False)

    def _check_value_passes(self):
        if not self._product:
            return
        if self.test_type == ProductQualityTest.TYPE_BOOLEAN:
            value = self.model.boolean_value
        else:
            value = self.model.decimal_value

        test = self.model.quality_test
        if test.result_value_passes(value):
            self.result_icon.set_from_stock(gtk.STOCK_OK,
                                            gtk.ICON_SIZE_BUTTON)
        else:
            self.result_icon.set_from_stock(gtk.STOCK_DIALOG_WARNING,
                                            gtk.ICON_SIZE_BUTTON)

    #
    #   Public API
    #

    def set_item_tests(self, items, product):
        self._items = items
        self.quality_vbox.set_sensitive(bool(product and items))

        # Tests didnt change
        if self._product == product:
            return

        self._product = product
        if product:
            self.quality_test.prefill([(i.description, i)
                            for i in product.quality_tests])

    def apply(self):
        if self.test_type == ProductQualityTest.TYPE_BOOLEAN:
            value = self.model.boolean_value
        else:
            value = self.model.decimal_value

        for item in self._items:
            result = item.set_test_result_value(self.model.quality_test, value,
                                                get_current_user(self.conn))
            self.emit('test-updated', item, self.model.quality_test, result)

    def after_quality_test__changed(self, widget):
        if not widget.get_selected():
            return
        if self.test_type == ProductQualityTest.TYPE_BOOLEAN:
            self.boolean_value.show()
            self.decimal_value.hide()
        else:
            self.boolean_value.hide()
            self.decimal_value.show()

        self._check_value_passes()

    def after_boolean_value__changed(self, widget):
        self._check_value_passes()

    def after_decimal_value__changed(self, widget):
        self._check_value_passes()

    def on_apply_button__clicked(self, widget):
        self.apply()
