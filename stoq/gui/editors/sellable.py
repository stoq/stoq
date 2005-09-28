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
##              Bruno Rafael Garcia         <brg@async.com.br>
##
"""
stoq/gui/editors/sellable.py:

   Editors definitions for sellable.
"""

import gettext

from stoqlib.gui.editors import BaseEditor
from stoqlib.gui.dialogs import run_dialog

from stoq.domain.sellable import SellableCategory, AbstractSellable
from stoq.domain.interfaces import ISellable, IStorable


_ = gettext.gettext


#
# Slaves
#


class SellablePriceEditor(BaseEditor):
    model_name = 'Product Price'
    model_type = AbstractSellable
    gladefile = 'SellablePriceEditor'

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
        self.update_comission()

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

    def update_comission(self):
        if self.model.get_comission() is not None:
            return
        self.model.set_default_comission()
        self.main_proxy.update('comission')

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



    def get_title_model_attribute(self, model):
        return self.model_name

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
# Editors
#



class SellableEditor(BaseEditor):
    """This is a base class for ProductEditor and ServiceEditor and should be used
    when editing sellable objects. Note that sellable objects are instances
    inherited by AbstractSellable."""

    # This must be be properly defined in the child classes
    model_name = None
    model_type = None

    gladefile = 'SellableEditor' 
    product_widgets = ('notes',)
    sellable_widgets = ('code',
                        'description',
                        'category_combo',
                        'cost',
                        'price',
                        'notes_lbl')

    storable_widgets = ('stock_total_lbl', 'stock_lbl')

    widgets = (('sale_price_button', 'product_supplier_holder')
                + product_widgets + sellable_widgets + storable_widgets)

    def __init__(self, conn, model=None):
        BaseEditor.__init__(self, conn, model)
        self.setup_widgets()

    def set_widget_formats(self):
        for widget in (self.cost, self.stock_total_lbl, self.price):
            widget.set_data_format('%.02f')

    def edit_sale_price(self):
        sellable = ISellable(self.model)
        result = run_dialog(SellablePriceEditor, self, self.conn, sellable)
        if result:
            self.sellable_proxy.update('price')

    def setup_widgets(self):
        raise NotImplementederror

    #
    # BaseEditor hooks
    #



    def get_title_model_attribute(self, model):
        return ISellable(model).description

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
