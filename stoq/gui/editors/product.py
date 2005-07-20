# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2004 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s):   Henrique Romano             <henrique@async.com.br>
##              Evandro Vale Miquelito      <evandro@async.com.br>
##
"""
stoq/gui/editors/product.py:

   Product editor implementation.
"""

from kiwi.datatypes import ValidationError
from kiwi.ui.widgets.list import Column
from stoqlib.gui.lists import SimpleListDialog
from stoqlib.gui.editors import BaseEditor
from stoqlib.gui.dialogs import run_dialog

from stoq.domain.sellable import SellableCategory
from stoq.domain.person import PersonAdaptToSupplier
from stoq.domain.product import (ProductSupplierInfo, Product,
                                 ProductAdaptToSellable)
from stoq.domain.interfaces import ISellable, IStorable
from stoq.lib.parameters import get_system_parameter



#
# Editor slaves implementation
#



class ProductSupplierEditor(BaseEditor):
    gladefile = 'ProductSupplierEditor'
    model_type = Product
    title = _('Costs Details')

    proxy_widgets = ('supplier_combo',
                     'base_cost',
                     'notes')

    widgets = ('supplier_list_button',
               'new_supplier_button') + proxy_widgets

    def __init__(self, conn, model=None):
        BaseEditor.__init__(self, conn, model)
        # XXX: Waiting fix for bug #2043
        self.new_supplier_button.set_sensitive(False)

    def set_widget_formats(self):
        self.base_cost.set_data_format('%.02f')

    def setup_combos(self):
        table = PersonAdaptToSupplier
        supplier_list = table.select(connection=self.conn)
        items = [(obj.get_adapted().name, obj) for obj in supplier_list]

        assert items, ("There is no suppliers in database!")

        self.supplier_combo.prefill(items)

    def list_suppliers(self):
        cols = [Column('name', title=_('Supplier name'), width=350),
                Column('base_cost', title=_('Base Cost'), width=120)]

        run_dialog(SimpleListDialog, self, cols, self.model.suppliers)

    def update_model(self):
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
        self.prod_supplier_proxy.new_model(model)

        # updating the field for the widget validation works fine
        self.prod_supplier_proxy.update('base_cost')



    #
    # BaseEditor hooks
    #



    def setup_proxies(self):
        self.setup_combos()

        model = self.model.get_main_supplier_info()
        if not model:
            sparam = get_system_parameter(self.conn)
            supplier = sparam.SUPPLIER_SUGGESTED
            model = ProductSupplierInfo(connection=self.conn, product=None, 
                                        is_main_supplier=True,
                                        supplier=supplier)
        self.set_widget_formats()

        self.prod_supplier_proxy = self.add_proxy(model, 
                                                  self.proxy_widgets)

        # XXX:  GTK don't allow me get the supplier selected in the combo
        # *when* the 'changed' signal is emitted, i.e, when the 'changed'
        # callback is called, the model already have the new value selected
        # by user, so I need to store in a local attribute the last model
        # selected.
        self._last_supplier = model.supplier

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

    def on_supplier_combo__changed(self, *args):
        self.update_model()

    def on_base_cost__validate(self, entry, value):
        if not value or value <= 0.0:
            return ValidationError("Value must be greater than zero.")

class ProductPriceEditor(BaseEditor):
    gladefile = 'ProductPriceEditor'
    model_type = ProductAdaptToSellable
    title = _('Price Details')

    proxy_widgets = ('cost',
                     'markup',
                     'on_sale_start_date',
                     'on_sale_end_date',
                     'max_discount',
                     'comission',
                     'on_sale_price',
                     'price')

    general_widgets = ('base_markup',)

    widgets = proxy_widgets + general_widgets

    def __init__(self, conn, model=None):
        BaseEditor.__init__(self, conn, model)
        self.update_markup()

    def set_widget_formats(self):
        widgets = (self.markup, self.base_markup, self.max_discount,
                   self.comission, self.on_sale_price, self.price,
                   self.cost)
        for widget in widgets:
            widget.set_data_format('%.02f')

    def update_markup(self):
        price = self.model.price or 1.0
        cost = self.model.cost or 1.0

        self.model.markup = ((price / cost) - 1) * 100
        self.main_proxy.update('markup')

    def update_price(self):
        cost = self.model.cost
        markup = self.model.markup 
        # XXX: Kiwi call spinbutton's callback two times, in the first one
        # the spin value is None, so we need to manage this.
        if markup is None:
            return
        self.model.price = cost + ((markup / 100) * cost)
        self.main_proxy.update('price')



    #
    # BaseEditor hooks
    #



    def setup_proxies(self):
        self.set_widget_formats()
        self.main_proxy = self.add_proxy(self.model, self.proxy_widgets)

        if self.model.markup is not None:
            return

        sellable = ISellable(self.model.get_adapted())
        assert sellable
        self.model.markup = sellable.get_suggested_markup()
        self.main_proxy.update('markup')



    #
    # Kiwi handlers
    # 



    def after_price__changed(self, entry_box):
        self.handler_block(self.markup, 'changed')
        self.update_markup()
        self.handler_unblock(self.markup, 'changed')

    def after_markup__changed(self, spin_button):
        self.handler_block(self.price, 'changed')
        self.update_price()
        self.handler_unblock(self.price, 'changed')



#
# Editor implementation
#



class ProductEditor(BaseEditor):
    title = _('Product Editor')
    gladefile = 'ProductEditor' 
    model_type = Product


    product_widgets = ('notes',
                       'supplier_lbl')

    sellable_widgets = ('code',
                        'description',
                        'category_combo',
                        'cost',
                        'price')

    storable_widgets = ('stock_price_lbl', )

    widgets = ('supplier_button',
               'sale_price_button') + product_widgets + sellable_widgets + \
               storable_widgets

    def __init__(self, conn, model=None):
        if not model:
            model = Product(connection=conn)
            model.addFacet(ISellable, code='', description='', price=0.0, 
                           connection=conn)
            model.addFacet(IStorable, connection=conn)

        BaseEditor.__init__(self, conn, model)

    def set_widget_formats(self):
        for widget in (self.cost, self.stock_price_lbl, self.price):
            widget.set_data_format('%.02f')

    def edit_supplier(self):
        result = run_dialog(ProductSupplierEditor, self, self.conn, self.model)
        if not result:
            return

        self.main_proxy.update('main_supplier_info.name')

        if not self.sellable_proxy.model.cost and self.model.suppliers:
            base_cost = self.model.get_main_supplier_info().base_cost
            self.sellable_proxy.model.cost = base_cost or 0.0
            self.sellable_proxy.update('cost')

        if self.sellable_proxy.model.price:
            return

        cost = self.sellable_proxy.model.cost
        markup = self.sellable_proxy.model.get_suggested_markup()
        self.sellable_proxy.model.price = cost + ((markup / 100) * cost)
        self.sellable_proxy.update('price')

    def edit_sale_price(self):
        sellable = ISellable(self.model)
        result = run_dialog(ProductPriceEditor, self, self.conn, sellable)
        if result:
            self.sellable_proxy.update('price')



    #
    # BaseEditor hooks
    #



    def setup_combos(self):
        table = SellableCategory
        category_list = table.select(connection=self.conn)
        items = [('%s %s' % (obj.base_category.category_data.description, 
                             obj.category_data.description), obj)
                 for obj in category_list]

        self.category_combo.prefill(items)

    def setup_proxies(self):
        self.set_widget_formats()
        self.setup_combos()

        self.main_proxy = self.add_proxy(self.model, self.product_widgets)

        sellable = ISellable(self.model)
        self.sellable_proxy = self.add_proxy(sellable, self.sellable_widgets)
        storable = IStorable(self.model)
        self.storable_proxy = self.add_proxy(storable, self.storable_widgets)



    #
    # Kiwi handlers
    #



    def on_sale_price_button__clicked(self, button):
        self.edit_sale_price()

    def on_supplier_button__clicked(self, button):
        self.edit_supplier()

