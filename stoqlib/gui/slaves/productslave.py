# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2015 Async Open Source <http://www.async.com.br>
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

import collections
from decimal import Decimal

import gtk
from kiwi.currency import currency
from kiwi.datatypes import ValidationError
from kiwi.enums import ListType
from kiwi.ui.objectlist import Column, SummaryLabel
from kiwi.ui.widgets.combo import ProxyComboBox
from storm.expr import Eq, And

from stoqlib.api import api
from stoqlib.domain.person import Supplier
from stoqlib.domain.product import (ProductSupplierInfo, ProductComponent,
                                    ProductQualityTest, Product,
                                    ProductManufacturer, Storable, GridGroup)
from stoqlib.domain.production import ProductionOrderProducingView
from stoqlib.domain.taxes import ProductTaxTemplate
from stoqlib.domain.views import ProductFullStockView
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.lists import ModelListSlave
from stoqlib.gui.editors.baseeditor import (BaseEditorSlave,
                                            BaseRelationshipEditorSlave)
from stoqlib.gui.editors.grideditor import GridAttributeEditor
from stoqlib.gui.editors.producteditor import (TemporaryProductComponent,
                                               ProductComponentEditor,
                                               QualityTestEditor,
                                               ProductSupplierEditor,
                                               ProductPackageComponentEditor)
from stoqlib.gui.fields import GridGroupField
from stoqlib.lib.decorators import cached_property
from stoqlib.lib.defaults import quantize, MAX_INT
from stoqlib.lib.formatters import get_formatted_cost
from stoqlib.lib.message import info, yesno, warning
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class ProductAttributeSlave(BaseEditorSlave):
    gladefile = 'ProductAttributeSlave'
    model_type = object

    @cached_property()
    def fields(self):
        return collections.OrderedDict(
            attribute_group=GridGroupField(_('Attribute group'), mandatory=True),
        )

    def __init__(self, store, model=None, visual_mode=False, edit_mode=None):
        self._widgets = {}
        self._create_attribute_box = None
        super(ProductAttributeSlave, self).__init__(
            store, model=model, visual_mode=visual_mode, edit_mode=edit_mode)

    def _setup_widgets(self):
        group = GridGroup.get_active_groups(self.store)
        self.attribute_group.prefill(
            api.for_combo(group, attr='description', empty=_("Select a group")))

    def _add_attribute(self, attr):
        if not attr.is_active:
            # Do not attach the widget if the attribute is inactive
            return
        widget = gtk.CheckButton(label=attr.description)
        widget.set_sensitive(attr.has_active_options())
        self.main_box.pack_start(widget, expand=False)
        widget.show()
        self._widgets[widget] = attr

    def setup_proxies(self):
        self._setup_widgets()

    def get_selected_attributes(self):
        active_check_box = []
        for widget, value in self._widgets.iteritems():
            if widget.get_active():
                active_check_box.append(value)
        return active_check_box

    def _refresh_attributes(self):
        if self._create_attribute_box is not None:
            self.main_box.remove(self._create_attribute_box)
            self._create_attribute_box.destroy()

        for check_box in self._widgets.keys():
            self.main_box.remove(check_box)
            check_box.destroy()

        # After we destroy the check buttons we should reset the list of widgets
        self._widgets = {}
        group = self.attribute_group.get_selected()
        if not group:
            return

        for attr in group.attributes:
            self._add_attribute(attr)

        self._create_attribute_box = gtk.HBox()
        btn = gtk.Button(_("Add a new attribute"))
        btn.connect('clicked', self._on_add_new_attribute_btn__clicked)
        self._create_attribute_box.pack_start(btn, expand=False)
        self._create_attribute_box.pack_start(gtk.Label(), expand=True)
        self._create_attribute_box.show_all()
        self.main_box.pack_start(self._create_attribute_box, expand=False)

    #
    # Kiwi Callbacks
    #

    def on_attribute_group__content_changed(self, widget):
        self._refresh_attributes()

    def _on_add_new_attribute_btn__clicked(self, btn):
        group = self.attribute_group.get_selected()
        with api.new_store() as store:
            retval = run_dialog(GridAttributeEditor,
                                parent=None, store=store,
                                group=store.fetch(group))

        if retval:
            self._refresh_attributes()


class ProductGridSlave(BaseEditorSlave):
    gladefile = 'ProductGridSlave'
    model_type = Product

    def __init__(self, store, model, visual_mode=False):
        self._attr_list = list(model.attributes)
        self._option_list = {}
        self._widgets = {}
        BaseEditorSlave.__init__(self, store, model, visual_mode)

    def _setup_widgets(self):
        self.attr_table.resize(len(self._attr_list), 2)
        for pos, attribute in enumerate(self._attr_list):
            self._add_options(attribute, pos)
        self.add_product_button.set_sensitive(False)
        self.product_list.set_columns(self._get_columns())
        self.product_list.add_list(self.model.children)

    def _add_options(self, attr, pos):
        combo = ProxyComboBox()
        label = gtk.Label(attr.attribute.description)

        # This dictionary is populated with the purpose of tests
        self._widgets[attr.attribute.description] = combo
        self.attr_table.attach(label, 0, 1, pos, pos + 1, 0, 0, 0, 0)
        self.attr_table.attach(combo, 1, 2, pos, pos + 1, 0, gtk.EXPAND | gtk.FILL, 0, 0)
        self.attr_table.show_all()
        self._fill_options(combo, attr)
        combo.connect('changed', self._on_combo_selection__changed)

    def _fill_options(self, widget, attr):
        options = attr.options.find(is_active=True)
        widget.prefill(api.for_combo(options, empty=_("Select an option"),
                       sorted=False))

    def _get_columns(self):
        return [Column('description', title=_('Description'), data_type=str,
                       expand=True, sorted=True),
                Column('sellable.code', title=_('Code'), data_type=str)]

    def can_add(self):
        selected_option = self._option_list.values()
        # In order to add a new product...
        # ...The user should select all options...
        if len(selected_option) != len(self._attr_list):
            return False

        # ...and he should have selected valid options
        if not all(selected_option):
            return False

        # Also, make sure a product with those options doesn't exists.
        child_exists = self.model.child_exists(selected_option)
        if child_exists:
            return False

        return True

    def setup_proxies(self):
        self._setup_widgets()

    #
    # Kiwi Callbacks
    #

    def _on_combo_selection__changed(self, widget):
        self._option_list[widget] = widget.get_selected()
        self.add_product_button.set_sensitive(self.can_add())

    def on_add_product_button__clicked(self, widget):
        if not self.model.description:
            warning(_('You should fill the description first'))
            return False
        self.model.add_grid_child(self._option_list.values())
        self.product_list.add_list(self.model.children)
        self.add_product_button.set_sensitive(False)


class ProductInformationSlave(BaseEditorSlave):
    gladefile = 'ProductInformationSlave'
    model_type = Product
    proxy_widgets = ['location', 'part_number', 'manufacturer', 'width',
                     'height', 'depth', 'weight', 'ncm', 'ex_tipi', 'genero',
                     'product_model', 'brand', 'family', 'internal_use']
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

        if self.model.parent is not None:
            self._disable_child_widgets()

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

    def _disable_child_widgets(self):
        widgets = [self.manufacturer, self.brand, self.family, self.width,
                   self.height, self.weight, self.depth, self.ncm, self.ex_tipi,
                   self.genero]

        for widget in widgets:
            widget.set_property('sensitive', False)

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
    proxy_widgets = ['icms_template', 'ipi_template', 'pis_template',
                     'cofins_template']

    def update_visual_mode(self):
        self.icms_template.set_sensitive(False)
        self.ipi_template.set_sensitive(False)
        self.pis_template.set_sensitive(False)
        self.cofins_template.set_sensitive(False)

    def _fill_combo(self, combo, type):
        types = [(None, None)]
        types.extend([(t.name, t.get_tax_model()) for t in
                      self.store.find(ProductTaxTemplate, tax_type=type)])
        combo.prefill(types)

    def _setup_widgets(self):
        self._fill_combo(self.icms_template, ProductTaxTemplate.TYPE_ICMS)
        self._fill_combo(self.ipi_template, ProductTaxTemplate.TYPE_IPI)
        self._fill_combo(self.pis_template, ProductTaxTemplate.TYPE_PIS)
        self._fill_combo(self.cofins_template, ProductTaxTemplate.TYPE_COFINS)

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)
        if self.model.parent is not None:
            self._disable_child_widgets()

    def _disable_child_widgets(self):
        self.icms_template.set_property('sensitive', False)
        self.ipi_template.set_property('sensitive', False)
        self.pis_template.set_property('sensitive', False)
        self.cofins_template.set_property('sensitive', False)


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
        is_package = self.model.product.is_package
        component_list = list(self._get_products(additional_query=is_package))
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

    def _get_products(self, sort_by_name=True, additional_query=False):
        # FIXME: This is a kind of workaround until we have the
        # SQLCompletion funcionality, then we will not need to sort the
        # data.
        if sort_by_name:
            attr = ProductFullStockView.description
        else:
            attr = ProductFullStockView.category_description

        products = []
        query = Eq(Product.is_grid, False)
        if additional_query:
            # XXX For now, we are not allowing package_product to have another
            # package_product or batch_product as component
            query = And(query, Eq(Storable.is_batch, False))
        for product_view in self.store.find(ProductFullStockView, query).order_by(attr):
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
            yield TemporaryProductComponent(
                self.store,
                product=component.product,
                component=component.component,
                quantity=component.quantity,
                design_reference=component.design_reference,
                price=component.price)

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
                self.store,
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
        if self.model.product.is_package:
            model = run_dialog(ProductPackageComponentEditor, toplevel,
                               self.store, product_component)
        else:
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
        return TemporaryProductComponent(self.store, product=self._product)

    def on_confirm(self):
        for component in self._remove_component_list:
            component.delete_product_component(self.store)

        for component in self.component_tree:
            component.add_or_update_product_component(self.store)
        self._product.update_sellable_price()

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
        is_package = self.model.product.is_package
        self.component_combo.prefill(
            self._get_products(sort_by_name=sort_by_name,
                               additional_query=is_package))
        self.component_combo.select_item_by_position(0)


class ProductPackageSlave(ProductComponentSlave):
    def _setup_widgets(self):
        super(ProductPackageSlave, self)._setup_widgets()
        self.production_time_box.hide()

    def _get_columns(self):
            return [Column('code', title=_(u'Code'), data_type=int,
                           expander=True, sorted=True),
                    Column('quantity', title=_(u'Quantity'),
                           data_type=Decimal),
                    Column('unit', title=_(u'Unit'), data_type=str),
                    Column('description', title=_(u'Description'),
                           data_type=str, expand=True),
                    Column('category', title=_(u'Category'), data_type=str),
                    Column('total_production_cost', title=_(u'Total'),
                           format_func=get_formatted_cost, data_type=currency),
                    Column('price', title=_(u'Price'),
                           format_func=get_formatted_cost, data_type=currency)]


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

        if self._product.parent is not None:
            self._disable_child_widgets()

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

    def _disable_child_widgets(self):
        self.add_button.set_property('sensitive', False)
        self.target_combo.set_property('sensitive', False)
        self.relations_list.set_list_type(ListType.READONLY)
