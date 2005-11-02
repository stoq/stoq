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
##              Henrique Romano             <henrique@async.com.br>
##
"""
stoq/gui/search/sellable:

    Implementation of sellable search
"""

import gettext

import gtk
from kiwi.ui.widgets.list import Column
from stoqlib.gui.search import SearchDialog
from stoqlib.gui.columns import AccessorColumn

from stoq.gui.slaves.filter import FilterSlave
from stoq.lib.defaults import ALL_BRANCHES, ALL_ITEMS_INDEX
from stoq.lib.parameters import sysparam
from stoq.lib.validators import get_formatted_price
from stoq.domain.sellable import AbstractSellable
from stoq.domain.product import Product
from stoq.domain.person import Person
from stoq.domain.interfaces import IStorable, IBranch, ISellable

_ = gettext.gettext


class SellableSearch(SearchDialog):
    title = _('Search for sellable items') 
    size = (800, 500)
    search_table = AbstractSellable
 
    def __init__(self, conn, search_str=None):
        selection_mode = gtk.SELECTION_MULTIPLE
        SearchDialog.__init__(self, self.search_table, hide_footer=False,
                              parent_conn=conn, 
                              selection_mode=selection_mode)
        self.set_searchbar_labels(_('matching:'))
        self.search_bar.search_items()
        self.set_ok_label(_('Add product/service'))
                
    #
    # Accessors
    #
    
    def get_stock_balance(self, instance):
        """Accessor called by AccessorColumn"""
        table = Product.getAdapterClass(ISellable)
        if not isinstance(instance, table):
            return
        branch = self.filter_slave.get_selected_status()
        if branch == ALL_ITEMS_INDEX:
            branch = None
        adapted = instance.get_adapted()
        storable = IStorable(adapted)
        return storable.get_full_balance_string(branch)
    
    #
    # Hooks
    #
    
    def get_columns(self):
        """Hook called by SearchDialog"""
        self.has_stock_mode = sysparam(self.conn).HAS_STOCK_MODE
        columns = [Column('code', title=_('Code'), sorted=True,
                          data_type=str, width=100),
                   Column('description', title=_('Description'),
                          expand=True, data_type=str, searchable=True),
                   Column('price', title=_('Price'), data_type=float,
                          format_func=get_formatted_price,
                          width=90)]
        if self.has_stock_mode:
            column = AccessorColumn('stock', self.get_stock_balance, 
                                    title=_('Stock'), data_type=float)
            columns.append(column) 
        return columns

    def setup_slaves(self, **kwargs):
        SearchDialog.setup_slaves(self, **kwargs)
        singular, plural = _('product/service'), _('products/services')
        self.set_result_strings(singular, plural)

    def get_filter_slave(self):
        if not self.has_stock_mode:
            return
        table = Person.getAdapterClass(IBranch)
        branch_list = table.select(connection=self.conn)
        items = [(branch.get_adapted().name, branch) 
                    for branch in branch_list]
        if not items:
            raise ValueError('You should have at least one branch at '
                             'this point')
        items.append(ALL_BRANCHES)
        self.filter_slave = FilterSlave(items, selected=ALL_ITEMS_INDEX)
        self.filter_slave.set_filter_label(_('Show products/services at:'))
        return self.filter_slave

    def after_search_bar_created(self):
        self.filter_slave.connect('status-changed',
                                  self.search_bar.search_items)
