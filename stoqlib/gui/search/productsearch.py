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
## Author(s):   Bruno Rafael Garcia         <brg@async.com.br>
##              Evandro Vale Miquelito      <evandro@async.com.br>
##
""" Search dialogs for product objects """

from decimal import Decimal

import gtk
from kiwi.datatypes import currency
from kiwi.ui.objectlist import Column
from kiwi.argcheck import argcheck
from sqlobject.sqlbuilder import AND

from stoqlib.domain.product import Product, ProductFullStockView
from stoqlib.gui.editors.producteditor import ProductEditor
from stoqlib.gui.slaves.productslave import ProductFilterSlave
from stoqlib.gui.search.sellablesearch import SellableSearch, SellableView
from stoqlib.gui.base.dialogs import print_report
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.defaults import ALL_ITEMS_INDEX
from stoqlib.lib.validators import format_quantity
from stoqlib.reporting.product import ProductReport

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

    def _hide_column(self, colname):
        column = self.klist.get_column_by_name(colname)
        col_index = self.klist.get_columns().index(column)
        self.klist.set_column_visibility(col_index, False)

    def on_print_button_clicked(self, button):
        print_report(ProductReport, list(self.klist))

    #
    # SearchDialog Hooks
    #

    def get_filter_slave(self):
        self.filter_slave = ProductFilterSlave(self.conn)
        return self.filter_slave

    def get_branch(self):
        # We have not a filter for branches in this dialog and in this case
        # there is no filter for branches when getting the stocks
        return

    #
    # SearchEditor Hooks
    #

    @argcheck(SellableView)
    def get_editor_model(self, model):
        return Product.get(model.product_id, connection=self.conn)

    def get_columns(self):
        return [Column('code', title=_('Code'), data_type=int, sorted=True,
                       format='%03d', width=70),
                Column('barcode', title=_('Barcode'), data_type=str,
                       width=120),
                Column('description', title=_('Description'), data_type=str,
                       expand=True),
                Column('supplier_name', title=_('Supplier'), data_type=str,
                       width=150),
                Column('cost', _('Cost'), data_type=currency,
                       width=80),
                Column('price', title=_('Price'), data_type=currency,
                       width=80),
                Column('stock', title=_('Stock Total'),
                       format_func=format_quantity,
                       data_type=Decimal, width=100)]

    def get_extra_query(self):
        branch = self.filter_slave.get_selected_branch()
        status = self.filter_slave.get_selected_status()
        if branch != ALL_ITEMS_INDEX:
            self.set_searchtable(SellableView)
            q1 = self.search_table.q.branch_id == branch.id
            if status == ALL_ITEMS_INDEX:
                return q1
            else:
                return AND(q1, self.search_table.q.status == status)
        else:
            self.set_searchtable(ProductFullStockView)
            if status != ALL_ITEMS_INDEX:
                return self.search_table.q.status == status
