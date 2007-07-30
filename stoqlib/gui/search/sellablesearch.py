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
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##              Henrique Romano             <henrique@async.com.br>
##              Johan Dahlin                <jdahlin@async.com.br>
##
##
""" Implementation of sellable search """

from decimal import Decimal

import gtk
from kiwi.datatypes import currency
from kiwi.enums import SearchFilterPosition
from kiwi.ui.objectlist import Column
from sqlobject.sqlbuilder import AND

from stoqlib.domain.person import PersonAdaptToBranch
from stoqlib.domain.product import Product
from stoqlib.domain.interfaces import ISellable, IStorable
from stoqlib.domain.sellable import ASellable
from stoqlib.domain.views import SellableFullStockView
from stoqlib.gui.base.columns import AccessorColumn
from stoqlib.gui.base.search import SearchEditor
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.validators import format_quantity
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class SellableSearch(SearchEditor):
    title = _('Search for sale items')
    size = (750, 500)
    table = search_table = SellableFullStockView
    editor_class = None
    model_list_lookup_attr = 'product_id'
    footer_ok_label = _('_Add sale items')
    searchbar_result_strings = (_('sale item'), _('sale items'))

    def __init__(self, conn, hide_footer=False, hide_toolbar=True,
                 selection_mode=gtk.SELECTION_MULTIPLE, search_str=None,
                 sale_items=None, quantity=None, double_click_confirm=False):
        """
        @param conn: a sqlobject Transaction instance
        @param hide_footer: do I have to hide the dialog footer?
        @param hide_toolbar: do I have to hide the dialog toolbar?
        @param selection_mode: the kiwi list selection mode
        @param search_str: FIXME
        @param sale_items: optionally, a list of sellables which will be
           used to deduct stock values
        @param quantity: the quantity of stock to add to the order,
                      is necessary to supply if you supply an order.
        @param double_click_confirm: If double click a item in the list should
          automatically confirm
        """
        self.quantity = quantity
        self.has_stock_mode = sysparam(conn).HAS_STOCK_MODE
        self._delivery_service = sysparam(conn).DELIVERY_SERVICE
        SearchEditor.__init__(self, conn, table=self.table,
                              search_table=self.search_table,
                              editor_class=self.editor_class,
                              hide_footer=hide_footer,
                              hide_toolbar=hide_toolbar,
                              selection_mode=selection_mode,
                              double_click_confirm=double_click_confirm)
        self.set_searchbar_labels(_('matching:'))
        self.set_result_strings(*self.searchbar_result_strings)
        self.set_ok_label(self.footer_ok_label)
        self.product_table = Product.getAdapterClass(ISellable)
        if search_str:
            self.set_searchbar_search_string(search_str)
            self.search.refresh()

        # FIXME: This dictionary should be used to deduct from the
        #        current stock (in the current branch) and not others
        self.current_sale_stock = {}

        if sale_items:
            if selection_mode == gtk.SELECTION_MULTIPLE:
                raise TypeError("gtk.SELECTION_MULTIPLE is not supported "
                                "when supplying an order")
            if self.quantity is None:
                raise TypeError("You need to specify a quantity "
                                "when supplying an order")
            for item in sale_items:
                if IStorable(item.sellable.get_adapted(), None):
                    quantity = self.current_sale_stock.get(item.sellable.id, 0)
                    quantity += item.quantity
                    self.current_sale_stock[item.sellable.id] = quantity

    #
    # Hooks
    #

    def create_filters(self):
        #if not self.has_stock_mode:
        #    return
        self.set_text_field_columns(['description'])
        self.executer.set_query(self._executer_query)

        self.branch_filter = self.create_branch_filter(
            _('Show sale items at'))
        self.search.add_filter(self.branch_filter, SearchFilterPosition.TOP)

    def get_columns(self):
        """Hook called by SearchEditor"""
        columns = [Column('id', title=_('Code'), data_type=int,
                          format="%03d", sorted=True, width=90,
                          justify=gtk.JUSTIFY_RIGHT),
                   Column('barcode', title=_('Barcode'), data_type=str,
                          width=90, visible=False),
                   Column('description', title= _('Description'),
                          data_type=str, expand=True),
                   Column('price', title=_('Price'), data_type=currency,
                          width=80, justify=gtk.JUSTIFY_RIGHT)]
        if self.has_stock_mode:
            column = AccessorColumn('stock', title=_('Stock'),
                                    accessor=self._get_available_stock,
                                    format_func=format_quantity,
                                    data_type=Decimal,
                                    width=80)
            columns.append(column)
        return columns

    def update_widgets(self):
        sellable_view = self.results.get_selected()
        if not sellable_view:
            return
        sellable = ASellable.get(sellable_view.id, self.conn)
        if (IStorable(sellable.get_adapted(), None) and
            self.quantity > self._get_available_stock(sellable_view)):
            self.ok_button.set_sensitive(False)
        else:
            self.ok_button.set_sensitive(True)

    #
    # Private
    #

    def _executer_query(self, query, conn):
        queries = []
        if query is not None:
            queries.append(query)

        if self._delivery_service :
            queries.append(AND(
                SellableFullStockView.q.status == ASellable.STATUS_AVAILABLE,
                SellableFullStockView.q.id != self._delivery_service.id))
        # If we select a quantity which is not an integer, filter out
        # sellables without a unit set
        if self.quantity is not None and (self.quantity % 1) != 0:
            queries.append(ASellable.q.unitID != None)
        branch = self.branch_filter.get_state().value
        if branch is not None:
            branch = PersonAdaptToBranch.get(branch, connection=conn)
        query = AND(*queries)
        return SellableFullStockView.select_by_branch(query, branch,
                                                      connection=conn)

    def _get_available_stock(self, sellable_view):
        if sellable_view.stock is None:
            return None
        return sellable_view.stock - self.current_sale_stock.get(
            sellable_view.id, 0)

