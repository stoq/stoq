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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s):       Evandro Vale Miquelito      <evandro@async.com.br>
##
""" Implementation of sales application.  """

import gettext
import decimal
from datetime import date

import gtk
from kiwi.datatypes import currency
from kiwi.ui.widgets.list import Column, SummaryLabel

from stoqlib.lib.defaults import ALL_ITEMS_INDEX
from stoqlib.lib.validators import format_quantity
from stoqlib.domain.sale import Sale, SaleView
from stoqlib.gui.search.person import ClientSearch
from stoqlib.gui.search.product import ProductSearch
from stoqlib.gui.search.service import ServiceSearch
from stoqlib.gui.search.giftcertificate import GiftCertificateSearch
from stoqlib.gui.slaves.sale import SaleListToolbar

from stoq.gui.application import SearchableAppWindow


_ = gettext.gettext


class SalesApp(SearchableAppWindow):

    app_name = _('Sales')
    app_icon_name = 'stoq-sales-app'
    gladefile = 'sales_app'
    searchbar_table = SaleView
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
        value_format = '<b>%s</b>'
        self.summary_label = SummaryLabel(klist=self.sales,
                                          column='total',
                                          label='<b>Total:</b>',
                                          value_format=value_format)
        self.summary_label.show()
        self.list_vbox.pack_start(self.summary_label, False)

    def _setup_slaves(self):
        slave = SaleListToolbar(self.conn, self.searchbar, self.sales)
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

    #
    # Hooks
    #

    def get_filterslave_default_selected_item(self):
        return Sale.STATUS_OPENED

    def get_columns(self):
        return [Column('order_number', title=_('Number'), width=80,
                       data_type=int, sorted=True),
                Column('open_date', title=_('Date Started'), width=120,
                       data_type=date, justify=gtk.JUSTIFY_RIGHT),
                Column('client_name', title=_('Client'),
                       data_type=str, width=140),
                Column('salesperson_name', title=_('Salesperson'),
                       data_type=str, width=210),
                Column('total_quantity', title=_('Items Quantity'),
                       data_type=decimal.Decimal, width=120,
                       format_func=format_quantity),
                Column('total', title=_('Total'), data_type=currency)]

    def get_extra_query(self):
        status = self.filter_slave.get_selected_status()
        if status != ALL_ITEMS_INDEX:
            return SaleView.q.status == status

    #
    # Kiwi callbacks
    #

    def _on_clients_action__clicked(self, *args):
        self.run_dialog(ClientSearch, self.conn, hide_footer=True)

    def _on_products_action__clicked(self, *args):
        self.run_dialog(ProductSearch, self.conn, hide_footer=True,
                        hide_toolbar=True, hide_cost_column=True)

    def _on_gift_certificates_action_clicked(self, *args):
        self.run_dialog(GiftCertificateSearch, self.conn)

    def _on_services_action_clicked(self, *args):
        self.run_dialog(ServiceSearch, self.conn, hide_cost_column=True,
                        hide_toolbar=True)
