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
## Author(s):   Evandro Vale Miquelito  <evandro@async.com.br>
##
"""
stoq/gui/search/giftcertificate.py
    
    Search dialogs for gift certificates
"""

import gettext
import gtk

from stoqlib.gui.search import SearchEditor
from stoqlib.gui.columns import Column

from stoq.lib.validators import get_formatted_price
from stoq.lib.defaults import ALL_ITEMS_INDEX
from stoq.domain.sellable import AbstractSellable
from stoq.domain.interfaces import ISellable
from stoq.domain.giftcertificate import GiftCertificate
from stoq.gui.editors.giftcertificate import GiftCertificateEditor
from stoq.gui.slaves.filter import FilterSlave

_ = gettext.gettext


class GiftCertificateSearch(SearchEditor):
    """A search dialog for different types of gift certificates"""
    title = _('Gift Certificate Search')
    size = (800, 600)
    table = GiftCertificate
    search_table = GiftCertificate.getAdapterClass(ISellable)
    editor_class = GiftCertificateEditor
    
    def __init__(self, hide_footer=True):
        SearchEditor.__init__(self, self.table, self.editor_class,
                              search_table=self.search_table,
                              hide_footer=hide_footer,
                              title=self.title)
        self.search_bar.set_result_strings(_('gift certificate'), 
                                           _('gift certificates'))
        self.search_bar.set_searchbar_labels(_('gift certificates matching'))

    #
    # SearchDialog Hooks
    #
    
    def get_filter_slave(self):
        products = [(value, key) for key, value in
                    self.search_table.states.items()]
        products.append((_('Any'), ALL_ITEMS_INDEX))
        self.filter_slave = FilterSlave(products, selected=ALL_ITEMS_INDEX)
        self.filter_slave.set_filter_label(_('Show'))
        return self.filter_slave

    def after_search_bar_created(self):
        self.filter_slave.connect('status-changed',
                                  self.search_bar.search_items)

    #
    # SearchEditor Hooks
    #

    def get_model(self, model):
        return model.get_adapted()

    def get_columns(self):
        return [Column('code', _('Code'), data_type=str, sorted=True, 
                       width=80),
                Column('description', _('Description'), data_type=str, 
                       width=260),
                Column('cost', _('Cost'), data_type=float,
                       format_func=get_formatted_price, 
                       width=80, justify=gtk.JUSTIFY_RIGHT),
                Column('price', _('Price'), data_type=float,
                       format_func=get_formatted_price, width=80, 
                       justify=gtk.JUSTIFY_RIGHT),
                Column('states_string', _('State'), data_type=str)]

    def get_extra_query(self):
        state = self.filter_slave.get_selected_status()
        if state != ALL_ITEMS_INDEX:
            return AbstractSellable.q.state == state
