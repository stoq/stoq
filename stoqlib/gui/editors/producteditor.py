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
## Author(s):   Henrique Romano             <henrique@async.com.br>
##              Evandro Vale Miquelito      <evandro@async.com.br>
##              Bruno Rafael Garcia         <brg@async.com.br>
##              Johan Dahlin                <jdahlin@async.com.br>
##
""" Editors definitions for products"""

from decimal import Decimal

import gtk

from kiwi.datatypes import ValidationError, currency
from kiwi.ui.widgets.list import Column, SummaryLabel

from stoqdrivers.enum import TaxType

from stoqlib.domain.interfaces import IStorable
from stoqlib.domain.person import PersonAdaptToSupplier
from stoqlib.domain.product import ProductSupplierInfo, Product, ProductComponent
from stoqlib.domain.sellable import (BaseSellableInfo, Sellable,
                                     SellableTaxConstant)
from stoqlib.domain.views import ProductFullStockView
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.baseeditor import (BaseEditor, BaseEditorSlave,
                                            BaseRelationshipEditorSlave)
from stoqlib.gui.editors.sellableeditor import SellableEditor
from stoqlib.gui.slaves.productslave import ProductDetailsSlave
from stoqlib.lib.message import info, yesno
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.validators import get_formatted_price

_ = stoqlib_gettext


#
# Slaves
#
class _TemporaryProductComponent(object):
    def __init__(self, product=None, component=None, quantity=Decimal(1)):
        self.product = product
        self.component = component
        self.quantity = quantity

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
        else:
            # adding
            ProductComponent(product=self.product,
                             component=self.component,
                             quantity=self.quantity,
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
                Column('production_cost', title=_(u'Production Cost'),
                        data_type=currency),
                ]

    def _setup_widgets(self):
        self.component_combo.prefill(list(self._get_products()))

        self.component_tree.set_columns(self._get_columns())
        self._populate_component_tree()
        self.component_label = SummaryLabel(klist=self.component_tree,
                                            column='production_cost',
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
        # summary label
        value = 0
        for component in self.component_tree:
            value += component.get_total_production_cost()
        self.component_label.set_value(get_formatted_price(value))

    def _populate_component_tree(self):
        self._add_to_component_tree()

    def _get_components(self, product):
        for component in ProductComponent.selectBy(product=product,
                                                   connection=self.conn):
            yield _TemporaryProductComponent(product=component.product,
                                             component=component.component,
                                             quantity=component.quantity)

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
            component = self.component_combo.read()
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

        msg = _(u'Do you really want to remove the component "%s" ?' %
                root_component.description)
        if not yesno(msg, gtk.RESPONSE_NO, _(u'Remove'), _(u'Cancel')):
            return

        self._remove_component_list.append(root_component)
        self._totally_remove_component(root_component)
        self._update_widgets()

    #
    # BaseEditorSlave
    #

    def create_model(self, conn):
        return _TemporaryProductComponent(product=self._product)

    def on_confirm(self):
        for component in self._remove_component_list:
            component.delete_product_component(self.conn)

        for component in self.component_tree:
            component.add_or_update_product_component(self.conn)

        return self.model

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

class ProductSupplierEditor(BaseEditor):
    model_name = _('Product Supplier')
    model_type = ProductSupplierInfo
    gladefile = 'ProductSupplierEditor'

    proxy_widgets = ('base_cost', 'icms', 'notes', 'lead_time')

    def __init__(self, conn, model=None):
        BaseEditor.__init__(self, conn, model)

    #
    # BaseEditor hooks
    #

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)

    def validate_confirm(self):
        return self.base_cost.read() > 0

    #
    # Kiwi handlers
    #
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
                Column('base_cost', title=_(u'Cost'),
                        data_type=currency),]

    def create_model(self):
        product = self._product
        supplier = self.target_combo.read()

        if product.is_supplied_by(supplier):
            product_desc = self._product.sellable.get_description()
            info(_(u'%s is already supplied by %s' % (product_desc,
                                                      supplier.person.name)))
            return

        model = ProductSupplierInfo(product=product,
                                    supplier=supplier,
                                    connection=self.conn)
        return model


#
# Editors
#


class ProductComponentEditor(BaseEditor):
    gladefile = 'ProductComponentEditor'
    proxy_widgets = ['quantity',]
    title = _(u'Product Component')
    model_type = _TemporaryProductComponent

    def __init__(self, conn, product_component):
        BaseEditor.__init__(self, conn, model=product_component)
        self._setup_widgets()

    def _setup_widgets(self):
        self.component_description.set_text(self.model.description)
        # set a default quantity value for new components
        if not self.model.quantity:
            self.quantity.set_value(1)

    #
    # BaseEditor
    #

    def setup_proxies(self):
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

    def __init__(self, conn, model=None):
        self._has_composed_product = sysparam(conn).ENABLE_COMPOSED_PRODUCT
        SellableEditor.__init__(self, conn, model)

    def get_taxes(self):
        constants = SellableTaxConstant.select(connection=self.conn)
        return [(c.description, c) for c in constants
                                   if c.tax_type != TaxType.SERVICE]

    #
    # BaseEditor
    #

    def setup_slaves(self):
        details_slave = ProductDetailsSlave(self.conn, self.model.sellable)
        self.add_extra_tab(_(u'Details'), details_slave)

        self._suppliers_slave = ProductSupplierSlave(self.conn, self.model)
        self.add_extra_tab(_(u'Suppliers'), self._suppliers_slave)

        if self._has_composed_product:
            self._component_slave = ProductComponentSlave(self.conn, self.model)
            self.add_extra_tab(_(u'Components'), self._component_slave)

    def setup_widgets(self):
        self.stock_total_lbl.show()
        self.stock_lbl.show()

    def create_model(self, conn):
        sellable_info = BaseSellableInfo(connection=conn)
        tax_constant = sysparam(conn).DEFAULT_PRODUCT_TAX_CONSTANT
        sellable = Sellable(base_sellable_info=sellable_info,
                            tax_constant=tax_constant,
                            connection=conn)
        model = Product(connection=conn, sellable=sellable)
        model.addFacet(IStorable, connection=conn)
        return model

    def on_confirm(self):
        if self._has_composed_product:
            return self._component_slave.on_confirm()

        return self.model

