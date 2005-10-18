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
## Author(s):       Evandro Vale Miquelito      <evandro@async.com.br>
##
"""
stoq/gui/sales/sale.py:

    Implementation of sales application.
"""

import gtk
import gettext
from datetime import date

from sqlobject.sqlbuilder import AND, LEFTJOINOn
from kiwi.ui.widgets.list import Column
from stoqlib.gui.search import SearchBar
from stoqlib.gui.columns import ForeignKeyColumn
from stoqlib.database import rollback_and_begin

from stoq.domain.sale import Sale
from stoq.domain.person import Person
from stoq.domain.interfaces import IClient, ISalesPerson
from stoq.lib.runtime import new_transaction
from stoq.lib.validators import get_formatted_price
from stoq.lib.defaults import ALL_ITEMS_INDEX
from stoq.gui.application import AppWindow
from stoq.gui.search.person import ClientSearch
from stoq.gui.slaves.filter import FilterSlave

_ = gettext.gettext

class SalesApp(AppWindow):

    app_name = _('Sales')
    gladefile = 'sales'
    widgets = ('sales_list',
               'cancel_button',
               'installments_button',
               'details_button',
               'total_value',
               'total_label')

    def __init__(self, app):
        AppWindow.__init__(self, app)
        self.conn = new_transaction()
        self._setup_slaves()
        self._setup_widgets()
        self._update_widgets()

    def _setup_widgets(self):
        widgets = [self.total_label, self.total_value]
        for widget in widgets:
            widget.set_size('large')
            widget.set_bold(True)
        self.sales_list.set_columns(self._get_columns())
        self.sales_list.set_selection_mode(gtk.SELECTION_BROWSE)

    def _update_widgets(self):
        has_sales = len(self.sales_list) > 0
        widgets = [self.cancel_button, self.installments_button,
                   self.details_button]
        for widget in widgets:
            widget.set_sensitive(has_sales)
        self._update_total_label()

    def _update_total_label(self):
        total_amount = sum([sale.get_total_sale_amount() 
                            for sale in self.sales_list], 0.0)
        total_str = get_formatted_price(total_amount)
        self.total_value.set_text(total_str)



    def _setup_slaves(self):
        items = [(value, key) for key, value in Sale.statuses.items()]
        items.append(('All sales', ALL_ITEMS_INDEX))
        self.filter_slave = FilterSlave(items, selected=ALL_ITEMS_INDEX)
        self.searchbar = SearchBar(self, Sale, self._get_columns(),
                                   query_args=self._get_query_args(),
                                   filter_slave=self.filter_slave,
                                   searching_by_date=True)
        self.searchbar.set_result_strings(_('sale'), _('sales'))
        self.searchbar.set_searchbar_labels(_('Containing:'),
                                            _('Find sales from:'))
        self.filter_slave.connect('status-changed', 
                                  self.searchbar.search_items)
        self.attach_slave('searchbar_holder', self.searchbar)

    def _get_query_args(self):
        # It seems that there is a bug in SQLObject which doesn't allow us
        # to have and LEFTJoin and single joins at the same time.
        # See bug 2207
        client_table = Person.getAdapterClass(IClient)
        return dict(join=LEFTJOINOn(Sale, client_table,
                                    Sale.q.clientID == client_table.q.id))

    #
    # SearchBar hooks
    #

    def _get_columns(self):
        return [Column('order_number', title=_('Number'), width=100, 
                       data_type=str, sorted=True),
                Column('open_date', title=_('Date Started'), width=120, 
                       data_type=date, justify=gtk.JUSTIFY_RIGHT),
                ForeignKeyColumn(Person, 'name', title=_('Client'), 
                                 data_type=str, width=220,
                                 obj_field='client._original'),
                ForeignKeyColumn(Person, 'name', title=_('Salesperson'), 
                                 data_type=str, width=180,
                                 obj_field='salesperson._original'),
                Column('status_name', title=_('Status'), width=80, 
                       data_type=str), 
                Column('total_sale_amount', title=_('Total'), 
                       data_type=float, justify=gtk.JUSTIFY_RIGHT,
                       format_func=get_formatted_price)]

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
        self.sales_list.clear()
        for sale in sales:
            # Since search bar change the connection internally we must get
            # the objects back in our main connection
            obj = Sale.get(sale.id, connection=self.conn)
            self.sales_list.append(obj)
        self._update_widgets()

    #
    # Kiwi callbacks
    #

    def _on_clients_action__clicked(self, *args):
        self.run_dialog(ClientSearch)

    def _on_products_action__clicked(self, *args):
        # TODO It will be implemented on bug 2206
        pass
