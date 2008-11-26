# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2007 Async Open Source <http://www.async.com.br>
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
##                  Johan Dahlin                <jdahlin@async.com.br>
##
""" Implementation of sales application.  """

import gettext
import decimal
from datetime import date

import pango
import gtk
from kiwi.datatypes import currency
from kiwi.enums import SearchFilterPosition
from kiwi.ui.search import DateSearchFilter, ComboSearchFilter
from kiwi.ui.widgets.list import Column

from stoqlib.database.runtime import get_current_branch, get_current_station
from stoqlib.domain.inventory import Inventory
from stoqlib.domain.invoice import InvoicePrinter
from stoqlib.domain.sale import Sale, SaleView
from stoqlib.gui.dialogs.openinventorydialog import show_inventory_process_message
from stoqlib.gui.search.commissionsearch import CommissionSearch
from stoqlib.gui.search.personsearch import ClientSearch
from stoqlib.gui.search.productsearch import ProductSearch
from stoqlib.gui.search.servicesearch import ServiceSearch
from stoqlib.gui.slaves.saleslave import SaleListToolbar
from stoqlib.lib.invoice import SaleInvoice
from stoqlib.lib.validators import format_quantity
from stoqlib.lib.message import info

from stoq.gui.application import SearchableAppWindow


_ = gettext.gettext


class SalesApp(SearchableAppWindow):

    app_name = _('Sales')
    app_icon_name = 'stoq-sales-app'
    gladefile = 'sales_app'
    search_table = SaleView
    search_label = _('matching:')

    cols_info = {Sale.STATUS_INITIAL: ('open_date', _("Date Started")),
                 Sale.STATUS_CONFIRMED: ('confirm_date', _("Confirm Date")),
                 Sale.STATUS_PAID: ('close_date', _("Close Date")),
                 Sale.STATUS_CANCELLED: ('cancel_date', _("Cancel Date")),
                 Sale.STATUS_RETURNED: ('return_data', _('Return Date')),}

    def __init__(self, app):
        SearchableAppWindow.__init__(self, app)
        self.summary_label = None
        self._columns_set = False
        self._setup_columns()
        self._setup_slaves()

    #
    # SearchableAppWindow
    #

    def create_filters(self):
        self.set_text_field_columns(['client_name', 'salesperson_name'])
        date_filter = DateSearchFilter(_('Paid or due date:'))
        self.add_filter(
            date_filter, columns=['open_date'])
        status_filter = ComboSearchFilter(_('Show sales with status'),
                                          self._get_status_values())
        status_filter.select(Sale.STATUS_CONFIRMED)
        self.executer.add_filter_query_callback(
            status_filter, self._get_status_query)
        self.add_filter(status_filter, position=SearchFilterPosition.TOP)

    def get_columns(self):
        return [Column('id', title=_('Number'), width=80,
                       format='%05d', data_type=int, sorted=True),
                Column('client_name', title=_('Client'),
                       data_type=str, width=140, expand=True,
                       ellipsize=pango.ELLIPSIZE_END),
                Column('salesperson_name', title=_('Salesperson'),
                       data_type=str, width=130,
                       ellipsize=pango.ELLIPSIZE_END),
                Column('total_quantity', title=_('Items Quantity'),
                       data_type=decimal.Decimal, width=140,
                       format_func=format_quantity),
                Column('total', title=_('Total'), data_type=currency,
                       width=120)]

    #
    # Private
    #

    def _create_summary_label(self):
        self.search.set_summary_label(column='total',
                                      label='<b>Total:</b>',
                                      format='<b>%s</b>')

    def _setup_slaves(self):
        self.sale_toolbar = SaleListToolbar(self.conn, self.results)
        self.sale_toolbar.connect('sale-returned',
                                  self._on_sale_toolbar__sale_returned)
        self.attach_slave("list_toolbar_holder", self.sale_toolbar)
        self._klist.connect("selection-changed",
                            self._update_toolbar)
        self._update_toolbar()

        if Inventory.has_open(self.conn, get_current_branch(self.conn)):
            show_inventory_process_message()

    def _update_toolbar(self, *args):
        sale_view = self._klist.get_selected()
        can_print_invoice = bool(sale_view and
                                 sale_view.client_name is not None)
        self.print_invoice.set_sensitive(can_print_invoice)

        if Inventory.has_open(self.conn, get_current_branch(self.conn)):
            can_return = False
        else:
            can_return = bool(sale_view and sale_view.sale.can_return())
        self.sale_toolbar.return_sale_button.set_sensitive(can_return)

    def _print_invoice(self):
        sale_view = self._klist.get_selected()
        assert sale_view
        sale = Sale.get(sale_view.id, connection=self.conn)
        station = get_current_station(self.conn)
        printer = InvoicePrinter.get_by_station(station, self.conn)
        if printer is None:
            info(_("There are no invoice printer configured for this station"))
            return
        assert printer.layout
        invoice = SaleInvoice(sale, printer.layout)
        invoice.send_to_printer(printer.device_name)

    def _setup_columns(self, sale_status=Sale.STATUS_CONFIRMED):
        if sale_status is None:
            # When there is no filter for sale status, show the
            # 'date started' column by default
            sale_status = Sale.STATUS_INITIAL
        cols = self.get_columns()
        if not sale_status in self.cols_info.keys():
            raise ValueError("Invalid Sale status, got %d" % sale_status)

        attr_name, title = self.cols_info[sale_status]
        date_col = Column(attr_name, title=title, width=120,
                          data_type=date, justify=gtk.JUSTIFY_RIGHT)
        cols.insert(1, date_col)
        self._klist.set_columns(cols)
        # Adding summary label again and make it properly aligned with the
        # new columns setup
        self._create_summary_label()
        #self.set_searchbar_columns(cols)

    def _get_status_values(self):
        items = [(value, key) for key, value in Sale.statuses.items()
                    # No reason to show orders in sales app
                    if key != Sale.STATUS_ORDERED]
        items.insert(0, (_('Any'), None))
        return items

    def _get_status_query(self, state):
        if not self._columns_set:
            self._setup_columns(state.value)
            self._columns_set = True
        if state.value is None:
            return SaleView.q.status != Sale.STATUS_ORDERED
        return SaleView.q.status == state.value

    #
    # Kiwi callbacks
    #

    def _on_clients_action__clicked(self, button):
        self.run_dialog(ClientSearch, self.conn, hide_footer=True)

    def _on_products_action__clicked(self, button):
        self.run_dialog(ProductSearch, self.conn, hide_footer=True,
                        hide_toolbar=True)

    def _on_commission_action__clicked(self, button):
        self.run_dialog(CommissionSearch, self.conn)

    def _on_services_action_clicked(self, button):
        self.run_dialog(ServiceSearch, self.conn, hide_toolbar=True)

    def _on_print_invoice__activate(self, action):
        return self._print_invoice()

    def _on_sale_toolbar__sale_returned(self, toolbar, sale):
        self.search.refresh()
