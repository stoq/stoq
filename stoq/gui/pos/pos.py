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
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##              Henrique Romano             <henrique@async.com.br>
##
"""
gui/pos/pos.py:

    Main interface definition for pos application.
"""

import operator

from kiwi.ui.widgets.list import Column
from stoqlib.gui.search import SearchBar, BaseListSlave
from stoqlib.gui.columns import FacetColumn

from stoq.gui.application import AppWindow
from stoq.lib.runtime import get_current_user, new_transaction
from stoq.lib.parameters import get_system_parameter
from stoq.domain.sellable import AbstractSellable, get_formated_price
from stoq.domain.person import Person
from stoq.domain.product import Product
from stoq.domain.interfaces import (IIndividual, IClient, ISellable,
                                    ISellableItem)
from stoq.gui.editors.product import ProductEditor
from stoq.gui.search.sellable import SellableSearch
from stoq.gui.search.category import (BaseSellableCatSearch,
                                      SellableCatSearch)
from stoq.gui.search.person import (ClientSearch, 
                                    EmployeeSearch,
                                    SupplierSearch)

class POS(AppWindow):
   
    toplevel_name = gladefile = "pos"
    
    product_widgets = ('product',
                       'quantity')

    client_widgets =  ('client_name',)
    
    widgets = ('total',
               'price',
               'client_select_button',
               'client_details_button',
               'reset_order_button',
               'delivery_button',
               'checkout_button',
               'remove_item_button',
               'product_details_button',
               'edit_button',
               'SalesMenu',
               'UsersMenu',) + product_widgets + client_widgets
    
    def __init__(self, app):
        AppWindow.__init__(self, app)
        self.conn = new_transaction()
        self._setup_slaves()
        self._setup_signals()
        self._setup_proxies()
        self._setup_widgets()
        self.update_widgets()
        self.reset_order()

    def _setup_slaves(self):
        order_list_slave = BaseListSlave(parent=self)
        self.attach_slave('orderlist_holder', order_list_slave)
        self.order_list = order_list_slave.klist
    
        self.search_bar = SearchBar(self, AbstractSellable,
                                    search_callback=self.run_search) 
        self.attach_slave("search_bar_holder", self.search_bar)

    def _setup_proxies(self):
        self.product_proxy = self.add_proxy(widgets=self.product_widgets)
        self.person_proxy = self.add_proxy(widgets=self.client_widgets)

    def _setup_signals(self):
        # connect list signals
        selection = self.order_list.treeview.get_selection()
        selection.connect("changed", self._on_order_list_selection_changed)

    def _setup_widgets(self):
        self.price.set_size('large')
        self.price.set_bold(1)
        self.product.set_size('large')
        self.product.set_bold(1)
        self.total.set_size('x-large')
        self.total.set_bold(1)

        user_menu_label = "%s: %s" % (self.UsersMenu.get_property('label'),
                                      get_current_user().username)
        self.UsersMenu.set_property('label', user_menu_label)

    def _update_order_lbls(self):
        if self.order_list:
            totals = [item.get_total() for item in self.order_list]
            total = reduce(operator.add, totals, 0.0) 
            text = get_formated_price(total)
        else:
            text = ''
        self.total.set_text(text)

    def _update_product_widgets(self, model):
        has_model = bool(model)
        self.product_model = model
        self.product_proxy.new_model(model, relax_type=True)
        self.remove_item_button.set_sensitive(has_model)
        self.product_details_button.set_sensitive(has_model)
        self.edit_button.set_sensitive(has_model)
        if not has_model:
            self.product.set_text(_('No product selected'))
            self.product.set_color('DarkGray')
            
            self.price.hide()

            self.quantity.set_text('0')
            self.quantity.set_sensitive(False)
        else:
            sellable = self.get_sellable_model(model)
            self.price.show()
            self.product.set_color('black')
            self.product.set_text(sellable.description)
            self.quantity.set_sensitive(True)

    def get_sellable_model(self, sellable_item):
        adapted = sellable_item.get_adapted()
        return ISellable(adapted, connection=self.conn)

    def search_clients(self):
        person = self.run_dialog(ClientSearch)
        if person:
            self.person_proxy.new_model(person, relax_type=True)
        self.update_widgets()

    def add_sellable_item(self, item):
        adapted = item.get_adapted()
        sellable_item = ISellableItem(adapted)
        if sellable_item in self.order_list:
            return
        sellable_item = adapted.addFacet(ISellableItem, price=item.price,
                                         connection=self.conn)
        self.order_list.add_instance(sellable_item)

    def select_first_item(self):
        if len(self.order_list):
            # XXX Probably kiwi should handle this for us. Waiting for
            # support
            self.order_list.select_instance(self.order_list[0])

    def reset_order(self):
        self.person_proxy.new_model(None, relax_type=True)
        self.product_proxy.new_model(None, relax_type=True)
        items = self.order_list[:]
        for item in items:
            self.order_list.remove_instance(item)
            table = type(item)
            table.delete(item.id, connection=self.conn)
        self.update_widgets()
        self._update_order_lbls()



    #
    # Hooks
    #



    def update_widgets(self):
        """Hook called by BaseListSlave"""
        has_client = bool(self.person_proxy.model)
        self.client_details_button.set_sensitive(has_client)
        if not has_client:
            self.client_name.set_text('Not selected')
            self.client_name.set_color('red')
        else:
            self.client_name.set_color('black')
        model = self.order_list.get_selected()
        if model:
            sellable = self.get_sellable_model(model)
            self._update_product_widgets(model)
            self.price.set_text(sellable.get_price_string())
        else:
            self._update_product_widgets(self.product_proxy.model)
        self._update_order_lbls()

    def run_search(self):
        """Hook called by SearchDialog"""
        search_str = self.search_bar.get_search_string()
        items = self.run_dialog(SellableSearch, search_str)
        for item in items:
            self.add_sellable_item(item)
        self.select_first_item()
        self._update_order_lbls()

    def get_columns(self):
        """Hook called by BaseListSlave"""
        return [FacetColumn(ISellable, 'code', title=_('Code'), 
                            sorted=True, data_type=str, width=50),
                FacetColumn(ISellable, 'description', 
                            title=_('Description'), data_type=str, 
                            width=260),
                FacetColumn(ISellable, 'price', title=_('Price'), 
                            data_type=float, width=50),
                Column('quantity', title=_('Quantity'), data_type=float,
                       width=20),
                Column('total', title=_('Total'), data_type=float,
                      width=50)]



    #
    # Callbacks
    #

    

    def _on_order_list_selection_changed(self, *args):
        self.update_widgets()

    def on_client_select_button__clicked(self, *args):
        self.search_clients()

    def _on_selectclient_action__clicked(self, *args):
        self.search_clients()

    def on_quantity__changed(self, kiwispin):
        if self.product_proxy.model is None:
            return
        qty = self.quantity.get_text()
        if qty:
            self.product_model.quantity = float(qty)
            self.order_list.update_instance(self.product_proxy.model)
        self._update_order_lbls()

    def on_remove_item_button__clicked(self, *args):
        item = self.product_model
        self.order_list.remove_instance(item)
        self.product_proxy.new_model(None, relax_type=True)
        self.select_first_item()
        self.update_widgets()

    def on_reset_order_button__clicked(self, *args):
        self.reset_order()

    def on_product_details_button__clicked(self, *args):
        pass

    def _on_resetorder_action__clicked(self, *args):
        self.reset_order()

    def _on_clients_action__clicked(self, *args):
        self.search_clients()

    def _on_suppliers_action__clicked(self, *args):
        self.run_dialog(SupplierSearch, hide_footer=True)

    def _on_employees_action__clicked(self, *args):
        self.run_dialog(EmployeeSearch, hide_footer=True)

    def _on_sales_action__clicked(self, *args):
        pass
                      
    def on_delivery_button__clicked(self, *args):
        #dialog not implemented yet
        pass
    
    def _on_products_action__clicked(self, *args):
        conn = new_transaction()
        model = self.run_dialog(ProductEditor, conn)
        if model:
            conn.commit()
            return
        conn.rollback()

    def _on_sellable_category__clicked(self, *args):
        dlg = BaseSellableCatSearch
        self.run_dialog(dlg)

    def _on_sellable_subcategory__clicked(self, *args):
        dlg = SellableCatSearch
        self.run_dialog(dlg)

    def on_edit_button__clicked(self, *args):
        #dialog not implemented yet
        pass

    def on_checkout_button__clicked(self, *args):
        #dialog not implemented yet
        pass

