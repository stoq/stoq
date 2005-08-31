# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2004 Async Open Source <http://www.async.com.br>
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
import operator

import gtk
from kiwi.ui.widgets.list import Column
from kiwi.ui.views import SlaveView
from kiwi.ui.delegates import SlaveDelegate
from stoqlib.gui.search import SearchDialog
from stoqlib.gui.columns import AccessorColumn

from stoq.lib.defaults import ALL_BRANCHES
from stoq.lib.parameters import sysparam
from stoq.domain.sellable import AbstractSellable, get_formated_price
from stoq.domain.product import ProductAdaptToSellable
from stoq.domain.person import PersonAdaptToBranch
from stoq.domain.interfaces import IStorable

_ = gettext.gettext


#
# Slaves
#



class SellableSearchHeaderSlave(SlaveView):
    gladefile = 'SellableSearchHeader'
    widgets = ('sellable_description', 'price')

    def __init__(self, parent):
        SlaveView.__init__(self, gladefile=self.gladefile, 
                           widgets=self.widgets)
        self.parent = parent
        self.sellable_description.set_size('x-large')
        self.price.set_size('x-large')
        self.update_widgets()
                    
    def update_widgets(self, sellables=None):
        color = 'black'
        if not sellables:
            desc = _('No item selected ')
            price_desc = ''
            color = 'DarkGray'
        elif len(sellables) > 1:
            desc = _('Multiple items selected')
            prices = [s.get_price() for s in sellables]
            total = reduce(operator.add, prices, 0.0)
            total_str = get_formated_price(total)
            price_desc = 'Total: %s' % total_str
        else:
            sellable = sellables[0]
            price_desc = sellable.get_price_string()
            desc = sellable.description
            
        self.sellable_description.set_color(color)
        self.price.set_text(price_desc)
        self.sellable_description.set_text(desc)


class SellableSearchFooter(SlaveDelegate):
    gladefile = 'SellableSearchFooter'
    widgets = ('branch_combo',)

    def __init__(self, parent, conn):
        SlaveDelegate.__init__(self, gladefile=self.gladefile,
                               widgets=self.widgets)
        self.parent = parent
        self.conn = conn
        self.setup_branch_combo()

    def setup_branch_combo(self):
        table = PersonAdaptToBranch

        branch_list = table.select(connection=self.conn)
        items = [(o.get_adapted().name, o) for o in branch_list]
        items.append(ALL_BRANCHES)

        assert items
        if len(items) == 1:
            for widget in (self.branch_combo, self.update_button):
                widget.set_sensitive(False)
        else:
            self.branch_combo.prefill(items)
            self.branch_combo.select_item_by_data(ALL_BRANCHES[1])

    def get_selected_branch(self):
        return self.branch_combo.get_selected_data()

    def on_branch_combo__content_changed(self, *args):
        self.parent.search_bar.search_items()


class SellableSearch(SearchDialog):
    title = _('Search for sellable items') 
    size = (800, 500)
    search_table = AbstractSellable
 
    def __init__(self, conn, search_str=None):
        selection_mode = gtk.SELECTION_MULTIPLE
        SearchDialog.__init__(self, self.search_table, hide_footer=False,
                              parent_conn=conn,
                              selection_mode=selection_mode,
                              search_lbl_text=_('Find Sellables'))
        self.search_bar.set_search_string(search_str)
        self.search_bar.search_items()

    def setup_slaves(self, **kwargs):
        SearchDialog.setup_slaves(self, **kwargs)
        self.header_slave = SellableSearchHeaderSlave(self)
        self.attach_slave('extra_header', self.header_slave)

        if self.has_stock_mode:
            self.footer_slave = SellableSearchFooter(self, self.conn)
            self.attach_slave('extra_holder', self.footer_slave)
        else:
            self.footer_slave = None


    
    #
    # Accessors
    #
    

    
    def get_stock_balance(self, instance):
        """Accessor called by AccessorColumn"""
        if not isinstance(instance, ProductAdaptToSellable):
            return 'No stock'
        assert self.footer_slave
        branch = self.footer_slave.get_selected_branch()
    
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
                          expand=True, data_type=str),
                   Column('price', title=_('Price'), data_type=float,
                          width=90)]
        if self.has_stock_mode:
            column = AccessorColumn('stock', self.get_stock_balance, 
                                    title=_('Stock'), data_type=float)
            columns.append(column) 
        return columns

    def update_widgets(self, *args):
        """Hook called by BaseListSlave"""
        items = self.klist.get_selected_rows()
        self.header_slave.update_widgets(items)
