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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##              Henrique Romano             <henrique@async.com.br>
##
##
""" Implementation of sellable search """

import gettext
import decimal

import gtk
from kiwi.datatypes import currency
from kiwi.ui.widgets.list import Column
from sqlobject.sqlbuilder import AND

from stoqlib.gui.base.search import SearchEditor
from stoqlib.gui.base.columns import AccessorColumn, ForeignKeyColumn
from stoqlib.lib.defaults import ALL_BRANCHES, ALL_ITEMS_INDEX
from stoqlib.gui.slaves.filter import FilterSlave
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.validators import format_quantity
from stoqlib.domain.sellable import AbstractSellable, BaseSellableInfo
from stoqlib.domain.product import Product
from stoqlib.domain.person import Person
from stoqlib.domain.interfaces import IStorable, IBranch, ISellable

_ = lambda msg: gettext.dgettext('stoqlib', msg)


class SellableSearch(SearchEditor):
    title = _('Search for sale items')
    size = (750, 500)
    table = search_table = AbstractSellable
    editor_class = None
    footer_ok_label = _('_Add sale items')
    searchbar_result_strings = (_('sale item'), _('sale items'))

    def __init__(self, conn, hide_footer=False, hide_toolbar=True,
                 selection_mode=gtk.SELECTION_MULTIPLE):
        self.has_stock_mode = sysparam(conn).HAS_STOCK_MODE
        SearchEditor.__init__(self, conn, table=self.table,
                              editor_class=self.editor_class,
                              search_table=self.search_table,
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

    def get_stock_balance(self, product):
        if not isinstance(product, self.product_table):
            return decimal.Decimal('0.0')
        branch = self.get_branch()
        adapted = product.get_adapted()
        conn = adapted.get_connection()
        storable = IStorable(adapted, connection=conn)
        return storable.get_full_balance(branch)

    #
    # Hooks
    #

    def get_columns(self):
        """Hook called by SearchEditor"""
        columns = [Column('code', _('Code'), data_type=str, sorted=True,
                          width=80),
                   ForeignKeyColumn(BaseSellableInfo, 'description',
                                    _('Description'), data_type=str,
                                    obj_field='base_sellable_info',
                                    width=260),
                   ForeignKeyColumn(BaseSellableInfo, 'price',
                                    _('Price'), data_type=currency,
                                    obj_field='base_sellable_info',
                                    width=80)]
        if self.has_stock_mode:
            column = AccessorColumn('stock', self.get_stock_balance,
                                    format_func=format_quantity,
                                    title=_('Stock'), data_type=float)
            columns.append(column)
        return columns

    def get_extra_query(self):
        """Hook called by SearchBar"""
        q1 = BaseSellableInfo.q.id == AbstractSellable.q.base_sellable_infoID
        q2 = AbstractSellable.get_available_sellables_query(self.conn)
        return AND(q1, q2)

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
        self.filter_slave = FilterSlave(items, selected=ALL_ITEMS_INDEX)
        self.filter_slave.set_filter_label(_('Show sale items at'))
        return self.filter_slave

    def after_search_bar_created(self):
        self.filter_slave.connect('status-changed',
                                  self.search_bar.search_items)
