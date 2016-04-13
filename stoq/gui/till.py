# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2011 Async Open Source <http://www.async.com.br>
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
""" Implementation of till application.  """

import decimal
from datetime import date
import logging

import pango
import gtk
from kiwi.currency import currency
from kiwi.datatypes import converter
from kiwi.ui.objectlist import Column
from storm.expr import And, Or
from stoqlib.api import api
from stoqlib.enums import SearchFilterPosition
from stoqlib.exceptions import (StoqlibError, TillError, SellError,
                                ModelDataError)
from stoqlib.database.expr import Date
from stoqlib.domain.sale import Sale, SaleView
from stoqlib.domain.till import Till
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.workorder import WorkOrder
from stoqlib.lib.dateutils import localtoday
from stoqlib.lib.formatters import format_quantity
from stoqlib.lib.message import yesno, warning
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext as _
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.dialogs.missingitemsdialog import (MissingItemsDialog,
                                                    get_missing_items)
from stoqlib.gui.dialogs.saledetails import SaleDetailsDialog
from stoqlib.gui.dialogs.tilldailymovement import TillDailyMovementDialog
from stoqlib.gui.dialogs.tillhistory import TillHistoryDialog
from stoqlib.gui.editors.paymentseditor import SalePaymentsEditor
from stoqlib.gui.editors.tilleditor import CashInEditor, CashOutEditor
from stoqlib.gui.fiscalprinter import FiscalPrinterHelper
from stoqlib.gui.search.paymentsearch import CardPaymentSearch
from stoqlib.gui.search.paymentreceivingsearch import PaymentReceivingSearch
from stoqlib.gui.search.personsearch import ClientSearch
from stoqlib.gui.search.salesearch import (SaleWithToolbarSearch,
                                           SoldItemsByBranchSearch)
from stoqlib.gui.search.searchcolumns import IdentifierColumn, SearchColumn
from stoqlib.gui.search.searchfilters import ComboSearchFilter
from stoqlib.gui.search.tillsearch import TillFiscalOperationsSearch, TillClosedSearch
from stoqlib.gui.slaves.saleslave import return_sale
from stoqlib.gui.utils.keybindings import get_accels
from stoqlib.reporting.sale import SalesReport

from stoq.gui.shell.shellapp import ShellApp

log = logging.getLogger(__name__)

LOGO_WIDTH = 91
LOGO_HEIGHT = 32


class TillApp(ShellApp):

    app_title = _(u'Till')
    gladefile = 'till'
    search_spec = SaleView
    search_labels = _(u'matching:')
    report_table = SalesReport

    #
    # Application
    #

    def create_actions(self):
        group = get_accels('app.till')
        actions = [
            ('SaleMenu', None, _('Sale')),
            ('TillOpen', None, _('Open till...'),
             group.get('open_till')),
            ('TillClose', None, _('Close till...'),
             group.get('close_till')),
            ('TillVerify', None, _('Verify till...'),
             group.get('verify_till')),
            ("TillDailyMovement", None, _("Till daily movement..."),
             group.get('daily_movement')),
            ('TillAddCash', None, _('Cash addition...'), ''),
            ('TillRemoveCash', None, _('Cash removal...'), ''),
            ("PaymentReceive", None, _("Payment receival..."),
             group.get('payment_receive'),
             _("Receive payments")),
            ("SearchClient", None, _("Clients..."),
             group.get('search_clients'),
             _("Search for clients")),
            ("SearchSale", None, _("Sales..."),
             group.get('search_sale'),
             _("Search for sales")),
            ("SearchCardPayment", None, _("Card payments..."),
             None, _("Search for card payments")),
            ("SearchSoldItemsByBranch", None, _("Sold items by branch..."),
             group.get('search_sold_items_by_branch'),
             _("Search for items sold by branch")),
            ("SearchTillHistory", None, _("Till entry history..."),
             group.get('search_till_history'),
             _("Search for till history")),
            ("SearchFiscalTillOperations", None, _("Fiscal till operations..."),
             group.get('search_fiscal_till_operations'),
             _("Search for fiscal till operations")),
            ("SearchClosedTill", None, _("Closed till search..."),
             group.get('search_closed_till'),
             _("Search for all closed tills")),
            ("Confirm", gtk.STOCK_APPLY, _("Confirm..."),
             group.get('confirm_sale'),
             _("Confirm the selected sale, decreasing stock and making it "
               "possible to receive it's payments")),
            # FIXME: This button should change the label to "Cancel" when the
            # selected sale can be cancelled and not returned, since that's
            # what is going to happen when the user click in it
            ("Return", gtk.STOCK_CANCEL, _("Return..."),
             group.get('return_sale'),
             _("Return the selected sale, returning stock and the client's "
               "payments")),
            ("Details", gtk.STOCK_INFO, _("Details..."),
             group.get('sale_details'),
             _("Show details of the selected sale")),
        ]

        self.till_ui = self.add_ui_actions('', actions,
                                           filename="till.xml")
        self.set_help_section(_("Till help"), 'app-till')

        self.Confirm.set_short_label(_('Confirm'))
        self.Return.set_short_label(_('Return'))
        self.Details.set_short_label(_('Details'))
        self.Confirm.props.is_important = True
        self.Return.props.is_important = True
        self.Details.props.is_important = True

    def create_ui(self):
        self.popup = self.uimanager.get_widget('/TillSelection')

        self.current_branch = api.get_current_branch(self.store)
        # Groups
        self.main_vbox.set_focus_chain([self.app_vbox])
        self.app_vbox.set_focus_chain([self.search_holder, self.list_vbox])

        # Setting up the toolbar
        self.list_vbox.set_focus_chain([self.footer_hbox])
        self._setup_printer()
        self._setup_widgets()
        self.status_link.set_use_markup(True)
        self.status_link.set_justify(gtk.JUSTIFY_CENTER)

    def get_title(self):
        return _('[%s] - Till') % (
            api.get_current_branch(self.store).get_description(), )

    def activate(self, refresh=True):
        self.window.add_new_items([self.TillAddCash,
                                   self.TillRemoveCash])
        self.window.add_search_items([self.SearchFiscalTillOperations,
                                      self.SearchClient,
                                      self.SearchSale])
        self.window.Print.set_tooltip(_("Print a report of these sales"))
        if refresh:
            self.refresh()
        self._printer.run_initial_checks()
        self.check_open_inventory()

        self.search.focus_search_entry()

    def deactivate(self):
        self.uimanager.remove_ui(self.till_ui)

    def new_activate(self):
        if not self.TillAddCash.get_sensitive():
            return
        self._run_add_cash_dialog()

    def search_activate(self):
        self._run_search_dialog(TillFiscalOperationsSearch)

    #
    # ShellApp
    #

    def set_open_inventory(self):
        self.set_sensitive(self._inventory_widgets, False)

    def create_filters(self):
        self.search.set_query(self._query_executer)
        self.set_text_field_columns(['client_name', 'salesperson_name',
                                     'identifier_str'])
        self.status_filter = ComboSearchFilter(_(u"Show orders"),
                                               self._get_status_values())
        self.add_filter(self.status_filter, position=SearchFilterPosition.TOP,
                        columns=['status'])

    def get_columns(self):
        return [IdentifierColumn('identifier', title=_('Sale #'),
                                 sorted=True),
                Column('status_name', title=_(u'Status'), data_type=str,
                       visible=True),
                SearchColumn('open_date', title=_('Date Started'), width=110,
                             data_type=date, justify=gtk.JUSTIFY_RIGHT),
                SearchColumn('client_name', title=_('Client'),
                             data_type=str, expand=True,
                             ellipsize=pango.ELLIPSIZE_END),
                SearchColumn('salesperson_name', title=_('Salesperson'),
                             data_type=str, width=180,
                             ellipsize=pango.ELLIPSIZE_END),
                SearchColumn('total_quantity', title=_('Quantity'),
                             data_type=decimal.Decimal, width=100,
                             format_func=format_quantity),
                SearchColumn('total', title=_('Total'), data_type=currency,
                             width=100)]

    #
    # Private
    #

    def _query_executer(self, store):
        # We should only show Sales that
        # 1) In the current branch (FIXME: Should be on the same station.
                                    # See bug 4266)
        # 2) Are in the status QUOTE or ORDERED.
        # 3) For the order statuses, the date should be the same as today

        query = And(Sale.branch == self.current_branch,
                    Or(Sale.status == Sale.STATUS_QUOTE,
                       Sale.status == Sale.STATUS_ORDERED,
                       Date(Sale.open_date) == date.today()))

        return store.find(self.search_spec, query)

    def _setup_printer(self):
        self._printer = FiscalPrinterHelper(self.store,
                                            parent=self)
        self._printer.connect('till-status-changed',
                              self._on_PrinterHelper__till_status_changed)
        self._printer.connect('ecf-changed',
                              self._on_PrinterHelper__ecf_changed)
        self._printer.setup_midnight_check()

    def _get_status_values(self):
        statuses = [(v, k) for k, v in Sale.statuses.items()]
        statuses.insert(0, (_('Any'), None))
        return statuses

    def _create_sale_payments(self, order_view):
        store = api.new_store()
        sale = store.fetch(order_view.sale)
        retval = run_dialog(SalePaymentsEditor, self, store, sale)

        # Change the sale status to ORDERED
        if retval and sale.can_order():
            sale.order()

        if store.confirm(retval):
            self.refresh()
        store.close()

    def _confirm_order(self, order_view):
        if self.check_open_inventory():
            return

        store = api.new_store()
        sale = store.fetch(order_view.sale)
        expire_date = sale.expire_date

        if (sale.status == Sale.STATUS_QUOTE and
            expire_date and expire_date.date() < date.today() and
            not yesno(_("This quote has expired. Confirm it anyway?"),
                      gtk.RESPONSE_YES,
                      _("Confirm quote"), _("Don't confirm"))):
            store.close()
            return

        missing = get_missing_items(sale, store)

        if missing:
            retval = run_dialog(MissingItemsDialog, self, sale, missing)
            if retval:
                self.refresh()
            store.close()
            return

        coupon = self._open_coupon(sale)
        if not coupon:
            store.close()
            return
        subtotal = self._add_sale_items(sale, coupon)
        try:
            if coupon.confirm(sale, store, subtotal=subtotal):
                workorders = WorkOrder.find_by_sale(store, sale)
                for order in workorders:
                    order.close()
                store.commit()
                self.refresh()
            else:
                coupon.cancel()
        except SellError as err:
            warning(str(err))
        except ModelDataError as err:
            warning(str(err))

        store.close()

    def _open_coupon(self, sale=None):
        coupon = self._printer.create_coupon(sale=sale)

        if coupon:
            while not coupon.open():
                if not yesno(_("Failed to open the fiscal coupon.\n"
                               "Until it is opened, it's not possible to "
                               "confirm the sale. Do you want to try again?"),
                             gtk.RESPONSE_YES, _("Try again"), _("Cancel coupon")):
                    return None

        return coupon

    def _add_sale_items(self, sale, coupon):
        subtotal = 0
        for sale_item in sale.get_items(with_children=False):
            sellable = sale_item.sellable
            if (sellable.service or
                    (sellable.product and not sellable.product.is_package)):
                # Do not add the package item itself on the coupon
                coupon.add_item(sale_item)
                subtotal += sale_item.price * sale_item.quantity

            for child in sale_item.children_items:
                coupon.add_item(child)
                subtotal += child.price * child.quantity
        return subtotal

    def _update_total(self):
        balance = currency(self._get_till_balance())
        text = _(u"Total: %s") % converter.as_string(currency, balance)
        self.total_label.set_text(text)

    def _update_payment_total(self):
        balance = currency(self._get_total_paid_payment())
        text = _(u"Total payments: %s") % converter.as_string(currency, balance)
        self.total_payment_label.set_text(text)

    def _get_total_paid_payment(self):
        """Returns the total of payments of the day"""
        payments = self.store.find(Payment,
                                   Date(Payment.paid_date) == localtoday())
        return payments.sum(Payment.paid_value) or 0

    def _get_till_balance(self):
        """Returns the balance of till operations"""
        try:
            till = Till.get_current(self.store)
        except TillError:
            till = None

        if till is None:
            return currency(0)

        return till.get_balance()

    def _setup_widgets(self):
        # SearchSale is here because it's possible to return a sale inside it
        self._inventory_widgets = [self.Confirm, self.SearchSale,
                                   self.Return]
        self.register_sensitive_group(self._inventory_widgets,
                                      lambda: not self.has_open_inventory())

        self.total_label.set_size('xx-large')
        self.total_label.set_bold(True)
        if not sysparam.get_bool('SHOW_TOTAL_PAYMENTS_ON_TILL'):
            self.total_payment_label.hide()
        else:
            self.total_payment_label.set_size('large')
            self.total_payment_label.set_bold(True)
            self.total_label.set_size('large')

        self.small_status.set_size('xx-large')
        self.small_status.set_bold(True)

    def _update_toolbar_buttons(self):
        sale_view = self.results.get_selected()
        if sale_view:
            can_confirm = sale_view.can_confirm()
            # when confirming sales in till, we also might want to cancel
            # sales
            can_return = (sale_view.can_return() or
                          sale_view.can_cancel())
        else:
            can_confirm = can_return = False

        self.set_sensitive([self.Details], bool(sale_view))
        self.set_sensitive([self.Confirm], can_confirm)
        self.set_sensitive([self.Return], can_return)

    def _check_selected(self):
        sale_view = self.results.get_selected()
        if not sale_view:
            raise StoqlibError("You should have a selected item at "
                               "this point")
        return sale_view

    def _run_search_dialog(self, dialog_type, **kwargs):
        store = api.new_store()
        self.run_dialog(dialog_type, store, **kwargs)
        store.close()

    def _run_details_dialog(self):
        sale_view = self._check_selected()
        run_dialog(SaleDetailsDialog, self, self.store, sale_view)

    def _run_add_cash_dialog(self):
        with api.new_store() as store:
            try:
                run_dialog(CashInEditor, self, store)
            except TillError as err:
                # Inform the error to the user instead of crashing
                warning(str(err))
                return

        if store.committed:
            self._update_total()

    def _return_sale(self):
        if self.check_open_inventory():
            return

        sale_view = self._check_selected()

        with api.new_store() as store:
            return_sale(self.get_toplevel(), store.fetch(sale_view.sale), store)

        if store.committed:
            self._update_total()
            self.refresh()

    def _update_ecf(self, has_ecf):
        # If we have an ecf, let the other events decide what to disable.
        if has_ecf:
            return

        # We dont have an ecf. Disable till related operations
        widgets = [self.TillOpen, self.TillClose, self.TillVerify, self.TillAddCash,
                   self.TillRemoveCash, self.SearchTillHistory, self.app_vbox,
                   self.Confirm, self.Return, self.Details]
        self.set_sensitive(widgets, has_ecf)
        text = _(u"Till operations requires a connected fiscal printer")
        self.small_status.set_text(text)

    def _update_till_status(self, closed, blocked):
        # Three different situations:
        #
        # - Till is closed
        # - Till is opened
        # - Till was not closed the previous fiscal day (blocked)

        self.set_sensitive([self.TillOpen], closed)
        self.set_sensitive([self.TillClose], not closed or blocked)
        widgets = [self.TillVerify, self.TillAddCash, self.TillRemoveCash,
                   self.SearchTillHistory, self.search_holder, self.PaymentReceive]
        self.set_sensitive(widgets, not closed and not blocked)

        def large(s):
            return '<span weight="bold" size="xx-large">%s</span>' % (
                api.escape(s), )

        if closed:
            text = large(_(u"Till closed"))
            self.search_holder.hide()
            self.footer_hbox.hide()
            self.large_status.show()
            self.clear()
            self.setup_focus()
            # Adding the label on footer without the link
            self.small_status.set_text(text)

            if not blocked:
                text += '\n\n<span size="large"><a href="open-till">%s</a></span>' % (
                    api.escape(_('Open till')))
            self.status_link.set_markup(text)
        elif blocked:
            self.search_holder.hide()
            self.footer_hbox.hide()
            text = large(_(u"Till blocked"))
            self.status_link.set_markup(text)
            self.small_status.set_text(text)
        else:
            self.search_holder.show()
            self.footer_hbox.show()
            self.large_status.hide()
            till = Till.get_current(self.store)
            text = _(u"Till opened on %s") % till.opening_date.strftime('%x')
            self.small_status.set_text(text)
        self._update_toolbar_buttons()
        self._update_total()
        if sysparam.get_bool('SHOW_TOTAL_PAYMENTS_ON_TILL'):
            self._update_payment_total()

    #
    # Callbacks
    #

    def on_Confirm__activate(self, action):
        selected = self.results.get_selected()

        # If there are unfinished workorders associated with the sale, we
        # cannot print the coupon yet. Instead lets just create the payments.
        workorders = WorkOrder.find_by_sale(self.store, selected.sale)
        if not all(wo.can_close() for wo in workorders):
            self._create_sale_payments(selected)
        else:
            self._confirm_order(selected)
        self._update_total()

    def on_results__double_click(self, results, sale):
        self._run_details_dialog()

    def on_results__selection_changed(self, results, sale):
        self._update_toolbar_buttons()

    def on_results__has_rows(self, results, has_rows):
        self._update_total()

    def on_results__right_click(self, results, result, event):
        self.popup.popup(None, None, None, event.button, event.time)

    def on_Details__activate(self, action):
        self._run_details_dialog()

    def on_Return__activate(self, action):
        self._return_sale()

    def on_status_link__activate_link(self, button, link):
        if link == 'open-till':
            self._printer.open_till()
        return True

    def _on_PrinterHelper__till_status_changed(self, printer, closed, blocked):
        self._update_till_status(closed, blocked)

    def _on_PrinterHelper__ecf_changed(self, printer, ecf):
        self._update_ecf(ecf)

    def on_PaymentReceive__activate(self, action):
        self.run_dialog(PaymentReceivingSearch, self.store)

    # Till

    def on_TillVerify__activate(self, button):
        self._printer.verify_till()

    def on_TillClose__activate(self, button):
        self._printer.close_till()

    def on_TillOpen__activate(self, button):
        self._printer.open_till()

    def on_TillAddCash__activate(self, action):
        self._run_add_cash_dialog()

    def on_TillRemoveCash__activate(self, action):
        with api.new_store() as store:
            run_dialog(CashOutEditor, self, store)
        if store.committed:
            self._update_total()

    def on_TillDailyMovement__activate(self, button):
        self.run_dialog(TillDailyMovementDialog, self.store)

    # Search

    def on_SearchClient__activate(self, action):
        self._run_search_dialog(ClientSearch, hide_footer=True)

    def on_SearchSale__activate(self, action):
        if self.check_open_inventory():
            return

        self._run_search_dialog(SaleWithToolbarSearch)
        self.refresh()

    def on_SearchCardPayment__activate(self, action):
        self.run_dialog(CardPaymentSearch, self.store)

    def on_SearchSoldItemsByBranch__activate(self, button):
        self._run_search_dialog(SoldItemsByBranchSearch)

    def on_SearchTillHistory__activate(self, button):
        self.run_dialog(TillHistoryDialog, self.store)

    def on_SearchFiscalTillOperations__activate(self, button):
        self._run_search_dialog(TillFiscalOperationsSearch)

    def on_SearchClosedTill__activate(self, button):
        self._run_search_dialog(TillClosedSearch)
