# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2009 Async Open Source <http://www.async.com.br>
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
""" Slaves for products """

from decimal import Decimal

import gtk
from kiwi.currency import currency
from kiwi.datatypes import ValidationError
from kiwi.enums import ListType
from kiwi.ui.objectlist import Column, SummaryLabel

from stoqlib.api import api
from stoqlib.domain.person import Supplier
from stoqlib.domain.product import (ProductSupplierInfo, ProductComponent,
                                    ProductQualityTest, Product,
                                    ProductManufacturer)
from stoqlib.domain.production import ProductionOrderProducingView
from stoqlib.domain.taxes import ProductTaxTemplate
from stoqlib.domain.views import ProductFullStockView
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.lists import ModelListSlave
from stoqlib.gui.editors.baseeditor import (BaseEditorSlave,
                                            BaseRelationshipEditorSlave)
from stoqlib.gui.editors.producteditor import (TemporaryProductComponent,
                                               ProductComponentEditor,
                                               QualityTestEditor,
                                               ProductSupplierEditor)
from stoqlib.lib.defaults import quantize, MAX_INT
from stoqlib.lib.formatters import get_formatted_cost
from stoqlib.lib.message import info, yesno, warning
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class ProductInformationSlave(BaseEditorSlave):
    gladefile = 'ProductInformationSlave'
    model_type = Product
    proxy_widgets = ['location', 'part_number', 'manufacturer', 'width',
                     'height', 'depth', 'weight', 'ncm', 'ex_tipi', 'genero',
                     'product_model', 'brand', 'family']
    storable_widgets = ['minimum_quantity', 'maximum_quantity']

    def __init__(self, store, model, db_form=None, visual_mode=False):
        self.db_form = db_form
        BaseEditorSlave.__init__(self, store, model, visual_mode)

    def _setup_unit_labels(self):
        unit = self.model.sellable.unit
        if unit is None:
            unit_desc = _(u'Unit(s)')
        else:
            unit_desc = unit.description

        for label in [self.min_unit, self.max_unit]:
            label.set_text(unit_desc)

    def _fill_manufacturers(self):
        options = self.store.find(ProductManufacturer)
        self.manufacturer.prefill(api.for_combo(options, empty=''))

    def _setup_widgets(self):
        self._setup_unit_labels()
        self._fill_manufacturers()

        for widget in [self.minimum_quantity, self.maximum_quantity,
                       self.width, self.height, self.depth, self.weight]:
            widget.set_adjustment(
                gtk.Adjustment(lower=0, upper=MAX_INT, step_incr=1))

        if not self.db_form:
            return
        self.db_form.update_widget(self.height, other=self.height_lbl)
        self.db_form.update_widget(self.width, other=self.width_lbl)
        self.db_form.update_widget(self.depth, other=self.depth_lbl)
        self.db_form.update_widget(self.location, other=self.location_lbl)
        self.db_form.update_widget(self.weight, other=[self.weight_lbl,
                                                       self.kg_lbl])
        self.db_form.update_widget(self.manufacturer,
                                   other=self.manufacturer_lbl)
        self.db_form.update_widget(self.part_number,
                                   other=self.part_number_lbl)
        # Stock details
        self.db_form.update_widget(self.minimum_quantity,
                                   other=[self.min_lbl,
                                          self.min_unit])
        self.db_form.update_widget(self.maximum_quantity,
                                   other=[self.max_lbl,
                                          self.max_unit])
        if (not self.minimum_quantity.get_visible() and
            not self.maximum_quantity.get_visible() and
            not self.location.get_visible()):
            self.storable_frame.hide()

        # Mercosul
        self.db_form.update_widget(self.ncm, other=self.ncm_lbl)
        self.db_form.update_widget(self.ex_tipi, other=self.ex_tipi_lbl)
        self.db_form.update_widget(self.genero, other=self.genero_lbl)

        if (not self.ncm.get_visible() and
            not self.ex_tipi.get_visible() and
            not self.genero.get_visible()):
            self.nfe_frame.hide()

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(
            self.model, ProductInformationSlave.proxy_widgets)

        storable = self.model.storable
        if storable is not None:
            self.storable_proxy = self.add_proxy(
                storable, ProductInformationSlave.storable_widgets)
        else:
            self.minimum_quantity.set_sensitive(False)
            self.maximum_quantity.set_sensitive(False)

    def update_visual_mode(self):
        self.minimum_quantity.set_sensitive(False)
        self.maximum_quantity.set_sensitive(False)

    def hide_stock_details(self):
        self.min_lbl.hide()
        self.max_lbl.hide()
        self.min_hbox.hide()
        self.max_hbox.hide()

        self.part_number_lbl.hide()
        self.part_number.hide()
        self.manufacturer_lbl.hide()
        self.manufacturer.hide()
        self.model_lbl.hide()
        self.product_model.hide()
        self.brand_lbl.hide()
        self.brand.hide()
        self.family_lbl.hide()
        self.family.hide()

    #
    # Kiwi Callbacks
    #

    def _positive_validator(self, value):
        if not value:
            return
        if value and value < 0:
            return ValidationError(_(u'The value must be positive.'))

    def on_width__validate(self, widget, value):
        return self._positive_validator(value)

    def on_height__validate(self, widget, value):
        return self._positive_validator(value)

    def on_depth__validate(self, widget, value):
        return self._positive_validator(value)

    def on_weight__validate(self, widget, value):
        return self._positive_validator(value)

    def on_ncm__validate(self, widget, value):
        if len(value) not in (0, 8):
            return ValidationError(_(u'NCM must have 8 digits.'))

    def on_ex_tipi__validate(self, widget, value):
        if len(value) not in (0, 2, 3):
            return ValidationError(_(u'EX TIPI must have 2 or 3 digits.'))

    def on_genero__validate(self, widget, value):
        if len(value) not in (0, 2):
            return ValidationError(_(u'Gênero must have 2 digits.'))

    def on_minimum_quantity__validate(self, widget, value):
        if value and value < 0:
            return ValidationError(_(u'Minimum value must be a positive value.'))

        maximum = self.maximum_quantity.read()
        if maximum and value > maximum:
            return ValidationError(_(u'Minimum must be lower than the '
                                     'maximum value.'))

    def on_maximum_quantity__validate(self, widget, value):
        if not value:
            return
        if value and value < 0:
            return ValidationError(_(u'Maximum value must be a positive value.'))

        minimum = self.minimum_quantity.read()
        if minimum and minimum > value:
            return ValidationError(_(u'Maximum must be greater than the '
                                     'minimum value.'))


class ProductTaxSlave(BaseEditorSlave):
    gladefile = 'ProductTaxSlave'
    model_type = Product
    proxy_widgets = ['icms_template', 'ipi_template']

    def update_visual_mode(self):
        self.icms_template.set_sensitive(False)
        self.ipi_template.set_sensitive(False)

    def _fill_combo(self, combo, type):
        types = [(None, None)]
        types.extend([(t.name, t.get_tax_model()) for t in
                      self.store.find(ProductTaxTemplate, tax_type=type)])
        combo.prefill(types)

    def _setup_widgets(self):
        self._fill_combo(self.icms_template, ProductTaxTemplate.TYPE_ICMS)
        self._fill_combo(self.ipi_template, ProductTaxTemplate.TYPE_IPI)

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)


class ProductComponentSlave(BaseEditorSlave):
    gladefile = 'ProductComponentSlave'
    model_type = TemporaryProductComponent
    proxy_widgets = ['production_time']

    def __init__(self, store, product=None, visual_mode=False):
        self._product = product
        self._remove_component_list = []
        BaseEditorSlave.__init__(self, store, model=None, visual_mode=visual_mode)
        self._setup_widgets()

    def _get_columns(self):
        return [Column('code', title=_(u'Code'), data_type=int,
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
        component_list = list(self._get_products())
        if component_list:
            self.component_combo.prefill(component_list)
        else:
            self.sort_components_check.set_sensitive(False)

        self.component_tree.set_columns(self._get_columns())
        self._populate_component_tree()
        self.component_label = SummaryLabel(
            klist=self.component_tree,
            column='total_production_cost',
            label='<b>%s</b>' % api.escape(_(u'Total:')),
            value_format='<b>%s</b>')
        self.component_label.show()
        self.component_tree_vbox.pack_start(self.component_label, False)
        self.info_label.set_bold(True)
        self._update_widgets()
        if self.visual_mode:
            self.component_combo.set_sensitive(False)
            self.add_button.set_sensitive(False)
            self.sort_components_check.set_sensitive(False)

    def _get_products(self, sort_by_name=True):
        # FIXME: This is a kind of workaround until we have the
        # SQLCompletion funcionality, then we will not need to sort the
        # data.
        if sort_by_name:
            attr = ProductFullStockView.description
        else:
            attr = ProductFullStockView.category_description

        products = []
        for product_view in self.store.find(ProductFullStockView).order_by(attr):
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

        if not self._validate_components():
            self.component_combo.set_sensitive(False)
            self.add_button.set_sensitive(False)
            self.edit_button.set_sensitive(False)
            self.remove_button.set_sensitive(False)
            self.info_label.set_text(_(u"This product is being produced. "
                                       "Can't change components."))

    def _populate_component_tree(self):
        self._add_to_component_tree()

    def _get_components(self, product):
        for component in self.store.find(ProductComponent, product=product):
            yield TemporaryProductComponent(product=component.product,
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
            product_component = TemporaryProductComponent(
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

        toplevel = self.get_toplevel().get_toplevel()
        # We cant use savepoint here, since product_component
        # is not an ORM object.
        model = run_dialog(ProductComponentEditor, toplevel, self.store,
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

        msg = _("This will remove the component \"%s\". Are you sure?") % (
            root_component.description)
        if not yesno(msg, gtk.RESPONSE_NO,
                     _("Remove component"),
                     _("Keep component")):
            return

        self._remove_component_list.append(root_component)
        self._totally_remove_component(root_component)
        self._update_widgets()

    def _validate_components(self):
        return not ProductionOrderProducingView.is_product_being_produced(
            self.model.product)

    #
    # BaseEditorSlave
    #

    def setup_proxies(self):
        self.proxy = self.add_proxy(self._product, self.proxy_widgets)

    def create_model(self, store):
        return TemporaryProductComponent(product=self._product)

    def on_confirm(self):
        for component in self._remove_component_list:
            component.delete_product_component(self.store)

        for component in self.component_tree:
            component.add_or_update_product_component(self.store)

    def validate_confirm(self):
        if not len(self.component_tree) > 0:
            info(_(u'There is no component in this product.'))
            return False
        return True

    def get_component_cost(self):
        value = Decimal('0')
        for component in self.component_tree:
            if self.component_tree.get_parent(component):
                continue
            value += component.get_total_production_cost()
        return quantize(value)

    #
    # Kiwi Callbacks
    #

    def on_component_combo__content_changed(self, widget):
        self._update_widgets()

    def on_component_tree__selection_changed(self, widget, value):
        if self.visual_mode:
            return
        self._update_widgets()

    def on_component_tree__row_activated(self, widget, selected):
        if self.visual_mode:
            return

        if not self._validate_components():
            return

        self._edit_component()

    def on_component_tree__row_expanded(self, widget, value):
        if self.visual_mode:
            return
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


class ProductQualityTestSlave(ModelListSlave):
    model_type = ProductQualityTest
    editor_class = QualityTestEditor
    columns = [
        Column('description', title=_(u'Description'),
               data_type=str, expand=True),
        Column('type_str', title=_(u'Type'), data_type=str),
        Column('success_value_str', title=_(u'Success Value'), data_type=str),
    ]

    def __init__(self, parent, store, product,
                 visual_mode=False, reuse_store=True):
        self._product = product
        ModelListSlave.__init__(self, parent, store=store,
                                reuse_store=reuse_store)
        if visual_mode:
            self.set_list_type(ListType.READONLY)

        self.refresh()

    #
    #   ListSlave Implementation
    #

    def populate(self):
        return self._product.quality_tests

    def run_editor(self, store, model):
        return self.run_dialog(self.editor_class, store=store, model=model,
                               product=self._product)

    def remove_item(self, item):
        # If the test was used before in a production, it cannot be
        # removed
        if not item.can_remove():
            warning(_(u'You can not remove this test, since it\'s already '
                      'been used.'))
            return False

        return ModelListSlave.remove_item(self, item)


class ProductSupplierSlave(BaseRelationshipEditorSlave):
    """A slave for changing the suppliers for a product.
    """
    target_name = _(u'Supplier')
    editor = ProductSupplierEditor
    model_type = ProductSupplierInfo

    def __init__(self, store, product, visual_mode=False):
        self._product = product
        BaseRelationshipEditorSlave.__init__(self, store, visual_mode=visual_mode)

        suggested = sysparam.get_object(store, 'SUGGESTED_SUPPLIER')
        if suggested is not None:
            self.target_combo.select(suggested)

    def get_targets(self):
        suppliers = Supplier.get_active_suppliers(self.store)
        return api.for_person_combo(suppliers)

    def get_relations(self):
        return self._product.get_suppliers_info()

    def get_columns(self):
        return [Column('name', title=_(u'Supplier'),
                       data_type=str, expand=True, sorted=True),
                Column('supplier_code', title=_(u'Product Code'),
                       data_type=str),
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
            info(_(u'%s is already supplied by %s') % (product_desc,
                                                       supplier.person.name))
            return

        model = ProductSupplierInfo(product=product,
                                    supplier=supplier,
                                    store=self.store)
        model.base_cost = product.sellable.cost
        return model
