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
stoq/gui/warehouse/warehouse.py:

    Main gui definition for warehouse application.
"""

import gettext

import gtk
from kiwi.ui.widgets.list import Column, SummaryLabel
from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.gui.search import SearchBar
from stoqlib.gui.columns import AccessorColumn
from stoqlib.database import rollback_and_begin

from stoq.gui.application import AppWindow
from stoq.gui.slaves.filter import FilterSlave
from stoq.lib.validators import get_price_format_str
from stoq.lib.runtime import new_transaction
from stoq.lib.defaults import ALL_ITEMS_INDEX, ALL_BRANCHES
from stoq.domain.person import Person
from stoq.domain.product import Product
from stoq.domain.sellable import AbstractSellable
from stoq.domain.interfaces import ISellable, IStorable, IBranch

_ = gettext.gettext


class WarehouseApp(AppWindow):
    app_name = _('Warehouse')
    gladefile = "warehouse"
    widgets = ('sellable_list', 
               'list_vbox',
               'retention_button',
               'history_button',
               'receive_action',
               'transfer_action')
    

    def __init__(self, app):
        self.conn = new_transaction()
        AppWindow.__init__(self, app)
        self._setup_slaves()
        self._setup_widgets()
        self._update_view()

    def _select_first_item(self, list):
        if len(list):
            # XXX this part will be removed after bug 2178
            list.select(list[0])

    def _setup_widgets(self):
        self.sellable_list.set_columns(self._get_columns())
        self.sellable_list.set_selection_mode(gtk.SELECTION_MULTIPLE)
        value_format = '<b>%s</b>' % get_price_format_str()
        self.summary_label = SummaryLabel(klist=self.sellable_list,
                                          column='quantity',
                                          label=_('<b>Stock Total:</b>'),
                                          value_format=value_format)
        self.summary_label.show()
        self.list_vbox.pack_start(self.summary_label, False)
        self.search_bar.set_focus()

    def _setup_slaves(self):
        table = Person.getAdapterClass(IBranch)
        items = [(o.get_adapted().name, o) 
                  for o in table.select(connection=self.conn)]
        if not items:
            raise DatabaseInconsistency('You should have at least one '
                                        'branch on your database.'
                                        'Found zero')
        items.append(ALL_BRANCHES)
        self.filter_slave = FilterSlave(items, selected=ALL_ITEMS_INDEX)
        self.filter_slave.set_filter_label(_('Show products at:'))
        self.search_bar = SearchBar(self, AbstractSellable,
                                    self._get_columns(), 
                                    filter_slave=self.filter_slave) 
        self.filter_slave.connect('status-changed',
                                  self._on_filter_slave_changed)
        self.search_bar.set_searchbar_labels(_('Matching:'))
        self.search_bar.set_result_strings(_('product'), _('products'))
        self.attach_slave("search_bar_holder", self.search_bar)

    def _update_view(self):
        has_stock = len(self.sellable_list) > 0
        self.retention_button.set_sensitive(has_stock)
        one_selected = len(self.sellable_list.get_selected_rows()) == 1
        self.history_button.set_sensitive(one_selected)

    def _get_columns(self):
        return [Column('code', title=_('Code'), sorted=True,
                       data_type=str, width=100),
                Column('base_sellable_info.description', 
                       title=_('Description'),
                       expand=True, data_type=str, searchable=True),
                AccessorColumn('supplier', self._get_supplier, 
                               title=_('Supplier'), data_type=str),
                AccessorColumn('quantity', self._get_stock_balance, 
                               title=_('Quantity'), data_type=float)]
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
        branch = self.filter_slave.get_selected_status()
        if branch == ALL_ITEMS_INDEX:
            branch = None
        storable = self._get_storable(instance)
        return storable.get_full_balance(branch)

    def _update_stock_total(self):
        self.summary_label.update_total()

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
        self._select_first_item(self.sellable_list)
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

    def _on_filter_slave_changed(self, slave):
        self.sellable_list.refresh()
        self._update_stock_total()

    def on_sellable_list__selection_changed(self, *args):
        self._update_view()
