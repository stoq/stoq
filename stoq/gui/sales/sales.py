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
from kiwi.ui.search import ComboSearchFilter
from kiwi.ui.objectlist import Column, SearchColumn

from stoqlib.database.runtime import (get_current_branch, get_current_station,
                                      new_transaction, finish_transaction)
from stoqlib.domain.inventory import Inventory
from stoqlib.domain.invoice import InvoicePrinter
from stoqlib.domain.sale import Sale, SaleView
from stoqlib.gui.editors.invoiceeditor import SaleInvoicePrinterDialog
from stoqlib.gui.dialogs.openinventorydialog import show_inventory_process_message
from stoqlib.gui.search.commissionsearch import CommissionSearch
from stoqlib.gui.search.personsearch import ClientSearch
from stoqlib.gui.search.productsearch import ProductSearch, ProductsSoldSearch
from stoqlib.gui.search.salesearch import DeliverySearch
from stoqlib.gui.search.servicesearch import ServiceSearch
from stoqlib.gui.slaves.saleslave import SaleListToolbar
from stoqlib.gui.wizards.salequotewizard import SaleQuoteWizard
from stoqlib.lib.invoice import SaleInvoice, print_sale_invoice
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

    cols_info = {Sale.STATUS_INITIAL: 'open_date',
                 Sale.STATUS_CONFIRMED: 'confirm_date',
                 Sale.STATUS_PAID: 'close_date',
                 Sale.STATUS_CANCELLED: 'cancel_date',
                 Sale.STATUS_QUOTE: 'open_date',
                 Sale.STATUS_RETURNED: 'return_date',
                 Sale.STATUS_RENEGOTIATED: 'close_date',}

    def __init__(self, app):
        SearchableAppWindow.__init__(self, app)
        self.summary_label = None
        self._visible_date_col = None
        self._columns = self.get_columns()
        self._setup_columns()
        self._setup_slaves()

    #
    # SearchableAppWindow
    #

    def create_filters(self):
        self.set_text_field_columns(['client_name', 'salesperson_name'])
        status_filter = ComboSearchFilter(_('Show sales with status'),
                                          self._get_status_values())
        status_filter.select(Sale.STATUS_CONFIRMED)
        self.executer.add_filter_query_callback(
            status_filter, self._get_status_query)
        self.add_filter(status_filter, position=SearchFilterPosition.TOP)

    def get_columns(self):
        self._status_col = Column('status_name', title=_('Status'),
                                  data_type=str, width=80, visible=False)

        cols = [SearchColumn('id', title=_('Number'), width=80,
                             format='%05d', data_type=int, sorted=True),
                SearchColumn('open_date', title=_('Open Date'), width=120,
                             data_type=date, justify=gtk.JUSTIFY_RIGHT,
                             visible=False),
                SearchColumn('close_date', title=_('Close Date'), width=120,
                             data_type=date, justify=gtk.JUSTIFY_RIGHT,
                             visible=False),
                SearchColumn('confirm_date', title=_('Confirm Date'),
                             data_type=date, justify=gtk.JUSTIFY_RIGHT,
                             visible=False, width=120),
                SearchColumn('cancel_date', title=_('Cancel Date'), width=120,
                             data_type=date, justify=gtk.JUSTIFY_RIGHT,
                             visible=False),
                SearchColumn('return_date', title=_('Return Date'), width=120,
                             data_type=date, justify=gtk.JUSTIFY_RIGHT,
                             visible=False),
                SearchColumn('expire_date', title=_('Expire Date'), width=120,
                             data_type=date, justify=gtk.JUSTIFY_RIGHT,
                             visible=False),
                self._status_col,
                SearchColumn('client_name', title=_('Client'),
                             data_type=str, width=140, expand=True,
                             ellipsize=pango.ELLIPSIZE_END),
                SearchColumn('salesperson_name', title=_('Salesperson'),
                              data_type=str, width=130,
                              ellipsize=pango.ELLIPSIZE_END),
                SearchColumn('total_quantity', title=_('Items'),
                              data_type=decimal.Decimal, width=60,
                              format_func=format_quantity),
                SearchColumn('total', title=_('Total'), data_type=currency,
                             width=120)]
        return cols

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
        self.sale_toolbar.connect('sale-edited',
                                  self._on_sale_toolbar__sale_edited)
        self.attach_slave("list_toolbar_holder", self.sale_toolbar)
        self._klist.connect("selection-changed",
                            self._update_toolbar)
        self._update_toolbar()

        if Inventory.has_open(self.conn, get_current_branch(self.conn)):
            show_inventory_process_message()

    def _can_cancel(self, view):
        # Here we want to cancel only quoting sales. This is why we don't use
        # Sale.can_cancel here.
        return bool(view and view.status == Sale.STATUS_QUOTE)

    def _update_toolbar(self, *args):
        sale_view = self._klist.get_selected()
        #FIXME: Disable invoice printing if the sale was returned. Remove this
        #       when we add proper support for returned sales invoice.
        can_print_invoice = bool(sale_view and
                                 sale_view.client_name is not None and
                                 sale_view.status != Sale.STATUS_RETURNED)
        self.print_invoice.set_sensitive(can_print_invoice)
        self.cancel_menu.set_sensitive(self._can_cancel(sale_view))

        if Inventory.has_open(self.conn, get_current_branch(self.conn)):
            can_return = False
        else:
            can_return = bool(sale_view and sale_view.sale.can_return())
        self.sale_toolbar.return_sale_button.set_sensitive(can_return)
        self.sale_toolbar.set_report_filters(self.search.get_search_filters())

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
        if not invoice.has_invoice_number() or sale.invoice_number:
            print_sale_invoice(invoice, printer)
        else:
            trans = new_transaction()
            retval = self.run_dialog(SaleInvoicePrinterDialog, trans,
                                     trans.get(sale), printer)
            finish_transaction(trans, retval)
            trans.close()

    def _setup_columns(self, sale_status=Sale.STATUS_CONFIRMED):
        self._status_col.visible = False

        if sale_status is None:
            # When there is no filter for sale status, show the
            # 'date started' column by default
            sale_status = Sale.STATUS_INITIAL
            self._status_col.visible = True

        if self._visible_date_col:
            self._visible_date_col.visible = False

        for col in self._columns:
            if col.attribute == self.cols_info[sale_status]:
                self._visible_date_col = col
                col.visible = True
                break

        self._klist.set_columns(self._columns)
        # Adding summary label again and make it properly aligned with the
        # new columns setup
        self._create_summary_label()

    def _get_status_values(self):
        items = [(value, key) for key, value in Sale.statuses.items()
                    # No reason to show orders in sales app
                    if key != Sale.STATUS_ORDERED]
        items.insert(0, (_('Any'), None))
        return items

    def _get_status_query(self, state):
        self._setup_columns(state.value)
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
                        hide_toolbar=True, hide_cost_column=True)

    def _on_commission_action__clicked(self, button):
        self.run_dialog(CommissionSearch, self.conn)

    def _on_services_action_clicked(self, button):
        self.run_dialog(ServiceSearch, self.conn, hide_toolbar=True)

    def _on_print_invoice__activate(self, action):
        return self._print_invoice()

    def _on_sale_toolbar__sale_returned(self, toolbar, sale):
        self.search.refresh()

    def _on_sale_toolbar__sale_edited(self, toolbar, sale):
        self.search.refresh()

    def on_quote_menu__activate(self, action):
        trans = new_transaction()
        model = self.run_dialog(SaleQuoteWizard, trans)
        rv = finish_transaction(trans, model)
        trans.close()

        return model

    def on_cancel_menu__activate(self, action):
        trans = new_transaction()
        sale_view = self._klist.get_selected()
        sale = trans.get(sale_view.sale)
        sale.cancel()
        finish_transaction(trans, True)
        self.search.refresh()

    def on_DeliverySearch__activate(self, action):
        self.run_dialog(DeliverySearch, self.conn)

    def on_Deliveries__activate(self, action):
        self.run_dialog(DeliverySearch, self.conn)

    def on_ProductsSoldSearch__activate(self, action):
        self.run_dialog(ProductsSoldSearch, self.conn)
