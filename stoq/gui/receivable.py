# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2012 Async Open Source <http://www.async.com.br>
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
"""
stoq/gui/receivable/receivable.py:

    Implementation of receivable application.
"""

import datetime

import pango
import gtk
from kiwi.currency import currency
from kiwi.python import all
from kiwi.ui.gadgets import render_pixbuf
from kiwi.ui.objectlist import Column

from stoqlib.api import api
from stoqlib.domain.payment.category import PaymentCategory
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.payment.views import InPaymentView
from stoqlib.domain.till import Till
from stoqlib.exceptions import TillError
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.paymenteditor import InPaymentEditor
from stoqlib.gui.editors.paymentseditor import SalePaymentsEditor
from stoqlib.gui.search.paymentsearch import InPaymentBillCheckSearch
from stoqlib.gui.search.paymentsearch import CardPaymentSearch
from stoqlib.gui.search.searchcolumns import IdentifierColumn, SearchColumn
from stoqlib.gui.search.searchfilters import DateSearchFilter
from stoqlib.gui.slaves.paymentconfirmslave import SalePaymentConfirmSlave
from stoqlib.gui.utils.keybindings import get_accels
from stoqlib.gui.utils.printing import print_report
from stoqlib.gui.wizards.renegotiationwizard import PaymentRenegotiationWizard
from stoqlib.lib.dateutils import localtoday
from stoqlib.lib.message import warning
from stoqlib.lib.translation import stoqlib_gettext as _
from stoqlib.reporting.payment import ReceivablePaymentReport
from stoqlib.reporting.paymentsreceipt import InPaymentReceipt

from stoq.gui.accounts import BaseAccountWindow, FilterItem


class ReceivableApp(BaseAccountWindow):

    # TODO: Change all widget.set_sensitive to self.set_sensitive([widget])

    app_title = _('Accounts receivable')
    gladefile = 'receivable'
    search_spec = InPaymentView
    search_label = _('matching:')
    report_table = ReceivablePaymentReport
    editor_class = InPaymentEditor

    payment_category_type = PaymentCategory.TYPE_RECEIVABLE

    #
    # Application
    #

    def create_actions(self):
        group = get_accels('app.receivable')
        actions = [
            # File
            ('AddReceiving', gtk.STOCK_ADD, _('Account receivable...'),
             group.get('add_receiving'),
             _('Create a new account receivable')),
            ('PaymentFlowHistory', None,
             _('Payment _flow history...'),
             group.get('payment_flow_history')),

            # Payment
            ('PaymentMenu', None, _('Payment')),
            ('Details', gtk.STOCK_INFO, _('Details...'),
             group.get('payment_details'),
             _('Show details for the selected payment'), ),
            ('Receive', gtk.STOCK_APPLY, _('Receive...'),
             group.get('payment_receive'),
             _('Receive the selected payments')),
            ('CancelPayment', gtk.STOCK_REMOVE, _('Cancel payment...'),
             group.get('payment_cancel'),
             _('Cancel the selected payment')),
            ('SetNotPaid', gtk.STOCK_UNDO, _('Set as not paid...'),
             group.get('payment_set_not_paid'),
             _('Mark the selected payment as not paid')),
            ('ChangeDueDate', gtk.STOCK_REFRESH, _('Change due date...'),
             group.get('payment_change_due_date'),
             _('Change the due date of the selected payment')),
            ('Renegotiate', None, _('Renegotiate...'),
             group.get('payment_renegotiate'),
             _('Renegotiate the selected payments')),
            ('Edit', None, _('Edit installments...'),
             group.get('payment_edit_installments'),
             _('Edit the selected payment installments')),
            ('Comments', None, _('Comments...'),
             group.get('payment_comments'),
             _('Add comments to the selected payment')),
            ('PrintDocument', gtk.STOCK_PRINT, _('Print document...'),
             group.get('payment_print_bill'),
             _('Print a bill for the selected payment')),
            ('PrintReceipt', None, _('Print _receipt...'),
             group.get('payment_print_receipt'),
             _('Print a receipt for the selected payment')),

            # Search
            ('PaymentCategories', None, _("Payment categories..."),
             group.get('search_payment_categories'),
             _('Search for payment categories')),
            ('BillCheckSearch', None, _('Bills and checks...'),
             group.get('search_bills'),
             _('Search for bills and checks')),
            ('CardPaymentSearch', None, _('Card payments...'),
             group.get('search_card_payments'),
             _('Search for card payments')),
        ]
        self.receivable_ui = self.add_ui_actions(None, actions,
                                                 filename='receivable.xml')
        self.set_help_section(_("Accounts receivable help"), 'app-receivable')

        self.Receive.set_short_label(_('Receive'))
        self.Details.set_short_label(_('Details'))
        self.Receive.props.is_important = True
        self.window.add_new_items([self.AddReceiving])
        self.window.add_search_items([self.BillCheckSearch,
                                      self.CardPaymentSearch])
        self.window.Print.set_tooltip(
            _("Print a report of this payments"))
        self.popup = self.uimanager.get_widget('/ReceivableSelection')

    def activate(self, refresh=True):
        self._update_widgets()

        if refresh:
            self.refresh()

        self.search.focus_search_entry()

    def deactivate(self):
        self.uimanager.remove_ui(self.receivable_ui)

    def new_activate(self):
        self.add_payment()

    def search_activate(self):
        self._run_bill_check_search()

    def create_filters(self):
        self.set_text_field_columns(['description', 'drawee', 'identifier_str'])
        self.create_main_filter()

    def get_columns(self):
        return [IdentifierColumn('identifier', title=_('Payment #')),
                SearchColumn('description', title=_('Description'),
                             data_type=str, ellipsize=pango.ELLIPSIZE_END,
                             expand=True, pack_end=True),
                Column('color', title=_('Description'), width=20,
                       data_type=gtk.gdk.Pixbuf, format_func=render_pixbuf,
                       column='description'),
                Column('comments_number', title=_(u'Comments'),
                       visible=False),
                SearchColumn('drawee', title=_('Drawee'), data_type=str,
                             ellipsize=pango.ELLIPSIZE_END, width=140),
                SearchColumn('due_date', title=_('Due date'),
                             data_type=datetime.date, width=100, sorted=True),
                SearchColumn('paid_date', title=_('Paid date'),
                             data_type=datetime.date, width=100),
                SearchColumn('status_str', title=_('Status'), width=100,
                             data_type=str, search_attribute='status',
                             valid_values=self._get_status_values(),
                             visible=False),
                SearchColumn('value', title=_('Value'), data_type=currency,
                             width=90),
                SearchColumn('paid_value', title=_('Paid'),
                             long_title=_('Paid value'),
                             data_type=currency, width=90),
                SearchColumn('category', title=_('Category'), data_type=str,
                             long_title=_('Payment category'), width=110,
                             visible=False)]

    #
    # Public API
    #

    def search_for_date(self, date):
        self.main_filter.select(None)
        dfilter = DateSearchFilter(_("Paid or due date"))
        dfilter.set_removable()
        dfilter.select(data=DateSearchFilter.Type.USER_DAY)
        self.add_filter(dfilter, columns=["paid_date", "due_date"])
        dfilter.start_date.set_date(date)
        self.refresh()

    #
    # Private
    #

    def _update_widgets(self):
        selected = self.results.get_selected_rows()
        one_item = len(selected) == 1
        self.Receive.set_sensitive(self._can_receive(selected))
        self.Details.set_sensitive(
            one_item and self._can_show_details(selected))
        self.Comments.set_sensitive(
            one_item and self._can_show_comments(selected))
        self.ChangeDueDate.set_sensitive(
            one_item and self._can_change_due_date(selected))
        self.CancelPayment.set_sensitive(
            one_item and self._can_cancel_payment(selected))
        self.PrintReceipt.set_sensitive(
            one_item and self._is_paid(selected))
        self.SetNotPaid.set_sensitive(
            one_item and self._is_paid(selected) and
            self._can_set_not_paid(selected))
        self.Edit.set_sensitive(self._can_edit(selected))
        self.PrintDocument.set_sensitive(self._can_print(selected))

    def _get_status_values(self):
        values = [(v, k) for k, v in Payment.statuses.items()]
        values.insert(0, (_("Any"), None))
        return values

    def _receive(self, receivable_views):
        """
        Receives a list of items from a receivable_views, note that
        the list of receivable_views must reference the same sale
        @param receivable_views: a list of receivable_views
        """
        assert self._can_receive(receivable_views)

        store = api.new_store()

        payments = [store.fetch(view.payment) for view in receivable_views]

        retval = run_dialog(SalePaymentConfirmSlave, self, store,
                            payments=payments)

        if store.confirm(retval):
            # We need to refresh the whole list as the payment(s) can possibly
            # disappear for the selected view
            self.refresh()

        store.close()
        self._update_widgets()

    def _is_paid(self, receivable_view):
        """
        Determines if the selected payment is paid.
        To do so he must meet the following condition:
          - The payment status needs to be set to PAID
        """
        if not receivable_view:
            return False

        return receivable_view[0].is_paid()

    def _can_set_not_paid(self, receivable_views):
        return all(view.payment.method.operation.can_set_not_paid(view.payment)
                   for view in receivable_views)

    def _can_receive(self, receivable_views):
        """
        Determines if a list of receivable_views can be received.
        To do so they must meet the following conditions:
          - Be in the same sale
          - The payment status needs to be set to PENDING
        """

        if not receivable_views:
            return False

        if not any(view.operation.can_pay(view.payment)
                   for view in receivable_views):
            return False

        if len(receivable_views) == 1:
            return receivable_views[0].status == Payment.STATUS_PENDING

        sale = receivable_views[0].sale
        if sale is None:
            return False
        return all(view.sale == sale and
                   view.status == Payment.STATUS_PENDING
                   for view in receivable_views)

    def _can_renegotiate(self, receivable_views):
        """whether or not we can renegotiate this payments

        This do to much queries. Dont call inside _update_widgets to avoid
        unecessary queries. Instead, call before the user actually tries to
        renegotiate.
        """
        if not len(receivable_views):
            return False

        # Parent is a Sale or a PaymentRenegotiation
        parent = receivable_views[0].get_parent()

        if not parent:
            return False

        client = parent.client

        return all(view.get_parent() and
                   view.get_parent().client is client and
                   view.get_parent().can_set_renegotiated()
                   for view in receivable_views)

    def _can_edit(self, views):
        """Determines if we can edit the selected payments
        """
        if not views:
            return False
        # Installments of renegotiated payments can not be edited.
        if views[0].group.renegotiation:
            return False

        sale_id = views[0].sale_id
        # Lonely payments are not created as sales, and it's installments
        # are edited differently.
        if not sale_id:
            return False
        can_edit = all(rv.sale_id == sale_id for rv in views)
        return can_edit

    def _can_cancel_payment(self, receivable_views):
        """whether or not we can cancel the receiving.
        """
        if len(receivable_views) != 1:
            return False

        if not any(view.operation.can_cancel(view.payment)
                   for view in receivable_views):
            return False

        return receivable_views[0].can_cancel_payment()

    def _can_change_due_date(self, receivable_views):
        """
        Determines if a list of receivable_views can have it's due date
        changed. To do so they must meet the following conditions:
          - The list  must have only one element
          - The payment was not paid
        """
        if len(receivable_views) != 1:
            return False

        if not any(view.operation.can_change_due_date(view.payment)
                   for view in receivable_views):
            return False

        return receivable_views[0].can_change_due_date()

    def _can_show_details(self, receivable_views):
        """Determines if we can show the receiving details for a list of
        receivable views.
        To do so they must meet the following conditions:
          - Be in the same sale or
          - One receiving that not belong to any sale
        """
        if not receivable_views:
            return False

        sale = receivable_views[0].sale_id
        if sale is None:
            if len(receivable_views) == 1:
                return True
            else:
                return False

        return all(view.sale_id == sale for view in receivable_views[1:])

    def _can_show_comments(self, receivable_views):
        return len(receivable_views) == 1

    def _can_print(self, receivable_views):
        if len(receivable_views) == 1:
            view = receivable_views[0]
            return view.operation.can_print(view.payment)
        return False

    def _run_card_payment_search(self):
        run_dialog(CardPaymentSearch, self, self.store)

    def _run_bill_check_search(self):
        run_dialog(InPaymentBillCheckSearch, self, self.store)

    def _update_filter_items(self):
        options = [
            FilterItem(_('Received payments'), 'status:paid'),
            FilterItem(_('To receive'), 'status:not-paid'),
            FilterItem(_('Late payments'), 'status:late'),
        ]
        self.add_filter_items(PaymentCategory.TYPE_RECEIVABLE, options)

    #
    # Kiwi callbacks
    #

    def on_results__row_activated(self, klist, receivable_view):
        self.show_details(receivable_view)

    def on_results__selection_changed(self, receivables, selected):
        self._update_widgets()

    def on_results__right_click(self, results, result, event):
        self.popup.popup(None, None, None, event.button, event.time)

    def on_Details__activate(self, button):
        selected = self.results.get_selected_rows()[0]
        self.show_details(selected)

    def on_Receive__activate(self, button):
        self._receive(self.results.get_selected_rows())

    def on_Comments__activate(self, action):
        receivable_view = self.results.get_selected_rows()[0]
        self.show_comments(receivable_view)

    def on_PrintReceipt__activate(self, action):
        receivable_view = self.results.get_selected_rows()[0]
        payment = receivable_view.payment
        date = localtoday().date()
        print_report(InPaymentReceipt, payment=payment,
                     order=receivable_view.sale, date=date)

    def on_AddReceiving__activate(self, action):
        self.add_payment()

    def on_CancelPayment__activate(self, action):
        receivable_view = self.results.get_selected_rows()[0]
        order = receivable_view.sale
        self.change_status(receivable_view, order, Payment.STATUS_CANCELLED)

    def on_SetNotPaid__activate(self, action):
        receivable_view = self.results.get_selected_rows()[0]
        order = receivable_view.sale
        self.change_status(receivable_view, order, Payment.STATUS_PENDING)

    def on_ChangeDueDate__activate(self, action):
        receivable_view = self.results.get_selected_rows()[0]
        self.change_due_date(receivable_view, receivable_view.sale)

    def on_BillCheckSearch__activate(self, action):
        self._run_bill_check_search()

    def on_CardPaymentSearch__activate(self, action):
        self._run_card_payment_search()

    def on_Renegotiate__activate(self, action):
        try:
            Till.get_current(self.store)
        except TillError as e:
            warning(str(e))
            return
        receivable_views = self.results.get_selected_rows()
        if not self._can_renegotiate(receivable_views):
            warning(_('Cannot renegotiate selected payments'))
            return
        store = api.new_store()

        groups = list(set([store.fetch(v.group) for v in receivable_views]))
        retval = run_dialog(PaymentRenegotiationWizard, self, store,
                            groups)

        if store.confirm(retval):
            # FIXME: Storm is not expiring the groups correctly.
            # Figure out why. See bug 5087
            self.refresh()
            self._update_widgets()
        store.close()

    def on_Edit__activate(self, action):
        try:
            Till.get_current(self.store)
        except TillError as e:
            warning(str(e))
            return

        store = api.new_store()
        views = self.results.get_selected_rows()
        sale = store.fetch(views[0].sale)
        retval = run_dialog(SalePaymentsEditor, self, store, sale)

        if store.confirm(retval):
            self.refresh()
        store.close()

    def on_PrintDocument__activate(self, action):
        view = self.results.get_selected_rows()[0]
        payments = [view.payment]
        report = view.operation.print_(payments)
        if report is not None:
            print_report(report, payments)
