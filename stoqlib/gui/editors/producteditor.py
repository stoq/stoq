# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2007 Async Open Source <http://www.async.com.br>
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
""" Editors definitions for products"""

from decimal import Decimal
import sys

import gtk
from kiwi.currency import currency
from kiwi.datatypes import ValidationError
from kiwi.ui.forms import TextField

from stoqdrivers.enum import TaxType

from stoqlib.api import api
from stoqlib.domain.product import (ProductSupplierInfo, Product,
                                    ProductComponent,
                                    ProductQualityTest, Storable,
                                    ProductManufacturer)
from stoqlib.domain.sellable import (Sellable,
                                     SellableTaxConstant)
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.editors.sellableeditor import SellableEditor
from stoqlib.lib.defaults import quantize
from stoqlib.lib.message import info
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


#
# Slaves
#

class TemporaryProductComponent(object):
    def __init__(self, product=None, component=None, quantity=Decimal(1),
                 design_reference=u''):
        self.product = product
        self.component = component
        self.quantity = quantity
        self.design_reference = design_reference

        if self.component is not None:
            # keep this values in memory in order to speed up the
            # data access
            sellable = self.component.sellable
            self.id = sellable.id
            self.code = sellable.code
            self.description = sellable.get_description()
            self.category = sellable.get_category_description()
            self.unit = sellable.get_unit_description()
            self.production_cost = self.component.get_production_cost()

    def _get_product_component(self, connection):
        return ProductComponent.selectOneBy(
            product=self.product, component=self.component,
            connection=connection)

    #
    # Public API
    #

    def get_total_production_cost(self):
        return quantize(self.production_cost * self.quantity)

    def delete_product_component(self, connection):
        component = self._get_product_component(connection)
        if component is not None:
            ProductComponent.delete(component.id,
                                    connection=connection)

    def add_or_update_product_component(self, connection):
        component = self._get_product_component(connection)
        if component is not None:
            # updating
            component.quantity = self.quantity
            component.design_reference = self.design_reference
        else:
            # adding
            ProductComponent(product=self.product,
                             component=self.component,
                             quantity=self.quantity,
                             design_reference=self.design_reference,
                             connection=connection)

#
#   Quality Test Editor & Slave
#


class QualityTestEditor(BaseEditor):
    model_name = _('Quality Test')
    model_type = ProductQualityTest
    gladefile = 'QualityTestEditor'

    proxy_widgets = ['description', 'test_type']
    confirm_widgets = ['description']

    def __init__(self, conn, model=None, product=None):
        self._product = product
        BaseEditor.__init__(self, conn=conn, model=model)

    def _setup_widgets(self):
        self.sizegroup1.add_widget(self.decimal_value)
        self.sizegroup1.add_widget(self.boolean_value)
        self.test_type.prefill([(value, key)
            for key, value in ProductQualityTest.types.items()])
        self.boolean_value.prefill([(_('True'), True), (_(('False')), False)])

        # Editing values
        if self.model.test_type == ProductQualityTest.TYPE_BOOLEAN:
            self.boolean_value.select(self.model.get_boolean_value())
        else:
            min_value, max_value = self.model.get_range_value()
            self.min_value.set_value(min_value)
            self.max_value.set_value(max_value)

    def create_model(self, conn):
        return ProductQualityTest(product=self._product, connection=conn)

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)

    def on_confirm(self):
        if self.model.test_type == ProductQualityTest.TYPE_BOOLEAN:
            self.model.set_boolean_value(self.boolean_value.read())
        else:
            self.model.set_range_value(self.min_value.read(),
                                       self.max_value.read())

    #
    #   Callbacks
    #

    def on_test_type__changed(self, widget):
        if self.model.test_type == ProductQualityTest.TYPE_BOOLEAN:
            self.boolean_value.show()
            self.decimal_value.hide()
        else:
            self.boolean_value.hide()
            self.decimal_value.show()


#
#   Product Supplier Editor & Slave
#

class ProductSupplierEditor(BaseEditor):
    model_name = _('Product Supplier')
    model_type = ProductSupplierInfo
    gladefile = 'ProductSupplierEditor'

    proxy_widgets = ('base_cost', 'icms', 'notes', 'lead_time',
                     'minimum_purchase', )
    confirm_widgets = ['base_cost', 'icms', 'lead_time', 'minimum_purchase']

    def _setup_widgets(self):
        unit = self.model.product.sellable.unit
        if unit is None:
            description = _(u'Unit(s)')
        else:
            description = unit.description
        self.unit_label.set_text(description)
        self.base_cost.set_digits(sysparam(self.conn).COST_PRECISION_DIGITS)
        self.base_cost.set_adjustment(
            gtk.Adjustment(lower=0, upper=sys.maxint, step_incr=1))
        self.minimum_purchase.set_adjustment(
            gtk.Adjustment(lower=0, upper=sys.maxint, step_incr=1))

    #
    # BaseEditor hooks
    #

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)

    def validate_confirm(self):
        return self.base_cost.read() > 0

    #
    # Kiwi handlers
    #

    def on_minimum_purchase__validate(self, entry, value):
        if not value or value <= Decimal(0):
            return ValidationError("Minimum purchase must be greater than zero.")

    def on_base_cost__validate(self, entry, value):
        if not value or value <= currency(0):
            return ValidationError("Value must be greater than zero.")

    def on_lead_time__validate(self, entry, value):
        if value < 1:
            return ValidationError("Lead time must be greater or equal one day")


#
# Editors
#


class ProductComponentEditor(BaseEditor):
    gladefile = 'ProductComponentEditor'
    proxy_widgets = ['quantity', 'design_reference']
    title = _(u'Product Component')
    model_type = TemporaryProductComponent

    def _setup_widgets(self):
        self.component_description.set_text(self.model.description)
        self.quantity.set_adjustment(
            gtk.Adjustment(lower=0, upper=sys.maxint, step_incr=1,
                           page_incr=10))
        # set a default quantity value for new components
        if not self.model.quantity:
            self.quantity.set_value(1)

    #
    # BaseEditor
    #

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(
            self.model, ProductComponentEditor.proxy_widgets)

    def validate_confirm(self):
        return self.quantity.read() > 0

    #
    # Kiwi Callbacks
    #

    def on_quantity__validate(self, widget, value):
        if not value > 0:
            #FIXME: value < upper bound
            return ValidationError(_(u'The component quantity must be '
                                    'greater than zero.'))


class ProductEditor(SellableEditor):
    model_name = _('Product')
    model_type = Product
    help_section = 'product'
    ui_form_name = 'product'

    _model_created = False

    def __init__(self, conn, model=None, visual_mode=False):
        SellableEditor.__init__(self, conn, model, visual_mode=visual_mode)
        # This can't be done in setup_slaves() as we need to access
        # self.main_dialog when setting up the quality test slave
        self._add_extra_tabs()

    def get_taxes(self):
        query = (SellableTaxConstant.q.tax_type != int(TaxType.SERVICE))
        constants = SellableTaxConstant.select(query,
                                        connection=self.conn).orderBy('id')
        return [(c.description, c) for c in constants]

    def update_status_unavailable_label(self):
        text = ''
        if self.statuses_combo.read() == Sellable.STATUS_UNAVAILABLE:
            text = ("<b>%s</b>"
                    % api.escape(
                _("This status changes automatically when the\n"
                  "product is purchased or an inicial stock is added.")))

        self.status_unavailable_label.set_text(text)

    #
    # BaseEditor
    #

    def setup_slaves(self):
        from stoqlib.gui.slaves.productslave import ProductDetailsSlave
        details_slave = ProductDetailsSlave(self.conn, self.model.sellable,
                                            self.db_form, self.visual_mode)
        self.add_extra_tab(_(u'Details'), details_slave)

    def _add_extra_tabs(self):
        for tabname, tabslave in self.get_extra_tabs():
            self.add_extra_tab(tabname, tabslave)

    def get_extra_tabs(self):
        from stoqlib.gui.slaves.productslave import (ProductTaxSlave,
                                                     ProductSupplierSlave)
        extra_tabs = []

        suppliers_slave = ProductSupplierSlave(self.conn, self.model,
                                               self.visual_mode)
        extra_tabs.append((_(u'Suppliers'), suppliers_slave))

        tax_slave = ProductTaxSlave(self.conn, self.model, self.visual_mode)
        extra_tabs.append((_(u'Taxes'), tax_slave))
        return extra_tabs

    def setup_widgets(self):
        self.cost.set_digits(sysparam(self.conn).COST_PRECISION_DIGITS)
        self.consignment_yes_button.set_active(self.model.consignment)
        self.consignment_yes_button.set_sensitive(self._model_created)
        self.consignment_no_button.set_sensitive(self._model_created)
        self.update_status_unavailable_label()
        self.description.grab_focus()

    def create_model(self, conn):
        self._model_created = True
        tax_constant = sysparam(conn).DEFAULT_PRODUCT_TAX_CONSTANT
        sellable = Sellable(tax_constant=tax_constant,
                            connection=conn)
        sellable.unit = sysparam(self.conn).SUGGESTED_UNIT
        model = Product(connection=conn, sellable=sellable)
        Storable(product=model, connection=conn)
        return model

    def on_consignment_yes_button__toggled(self, widget):
        self.model.consignment = widget.get_active()


class ProductionProductEditor(ProductEditor):

    _cost_msg = _(u'Cost must be greater than the sum of the components.')

    def _is_valid_cost(self, cost):
        if hasattr(self, '_component_slave'):
            component_cost = self.component_slave.get_component_cost()
            return cost >= component_cost
        return True

    def create_model(self, conn):
        model = ProductEditor.create_model(self, conn)
        model.is_composed = True
        return model

    def get_extra_tabs(self):
        from stoqlib.gui.slaves.productslave import (ProductTaxSlave,
                                                     ProductComponentSlave,
                                                     ProductQualityTestSlave)
        self.component_slave = ProductComponentSlave(self.conn, self.model,
                                                      self.visual_mode)
        tax_slave = ProductTaxSlave(self.conn, self.model, self.visual_mode)
        quality_slave = ProductQualityTestSlave(self, self.conn, self.model,
                                                self.visual_mode)
        return [(_(u'Components'), self.component_slave),
                (_(u'Taxes'), tax_slave),
                (_(u'Quality'), quality_slave),
                ]

    def validate_confirm(self):
        if not self._is_valid_cost(self.cost.read()):
            info(self._cost_msg)
            return False
        return True

    def on_cost__validate(self, widget, value):
        if value <= 0:
            return ValidationError(_(u'Cost cannot be zero or negative.'))
        if not self._is_valid_cost(value):
            return ValidationError(self._cost_msg)


class ProductStockEditor(BaseEditor):
    model_name = _('Product')
    model_type = Product
    gladefile = 'HolderTemplate'

    def setup_slaves(self):
        from stoqlib.gui.slaves.productslave import ProductDetailsSlave
        details_slave = ProductDetailsSlave(self.conn, self.model.sellable)
        details_slave.hide_stock_details()
        self.attach_slave('place_holder', details_slave)


class ProductManufacturerEditor(BaseEditor):
    model_name = _('Manufacturer')
    model_type = ProductManufacturer
    confirm_widgets = ['name']

    fields = dict(
        name=TextField(_('Name'), proxy=True, mandatory=True),
        )

    def create_model(self, trans):
        return ProductManufacturer(name='', connection=trans)

    def setup_proxies(self):
        self.name.grab_focus()

    #
    # Kiwi Callbacks
    #

    def on_name__validate(self, widget, new_name):
        if not new_name:
            return ValidationError(
                _("The manufacturer should have a name."))
        if self.model.check_unique_value_exists('name', new_name):
            return ValidationError(
                _("The manufacturer '%s' already exists.") % new_name)


def test_product():  # pragma nocover
    ec = api.prepare_test()
    product = ec.create_product()
    run_dialog(ProductEditor,
               parent=None, conn=ec.trans, model=product)


if __name__ == '__main__':  # pragma nocover
    test_product()
