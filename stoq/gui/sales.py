# -*- Mode: Python; coding: utf-8 -*-
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

import decimal
from datetime import date
from dateutil.relativedelta import relativedelta

import pango
import gtk
from kiwi.currency import currency
from storm.expr import And

from stoqlib.api import api
from stoqlib.database.expr import Date
from stoqlib.domain.events import SaleAvoidCancelEvent
from stoqlib.domain.invoice import InvoicePrinter
from stoqlib.domain.sale import Sale, SaleView, SaleComment
from stoqlib.enums import SearchFilterPosition
from stoqlib.gui.dialogs.invoicedialog import SaleInvoicePrinterDialog
from stoqlib.gui.editors.saleeditor import SaleClientEditor, SalesPersonEditor
from stoqlib.gui.editors.noteeditor import NoteEditor
from stoqlib.gui.search.callsearch import ClientCallsSearch
from stoqlib.gui.search.commissionsearch import CommissionSearch
from stoqlib.gui.search.deliverysearch import DeliverySearch
from stoqlib.gui.search.loansearch import LoanItemSearch, LoanSearch
from stoqlib.gui.search.returnedsalesearch import ReturnedSaleSearch
from stoqlib.gui.search.personsearch import (ClientSearch,
                                             ClientsWithSaleSearch,
                                             ClientsWithCreditSearch)
from stoqlib.gui.search.productsearch import ProductSearch
from stoqlib.gui.search.creditcheckhistorysearch import CreditCheckHistorySearch
from stoqlib.gui.slaves.saleslave import SaleListToolbar
from stoqlib.gui.search.salespersonsearch import SalesPersonSalesSearch
from stoqlib.gui.search.salesearch import (SalesByPaymentMethodSearch,
                                           SoldItemsByBranchSearch,
                                           SoldItemsByClientSearch,
                                           UnconfirmedSaleItemsSearch)
from stoqlib.gui.search.searchcolumns import IdentifierColumn, SearchColumn
from stoqlib.gui.search.searchfilters import ComboSearchFilter
from stoqlib.gui.search.servicesearch import ServiceSearch
from stoqlib.gui.stockicons import (STOQ_PRODUCTS, STOQ_SERVICES,
                                    STOQ_CLIENTS, STOQ_DELIVERY)
from stoqlib.gui.utils.keybindings import get_accels
from stoqlib.gui.wizards.loanwizard import NewLoanWizard, CloseLoanWizard
from stoqlib.gui.wizards.salequotewizard import SaleQuoteWizard
from stoqlib.gui.wizards.workorderquotewizard import WorkOrderQuoteWizard
from stoqlib.lib.formatters import format_quantity
from stoqlib.lib.invoice import SaleInvoice, print_sale_invoice
from stoqlib.lib.message import info, warning
from stoqlib.lib.permissions import PermissionManager
from stoqlib.lib.translation import stoqlib_gettext as _
from stoqlib.reporting.sale import SalesReport

from stoq.gui.shell.shellapp import ShellApp


class FilterItem(object):
    def __init__(self, name, value=None):
        self.name = name
        self.value = value
        self.id = value


SALES_FILTERS = {
    'sold': Sale.status == Sale.STATUS_CONFIRMED,
    'sold-today': And(Date(Sale.open_date) == date.today(),
                      Sale.status == Sale.STATUS_CONFIRMED),
    'sold-7days': And(Date(Sale.open_date) <= date.today(),
                      Date(Sale.open_date) >= date.today() - relativedelta(days=7),
                      Sale.status == Sale.STATUS_CONFIRMED),
    'sold-28days': And(Date(Sale.open_date) <= date.today(),
                       Date(Sale.open_date) >= date.today() - relativedelta(days=28),
                       Sale.status == Sale.STATUS_CONFIRMED),
    'expired-quotes': And(Date(Sale.expire_date) < date.today(),
                          Sale.status == Sale.STATUS_QUOTE),
}


class SalesApp(ShellApp):

    app_title = _('Sales')
    gladefile = 'sales_app'
    search_spec = SaleView
    search_label = _('matching:')
    report_table = SalesReport

    cols_info = {Sale.STATUS_INITIAL: 'open_date',
                 Sale.STATUS_CONFIRMED: 'confirm_date',
                 Sale.STATUS_ORDERED: 'open_date',
                 Sale.STATUS_CANCELLED: 'cancel_date',
                 Sale.STATUS_QUOTE: 'open_date',
                 Sale.STATUS_RETURNED: 'return_date',
                 Sale.STATUS_RENEGOTIATED: 'close_date'}

    action_permissions = {
        "SalesPrintInvoice": ('app.sales.print_invoice', PermissionManager.PERM_SEARCH),
    }

    def __init__(self, window, store=None):
        self.summary_label = None
        self._visible_date_col = None
        ShellApp.__init__(self, window, store=store)

    #
    # Application
    #

    def create_actions(self):
        group = get_accels('app.sales')
        actions = [
            # File
            ("SaleQuote", None, _("Sale quote..."), '',
             _('Create a new quote for a sale')),
            ("WorkOrderQuote", None, _("Sale with work order..."), '',
             _('Create a new quote for a sale with work orders')),
            ("LoanNew", None, _("Loan...")),
            ("LoanClose", None, _("Close loan...")),

            # Search
            ("SearchSoldItemsByBranch", None, _("Sold items by branch..."),
             group.get("search_sold_items_by_branch"),
             _("Search for sold items by branch")),
            ("SearchSalesByPaymentMethod", None,
             _("Sales by payment method..."),
             group.get("search_sales_by_payment")),
            ("SearchSalesPersonSales", None,
             _("Total sales made by salesperson..."),
             group.get("search_salesperson_sales"),
             _("Search for sales by payment method")),
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
            ("SearchCreditCheckHistory", None,
             _("Client credit check history..."),
             group.get("search_credit_check_history"),
             _("Search for client check history")),
            ("SearchCommission", None, _("Commissions..."),
             group.get("search_commissions"),
             _("Search for salespersons commissions")),
            ("LoanSearch", None, _("Loans..."),
             group.get("search_loans")),
            ("LoanSearchItems", None, _("Loan items..."),
             group.get("search_loan_items")),
            ("ReturnedSaleSearch", None, _("Returned sales..."),
             group.get("returned_sales")),
            ("SearchUnconfirmedSaleItems", None, _("Unconfirmed sale items..."),
             group.get("search_reserved_product"),
             _("Search for unconfirmed sale items")),
            ("SearchClientsWithSale", None, _("Clients with sales..."),
             None,
             _("Search for regular clients")),
            ("SearchClientsWithCredit", None, _("Clients with credit..."),
             None,
             _("Search for clients that have credit")),
            ("SearchSoldItemsByClient", None, _("Sold items by client..."),
             None,
             _("Search for products sold by client")),


            # Sale
            ("SaleMenu", None, _("Sale")),

            ("SalesCancel", None, _("Cancel...")),
            ("ChangeClient", gtk.STOCK_EDIT, _("Change client...")),
            ("ChangeSalesperson", gtk.STOCK_EDIT, _("Change salesperson...")),
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
        self.SaleQuote.set_short_label(_("New Sale Quote with Work Order"))
        self.SearchClient.set_short_label(_("Clients"))
        self.SearchProduct.set_short_label(_("Products"))
        self.SearchService.set_short_label(_("Services"))
        self.SearchDelivery.set_short_label(_("Deliveries"))
        self.SalesCancel.set_short_label(_("Cancel"))
        self.ChangeClient.set_short_label(_("Change Client"))
        self.ChangeSalesperson.set_short_label(_("Change Salesperson"))
        self.Edit.set_short_label(_("Edit"))
        self.Return.set_short_label(_("Return"))
        self.Details.set_short_label(_("Details"))

        self.set_help_section(_("Sales help"), 'app-sales')

    def create_ui(self):
        if api.sysparam.get_bool('SMART_LIST_LOADING'):
            self.search.enable_lazy_search()
        if not api.sysparam.get_bool('CHANGE_CLIENT_AFTER_CONFIRMED'):
            self.ChangeClient.set_visible(False)
        if not api.sysparam.get_bool('CHANGE_SALESPERSON_AFTER_CONFIRMED'):
            self.ChangeSalesperson.set_visible(False)

        self.popup = self.uimanager.get_widget('/SaleSelection')

        self._setup_columns()
        self._setup_widgets()

        self.window.add_new_items([self.SaleQuote, self.WorkOrderQuote])
        self.window.add_search_items([
            self.SearchProduct,
            self.SearchClient,
            self.SearchService,
            self.SearchDelivery])
        self.window.Print.set_tooltip(_("Print a report of these sales"))

    def activate(self, refresh=True):
        if refresh:
            self.refresh()

        self.check_open_inventory()
        self._update_toolbar()

        self.search.focus_search_entry()

    def deactivate(self):
        self.uimanager.remove_ui(self.sales_ui)

    def new_activate(self):
        self._new_sale_quote(wizard=SaleQuoteWizard)

    def search_activate(self):
        self._search_product()

    def set_open_inventory(self):
        self.set_sensitive(self._inventory_widgets, False)

    def create_filters(self):
        self.set_text_field_columns(['client_name', 'salesperson_name',
                                     'identifier_str'])

        status_filter = ComboSearchFilter(_('Show sales'),
                                          self._get_filter_options())
        status_filter.combo.set_row_separator_func(
            lambda model, titer: model[titer][0] == 'sep')

        executer = self.search.get_query_executer()
        executer.add_filter_query_callback(
            status_filter, self._get_status_query)
        self.add_filter(status_filter, position=SearchFilterPosition.TOP)

        self.create_branch_filter(column=Sale.branch_id)

    def get_columns(self):
        self._status_col = SearchColumn('status_name', title=_('Status'),
                                        data_type=str, width=80, visible=False,
                                        search_attribute='status',
                                        valid_values=self._get_status_values())

        cols = [IdentifierColumn('identifier', title=_('Sale #'),
                                 sorted=True),
                SearchColumn('coupon_id', title=_('Coupon #'), width=100,
                             data_type=int, visible=False),
                SearchColumn('paid', title=_('Paid'), width=120,
                             data_type=bool, visible=False),
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
                             width=120, search_attribute='_total')]
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
        self.sale_toolbar = SaleListToolbar(self.store, self.results,
                                            parent=self)

    def _update_toolbar(self, *args):
        sale_view = self.results.get_selected()
        # FIXME: Disable invoice printing if the sale was returned. Remove this
        #       when we add proper support for returned sales invoice.
        can_print_invoice = bool(sale_view and
                                 sale_view.client_name is not None and
                                 sale_view.status != Sale.STATUS_RETURNED)
        self.set_sensitive([self.SalesPrintInvoice], can_print_invoice)
        self.set_sensitive([self.SalesCancel],
                           bool(sale_view and sale_view.can_cancel()))
        self.set_sensitive([self.sale_toolbar.return_sale_button, self.Return],
                           bool(sale_view and sale_view.can_return()))
        self.set_sensitive([self.sale_toolbar.return_sale_button, self.Details],
                           bool(sale_view))
        self.set_sensitive([self.sale_toolbar.edit_button, self.Edit],
                           bool(sale_view and sale_view.can_edit()))
        # If the sale cannot be edit anymore, we only allow to change the client
        self.set_sensitive([self.ChangeClient],
                           bool(sale_view and not sale_view.can_edit()))
        self.set_sensitive([self.ChangeSalesperson],
                           bool(sale_view and not sale_view.can_edit()))
        self.sale_toolbar.set_report_filters(self.search.get_search_filters())

    def _print_invoice(self):
        sale_view = self.results.get_selected()
        assert sale_view
        sale = sale_view.sale
        station = api.get_current_station(self.store)
        printer = InvoicePrinter.get_by_station(station, self.store)
        if printer is None:
            info(_("There are no invoice printer configured for this station"))
            return
        assert printer.layout

        invoice = SaleInvoice(sale, printer.layout)
        if not invoice.has_invoice_number() or sale.invoice_number:
            print_sale_invoice(invoice, printer)
        else:
            store = api.new_store()
            retval = self.run_dialog(SaleInvoicePrinterDialog, store,
                                     store.fetch(sale), printer)
            store.confirm(retval)
            store.close()

    def _setup_columns(self, sale_status=Sale.STATUS_CONFIRMED):
        self._status_col.visible = False

        if sale_status is None:
            # When there is no filter for sale status, show the
            # 'date started' column by default
            sale_status = Sale.STATUS_INITIAL
            self._status_col.visible = True

        if self._visible_date_col:
            self._visible_date_col.visible = False

        col = self.search.get_column_by_attribute(self.cols_info[sale_status])
        if col is not None:
            self._visible_date_col = col
            col.visible = True

        self.results.set_columns(self.search.columns)
        # Adding summary label again and make it properly aligned with the
        # new columns setup
        self._create_summary_label()

    def _get_status_values(self):
        items = [(value, key) for key, value in Sale.statuses.items()]
        items.insert(0, (_('Any'), None))
        return items

    def _get_filter_options(self):
        options = [
            (_('All Sales'), None),
            (_('Confirmed today'), FilterItem('custom', 'sold-today')),
            (_('Confirmed in the last 7 days'), FilterItem('custom', 'sold-7days')),
            (_('Confirmed in the last 28 days'), FilterItem('custom', 'sold-28days')),
            (_('Expired quotes'), FilterItem('custom', 'expired-quotes')),
            ('sep', None),
        ]

        for key, value in Sale.statuses.items():
            options.append((value, FilterItem('status', key)))
        return options

    def _get_status_query(self, state):
        if state.value is None:
            # FIXME; We cannot return None here, otherwise, the query will have
            # a 'AND NULL', which will return nothing.
            return True

        if state.value.name == 'custom':
            self._setup_columns(None)
            return SALES_FILTERS[state.value.value]

        elif state.value.name == 'status':
            self._setup_columns(state.value.value)
            return SaleView.status == state.value.value

        raise AssertionError(state.value.name, state.value.value)

    def _new_sale_quote(self, wizard):
        if self.check_open_inventory():
            warning(_("You cannot create a quote with an open inventory."))
            return

        store = api.new_store()
        model = self.run_dialog(wizard, store)
        store.confirm(model)
        store.close()

        if model:
            self.refresh()

    def _search_product(self):
        hide_cost_column = not api.sysparam.get_bool('SHOW_COST_COLUMN_IN_SALES')
        self.run_dialog(ProductSearch, self.store, hide_footer=True,
                        hide_toolbar=True, hide_cost_column=hide_cost_column)

    def _change_sale_client(self):
        sale_view = self.results.get_selected()
        with api.new_store() as store:
            sale = store.fetch(sale_view.sale)
            self.run_dialog(SaleClientEditor, store=store, model=sale)

        if store.committed:
            self.refresh()

    def _change_salesperson(self):
        sale_view = self.results.get_selected()
        with api.new_store() as store:
            sale = store.fetch(sale_view.sale)
            self.run_dialog(SalesPersonEditor, store=store, model=sale)

        if store.committed:
            self.refresh()

    #
    # Kiwi callbacks
    #

    def _on_sale_toolbar__sale_returned(self, toolbar, sale):
        self.refresh()

    def _on_sale_toolbar__sale_edited(self, toolbar, sale):
        self.refresh()

    def on_results__selection_changed(self, results, sale):
        self._update_toolbar()

    def on_results__has_rows(self, results, has_rows):
        self._update_toolbar()

    def on_results__right_click(self, results, result, event):
        self.popup.popup(None, None, None, event.button, event.time)

    # Sales

    def on_SaleQuote__activate(self, action):
        self._new_sale_quote(wizard=SaleQuoteWizard)

    def on_WorkOrderQuote__activate(self, action):
        self._new_sale_quote(wizard=WorkOrderQuoteWizard)

    def on_SalesCancel__activate(self, action):
        sale_view = self.results.get_selected()
        # A plugin (e.g. ECF) can avoid the cancelation of a sale
        # because it wants it to be cancelled using another way
        if SaleAvoidCancelEvent.emit(sale_view.sale):
            return

        store = api.new_store()
        sale = store.fetch(sale_view.sale)
        msg_text = _(u"This will cancel the sale, Are you sure?")
        model = SaleComment(store=store, sale=sale,
                            author=api.get_current_user(store))

        retval = self.run_dialog(
            NoteEditor, store, model=model, attr_name='comment',
            message_text=msg_text, label_text=_(u"Reason"),
            mandatory=True, ok_button_label=_(u"Cancel sale"),
            cancel_button_label=_(u"Don't cancel"))

        if not retval:
            store.rollback()
            return

        sale.cancel()
        store.commit(close=True)
        self.refresh()

    def on_ChangeClient__activate(self, action):
        self._change_sale_client()

    def on_ChangeSalesperson__activate(self, action):
        self._change_salesperson()

    def on_SalesPrintInvoice__activate(self, action):
        return self._print_invoice()

    # Loan

    def on_LoanNew__activate(self, action):
        if self.check_open_inventory():
            return
        store = api.new_store()
        model = self.run_dialog(NewLoanWizard, store)
        store.confirm(model)
        store.close()

    def on_LoanClose__activate(self, action):
        if self.check_open_inventory():
            return
        store = api.new_store()
        model = self.run_dialog(CloseLoanWizard, store)
        store.confirm(model)
        store.close()

    def on_LoanSearch__activate(self, action):
        self.run_dialog(LoanSearch, self.store)

    def on_LoanSearchItems__activate(self, action):
        self.run_dialog(LoanItemSearch, self.store)

    def on_ReturnedSaleSearch__activate(self, action):
        self.run_dialog(ReturnedSaleSearch, self.store)

    def on_SearchUnconfirmedSaleItems__activate(self, action):
        self.run_dialog(UnconfirmedSaleItemsSearch, self.store)

    # Search

    def on_SearchClient__activate(self, button):
        self.run_dialog(ClientSearch, self.store, hide_footer=True)

    def on_SearchProduct__activate(self, button):
        self._search_product()

    def on_SearchCommission__activate(self, button):
        self.run_dialog(CommissionSearch, self.store)

    def on_SearchClientCalls__activate(self, action):
        self.run_dialog(ClientCallsSearch, self.store)

    def on_SearchCreditCheckHistory__activate(self, action):
        self.run_dialog(CreditCheckHistorySearch, self.store)

    def on_SearchService__activate(self, button):
        self.run_dialog(ServiceSearch, self.store, hide_toolbar=True)

    def on_SearchSoldItemsByBranch__activate(self, button):
        self.run_dialog(SoldItemsByBranchSearch, self.store)

    def on_SearchSalesByPaymentMethod__activate(self, button):
        self.run_dialog(SalesByPaymentMethodSearch, self.store)

    def on_SearchDelivery__activate(self, action):
        self.run_dialog(DeliverySearch, self.store)

    def on_SearchSalesPersonSales__activate(self, action):
        self.run_dialog(SalesPersonSalesSearch, self.store)

    def on_SearchClientsWithSale__activate(self, action):
        self.run_dialog(ClientsWithSaleSearch, self.store)

    def on_SearchClientsWithCredit__activate(self, action):
        self.run_dialog(ClientsWithCreditSearch, self.store)

    def on_SearchSoldItemsByClient__activate(self, action):
        self.run_dialog(SoldItemsByClientSearch, self.store)

    # Toolbar

    def on_Edit__activate(self, action):
        self.sale_toolbar.edit()

    def on_Details__activate(self, action):
        self.sale_toolbar.show_details()

    def on_Return__activate(self, action):
        if self.check_open_inventory():
            return
        self.sale_toolbar.return_sale()

    # Sale toobar

    def on_sale_toolbar__sale_edited(self, widget, sale):
        self.refresh()

    def on_sale_toolbar__sale_returned(self, widget, sale):
        self.refresh()
