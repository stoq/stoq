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
from kiwi.utils import gsignal

from stoqlib.domain.interfaces import ISellable, IStorable, ISupplier
from stoqlib.domain.sellable import BaseSellableInfo
from stoqlib.domain.person import Person, PersonAdaptToSupplier
from stoqlib.domain.product import ProductSupplierInfo, Product, ProductComponent
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.lists import SimpleListDialog
from stoqlib.gui.editors.baseeditor import BaseEditor, BaseEditorSlave
from stoqlib.gui.editors.sellableeditor import SellableEditor
from stoqlib.gui.slaves.productslave import ProductTributarySituationSlave
from stoqlib.lib.message import warning, info, yesno
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.validators import get_formatted_price

_ = stoqlib_gettext

#
# Slaves
#

class ProductSupplierSlave(BaseEditorSlave):
    """ A basic slave for suppliers selection.  This slave emits the
    'cost-changed' signal when the supplier's product cost has
    changed.
    """
    gladefile = 'ProductSupplierSlave'
    proxy_widgets = 'supplier_lbl',
    model_type = Product

    gsignal("cost-changed")

    def on_supplier_button__clicked(self, button):
        self.edit_supplier()

    def edit_supplier(self):
        suppliers = PersonAdaptToSupplier.select(connection=self.conn)
        if not suppliers:
            warning(_(u"There is no supplier registered in system"))
            return
        main_supplier = self.model.get_main_supplier_info()
        if not main_supplier:
            current_cost = currency(0)
        else:
            current_cost =  main_supplier.base_cost
        result = run_dialog(ProductSupplierEditor, self, self.conn,
                            self.model)
        if not result:
            return
        if result.base_cost != current_cost:
            self.emit("cost-changed")
        self.proxy.update('main_supplier_info.name')

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model,
                                    ProductSupplierSlave.proxy_widgets)


class _TemporaryProductComponent(object):
    def __init__(self, product=None, component=None, quantity=Decimal(1)):
        self.product = product
        self.component = component
        self.quantity = quantity

        if self.component is not None:
            # keep this values in memory in order to speed up the
            # data access
            sellable = ISellable(self.component)
            self.id = sellable.id
            self.description = sellable.get_description()
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
                Column('description', title=_(u'Description'),
                        data_type=str, expand=True),
                Column('unit', title=_(u'Unit'), data_type=str),
                Column('production_cost', title=_(u'Production Cost'),
                        data_type=currency),
                Column('quantity', title=_(u'Quantity'), data_type=Decimal)]

    def _setup_widgets(self):
        products = Product.select(Product.q.id!=self._product.id,
                                  connection=self.conn)
        components = [(ISellable(p).get_description(), p) for p in products]
        self.component_combo.prefill(components)

        self.component_tree.set_columns(self._get_columns())
        self._populate_component_tree()
        self.component_label = SummaryLabel(klist=self.component_tree,
                                            column='production_cost',
                                            label='<b>%s</b>' % _(u'Total:'),
                                            value_format='<b>%s</b>')
        self.component_label.show()
        self.component_tree_vbox.pack_start(self.component_label, False)
        self._update_widgets()

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
            product_desc = ISellable(self._product).get_description()
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


class ProductSupplierEditor(BaseEditor):
    model_name = _('Product Suppliers')
    model_type = Product
    gladefile = 'ProductSupplierEditor'

    proxy_widgets = ('supplier_combo',
                     'base_cost',
                     'icms',
                     'notes')

    def __init__(self, conn, model=None):
        self._last_supplier = None
        BaseEditor.__init__(self, conn, model)
        # XXX: Waiting fix for bug #2043
        self.new_supplier_button.set_sensitive(False)

    def setup_combos(self):
        # FIXME: Implement and use IDescribable on PersonAdaptToSupplier
        suppliers = Person.iselect(ISupplier, connection=self.conn)
        items = [(obj.person.name, obj) for obj in suppliers]

        assert items, ("There is no suppliers in database!")

        self.supplier_combo.prefill(sorted(items))

    def list_suppliers(self):
        cols = [Column('name', title=_('Supplier name'),
                       data_type=str, width=350),
                Column('base_cost', title=_('Base Cost'),
                       data_type=float, width=120)]

        run_dialog(SimpleListDialog, self, cols, self.model.suppliers)

    def update_model(self):
        # Don't update the model if the proxy is not created,
        # since content-changed is potentially called very early
        if not self.prod_supplier_proxy:
            return
        selected_supplier = self.supplier_combo.get_selected_data()

        # Kiwi proxy already sets the supplier attribute to new selected
        # supplier, so we need revert this and set the correct supplier:
        self.prod_supplier_proxy.model.supplier = self._last_supplier

        self._last_supplier = selected_supplier
        is_valid_model = self.prod_supplier_proxy.model.base_cost

        if is_valid_model:
            self.prod_supplier_proxy.model.product = self.model

        for supplier_info in self.model.suppliers:
            if supplier_info.supplier is selected_supplier:
                model = supplier_info
                break
        else:
            model = ProductSupplierInfo(connection=self.conn, product=None,
                                        supplier=selected_supplier)
        self.prod_supplier_proxy.set_model(model)

        # updating the field for the widget validation works fine
        self.prod_supplier_proxy.update('base_cost')

    #
    # BaseEditor hooks
    #

    def get_title(self, *args):
        return _('Add supplier information')

    def setup_proxies(self):
        self.prod_supplier_proxy = None
        self.setup_combos()
        model = self.model.get_main_supplier_info()
        if not model:
            supplier = sysparam(self.conn).SUGGESTED_SUPPLIER
            model = ProductSupplierInfo(connection=self.conn, product=None,
                                        is_main_supplier=True,
                                        supplier=supplier)
        self.prod_supplier_proxy = self.add_proxy(model,
                                                  self.proxy_widgets)

        # XXX:  GTK don't allow me get the supplier selected in the combo
        # *when* the 'changed' signal is emitted, i.e, when the 'changed'
        # callback is called, the model already have the new value selected
        # by user, so I need to store in a local attribute the last model
        # selected.
        self._last_supplier = model.supplier

    # Move this to Product domain class see #2400
    def update_main_supplier_references(self, main_supplier):
        if not self.model.suppliers:
            return
        for s in self.model.suppliers:
            if s is main_supplier:
                s.is_main_supplier = True
                continue
            s.is_main_supplier = False

    def on_confirm(self):
        current_supplier = self.prod_supplier_proxy.model
        is_valid_model = current_supplier and current_supplier.base_cost
        if not current_supplier or not is_valid_model:
            return

        current_supplier.product = self.model
        self.update_main_supplier_references(current_supplier)
        return current_supplier

    #
    # Kiwi handlers
    #

    def on_supplier_list_button__clicked(self, button):
        self.list_suppliers()

    def on_supplier_combo__content_changed(self, *args):
        self.update_model()

    def on_base_cost__validate(self, entry, value):
        if not value or value <= currency(0):
            return ValidationError("Value must be greater than zero.")

class ProductEditor(SellableEditor):
    model_name = _('Product')
    model_type = Product

    def __init__(self, conn, model=None):
        self._has_composed_product = sysparam(conn).ENABLE_COMPOSED_PRODUCT
        SellableEditor.__init__(self, conn, model)

    #
    # BaseEditor
    #

    def setup_slaves(self):
        supplier_slave = ProductSupplierSlave(self.conn, self.model)
        supplier_slave.connect("cost-changed",
                               self._on_supplier_slave__cost_changed)
        self.attach_slave('product_supplier_holder', supplier_slave)
        # XXX: tax_holder is a Brazil-specifc area
        tax_slave = ProductTributarySituationSlave(self.conn,
                                                   ISellable(self.model))
        self.attach_slave("tax_holder", tax_slave)

        if self._has_composed_product:
            self._component_slave = ProductComponentSlave(self.conn, self.model)
            self.add_extra_tab(_(u'Components'), self._component_slave)

    def setup_widgets(self):
        self.notes_lbl.set_text(_('Product details'))
        self.stock_total_lbl.show()
        self.stock_lbl.show()

    def create_model(self, conn):
        model = Product(connection=conn)
        sellable_info = BaseSellableInfo(connection=conn)
        tax_constant = sysparam(conn).DEFAULT_PRODUCT_TAX_CONSTANT
        model.addFacet(ISellable, base_sellable_info=sellable_info,
                       tax_constant=tax_constant,
                       connection=conn)
        model.addFacet(IStorable, connection=conn)
        supplier = sysparam(conn).SUGGESTED_SUPPLIER
        ProductSupplierInfo(connection=conn,
                            is_main_supplier=True,
                            supplier=supplier,
                            product=model)
        return model

    def on_confirm(self):
        if self._has_composed_product:
            return self._component_slave.on_confirm()

        return self.model

    #
    # Callbacks
    #

    def _on_supplier_slave__cost_changed(self, slave):
        if not self.sellable_proxy.model.cost and self.model.suppliers:
            base_cost = self.model.get_main_supplier_info().base_cost
            self.sellable_proxy.model.cost = base_cost or currency(0)
            self.sellable_proxy.update('cost')

        if self.sellable_proxy.model.base_sellable_info.price:
            return
        cost = self.sellable_proxy.model.cost or currency(0)
        markup = (self.sellable_proxy.model.get_suggested_markup()
                  or Decimal(0))
        price = cost + ((markup / 100) * cost)
        self.sellable_proxy.model.base_sellable_info.price = price
        self.sellable_proxy.update('base_sellable_info.price')
