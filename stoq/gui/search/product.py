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
## Author(s):   Bruno Rafael Garcia         <brg@async.com.br>
##              Evandro Vale Miquelito      <evandro@async.com.br>
##
"""
stoq/gui/search/product.py
    
    Search dialogs for product objects
"""

import gettext

import gtk
from kiwi.datatypes import currency
from sqlobject.sqlbuilder import AND
from stoqlib.gui.search import SearchEditor
from stoqlib.gui.columns import Column, AccessorColumn, ForeignKeyColumn

from stoq.lib.defaults import ALL_ITEMS_INDEX
from stoq.domain.sellable import AbstractSellable, BaseSellableInfo
from stoq.domain.interfaces import ISellable
from stoq.domain.product import Product
from stoq.gui.editors.product import ProductEditor
from stoq.gui.slaves.filter import FilterSlave

_ = gettext.gettext


class ProductSearch(SearchEditor):
    title = _('Product Search')
    size = (800, 600)
    table = Product
    search_table = Product.getAdapterClass(ISellable)
    editor_class = ProductEditor
    
    def __init__(self, conn, hide_footer=True, hide_toolbar=False,
                 selection_mode=gtk.SELECTION_BROWSE):
        SearchEditor.__init__(self, conn, self.table, self.editor_class,
                              search_table=self.search_table, 
                              hide_footer=hide_footer,
                              hide_toolbar=hide_toolbar,
                              selection_mode=selection_mode,
                              title=self.title)
        self.search_bar.set_result_strings(_('product'), _('products'))
        self.search_bar.set_searchbar_labels(_('matching'))

    #
    # SearchDialog Hooks
    #
    
    def get_filter_slave(self):
        products = [(value, key) for key, value in
                    self.search_table.statuses.items()]
        products.append((_('Any'), ALL_ITEMS_INDEX))
        self.filter_slave = FilterSlave(products, selected=ALL_ITEMS_INDEX)
        self.filter_slave.set_filter_label(_('Show products with status'))
        return self.filter_slave

    def after_search_bar_created(self):
        self.filter_slave.connect('status-changed',
                                 self.search_bar.search_items)

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
                                 width=260),
                AccessorColumn('suppliers', self.get_main_supplier_name,
                               title=_('Supplier'), data_type=str,
                               width=200),
                Column('cost', _('Cost'), data_type=currency, width=80),
                ForeignKeyColumn(BaseSellableInfo, 'price', 
                                 _('Price'), data_type=currency, 
                                 obj_field='base_sellable_info',
                                 width=80),
                Column('status_string', _('Status'), data_type=str)]

    def get_extra_query(self):
        # FIXME Waiting for a SQLObject bug Fix. We can not create sqlbuilder
        # queries for foreignkeys and inherited tables
        # table = self.search_table
        # q1 = AbstractSellable.q.id == table.q.id
        # q2 = BaseSellableInfo.q.id == table.q.base_sellable_infoID
        status = self.filter_slave.get_selected_status()
        if status != ALL_ITEMS_INDEX:
            return AbstractSellable.q.status == status
