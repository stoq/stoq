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
## Author(s): Stoq Team <stoq-devel@async.com.br>
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

from stoqlib.api import api
from stoqlib.domain.invoice import InvoicePrinter
from stoqlib.domain.sale import Sale, SaleView
from stoqlib.gui.editors.invoiceeditor import SaleInvoicePrinterDialog
from stoqlib.gui.keybindings import get_accels
from stoqlib.gui.search.callsearch import ClientCallsSearch
from stoqlib.gui.search.commissionsearch import CommissionSearch
from stoqlib.gui.search.loansearch import LoanItemSearch, LoanSearch
from stoqlib.gui.search.personsearch import ClientSearch
from stoqlib.gui.search.productsearch import ProductSearch
from stoqlib.gui.search.salesearch import DeliverySearch, SoldItemsByBranchSearch
from stoqlib.gui.search.servicesearch import ServiceSearch
from stoqlib.gui.slaves.saleslave import SaleListToolbar
from stoqlib.gui.stockicons import (STOQ_PRODUCTS, STOQ_SERVICES,
                                    STOQ_CLIENTS, STOQ_DELIVERY)
from stoqlib.gui.wizards.loanwizard import NewLoanWizard, CloseLoanWizard
from stoqlib.gui.wizards.salequotewizard import SaleQuoteWizard
from stoqlib.lib.formatters import format_quantity
from stoqlib.lib.invoice import SaleInvoice, print_sale_invoice
from stoqlib.lib.message import info, yesno
from stoqlib.reporting.sale import SalesReport

from stoq.gui.application import SearchableAppWindow


_ = gettext.gettext


class SalesApp(SearchableAppWindow):

    app_name = _('Sales')
    gladefile = 'sales_app'
    search_table = SaleView
    search_label = _('matching:')
    report_table = SalesReport
    embedded = True

    cols_info = {Sale.STATUS_INITIAL: 'open_date',
                 Sale.STATUS_CONFIRMED: 'confirm_date',
                 Sale.STATUS_PAID: 'close_date',
                 Sale.STATUS_CANCELLED: 'cancel_date',
                 Sale.STATUS_QUOTE: 'open_date',
                 Sale.STATUS_RETURNED: 'return_date',
                 Sale.STATUS_RENEGOTIATED: 'close_date'}

    def __init__(self, app):
        self.summary_label = None
        self._visible_date_col = None
        SearchableAppWindow.__init__(self, app)

    #
    # Application
    #

    def create_actions(self):
        group = get_accels('app.sales')
        actions = [
            # File
            ("SaleQuote", None, _("Sale quote..."), '',
             _('Create a new quote for a sale')),
            ("LoanNew", None, _("Loan...")),
            ("LoanClose", None, _("Close loan...")),

            # Search
            ("SearchSoldItemsByBranch", None, _("Sold items by branch..."),
             group.get("search_sold_items_by_branch"),
             _("Search for sold items by branch")),
            ("SearchProduct", STOQ_PRODUCTS, _("Products..."),
             group.get("search_products"),
             _("Search for products")),
            ("SearchService", STOQ_SERVICES, _("Services..."),
             group.get("search_services"),
             _("Search for services")),
            ("SearchDelivery", STOQ_DELIVERY, _("Deliveries..."),
             group.get("search_deliveries"),
             _("Search for deliveries")),
            ("SearchClient", STOQ_CLIENTS, _("Clients..."),
             group.get("search_clients"),
             _("Search for clients")),
            ("SearchClientCalls", None, _("Client Calls..."),
             group.get("search_client_calls"),
             _("Search for client calls")),
            ("SearchCommission", None, _("Commissions..."),
             group.get("search_commissions"),
             _("Search for salespersons commissions")),
            ("LoanSearch", None, _("Loans..."),
             group.get("search_loans")),
            ("LoanSearchItems", None, _("Loan items..."),
             group.get("search_loan_items")),

            # Sale
            ("SaleMenu", None, _("Sale")),

            ("SalesCancel", None, _("Cancel quote...")),
            ("SalesPrintInvoice", gtk.STOCK_PRINT, _("_Print invoice...")),
            ("Return", gtk.STOCK_CANCEL, _("Return..."), '',
             _("Return the selected sale, canceling it's payments")),
            ("Edit", gtk.STOCK_EDIT, _("Edit..."), '',
             _("Edit the selected sale, allowing you to change the details "
               "of it")),
            ("Details", gtk.STOCK_INFO, _("Details..."), '',
             _("Show details of the selected sale"))
        ]

        self.sales_ui = self.add_ui_actions("", actions,
                                            filename="sales.xml")

        self.SaleQuote.set_short_label(_("New Sale Quote"))
        self.SearchClient.set_short_label(_("Clients"))
        self.SearchProduct.set_short_label(_("Products"))
        self.SearchService.set_short_label(_("Services"))
        self.SearchDelivery.set_short_label(_("Deliveries"))
        self.SalesCancel.set_short_label(_("Cancel"))
        self.Edit.set_short_label(_("Edit"))
        self.Return.set_short_label(_("Return"))
        self.Details.set_short_label(_("Details"))

        self.set_help_section(_("Sales help"), 'app-sales')

    def create_ui(self):
        self.popup = self.uimanager.get_widget('/SaleSelection')

        self._columns = self.get_columns()
        self._setup_columns()
        self._setup_widgets()

        self.app.launcher.add_new_items([self.SaleQuote])
        self.app.launcher.add_search_items([
          self.SearchProduct,
          self.SearchClient,
          self.SearchService,
          self.SearchDelivery])
        self.app.launcher.Print.set_tooltip(_("Print a report of these sales"))

    def activate(self, params):
        self.check_open_inventory()
        self._update_toolbar()

    def setup_focus(self):
        self.search.refresh()

    def deactivate(self):
        self.uimanager.remove_ui(self.sales_ui)

    def new_activate(self):
        self._new_sale_quote()

    def search_activate(self):
        self._search_product()

    def set_open_inventory(self):
        self.set_sensitive(self._inventory_widgets, False)

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

        cols = [SearchColumn('id', title=_('#'), width=80,
                             format='%05d', data_type=int, sorted=True),
                SearchColumn('open_date', title=_('Open date'), width=120,
                             data_type=date, justify=gtk.JUSTIFY_RIGHT,
                             visible=False),
                SearchColumn('close_date', title=_('Close date'), width=120,
                             data_type=date, justify=gtk.JUSTIFY_RIGHT,
                             visible=False),
                SearchColumn('confirm_date', title=_('Confirm date'),
                             data_type=date, justify=gtk.JUSTIFY_RIGHT,
                             visible=False, width=120),
                SearchColumn('cancel_date', title=_('Cancel date'), width=120,
                             data_type=date, justify=gtk.JUSTIFY_RIGHT,
                             visible=False),
                SearchColumn('return_date', title=_('Return date'), width=120,
                             data_type=date, justify=gtk.JUSTIFY_RIGHT,
                             visible=False),
                SearchColumn('expire_date', title=_('Expire date'), width=120,
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
                                      format='<b>%s</b>',
                                      parent=self.get_statusbar_message_area())

    def _setup_widgets(self):
        self._setup_slaves()
        self._inventory_widgets = [self.sale_toolbar.return_sale_button,
                                   self.Return, self.LoanNew, self.LoanClose]
        self.register_sensitive_group(self._inventory_widgets,
                                      lambda: not self.has_open_inventory())

    def _setup_slaves(self):
        # This is only here to reuse the logic in it.
        self.sale_toolbar = SaleListToolbar(self.conn, self.results)

    def _can_cancel(self, view):
        # Here we want to cancel only quoting sales. This is why we don't use
        # Sale.can_cancel here.
        return bool(view and view.status == Sale.STATUS_QUOTE)

    def _can_edit(self, view):
        return bool(view and view.status == Sale.STATUS_QUOTE)

    def _update_toolbar(self, *args):
        sale_view = self.results.get_selected()
        #FIXME: Disable invoice printing if the sale was returned. Remove this
        #       when we add proper support for returned sales invoice.
        can_print_invoice = bool(sale_view and
                                 sale_view.client_name is not None and
                                 sale_view.status != Sale.STATUS_RETURNED)
        self.set_sensitive([self.SalesPrintInvoice], can_print_invoice)
        self.set_sensitive([self.SalesCancel], self._can_cancel(sale_view))
        self.set_sensitive([self.sale_toolbar.return_sale_button, self.Return],
                           bool(sale_view and sale_view.can_return()))
        self.set_sensitive([self.sale_toolbar.return_sale_button, self.Details],
                           bool(sale_view))
        self.set_sensitive([self.sale_toolbar.edit_button, self.Edit],
                           self._can_edit(sale_view))

        self.sale_toolbar.set_report_filters(self.search.get_search_filters())

    def _print_invoice(self):
        sale_view = self.results.get_selected()
        assert sale_view
        sale = Sale.get(sale_view.id, connection=self.conn)
        station = api.get_current_station(self.conn)
        printer = InvoicePrinter.get_by_station(station, self.conn)
        if printer is None:
            info(_("There are no invoice printer configured for this station"))
            return
        assert printer.layout

        invoice = SaleInvoice(sale, printer.layout)
        if not invoice.has_invoice_number() or sale.invoice_number:
            print_sale_invoice(invoice, printer)
        else:
            trans = api.new_transaction()
            retval = self.run_dialog(SaleInvoicePrinterDialog, trans,
                                     trans.get(sale), printer)
            api.finish_transaction(trans, retval)
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

        self.results.set_columns(self._columns)
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

    def _new_sale_quote(self):
        trans = api.new_transaction()
        model = self.run_dialog(SaleQuoteWizard, trans)
        api.finish_transaction(trans, model)
        trans.close()

    def _search_product(self):
        hide_cost_column = not api.sysparam(self.conn).SHOW_COST_COLUMN_IN_SALES
        self.run_dialog(ProductSearch, self.conn, hide_footer=True,
                        hide_toolbar=True, hide_cost_column=hide_cost_column)

    #
    # Kiwi callbacks
    #

    def _on_sale_toolbar__sale_returned(self, toolbar, sale):
        self.search.refresh()

    def _on_sale_toolbar__sale_edited(self, toolbar, sale):
        self.search.refresh()

    def on_results__selection_changed(self, results, sale):
        self._update_toolbar()

    def on_results__has_rows(self, results, has_rows):
        self._update_toolbar()

    def on_results__right_click(self, results, result, event):
        self.popup.popup(None, None, None, event.button, event.time)

    # Sales

    def on_SaleQuote__activate(self, action):
        self._new_sale_quote()

    def on_SalesCancel__activate(self, action):
        if yesno(_('This will cancel the selected quote. Are you sure?'),
                 gtk.RESPONSE_NO, _("Don't cancel"), _("Cancel quote")):
            return
        trans = api.new_transaction()
        sale_view = self.results.get_selected()
        sale = trans.get(sale_view.sale)
        sale.cancel()
        api.finish_transaction(trans, True)
        self.search.refresh()

    def on_SalesPrintInvoice__activate(self, action):
        return self._print_invoice()

    # Loan

    def on_LoanNew__activate(self, action):
        if self.check_open_inventory():
            return
        trans = api.new_transaction()
        model = self.run_dialog(NewLoanWizard, trans)
        api.finish_transaction(trans, model)
        trans.close()

    def on_LoanClose__activate(self, action):
        if self.check_open_inventory():
            return
        trans = api.new_transaction()
        model = self.run_dialog(CloseLoanWizard, trans)
        api.finish_transaction(trans, model)
        trans.close()

    def on_LoanSearch__activate(self, action):
        self.run_dialog(LoanSearch, self.conn)

    def on_LoanSearchItems__activate(self, action):
        self.run_dialog(LoanItemSearch, self.conn)

    # Search

    def on_SearchClient__activate(self, button):
        self.run_dialog(ClientSearch, self.conn, hide_footer=True)

    def on_SearchProduct__activate(self, button):
        self._search_product()

    def on_SearchCommission__activate(self, button):
        self.run_dialog(CommissionSearch, self.conn)

    def on_SearchClientCalls__activate(self, action):
        self.run_dialog(ClientCallsSearch, self.conn)

    def on_SearchService__activate(self, button):
        self.run_dialog(ServiceSearch, self.conn, hide_toolbar=True)

    def on_SearchSoldItemsByBranch__activate(self, button):
        self.run_dialog(SoldItemsByBranchSearch, self.conn)

    def on_SearchDelivery__activate(self, action):
        self.run_dialog(DeliverySearch, self.conn)

    # Toolbar

    def on_Edit__activate(self, action):
        self.sale_toolbar.edit()

    def on_Details__activate(self, action):
        self.sale_toolbar.show_details()

    def on_Return__activate(self, action):
        if self.check_open_inventory():
            return
        self.sale_toolbar.return_sale()
