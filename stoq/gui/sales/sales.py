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

import gettext
from datetime import date

from kiwi.datatypes import currency
from kiwi.ui.widgets.list import Column, SummaryLabel
from sqlobject.sqlbuilder import AND, LEFTJOINOn
from stoqlib.gui.base.columns import ForeignKeyColumn
from stoqlib.lib.defaults import ALL_ITEMS_INDEX

from stoqlib.domain.sale import Sale
from stoqlib.domain.person import Person
from stoqlib.domain.interfaces import IClient, ISalesPerson
from stoqlib.lib.validators import get_price_format_str
from stoq.gui.application import SearchableAppWindow
from stoq.gui.search.person import ClientSearch, CreditProviderSearch
from stoq.gui.search.product import ProductSearch
from stoq.gui.search.service import ServiceSearch
from stoq.gui.search.giftcertificate import (GiftCertificateTypeSearch,
                                             GiftCertificateSearch)
from stoqlib.gui.slaves.sale import SaleListToolbar

_ = gettext.gettext

class SalesApp(SearchableAppWindow):

    app_name = _('Sales')
    app_icon_name = 'stoq-sales-app'
    gladefile = 'sales_app'
    searchbar_table = Sale
    searchbar_use_dates = True
    searchbar_result_strings = (_('sale'), _('sales'))
    searchbar_labels = (_('matching:'),)
    filter_slave_label = _('Show sales with status')
    klist_name = 'sales'

    def __init__(self, app):
        SearchableAppWindow.__init__(self, app)
        self._setup_widgets()
        self._update_widgets()
        self._setup_slaves()
        
    def _setup_widgets(self):
        value_format = '<b>%s</b>' % get_price_format_str()
        self.summary_label = SummaryLabel(klist=self.sales,
                                          column='total_sale_amount',
                                          label='<b>Total:</b>',
                                          value_format=value_format)
        self.summary_label.show()
        self.list_vbox.pack_start(self.summary_label, False)

    def _setup_slaves(self):
        slave = SaleListToolbar(self.conn, self.sales)
        self.attach_slave("list_toolbar_holder", slave)

    def on_searchbar_activate(self, slave, objs):
        SearchableAppWindow.on_searchbar_activate(self, slave, objs)
        self._update_widgets()

    def _update_widgets(self):
        self._update_total_label()

    def _update_total_label(self):
        self.summary_label.update_total()

    def get_filter_slave_items(self):
        items = [(value, key) for key, value in Sale.statuses.items()]
        items.append((_('Any'), ALL_ITEMS_INDEX))
        return items

    def get_query_args(self):
        # It seems that there is a bug in SQLObject which doesn't allow us
        # to have and LEFTJoin and single joins at the same time.
        # See bug 2207
        client_table = Person.getAdapterClass(IClient)
        return dict(join=LEFTJOINOn(Sale, client_table,
                                    Sale.q.clientID == client_table.q.id))

    #
    # SearchBar hooks
    #

    def get_columns(self):
        return [Column('order_number', title=_('Number'), width=100, 
                       data_type=str, sorted=True),
                Column('open_date', title=_('Date Started'), width=120, 
                       data_type=date),
                ForeignKeyColumn(Person, 'name', title=_('Client'), 
                                 data_type=str, width=220,
                                 obj_field='client', adapted=True),
                ForeignKeyColumn(Person, 'name', title=_('Salesperson'), 
                                 data_type=str, width=180,
                                 obj_field='salesperson', adapted=True),
                Column('status_name', title=_('Status'), width=80, 
                       data_type=str), 
                Column('total_sale_amount', title=_('Total'), 
                       data_type=currency)]

    def get_extra_query(self):
        salesperson_table = Person.getAdapterClass(ISalesPerson)
        q1 = Sale.q.salespersonID == salesperson_table.q.id
        q2 = salesperson_table.q._originalID == Person.q.id
        status = self.filter_slave.get_selected_status()
        if status != ALL_ITEMS_INDEX:
            q3 = Sale.q.status == status
            return AND(q1, q2, q3)
        return AND(q1, q2)

    #
    # Kiwi callbacks
    #

    def _on_clients_action__clicked(self, *args):
        self.run_dialog(ClientSearch, self.conn, hide_footer=True)

    def _on_products_action__clicked(self, *args):
        self.run_dialog(ProductSearch, self.conn, hide_footer=True,
                        hide_toolbar=True, hide_cost_column=True)

    def _on_credit_provider_action__clicked(self, *args):
        self.run_dialog(CreditProviderSearch, self.conn, hide_footer=True)

    def _on_gift_certificate_types_action_clicked(self, *args):
        self.run_dialog(GiftCertificateTypeSearch, self.conn)

    def _on_gift_certificates_action_clicked(self, *args):
        self.run_dialog(GiftCertificateSearch, self.conn)

    def _on_services_action_clicked(self, *args):
        self.run_dialog(ServiceSearch, self.conn, hide_cost_column=True,
                        hide_toolbar=True)
