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

from kiwi.datatypes import ValidationError, currency
from kiwi.ui.widgets.list import Column, SummaryLabel

from stoqdrivers.enum import TaxType


from stoqlib.domain.interfaces import IStorable
from stoqlib.domain.person import PersonAdaptToSupplier
from stoqlib.domain.product import (ProductSupplierInfo, Product,
                                    ProductComponent,
                                    ProductQualityTest)
from stoqlib.domain.sellable import (Sellable,
                                     SellableTaxConstant)
from stoqlib.domain.views import ProductFullStockView
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.lists import ModelListSlave
from stoqlib.gui.editors.baseeditor import (BaseEditor, BaseEditorSlave,
                                            BaseRelationshipEditorSlave)
from stoqlib.gui.editors.sellableeditor import SellableEditor
from stoqlib.gui.slaves.productslave import (ProductDetailsSlave,
                                             ProductTaxSlave)
from stoqlib.lib.message import info, yesno
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.formatters import get_formatted_cost
from stoqlib.lib.pluginmanager import get_plugin_manager

_ = stoqlib_gettext


#
# Slaves
#

class _TemporaryProductComponent(object):
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
        return self.production_cost * self.quantity

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


class ProductComponentSlave(BaseEditorSlave):
    gladefile = 'ProductComponentSlave'
    model_type = _TemporaryProductComponent

    def __init__(self, conn, product=None):
        self._product = product
        self._remove_component_list = []
        BaseEditorSlave.__init__(self, conn, model=None)
        self._setup_widgets()

    def _get_columns(self):
        return [Column('id', title=_(u'Code'), data_type=int,
                        expander=True, sorted=True),
                Column('quantity', title=_(u'Quantity'),
                        data_type=Decimal),
                Column('unit', title=_(u'Unit'), data_type=str),
                Column('description', title=_(u'Description'),
                        data_type=str, expand=True),
                Column('category', title=_(u'Category'), data_type=str),
                # Translators: Ref. is for Reference (as in design reference)
                Column('design_reference', title=_(u'Ref.'), data_type=str),
                Column('production_cost', title=_(u'Production Cost'),
                        format_func=get_formatted_cost, data_type=currency),
                Column('total_production_cost', title=_(u'Total'),
                        format_func=get_formatted_cost, data_type=currency),
                ]

    def _setup_widgets(self):
        self.component_combo.prefill(list(self._get_products()))

        self.component_tree.set_columns(self._get_columns())
        self._populate_component_tree()
        self.component_label = SummaryLabel(klist=self.component_tree,
                                            column='total_production_cost',
                                            label='<b>%s</b>' % _(u'Total:'),
                                            value_format='<b>%s</b>')
        self.component_label.show()
        self.component_tree_vbox.pack_start(self.component_label, False)
        self._update_widgets()

    def _get_products(self, sort_by_name=True):
        # FIXME: This is a kind of workaround until we have the
        # SQLCompletion funcionality, then we will not need to sort the
        # data.
        if sort_by_name:
            attr = 'description'
        else:
            attr = 'sellable_category.description'

        products = []
        for product_view in ProductFullStockView\
                .select(connection=self.conn).orderBy(attr):
            if product_view.product is self._product:
                continue

            description = product_view.get_product_and_category_description()
            products.append((description, product_view.product))

        return products

    def _update_widgets(self):
        has_selected = self.component_combo.read() is not None
        self.add_button.set_sensitive(has_selected)
        has_selected = self.component_tree.get_selected() is not None
        self.edit_button.set_sensitive(has_selected)
        self.remove_button.set_sensitive(has_selected)

        # FIXME: This is wrong. Summary label already calculates the total. We
        # are duplicating this.
        value = self.get_component_cost()
        self.component_label.set_value(get_formatted_cost(value))

    def _populate_component_tree(self):
        self._add_to_component_tree()

    def _get_components(self, product):
        for component in ProductComponent.selectBy(product=product,
                                                   connection=self.conn):
            yield _TemporaryProductComponent(product=component.product,
                                             component=component.component,
                                             quantity=component.quantity,
                                             design_reference=component.design_reference)

    def _add_to_component_tree(self, component=None):
        parent = None
        if component is None:
            # load all components that already exists
            subcomponents = self._get_components(self._product)
        else:
            if component not in self.component_tree:
                self.component_tree.append(None, component)
            subcomponents = self._get_components(component.component)
            parent = component

        for subcomponent in subcomponents:
            self.component_tree.append(parent, subcomponent)
            # recursively add the children
            self._add_to_component_tree(subcomponent)

    def _can_add_component(self, component):
        if component.component.is_composed_by(self._product):
            return False
        return True

    def _run_product_component_dialog(self, product_component=None):
        update = True
        if product_component is None:
            update = False
            component = self.component_combo.get_selected_data()
            product_component = _TemporaryProductComponent(
                product=self._product, component=component)
            # If we try to add a component which is already in tree,
            # just edit it
            for component in self.component_tree:
                if component.component == product_component.component:
                    update = True
                    product_component = component
                    break

        if not self._can_add_component(product_component):
            product_desc = self._product.sellable.get_description()
            component_desc = product_component.description
            info(_(u'You can not add this product as component, since '
                    '%s is composed by %s' % (component_desc, product_desc)))
            return

        model = run_dialog(ProductComponentEditor, self, self.conn,
                           product_component)
        if not model:
            return

        if update:
            self.component_tree.update(model)
        else:
            self._add_to_component_tree(model)
        self._update_widgets()

    def _edit_component(self):
        # Only allow edit the root components, since its the component
        # that really belongs to the current product
        selected = self.component_tree.get_selected()
        root = self.component_tree.get_root(selected)
        self._run_product_component_dialog(root)

    def _totally_remove_component(self, component):
        descendants = self.component_tree.get_descendants(component)
        for descendant in descendants:
            # we can not remove an item twice
            if descendant not in self.component_tree:
                continue
            else:
                self._totally_remove_component(descendant)
        self.component_tree.remove(component)

    def _remove_component(self, component):
        # Only allow remove the root components, since its the component
        # that really belongs to the current product
        root_component = self.component_tree.get_root(component)

        msg = _("This will remove the component \"%s\". Are you sure?" %
                root_component.description)
        if not yesno(msg, gtk.RESPONSE_NO,
                     _("Remove component"),
                     _("Keep component")):
            return

        self._remove_component_list.append(root_component)
        self._totally_remove_component(root_component)
        self._update_widgets()

    #
    # BaseEditorSlave
    #

    def setup_proxies(self):
        self.proxy = self.add_proxy(self._product, ['production_time'])
        # FIXME:
        self.production_time.set_value(self._product.production_time)

    def create_model(self, conn):
        return _TemporaryProductComponent(product=self._product)

    def on_confirm(self):
        for component in self._remove_component_list:
            component.delete_product_component(self.conn)

        for component in self.component_tree:
            component.add_or_update_product_component(self.conn)

        return self.model

    def validate_confirm(self):
        return len(self.component_tree) > 0

    def get_component_cost(self):
        value = 0
        for component in self.component_tree:
            if self.component_tree.get_parent(component):
                continue
            value += component.get_total_production_cost()
        return value

    #
    # Kiwi Callbacks
    #

    def on_component_combo__content_changed(self, widget):
        self._update_widgets()

    def on_component_tree__selection_changed(self, widget, value):
        self._update_widgets()

    def on_component_tree__row_activated(self, widget, selected):
        self._edit_component()

    def on_component_tree__row_expanded(self, widget, value):
        self._update_widgets()

    def on_add_button__clicked(self, widget):
        self._run_product_component_dialog()

    def on_edit_button__clicked(self, widget):
        self._edit_component()

    def on_remove_button__clicked(self, widget):
        selected = self.component_tree.get_selected()
        self._remove_component(selected)

    def on_sort_components_check__toggled(self, widget):
        sort_by_name = not widget.get_active()
        self.component_combo.prefill(
            self._get_products(sort_by_name=sort_by_name))
        self.component_combo.select_item_by_position(0)

#
#   Quality Test Editor & Slave
#


class QualityTestEditor(BaseEditor):
    model_name = _('Quality Test')
    model_type = ProductQualityTest
    gladefile = 'QualityTestEditor'

    proxy_widgets = ['description', 'test_type']
    confirm_widgets = ['description']

    def __init__(self, conn, model, product):
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
        return self.model

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


class ProductQualityTestSlave(ModelListSlave):
    model_type = ProductQualityTest

    def __init__(self, conn, product):
        self._product = product
        ModelListSlave.__init__(self)
        self.set_reuse_transaction(self._product.get_connection())
        self.set_editor_class(QualityTestEditor)
        self.set_model_type(self.model_type)

    #
    #   ListSlave Implementation
    #

    def get_columns(self):
        return [Column('description', title=_(u'Description'),
                        data_type=str, expand=True),
                Column('type_str', title=_(u'Type'), data_type=str),
                Column('success_value_str', title=_(u'Success Value'), data_type=str),
                ]

    def populate(self):
        return self._product.quality_tests

    def run_dialog(self, dialog_class, *args, **kwargs):
        kwargs['product'] = self._product
        return ModelListSlave.run_dialog(self, dialog_class, *args, **kwargs)


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


class ProductSupplierSlave(BaseRelationshipEditorSlave):
    """A slave for changing the suppliers for a product.
    """
    target_name = _(u'Supplier')
    editor = ProductSupplierEditor
    model_type = ProductSupplierInfo

    def __init__(self, conn, product):
        self._product = product
        BaseRelationshipEditorSlave.__init__(self, conn)

        suggested = sysparam(conn).SUGGESTED_SUPPLIER
        if suggested is not None:
            self.target_combo.select(suggested)

    def get_targets(self):
        suppliers = PersonAdaptToSupplier.get_active_suppliers(self.conn)
        return [(s.person.name, s) for s in suppliers]

    def get_relations(self):
        return self._product.get_suppliers_info()

    def get_columns(self):
        return [Column('name', title=_(u'Supplier'),
                        data_type=str, expand=True, sorted=True),
                Column('lead_time_str', title=_(u'Lead time'), data_type=str),
                Column('minimum_purchase', title=_(u'Minimum Purchase'),
                        data_type=Decimal),
                Column('base_cost', title=_(u'Cost'), data_type=currency,
                        format_func=get_formatted_cost)]

    def create_model(self):
        product = self._product
        supplier = self.target_combo.get_selected_data()

        if product.is_supplied_by(supplier):
            product_desc = self._product.sellable.get_description()
            info(_(u'%s is already supplied by %s' % (product_desc,
                                                      supplier.person.name)))
            return

        model = ProductSupplierInfo(product=product,
                                    supplier=supplier,
                                    connection=self.conn)
        model.base_cost = product.sellable.cost
        return model


#
# Editors
#


class ProductComponentEditor(BaseEditor):
    gladefile = 'ProductComponentEditor'
    proxy_widgets = ['quantity', 'design_reference']
    title = _(u'Product Component')
    model_type = _TemporaryProductComponent

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

    def get_taxes(self):
        constants = SellableTaxConstant.select(connection=self.conn)
        return [(c.description, c) for c in constants
                                   if c.tax_type != TaxType.SERVICE]

    def update_status_unavailable_label(self):
        text = ''
        if self.statuses_combo.read() == Sellable.STATUS_UNAVAILABLE:
            text = ("<b>%s</b>"
                    % _("This status changes automatically when the\n"
                        "product is purchased or an inicial stock is added."))

        self.status_unavailable_label.set_text(text)

    def _get_plugin_tabs(self):
        manager = get_plugin_manager()
        tab_list = []

        for plugin_name in manager.active_plugins_names:
            plugin = manager.get_plugin(plugin_name)
            if plugin.has_product_slave:
                slave_class = plugin.get_product_slave_class()
                plugin_product_slave = slave_class(self.conn, self.model)
                tab_list.append((slave_class.title, plugin_product_slave))

        return tab_list

    #
    # BaseEditor
    #

    def setup_slaves(self):
        details_slave = ProductDetailsSlave(self.conn, self.model.sellable,
                                            self.db_form)
        self.add_extra_tab(_(u'Details'), details_slave)

        for tabname, tabslave in self.get_extra_tabs():
            self.add_extra_tab(tabname, tabslave)

    def get_extra_tabs(self):
        extra_tabs = []
        extra_tabs.extend(self._get_plugin_tabs())

        suppliers_slave = ProductSupplierSlave(self.conn, self.model)
        extra_tabs.append((_(u'Suppliers'), suppliers_slave))

        tax_slave = ProductTaxSlave(self.conn, self.model)
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
        model.addFacet(IStorable, connection=conn)
        return model

    def on_consignment_yes_button__toggled(self, widget):
        self.model.consignment = widget.get_active()


class ProductionProductEditor(ProductEditor):

    _cost_msg = _(u'Cost must be greater than the sum of the components.')

    def _is_valid_cost(self, cost):
        if hasattr(self, '_component_slave'):
            component_cost = self._component_slave.get_component_cost()
            return cost >= component_cost
        return True

    def create_model(self, conn):
        model = ProductEditor.create_model(self, conn)
        model.is_composed = True
        return model

    def get_extra_tabs(self):
        self._component_slave = ProductComponentSlave(self.conn, self.model)
        tax_slave = ProductTaxSlave(self.conn, self.model)
        quality_slave = ProductQualityTestSlave(self.conn, self.model)
        return [(_(u'Components'), self._component_slave),
                (_(u'Taxes'), tax_slave),
                (_(u'Quality'), quality_slave),
                ]

    def validate_confirm(self):
        if not self._is_valid_cost(self.cost.read()):
            info(self._cost_msg)
            return False

        confirm = self._component_slave.validate_confirm()
        if not confirm:
            info(_(u'There is no component in this product.'))
        return confirm

    def on_confirm(self):
        self._component_slave.on_confirm()
        return self.model

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
        details_slave = ProductDetailsSlave(self.conn, self.model.sellable)
        details_slave.hide_stock_details()
        self.attach_slave('place_holder', details_slave)
