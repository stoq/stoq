# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
##
"""
stoq/gui/search/service.py
    
    Search dialogs for services
"""

import gettext

import gtk
from kiwi.datatypes import currency
from stoqlib.gui.columns import Column, ForeignKeyColumn

from stoq.lib.defaults import ALL_ITEMS_INDEX
from stoq.domain.sellable import BaseSellableInfo
from stoq.domain.interfaces import ISellable
from stoq.domain.service import Service
from stoq.gui.editors.service import ServiceEditor
from stoq.gui.slaves.filter import FilterSlave
from stoq.gui.search.sellable import SellableSearch

_ = gettext.gettext


class ServiceSearch(SellableSearch):
    title = _('Service Search')
    table = Service
    search_table = Service.getAdapterClass(ISellable)
    editor_class = ServiceEditor
    footer_ok_label = _('Add services')
    searchbar_result_strings = (_('service'), _('services'))
    
    def __init__(self, conn, hide_footer=True, hide_toolbar=False,
                 selection_mode=gtk.SELECTION_BROWSE, 
                 hide_cost_column=False, use_product_statuses=None,
                 hide_price_column=False):
        self.hide_cost_column = hide_cost_column
        self.hide_price_column = hide_price_column
        self.use_product_statuses = use_product_statuses
        SellableSearch.__init__(self, conn, hide_footer=hide_footer, 
                                hide_toolbar=hide_toolbar,
                                selection_mode=selection_mode)

    #
    # SearchDialog Hooks
    #
    
    def get_filter_slave(self):
        statuses = [(value, key) 
                        for key, value in self.search_table.statuses.items()]
        statuses.append((_('Any'), ALL_ITEMS_INDEX))
        self.filter_slave = FilterSlave(statuses, selected=ALL_ITEMS_INDEX)
        self.filter_slave.set_filter_label(_('Show services with status'))
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

    def get_columns(self):
        columns = [Column('code', _('Code'), data_type=str, sorted=True, 
                       width=80),
                   ForeignKeyColumn(BaseSellableInfo, 'description', 
                                    _('Description'), data_type=str, 
                                    obj_field='base_sellable_info',
                                    expand=True)]

        if not self.hide_cost_column:
            columns.append(Column('cost', _('Cost'), data_type=currency,
                           width=80))

        if not self.hide_price_column:
            columns.append(ForeignKeyColumn(BaseSellableInfo, 'price', 
                                            _('Price'), data_type=currency, 
                                            obj_field='base_sellable_info',
                                            width=80))

        columns.append(Column('status_string', _('Status'), data_type=str,
                              width=70))
        return columns

    def get_extra_query(self):
        # FIXME Waiting for a SQLObject bug Fix. We can not create sqlbuilder
        # queries for foreignkeys and inherited tables
        # table = self.search_table
        # q1 = AbstractSellable.q.id == table.q.id
        # q2 = BaseSellableInfo.q.id == table.q.base_sellable_infoID
        status = self.filter_slave.get_selected_status()
        if status != ALL_ITEMS_INDEX:
            return self.search_table.q.status == status
