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
## Author(s):       Bruno Rafael Garcia      <brg@async.com.br>
##
"""
stoq/gui/search/sale.py

    Search dialogs for sale objects
"""

import gettext
from datetime import date

import gtk
from kiwi.datatypes import currency
from kiwi.ui.widgets.list import Column
from sqlobject.sqlbuilder import AND, LEFTJOINOn
from stoqlib.database import rollback_and_begin
from stoqlib.gui.columns import ForeignKeyColumn
from stoqlib.gui.search import SearchDialog

from stoq.domain.interfaces import IClient, ISalesPerson
from stoq.domain.person import Person
from stoq.domain.sale import Sale
from stoq.lib.defaults import ALL_ITEMS_INDEX
from stoq.gui.slaves.filter import FilterSlave

_ = gettext.gettext


class SaleSearch(SearchDialog):
    title = _("Search for Sales")
    size = (800, 600)
    search_table = Sale

    def __init__(self):
        SearchDialog.__init__(self, self.search_table, title=self.title,
                              searching_by_date=True)
        self._setup_widgets()

    def _select_first_item(self, list):
        if len(list):
            # XXX this part will be removed after bug 2178
            list.select(list[0])

    def _setup_widgets(self):
        self.search_bar.set_result_strings(_('sale'), _('sales'))
        self.search_bar.set_searchbar_labels(_('matching:'))

    #
    # SearchBar Hooks
    #

    def get_columns(self):
        return [Column('order_number', title=_('Number'), width=80,
                       data_type=str, sorted=True),
                Column('open_date', title=_('Date Started'), width=120,
                       data_type=date, justify=gtk.JUSTIFY_RIGHT),
                ForeignKeyColumn(Person, 'name', title=_('Client'),
                                 data_type=str, expand=True, width=210,
                                 obj_field='client', adapted=True),
                ForeignKeyColumn(Person, 'name', title=_('Salesperson'),
                                 data_type=str, width=210,
                                 obj_field='salesperson', adapted=True),
                Column('status_name', title=_('Status'), width=80,
                       data_type=str),
                Column('total_sale_amount', title=_('Total'),
                       data_type=currency)]

    def get_query_args(self):
        # It seems that there is a bug in SQLObject which doesn't allow us
        # to have a LEFTJoin and single joins at the same time.
        # See bug 2207
        client_table = Person.getAdapterClass(IClient)
        return dict(join=LEFTJOINOn(Sale, client_table,
                                    Sale.q.clientID == client_table.q.id))

    def get_extra_query(self):
        salesperson_table = Person.getAdapterClass(ISalesPerson)
        q1 = Sale.q.salespersonID == salesperson_table.q.id
        q2 = salesperson_table.q._originalID == Person.q.id
        status = self.filter_slave.get_selected_status()
        if status != ALL_ITEMS_INDEX:
            q3 = Sale.q.status == status
            return AND(q1, q2, q3)
        return AND(q1, q2)

    def update_klist(self, sales=[]):
        rollback_and_begin(self.conn)
        self.klist.clear()
        for sale in sales:
            # Since search bar change the connection internally we must get
            # the objects back in our main connection
            obj = Sale.get(sale.id, connection=self.conn)
            self.klist.append(obj)
        self._select_first_item(self.klist)
            
    #
    # SearchDialog Hooks
    #

    def get_filter_slave(self):
        items = [(value, key) for key, value in Sale.statuses.items()]
        items.append((_('Any'), ALL_ITEMS_INDEX))
        self.filter_slave = FilterSlave(items, selected=ALL_ITEMS_INDEX)
        self.filter_slave.set_filter_label(_('Show sales with status'))
        return self.filter_slave

    def after_search_bar_created(self):
        self.filter_slave.connect('status-changed', 
                                  self.search_bar.search_items)
        

