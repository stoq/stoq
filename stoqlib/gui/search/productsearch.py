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
## Author(s):   Bruno Rafael Garcia         <brg@async.com.br>
##              Evandro Vale Miquelito      <evandro@async.com.br>
##              Johan Dahlin                <jdahlin@async.com.br>
##              Fabio Morbec                <fabio@async.com.br>
##
""" Search dialogs for product objects """

from decimal import Decimal

import gtk
from kiwi.datatypes import currency
from kiwi.enums import SearchFilterPosition
from kiwi.ui.search import ComboSearchFilter, DateSearchFilter, Today
from kiwi.ui.objectlist import Column

from stoqlib.domain.person import PersonAdaptToBranch
from stoqlib.domain.product import Product
from stoqlib.domain.sellable import ASellable
from stoqlib.domain.views import ProductFullStockView, ProductQuantityView
from stoqlib.gui.editors.producteditor import ProductEditor
from stoqlib.gui.search.sellablesearch import SellableSearch
from stoqlib.gui.base.dialogs import print_report
from stoqlib.gui.base.search import SearchDialog
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.validators import format_quantity
from stoqlib.reporting.product import ProductReport, ProductQuantityReport

_ = stoqlib_gettext


class ProductSearch(SellableSearch):
    title = _('Product Search')
    table = Product
    size = (775, 450)
    search_table = ProductFullStockView
    editor_class = ProductEditor
    footer_ok_label = _('Add products')
    searchbar_result_strings = (_('product'), _('products'))

    def __init__(self, conn, hide_footer=True, hide_toolbar=False,
                 selection_mode=gtk.SELECTION_BROWSE,
                 hide_cost_column=False, use_product_statuses=None,
                 hide_price_column=False):
        """
        @param conn: a sqlobject Transaction instance
        @param hide_footer: do I have to hide the dialog footer?
        @param hide_toolbar: do I have to hide the dialog toolbar?
        @param selection_mode: the kiwi list selection mode
        @param hide_cost_column: if it's True, no need to show the
                                 column 'cost'
        @param use_product_statuses: a list instance that, if provided, will
                                     overwrite the statuses list defined in
                                     get_filter_slave method
        @param hide_price_column: if it's True no need to show the
                                  column 'price'
        """
        self.use_product_statuses = use_product_statuses
        SellableSearch.__init__(self, conn, hide_footer=hide_footer,
                                hide_toolbar=hide_toolbar,
                                selection_mode=selection_mode)
        if hide_cost_column:
            self._hide_column('cost')
        if hide_price_column:
            self._hide_column('price')
        self.set_edit_button_sensitive(False)
        self.results.connect('selection-changed', self.on_selection_changed)

    def _hide_column(self, colname):
        column = self.results.get_column_by_name(colname)
        col_index = self.results.get_columns().index(column)
        self.results.set_column_visibility(col_index, False)

    def on_print_button_clicked(self, button):
        print_report(ProductReport, list(self.results))

    #
    # SearchDialog Hooks
    #

    def create_filters(self):
        self.set_text_field_columns(['description'])
        self.executer.set_query(self._executer_query)

        # Branch
        branch_filter = self.create_branch_filter(_('In branch:'))
        branch_filter.select(None)
        self.add_filter(branch_filter, columns=[])
        self.branch_filter = branch_filter

        # Status
        statuses = [(desc, id) for id, desc in ASellable.statuses.items()]
        statuses.insert(0, (_('Any'), None))
        status_filter = ComboSearchFilter(_('with status:'), statuses)
        status_filter.select(None)
        self.add_filter(status_filter, columns=['status'],
                        position=SearchFilterPosition.TOP)

    def get_branch(self):
        # We have not a filter for branches in this dialog and in this case
        # there is no filter for branches when getting the stocks
        return

    #
    # SearchEditor Hooks
    #

    def get_editor_model(self, product_full_stock_view):
        return product_full_stock_view.product

    def get_columns(self):
        return [Column('id', title=_('Code'), data_type=int, sorted=True,
                       format='%03d', width=70),
                Column('barcode', title=_('Barcode'), data_type=str,
                       width=120),
                Column('description', title=_('Description'), data_type=str,
                       width=150),
                Column('supplier_name', title=_('Supplier'), data_type=str,
                       width=150),
                Column('cost', _('Cost'), data_type=currency,
                       width=80),
                Column('price', title=_('Price'), data_type=currency,
                       width=80),
                Column('stock', title=_('Stock Total'),
                       format_func=format_quantity,
                       data_type=Decimal, width=100)]

    def _executer_query(self, query, conn):
        branch = self.branch_filter.get_state().value
        if branch is not None:
            branch = PersonAdaptToBranch.get(branch, connection=conn)
        return ProductFullStockView.select_by_branch(query, branch,
                                                     connection=conn)

    def on_selection_changed(self, results, selected):
        can_edit = bool(selected)
        self.set_edit_button_sensitive(can_edit)


def format_data(data):
    # must return zero or report printed show None instead of 0
    if data is None:
        return 0
    return format_quantity(data)


class ProductSearchQuantity(SearchDialog):
    title = _('Product Search')
    size = (775, 450)
    table = search_table = ProductQuantityView

    def on_print_button_clicked(self, button):
        print_report(ProductQuantityReport, list(self.results))

    #
    # SearchDialog Hooks
    #

    def create_filters(self):
        self.set_text_field_columns(['description'])

        # Branch
        branch_filter = self.create_branch_filter(_('In branch:'))
        branch_filter.select(None)
        self.add_filter(branch_filter, SearchFilterPosition.TOP,
                        columns=['branch'])
        self.branch_filter = branch_filter

        # Date
        date_filter = DateSearchFilter(_('Date:'))
        date_filter.select(Today)
        self.add_filter(date_filter, columns=['sold_date', 'received_date'])

    #
    # SearchEditor Hooks
    #

    def get_columns(self):
        return [Column('id', title=_('Code'), data_type=int,
                       sorted=True, format='%03d', width=70),
                Column('description', title=_('Description'), data_type=str,
                       expand=True),
                Column('quantity_sold', title=_('Quantity Sold'),
                       format_func=format_data,
                       data_type=Decimal, width=150),
                Column('quantity_received', title=_('Quantity Received'),
                       format_func=format_data,
                       data_type=Decimal, width=150)]
