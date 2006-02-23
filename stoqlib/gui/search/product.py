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
## Author(s):   Bruno Rafael Garcia         <brg@async.com.br>
##              Evandro Vale Miquelito      <evandro@async.com.br>
##
""" Search dialogs for product objects """

import gtk
from kiwi.datatypes import currency

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.base.columns import Column, AccessorColumn, ForeignKeyColumn
from stoqlib.lib.defaults import ALL_ITEMS_INDEX
from stoqlib.lib.validators import format_quantity
from stoqlib.domain.sellable import BaseSellableInfo
from stoqlib.domain.interfaces import ISellable
from stoqlib.domain.product import Product
from stoqlib.gui.editors.product import ProductEditor
from stoqlib.gui.slaves.filter import FilterSlave
from stoqlib.gui.search.sellable import SellableSearch

_ = stoqlib_gettext


class ProductSearch(SellableSearch):
    title = _('Product Search')
    table = Product
    search_table = Product.getAdapterClass(ISellable)
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

    #
    # SearchDialog Hooks
    #

    def get_filter_slave(self):
        statuses = [(value, key) 
                        for key, value in self.search_table.statuses.items()]
        statuses.append((_('Any'), ALL_ITEMS_INDEX))
        if self.use_product_statuses:
            statuses = [(value, key) for value, key in statuses 
                            if key in self.use_product_statuses]
            selected = self.use_product_statuses[0]
        else:
            selected = ALL_ITEMS_INDEX
        self.filter_slave = FilterSlave(statuses, selected=selected)
        self.filter_slave.set_filter_label(_('Show products with status'))
        return self.filter_slave

    def get_branch(self):
        # We have not a filter for branches in this dialog and in this case
        # there is no filter for branches when getting the stocks
        return

    #
    # SearchEditor Hooks
    #

    def get_model(self, model):
        return model.get_adapted()

    def get_main_supplier_name(self, sellable):
        return sellable.get_adapted().get_main_supplier_name()


    def get_columns(self):
        return [Column('code', _('Code'), data_type=str, sorted=True,
                       width=80),
                ForeignKeyColumn(BaseSellableInfo, 'description',
                                 _('Description'), data_type=str,
                                 obj_field='base_sellable_info',
                                 width=200),
                AccessorColumn('suppliers', self.get_main_supplier_name,
                               title=_('Supplier'), data_type=str,
                               width=150),
                Column('cost', _('Cost'), data_type=currency,
                       width=80),
                ForeignKeyColumn(BaseSellableInfo, 'price',
                                 _('Price'), data_type=currency,
                                 obj_field='base_sellable_info',
                                 width=80),
                Column('status_string', _('Status'),
                       data_type=str),
                AccessorColumn('stock', self.get_stock_balance,
                               format_func=format_quantity,
                               title=_('Stock Total'), data_type=float)]


    def get_extra_query(self):
        # FIXME Waiting for a SQLObject bug Fix. We can not create sqlbuilder
        # queries for foreignkeys and inherited tables
        # table = self.search_table
        # q1 = AbstractSellable.q.id == table.q.id
        # q2 = BaseSellableInfo.q.id == table.q.base_sellable_infoID
        status = self.filter_slave.get_selected_status()
        if status != ALL_ITEMS_INDEX:
            return self.search_table.q.status == status
