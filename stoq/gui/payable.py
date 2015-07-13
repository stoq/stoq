# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007-2012 Async Open Source <http://www.async.com.br>
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
stoq/gui/payable/payable.py:

    Implementation of payable application.
"""

import datetime

import pango
import gtk
from kiwi.currency import currency
from kiwi.python import all
from kiwi.ui.objectlist import Column
from kiwi.ui.gadgets import render_pixbuf

from stoqlib.api import api
from stoqlib.domain.payment.category import PaymentCategory
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.payment.views import OutPaymentView
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.paymenteditor import OutPaymentEditor
from stoqlib.gui.editors.paymentseditor import PurchasePaymentsEditor
from stoqlib.gui.search.paymentsearch import OutPaymentBillCheckSearch
from stoqlib.gui.search.searchcolumns import IdentifierColumn, SearchColumn
from stoqlib.gui.search.searchfilters import DateSearchFilter
from stoqlib.gui.slaves.paymentconfirmslave import PurchasePaymentConfirmSlave
from stoqlib.gui.utils.keybindings import get_accels
from stoqlib.gui.utils.printing import print_report
from stoqlib.lib.dateutils import localtoday
from stoqlib.lib.message import warning
from stoqlib.lib.translation import stoqlib_gettext as _
from stoqlib.reporting.payment import PayablePaymentReport
from stoqlib.reporting.paymentsreceipt import OutPaymentReceipt

from stoq.gui.accounts import BaseAccountWindow, FilterItem


class PayableApp(BaseAccountWindow):

    # TODO: Change all widget.set_sensitive to self.set_sensitive([widget])

    app_title = _('Accounts payable')
    gladefile = 'payable'
    search_spec = OutPaymentView
    search_label = _('matching:')
    report_table = PayablePaymentReport
    editor_class = OutPaymentEditor

    payment_category_type = PaymentCategory.TYPE_PAYABLE

    #
    # Application
    #

    def create_actions(self):
        group = get_accels('app.payable')

        actions = [
            # File
            ('AddPayment', gtk.STOCK_ADD, _('Account payable...'),
             group.get('add_payable'),
             _('Create a new account payable')),
            ('PaymentFlowHistory', None, _('Payment _flow history...'),
             group.get('payment_flow_history'),
             _('Show a report of payment expected to receive grouped by day')),

            # Payment
            ('PaymentMenu', None, _('Payment')),
            ('Details', gtk.STOCK_INFO, _('Details...'),
             group.get('payment_details'),
             _('Show details for the selected payment')),
            ('Pay', gtk.STOCK_APPLY, _('Pay...'),
             group.get('payment_pay'),
             _('Pay the order associated with the selected payment')),
            ('Edit', gtk.STOCK_EDIT, _('Edit installments...'),
             group.get('payment_edit'),
             _('Edit the selected payment installments')),
            ('CancelPayment', gtk.STOCK_REMOVE, _('Cancel...'),
             group.get('payment_cancel'),
             _('Cancel the selected payment')),
            ('SetNotPaid', gtk.STOCK_UNDO, _('Set as not paid...'),
             group.get('payment_set_not_paid'),
             _('Mark the selected payment as not paid')),
            ('ChangeDueDate', gtk.STOCK_REFRESH, _('Change due date...'),
             group.get('payment_change_due_date'),
             _('Change the due date of the selected payment')),
            ('Comments', None, _('Comments...'),
             group.get('payment_comments'),
             _('Add comments to the selected payment')),
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
        ]

        self.payable_ui = self.add_ui_actions(None, actions,
                                              filename='payable.xml')
        self.set_help_section(_("Accounts payable help"), 'app-payable')
        self.Pay.set_short_label(_('Pay'))
        self.Edit.set_short_label(_('Edit'))
        self.Details.set_short_label(_('Details'))
        self.Pay.props.is_important = True
        self.Pay.set_sensitive(False)
        self.PrintReceipt.set_sensitive(False)
        self.popup = self.uimanager.get_widget('/PayableSelection')
        self.window.add_new_items([self.AddPayment])
        self.window.NewToolItem.set_tooltip(self.AddPayment.get_tooltip())
        self.window.add_search_items([self.BillCheckSearch])
        self.window.SearchToolItem.set_tooltip(
            self.BillCheckSearch.get_tooltip())
        self.window.Print.set_tooltip(
            _("Print a report of these payments"))

    def activate(self, refresh=True):
        if refresh:
            self.refresh()
        self._update_widgets()

        self.search.focus_search_entry()

    def deactivate(self):
        self.uimanager.remove_ui(self.payable_ui)

    def new_activate(self):
        self.add_payment()

    def search_activate(self):
        run_dialog(OutPaymentBillCheckSearch, self, self.store)

    def create_filters(self):
        self.set_text_field_columns(['description', 'supplier_name',
                                     'identifier_str'])
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
                SearchColumn('supplier_name', title=_('Supplier'),
                             data_type=str, width=140,
                             ellipsize=pango.ELLIPSIZE_END),
                SearchColumn('due_date', title=_('Due date'),
                             data_type=datetime.date, width=100,
                             sorted=True),
                SearchColumn('paid_date', title=_('Paid date'),
                             data_type=datetime.date, width=100),
                SearchColumn('status_str', title=_('Status'), width=100,
                             data_type=str, search_attribute='status',
                             valid_values=self._get_status_values(),
                             visible=False),
                SearchColumn('value', title=_('Value'), data_type=currency,
                             width=90),
                SearchColumn('paid_value', title=_('Paid'), data_type=currency,
                             long_title=_('Paid value'), width=90),
                SearchColumn('category', title=_('Category'), data_type=str,
                             long_title=_('Payment category'), width=110,
                             visible=False),
                ]

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

    def _can_show_details(self, payable_views):
        """
        Determines if we can show details for a list of payables
        """
        can_show_details = (self._same_purchase(payable_views) or
                            self._same_sale(payable_views))
        if not can_show_details and len(payable_views) == 1:
            can_show_details = True
        return can_show_details

    def _can_show_comments(self, payable_views):
        return len(payable_views) == 1

    def _can_edit(self, payable_views):
        """Determines if we can edit the selected payments
        """
        if not self._same_purchase(payable_views):
            return False

        purchase = payable_views[0].purchase
        status = purchase and purchase.status

        if (status == PurchaseOrder.ORDER_CANCELLED or
            status == PurchaseOrder.ORDER_PENDING):
            return False

        return True

    def _can_cancel_payment(self, payable_views):
        """whether or not we can cancel the payment.
        """
        if len(payable_views) != 1:
            return False

        if not any(view.operation.can_cancel(view.payment)
                   for view in payable_views):
            return False

        return payable_views[0].can_cancel_payment()

    def _can_change_due_date(self, payable_views):
        """ Determines if a list of payables_views can have it's due
        date changed. To do so they must meet the following conditions:
            - The list must have only one element
            - The payment was not paid
        """
        if len(payable_views) != 1:
            return False

        if not any(view.operation.can_change_due_date(view.payment)
                   for view in payable_views):
            return False

        return payable_views[0].can_change_due_date()

    def _edit(self, payable_views):
        with api.new_store() as store:
            order = store.fetch(payable_views[0].purchase)
            run_dialog(PurchasePaymentsEditor, self, store, order)

        if store.committed:
            self.refresh()

    def _pay(self, payable_views):
        """
        Pay a list of items from a payable_views, note that
        the list of payable_views must reference the same order
        @param payables_views: a list of payable_views
        """
        assert self._can_pay(payable_views)

        # Do not allow confirming the payment if the purchase was not
        # completely received.
        purchase_order = payable_views[0].purchase

        if (purchase_order and
            api.sysparam.get_bool('BLOCK_INCOMPLETE_PURCHASE_PAYMENTS') and
            not purchase_order.status == PurchaseOrder.ORDER_CLOSED):

            return warning(_("Can't confirm the payment if the purchase "
                             "is not completely received yet."))

        with api.new_store() as store:
            payments = [store.fetch(view.payment) for view in payable_views]

            run_dialog(PurchasePaymentConfirmSlave, self, store,
                       payments=payments)

        if store.committed:
            # We need to refresh the whole list as the payment(s) can possibly
            # disappear for the selected view
            self.refresh()

        self._update_widgets()

    def _can_pay(self, payable_views):
        """
        Determines if a list of payables_views can be paid.
        To do so they must meet the following conditions:
          - Be in the same purchase order
          - The payment status needs to be set to PENDING
        """
        if not payable_views:
            return False

        if not any(view.operation.can_pay(view.payment)
                   for view in payable_views):
            return False

        if len(payable_views) == 1:
            return payable_views[0].status == Payment.STATUS_PENDING

        purchase = payable_views[0].purchase_id
        if purchase is None:
            return False
        return all(view.purchase_id == purchase and
                   view.status == Payment.STATUS_PENDING
                   for view in payable_views)

    def _are_paid(self, payable_views, respect_purchase=True):
        """
        Determines if a list of payables_views are paid.
        To do so they must meet the following conditions:
          - Be in the same purchase order.
            (This will be satistied only if respect_purchase is True)
          - The payment status needs to be set to PAID
        """
        if not payable_views:
            return False

        purchase = payable_views[0].purchase_id
        if not purchase and len(payable_views) > 1:
            return False

        return all((view.purchase_id == purchase or not respect_purchase) and
                   view.is_paid() for view in payable_views)

    def _can_set_not_paid(self, payable_views):
        return all(view.payment.method.operation.can_set_not_paid(view.payment)
                   for view in payable_views)

    def _same_purchase(self, payable_views):
        """Determines if a list of payable_views are in the same purchase"""
        if not payable_views:
            return False

        purchase = payable_views[0].purchase_id
        if purchase is None:
            return False
        return all(view.purchase_id == purchase for view in payable_views)

    def _same_sale(self, payable_views):
        """Determines if a list of payable_views are in the same sale"""
        if not payable_views:
            return False

        sale = payable_views[0].sale
        if sale is None:
            return False
        return all(view.sale == sale for view in payable_views)

    def _update_widgets(self):
        selected = self.results.get_selected_rows()
        self.Details.set_sensitive(self._can_show_details(selected))
        self.Comments.set_sensitive(self._can_show_comments(selected))
        self.ChangeDueDate.set_sensitive(self._can_change_due_date(selected))
        self.CancelPayment.set_sensitive(self._can_cancel_payment(selected))
        self.Edit.set_sensitive(self._can_edit(selected))
        self.Pay.set_sensitive(self._can_pay(selected))
        self.PrintReceipt.set_sensitive(self._are_paid(selected,
                                                       respect_purchase=True))
        self.SetNotPaid.set_sensitive(self._are_paid(
            selected, respect_purchase=False) and
            self._can_set_not_paid(selected))

    def _get_status_values(self):
        items = [(value, key) for key, value in Payment.statuses.items()]
        items.insert(0, (_('Any'), None))
        return items

    def _run_bill_check_search(self):
        run_dialog(OutPaymentBillCheckSearch, self, self.store)

    def _update_filter_items(self):
        options = [
            FilterItem(_('Paid payments'), 'status:paid'),
            FilterItem(_('To pay'), 'status:not-paid'),
            FilterItem(_('Late payments'), 'status:late'),
        ]

        self.add_filter_items(PaymentCategory.TYPE_PAYABLE, options)

    #
    # Kiwi callbacks
    #

    def on_results__row_activated(self, klist, payable_view):
        if self._can_show_details([payable_view]):
            self.show_details(payable_view)

    def on_results__right_click(self, results, result, event):
        self.popup.popup(None, None, None, event.button, event.time)

    def on_results__selection_changed(self, results, selected):
        self._update_widgets()

    def on_Comments__activate(self, action):
        payable_view = self.results.get_selected_rows()[0]
        self.show_comments(payable_view)

    def on_Details__activate(self, action):
        payable_view = self.results.get_selected_rows()[0]
        self.show_details(payable_view)

    def on_Pay__activate(self, action):
        self._pay(self.results.get_selected_rows())

    def on_Edit__activate(self, action):
        self._edit(self.results.get_selected_rows())

    def on_PrintReceipt__activate(self, action):
        payment_views = self.results.get_selected_rows()
        payments = [v.payment for v in payment_views]
        date = localtoday().date()
        print_report(OutPaymentReceipt, payment=payments[0],
                     order=payment_views[0].purchase, date=date)

    def on_AddPayment__activate(self, action):
        self.add_payment()

    def on_CancelPayment__activate(self, action):
        payable_view = self.results.get_selected_rows()[0]
        order = payable_view.sale or payable_view.purchase
        self.change_status(payable_view, order, Payment.STATUS_CANCELLED)

    def on_SetNotPaid__activate(self, action):
        payable_view = self.results.get_selected_rows()[0]
        order = payable_view.sale or payable_view.purchase
        self.change_status(payable_view, order, Payment.STATUS_PENDING)

    def on_ChangeDueDate__activate(self, action):
        payable_view = self.results.get_selected_rows()[0]
        order = payable_view.sale or payable_view.purchase
        self.change_due_date(payable_view, order)

    def on_BillCheckSearch__activate(self, action):
        self._run_bill_check_search()
