# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source <http://www.async.com.br>
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
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##              Henrique Romano             <henrique@async.com.br>
##
##
""" Implementation of sellable search """

import decimal

import gtk
from kiwi.datatypes import currency
from kiwi.ui.widgets.list import Column
from sqlobject.sqlbuilder import AND, OR

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.base.search import SearchEditor
from stoqlib.lib.defaults import ALL_BRANCHES, ALL_ITEMS_INDEX
from stoqlib.gui.slaves.filter import FilterSlave
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.validators import format_quantity
from stoqlib.domain.sellable import (AbstractSellable, SellableView,
                                     SellableFullStockView)
from stoqlib.domain.product import Product
from stoqlib.domain.person import Person
from stoqlib.domain.interfaces import IBranch, ISellable

_ = stoqlib_gettext


class SellableSearch(SearchEditor):
    title = _('Search for sale items')
    size = (750, 500)
    table = search_table = SellableView
    editor_class = None
    model_list_lookup_attr = 'product_id'
    footer_ok_label = _('_Add sale items')
    searchbar_result_strings = (_('sale item'), _('sale items'))

    def __init__(self, conn, hide_footer=False, hide_toolbar=True,
                 selection_mode=gtk.SELECTION_MULTIPLE):
        self.has_stock_mode = sysparam(conn).HAS_STOCK_MODE
        SearchEditor.__init__(self, conn, table=self.table,
                              search_table=self.search_table,
                              editor_class=self.editor_class,
                              hide_footer=hide_footer,
                              hide_toolbar=hide_toolbar,
                              selection_mode=selection_mode)
        self.set_searchbar_labels(_('matching:'))
        self.set_result_strings(*self.searchbar_result_strings)
        self.set_ok_label(self.footer_ok_label)
        self.product_table = Product.getAdapterClass(ISellable)

    #
    # Accessors
    #

    def get_branch(self):
        branch = self.filter_slave.get_selected_status()
        if branch == ALL_ITEMS_INDEX:
            branch = None
        return branch

    #
    # Hooks
    #

    def get_columns(self):
        """Hook called by SearchEditor"""
        columns = [Column('code', title=_('Code'), data_type=int,
                          format="%03d", sorted=True, width=90),
                   Column('barcode', title=_('Barcode'), data_type=str,
                          width=90, visible=False),
                   Column('description', title= _('Description'),
                          data_type=str, expand=True),
                   Column('supplier_name', title= _('Supplier'),
                          data_type=str, width=150),
                   Column('price', title=_('Price'), data_type=currency,
                          width=80)]
        if self.has_stock_mode:
            column = Column('stock', title=_('Stock'),
                            format_func=format_quantity,
                            data_type=decimal.Decimal,
                            width=80)
            columns.append(column)
        return columns

    def get_extra_query(self):
        """Hook called by SearchBar"""
        service = sysparam(self.conn).DELIVERY_SERVICE
        branch = self.filter_slave.get_selected_status()
        if branch != ALL_ITEMS_INDEX:
            self.set_searchtable(SellableView)
            q3 = OR(SellableView.q.branch_id == branch.id,
                    SellableView.q.branch_id == None)
        else:
            self.set_searchtable(SellableFullStockView)
            q3 = 1 == 1
        q1 = self.search_table.q.id != service.id
        q2 = self.search_table.q.status == AbstractSellable.STATUS_AVAILABLE
        return AND(q1, q2, q3)

    def get_filter_slave(self):
        if not self.has_stock_mode:
            return
        table = Person.getAdapterClass(IBranch)
        branch_list = table.get_active_branches(self.conn)
        items = [(branch.get_adapted().name, branch)
                    for branch in branch_list]
        if not items:
            raise ValueError('You should have at least one branch at '
                             'this point')
        items.append(ALL_BRANCHES)
        selected = sysparam(self.conn).CURRENT_BRANCH
        self.filter_slave = FilterSlave(items, selected=selected)
        self.filter_slave.set_filter_label(_('Show sale items at'))
        return self.filter_slave

    def after_search_bar_created(self):
        self.filter_slave.connect('status-changed',
                                  self.search_bar.search_items)
