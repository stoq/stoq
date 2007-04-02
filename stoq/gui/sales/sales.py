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
from stoqlib.gui.search.personsearch import ClientSearch
from stoqlib.gui.search.productsearch import ProductSearch
from stoqlib.gui.search.servicesearch import ServiceSearch
from stoqlib.gui.search.giftcertificatesearch import GiftCertificateSearch
from stoqlib.gui.slaves.saleslave import SaleListToolbar
from stoqlib.gui.editors.invoiceeditor import InvoiceDetailsEditor
from stoqlib.lib.invoice import SaleInvoice
from stoqlib.gui.base.dialogs import print_report

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

    cols_info = {Sale.STATUS_OPENED: ('open_date', _("Date Started")),
                 Sale.STATUS_CONFIRMED: ('confirm_date', _("Confirm Date")),
                 Sale.STATUS_CLOSED: ('close_date', _("Close Date")),
                 Sale.STATUS_CANCELLED: ('cancel_date', _("Cancel Date"))}

    def __init__(self, app):
        SearchableAppWindow.__init__(self, app)
        self.summary_label = None
        self._columns_set = False
        self._create_summary_label()
        self._update_widgets()
        self._setup_columns()
        self._setup_slaves()

    def _create_summary_label(self):
        if self.summary_label is not None:
            self.list_vbox.remove(self.summary_label)
        value_format = '<b>%s</b>'
        self.summary_label = SummaryLabel(klist=self.sales,
                                          column='total',
                                          label='<b>Total:</b>',
                                          value_format=value_format)
        self.summary_label.show()
        self.list_vbox.pack_start(self.summary_label, False)

    def _setup_slaves(self):
        self.sale_toolbar = SaleListToolbar(self.conn, self.searchbar,
                                            self.sales)
        self.attach_slave("list_toolbar_holder", self.sale_toolbar)
        self._klist.connect("selection-changed",
                            self._update_toolbar)
        self._update_toolbar()

    def _update_widgets(self):
        self._update_total_label()

    def _update_toolbar(self, *args):
        selected = self._klist.get_selected()
        can_print_invoice = bool(selected and
                                 selected.client_name is not None)
        self.print_invoice.set_sensitive(can_print_invoice)

        rejected = Sale.STATUS_CANCELLED, Sale.STATUS_ORDER
        can_cancel = bool(selected and selected.status not in rejected)
        self.sale_toolbar.return_sale_button.set_sensitive(can_cancel)

    def _update_total_label(self):
        self.summary_label.update_total()

    def _preview_invoice_as_pdf(self, fiscal_note, sale, *args, **kwargs):
        raise NotImplementedError("not implemented yet :)")

    def _print_invoice(self):
        assert self._klist.get_selected()
        invoice_data = self.run_dialog(InvoiceDetailsEditor, self.conn)
        if not invoice_data:
            return
        sale_view = self._klist.get_selected()
        sale = Sale.get(sale_view.id, connection=self.conn)
        print_report(SaleInvoice, sale, date=invoice_data,
                     default_filename=SaleInvoice.default_filename,
                     preview_callback=self._preview_invoice_as_pdf,
                     title=_(u"Printing Invoice"),
                     preview_label=_(u"Preview Model"))

    def _setup_columns(self, sale_status=Sale.STATUS_CONFIRMED):
        if sale_status == ALL_ITEMS_INDEX:
            # When there is no filter for sale status, show the
            # 'date started' column by default
            sale_status = Sale.STATUS_OPENED
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
        self.set_searchbar_columns(cols)

    #
    # SearchableAppWindow Hooks
    #

    def get_filter_slave_items(self):
        items = [(value, key) for key, value in Sale.statuses.items()
                    # No reason to show orders in sales app
                    if key != Sale.STATUS_ORDER]
        items.insert(0, (_('Any'), ALL_ITEMS_INDEX))
        return items

    def get_filterslave_default_selected_item(self):
        return Sale.STATUS_CONFIRMED

    def get_columns(self):
        return [Column('id', title=_('Number'), width=80,
                       format='%05d', data_type=int, sorted=True),
                Column('client_name', title=_('Client'),
                       data_type=str, width=140, expand=True),
                Column('salesperson_name', title=_('Salesperson'),
                       data_type=str, width=130),
                Column('total_quantity', title=_('Items Quantity'),
                       data_type=decimal.Decimal, width=140,
                       format_func=format_quantity),
                Column('total', title=_('Total'), data_type=currency,
                       width=120)]

    def get_extra_query(self):
        status = self.filter_slave.get_selected_status()
        if not self._columns_set:
            self._setup_columns(status)
            self._columns_set = True
        if status == ALL_ITEMS_INDEX:
            return SaleView.q.status != Sale.STATUS_ORDER
        return SaleView.q.status == status

    #
    # Callbacks
    #

    def on_searchbar_activate(self, slave, objs):
        SearchableAppWindow.on_searchbar_activate(self, slave, objs)
        self._update_widgets()

    #
    # Kiwi callbacks
    #

    def _on_clients_action__clicked(self, button):
        self.run_dialog(ClientSearch, self.conn, hide_footer=True)

    def _on_products_action__clicked(self, button):
        self.run_dialog(ProductSearch, self.conn, hide_footer=True,
                        hide_toolbar=True, hide_cost_column=True)

    def _on_gift_certificates_action_clicked(self, button):
        self.run_dialog(GiftCertificateSearch, self.conn)

    def _on_services_action_clicked(self, button):
        self.run_dialog(ServiceSearch, self.conn, hide_cost_column=True,
                        hide_toolbar=True)

    def _on_print_invoice__activate(self, action):
        return self._print_invoice()
