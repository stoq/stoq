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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
""" Implementation of sellable search """

from decimal import Decimal

import gtk
from kiwi.datatypes import currency
from kiwi.ui.objectlist import SearchColumn

from stoqlib.api import api
from stoqlib.database.orm import AND
from stoqlib.domain.interfaces import IStorable
from stoqlib.domain.sellable import Sellable
from stoqlib.domain.views import SellableFullStockView
from stoqlib.gui.base.columns import AccessorColumn
from stoqlib.gui.base.search import SearchEditor
from stoqlib.lib.defaults import sort_sellable_code
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.formatters import format_quantity
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
                 sale_items=None, quantity=None, double_click_confirm=False,
                 info_message=None):
        """
        Create a new SellableSearch object.
        @param conn: a orm Transaction instance
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
        self._first_search = True
        self._first_search_string = search_str
        self.quantity = quantity
        self._delivery_sellable = sysparam(conn).DELIVERY_SERVICE.sellable

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
                if IStorable(item.sellable.product, None):
                    quantity = self.current_sale_stock.get(item.sellable.id, 0)
                    quantity += item.quantity
                    self.current_sale_stock[item.sellable.id] = quantity

        SearchEditor.__init__(self, conn, table=self.table,
                              search_table=self.search_table,
                              editor_class=self.editor_class,
                              hide_footer=hide_footer,
                              hide_toolbar=hide_toolbar,
                              selection_mode=selection_mode,
                              double_click_confirm=double_click_confirm)
        self.set_searchbar_labels(_('Show items matching:'))
        self.set_result_strings(*self.searchbar_result_strings)
        self.set_ok_label(self.footer_ok_label)

        if info_message:
            self.add_message_bar(info_message, gtk.MESSAGE_INFO)

        if search_str:
            self.set_searchbar_search_string(search_str)
            self.search.refresh()

    def key_shift_Return(self):
        self.confirm()

    def key_control_Return(self):
        self.confirm()

    def key_shift_KP_Enter(self):
        self.confirm()

    def key_control_KP_Enter(self):
        self.confirm()

    def confirm(self):
        # FIXME: This is a hack, we need to do proper validation in the parent
        if not self.ok_button.props.sensitive:
            return
        super(SellableSearch, self).confirm()

    def create_filters(self):
        self.set_text_field_columns(['description', 'category_description',
                                     'barcode'])
        self.executer.set_query(self._executer_query)

    def get_columns(self):
        """Hook called by SearchEditor"""
        return [SearchColumn('code', title=_('Code'), data_type=str,
                              sort_func=sort_sellable_code,
                              sorted=True),
                SearchColumn('barcode', title=_('Barcode'), data_type=str,
                              visible=False),
                SearchColumn('description', title=_('Description'),
                             data_type=str, expand=True),
                SearchColumn('price', title=_('Price'), data_type=currency,
                              justify=gtk.JUSTIFY_RIGHT, width=120),
                SearchColumn('category_description', title=_('Category'),
                             data_type=str, visible=False),
                AccessorColumn('stock', title=_(u'Stock'),
                                accessor=self._get_available_stock,
                                format_func=format_quantity, width=90,
                                data_type=Decimal)]

    def update_widgets(self):
        sellable_view = self.results.get_selected()
        self.set_edit_button_sensitive(bool(sellable_view))
        if not sellable_view:
            return
        sellable = Sellable.get(sellable_view.id, self.conn)
        if (IStorable(sellable.product, None) and
            self.quantity > self._get_available_stock(sellable_view)):
            self.ok_button.set_sensitive(False)
        else:
            self.ok_button.set_sensitive(True)

    def search_completed(self, results, states):
        if not self._first_search:
            if self._first_search_string != self.get_searchbar_search_string():
                self.remove_message_bar()

        if len(results) >= 1:
            results.select(results[0])

        self.search.focus_search_entry()
        self._first_search = False

    #
    # Private
    #

    def _executer_query(self, query, having, conn):
        queries = []
        if query is not None:
            queries.append(query)

        if self._delivery_sellable:
            queries.append(AND(
                SellableFullStockView.q.status == Sellable.STATUS_AVAILABLE,
                SellableFullStockView.q.id != self._delivery_sellable.id))
        # If we select a quantity which is not an integer, filter out
        # sellables without a unit set
        if self.quantity is not None and (self.quantity % 1) != 0:
            queries.append(Sellable.q.unitID != None)
        branch = api.get_current_branch(conn)
        query = AND(*queries)
        return SellableFullStockView.select_by_branch(query, branch,
                                                      connection=conn)

    def _get_available_stock(self, sellable_view):
        if sellable_view.stock is None:
            return None
        return sellable_view.stock - self.current_sale_stock.get(
            sellable_view.id, 0)
