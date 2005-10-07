# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005 Async Open Source <http://www.async.com.br>
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
##
"""
stoq/gui/pos/warehouse.py:

    Main gui definition for warehouse application.
"""

import gettext

import gtk
from kiwi.ui.widgets.list import Column
from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.gui.search import SearchBar
from stoqlib.gui.columns import AccessorColumn
from stoqlib.database import rollback_and_begin

from stoq.gui.application import AppWindow
from stoq.gui.slaves.stock import FilterStockSlave
from stoq.lib.validators import get_formatted_price
from stoq.lib.runtime import new_transaction
from stoq.domain.product import Product
from stoq.domain.sellable import AbstractSellable
from stoq.domain.interfaces import ISellable, IStorable

_ = gettext.gettext


class WarehouseApp(AppWindow):
   
    app_name = _('Warehouse')
    gladefile = "warehouse"
    
    widgets = ('total',
               'sellable_list', 
               'retention_button',
               'history_button',
               'receive_action',
               'transfer_action')
    
    def __init__(self, app):
        self.conn = new_transaction()
        self.filterstock_slave = FilterStockSlave(self.conn)
        AppWindow.__init__(self, app)
        self._setup_widgets()
        self._setup_slaves()
        self._update_view()

    def _setup_widgets(self):
        self.total.set_size('x-large')
        self.total.set_bold(True)
        self.sellable_list.set_columns(self._get_columns())
        self.sellable_list.set_selection_mode(gtk.SELECTION_MULTIPLE)

    def _setup_slaves(self):
        search_label_text = _('Find products matching')
        self.search_bar = SearchBar(self, AbstractSellable,
                                    self._get_columns(), 
                                    search_lbl_text=search_label_text,
                                    filter_slave=self.filterstock_slave) 
        self.attach_slave("search_bar_holder", self.search_bar)

    def _update_view(self):
        has_stock = len(self.sellable_list) > 0
        self.retention_button.set_sensitive(has_stock)
        one_selected = len(self.sellable_list.get_selected_rows()) == 1
        self.history_button.set_sensitive(one_selected)

    def _get_columns(self):
        return [Column('code', title=_('Code'), sorted=True,
                       data_type=str, width=100),
                Column('description', title=_('Description'),
                       expand=True, data_type=str, searchable=True),
                AccessorColumn('supplier', self._get_supplier, 
                               title=_('Supplier'), data_type=str),
                AccessorColumn('quantity', self._get_stock_balance_str, 
                               title=_('Quantity'), data_type=float,
                               justify=gtk.JUSTIFY_RIGHT)]


    #
    # Accessor
    #



    def _get_supplier(self, instance):
        """Accessor called by AccessorColumn"""
        adapted = instance.get_adapted()
        main_supplier_info = adapted.get_main_supplier_info()
        if not main_supplier_info:
            return ''
        if not main_supplier_info.supplier:
            raise DatabaseInconsistency('A ProductSupplierInfo object must '
                                        'have a supplier set. Found None '
                                        'instead')
        person = main_supplier_info.supplier.get_adapted() 
        return person.name

    def _get_storable(self, instance):
        adapted = instance.get_adapted()
        return IStorable(adapted)

    def _get_stock_balance(self, instance):
        branch = self.filterstock_slave.get_selected_branch()
        storable = self._get_storable(instance)
        return storable.get_full_balance(branch)

    def _get_stock_balance_str(self, instance):
        """Accessor called by AccessorColumn"""
        balance = self._get_stock_balance(instance)
        storable = self._get_storable(instance)
        return storable.get_full_balance_string(full_balance=balance)

    def _update_stock_total(self):
        # FIXME We must implement a cache for stock total, which should be
        # updated when the accessor _get_stock_balance_str is called,  
        # after bug fix in kiwi.
        # Right now the accessors are called even when moving
        # the cursor over the list. In this case the stock total will be
        # completely wrong
        stock_total = 0.0
        for sellable in self.sellable_list:
            stock_total += self._get_stock_balance(sellable)
        total_str = get_formatted_price(stock_total)
        self.total.set_text(total_str)



    #
    # Hooks
    #



    def get_extra_query(self):
        """Hook called by SearchBar"""
        # TODO search by supplier name too. Bug 2180
        return
        
    def update_klist(self, sellables=None):
        """Hook called by SearchBar"""
        rollback_and_begin(self.conn)
        self.sellable_list.clear()
        for sellable in sellables:
            # Since search bar change the connection internally we must get
            # the objects back in our main connection
            obj = AbstractSellable.get(sellable.id, connection=self.conn)
            self.sellable_list.append(obj)
        self._update_view()
        self._update_stock_total()

    def filter_results(self, sellables):
        """Hook called by SearchBar"""
        table = Product.getAdapterClass(ISellable)
        return [sellable for sellable in sellables 
                        if isinstance(sellable, table)]
        


    #
    # Callbacks
    #

    

    def on_filterstock_slave__branchcombo_changed(self, slave):
        self.sellable_list.refresh()
        self._update_stock_total()

    def on_sellable_list__selection_changed(self, *args):
        self._update_view()
