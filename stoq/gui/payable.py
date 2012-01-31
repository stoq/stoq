# -*- Mode: Python; coding: iso-8859-1 -*-
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
import gettext

import pango
import gtk
from kiwi.datatypes import currency
from kiwi.enums import SearchFilterPosition
from kiwi.python import all
from kiwi.ui.search import ComboSearchFilter, DateSearchFilter
from kiwi.ui.objectlist import Column, SearchColumn
from kiwi.ui.gadgets import render_pixbuf
from stoqlib.api import api
from stoqlib.domain.payment.operation import register_payment_operations
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.payment.views import OutPaymentView
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.dialogs.paymentchangedialog import (PaymentDueDateChangeDialog,
                                                     PaymentStatusChangeDialog)
from stoqlib.gui.dialogs.paymentcommentsdialog import PaymentCommentsDialog
from stoqlib.gui.dialogs.paymentflowhistorydialog import PaymentFlowHistoryDialog
from stoqlib.gui.editors.paymenteditor import OutPaymentEditor
from stoqlib.gui.editors.paymentseditor import PaymentsEditor
from stoqlib.gui.keybindings import get_accels
from stoqlib.gui.printing import print_report
from stoqlib.gui.search.paymentsearch import OutPaymentBillCheckSearch
from stoqlib.lib.message import warning
from stoqlib.reporting.payment import PayablePaymentReport
from stoqlib.reporting.payments_receipt import OutPaymentReceipt

from stoq.gui.application import SearchableAppWindow
from stoqlib.gui.slaves.installmentslave import PurchaseInstallmentConfirmationSlave

_ = gettext.gettext


class PayableApp(SearchableAppWindow):

    # TODO: Change all widget.set_sensitive to self.set_sensitive([widget])

    app_name = _('Accounts payable')
    gladefile = 'payable'
    search_table = OutPaymentView
    search_label = _('matching:')
    report_table = PayablePaymentReport
    embedded = True

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
            ('Edit', gtk.STOCK_EDIT, _('Edit...'),
             group.get('payment_edit'),
             _('Edit the selected payment details')),
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
        self.popup = self.uimanager.get_widget('/PayableSelection')

    def create_ui(self):
        self.app.launcher.add_new_items([self.AddPayment])
        self.app.launcher.NewToolItem.set_tooltip(self.AddPayment.get_tooltip())
        self.app.launcher.add_search_items([self.BillCheckSearch])
        self.app.launcher.SearchToolItem.set_tooltip(
            self.BillCheckSearch.get_tooltip())
        self.app.launcher.Print.set_tooltip(
            _("Print a report of these payments"))
        self.Pay.set_sensitive(False)
        self.PrintReceipt.set_sensitive(False)
        self._setup_widgets()
        self.search.search.results.set_cell_data_func(
            self._on_results__cell_data_func)

    def activate(self, params):
        # FIXME: double negation is weird here
        if not params.get('no-refresh'):
            self.search.refresh()
        self._update_widgets()

    def deactivate(self):
        self.uimanager.remove_ui(self.payable_ui)

    def new_activate(self):
        self._add_payment()

    def search_activate(self):
        run_dialog(OutPaymentBillCheckSearch, self, self.conn)

    #
    # SearchableAppWindow
    #

    def create_filters(self):
        self.set_text_field_columns(['description', 'supplier_name'])
        self.status_filter = ComboSearchFilter(_('Show payments'),
                                               self._get_status_values())
        self.add_filter(self.status_filter,
                        SearchFilterPosition.TOP, ['status'])

    def get_columns(self):
        return [SearchColumn('id', title=_('#'), long_title=_('Payment ID'),
                             width=60, data_type=int,
                             format='%04d'),
                Column('color', title=_('Description'), width=20,
                       data_type=gtk.gdk.Pixbuf, format_func=render_pixbuf),
                Column('comments_number', title=_(u'Comments'),
                        visible=False),
                SearchColumn('description', title=_('Description'),
                              data_type=str, ellipsize=pango.ELLIPSIZE_END,
                              expand=True, column='color'),
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
        self.status_filter.select(None)
        dfilter = DateSearchFilter(_("Paid or due date"))
        dfilter.set_removable()
        dfilter.mode.select_item_by_position(5)
        self.add_filter(dfilter, columns=["paid_date", "due_date"])
        dfilter.start_date.set_date(date)
        self.search.refresh()

    #
    # Private
    #

    def _show_details(self, payable_view):
        with api.trans() as trans:
            payment = trans.get(payable_view.payment)
            run_dialog(OutPaymentEditor, self, trans, payment)

        if trans.committed:
            self.search.refresh()

    def _show_comments(self, payable_view):
        with api.trans() as trans:
            run_dialog(PaymentCommentsDialog, self, trans,
                       payable_view.payment)

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

        status = payable_views[0].purchase_status
        if (status == PurchaseOrder.ORDER_CANCELLED or
            status == PurchaseOrder.ORDER_PENDING):
            return False

        return True

    def _change_due_date(self, payable_view):
        """ Receives a payable_view and change the payment due date
        related to the view.
        @param payable_view: a OutPaymentView instance
        """
        assert payable_view.can_change_due_date()

        with api.trans() as trans:
            payment = trans.get(payable_view.payment)
            order = trans.get(payable_view.sale)

            if order is None:
                order = trans.get(payable_view.purchase)

            run_dialog(PaymentDueDateChangeDialog, self, trans,
                       payment, order)

        if trans.committed:
            payable_view.sync()
            self.results.update(payable_view)

    def _change_status(self, payable_view, status):
        """Show a dialog do enter a reason for status change
        @param payable_view: a OutPaymentView instance
        """
        with api.trans() as trans:
            payment = trans.get(payable_view.payment)
            order = trans.get(payable_view.sale)

            if order is None:
                order = trans.get(payable_view.purchase)

            run_dialog(PaymentStatusChangeDialog, self, trans,
                       payment, status, order)

        if trans.committed:
            payable_view.sync()
            self.results.update(payable_view)
            self.results.unselect_all()

    def _can_cancel_payment(self, payable_views):
        """whether or not we can cancel the payment.
        """
        if len(payable_views) != 1:
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

        return payable_views[0].can_change_due_date()

    def _edit(self, payable_views):
        with api.trans() as trans:
            order = trans.get(payable_views[0].purchase)
            run_dialog(PaymentsEditor, self, trans, order)

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
            api.sysparam(self.conn).BLOCK_INCOMPLETE_PURCHASE_PAYMENTS and
            not purchase_order.status == PurchaseOrder.ORDER_CLOSED):

            return warning(_("Can't confirm the payment if the purchase "
                             "is not completely received yet."))

        with api.trans() as trans:
            payments = [trans.get(view.payment) for view in payable_views]

            run_dialog(PurchaseInstallmentConfirmationSlave, self, trans,
                       payments=payments)

        if trans.committed:
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

    def _setup_widgets(self):
        self.results.set_selection_mode(gtk.SELECTION_MULTIPLE)
        self.search.set_summary_label(column='value',
                                      label='<b>Total:</b>',
                                      format='<b>%s</b>',
                                      parent=self.get_statusbar_message_area())

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
        self.SetNotPaid.set_sensitive(self._are_paid(selected, respect_purchase=False))

    def _get_status_values(self):
        items = [(value, key) for key, value in Payment.statuses.items()]
        items.insert(0, (_('Any'), None))
        return items

    def _add_payment(self):
        with api.trans() as trans:
            self.run_dialog(OutPaymentEditor, trans)

        self.search.refresh()
        if trans.committed:
            self.select_result(OutPaymentView.get(trans.retval.id))

    def _run_bill_check_search(self):
        run_dialog(OutPaymentBillCheckSearch, self, self.conn)

    #
    # Kiwi callbacks
    #

    def _on_results__cell_data_func(self, column, renderer, pv, text):
        if not isinstance(renderer, gtk.CellRendererText):
            return text

        if pv.paid_date and self.status_filter.get_state().value is None:
            renderer.set_property('strikethrough', True)
            renderer.set_property('strikethrough-set', True)
        else:
            renderer.set_property('strikethrough-set', False)
        if not pv.paid_date and pv.due_date < datetime.datetime.now():
            renderer.set_property('weight', pango.WEIGHT_BOLD)
            renderer.set_property('weight-set', True)
        else:
            renderer.set_property('weight-set', False)
        return text

    def on_results__row_activated(self, klist, payable_view):
        if self._can_show_details([payable_view]):
            self._show_details(payable_view)

    def on_results__right_click(self, results, result, event):
        self.popup.popup(None, None, None, event.button, event.time)

    def on_Comments__activate(self, action):
        payable_view = self.results.get_selected_rows()[0]
        self._show_comments(payable_view)

    def on_Details__activate(self, action):
        payable_view = self.results.get_selected_rows()[0]
        self._show_details(payable_view)

    def on_Pay__activate(self, action):
        self._pay(self.results.get_selected_rows())

    def on_Edit__activate(self, action):
        self._edit(self.results.get_selected_rows())

    def on_results__selection_changed(self, results, selected):
        self._update_widgets()

    def on_PrintReceipt__activate(self, action):
        register_payment_operations()
        payment_views = self.results.get_selected_rows()
        payments = [v.payment for v in payment_views]
        date = datetime.date.today()
        print_report(OutPaymentReceipt, payment=payments[0],
                     order=payment_views[0].purchase, date=date)

    def on_PaymentFlowHistory__activate(self, action):
        self.run_dialog(PaymentFlowHistoryDialog, self.conn)

    def on_AddPayment__activate(self, action):
        self._add_payment()

    def on_CancelPayment__activate(self, action):
        payable_view = self.results.get_selected_rows()[0]
        self._change_status(payable_view, Payment.STATUS_CANCELLED)

    def on_SetNotPaid__activate(self, action):
        payable_view = self.results.get_selected_rows()[0]
        self._change_status(payable_view, Payment.STATUS_PENDING)

    def on_ChangeDueDate__activate(self, action):
        payable_view = self.results.get_selected_rows()[0]
        self._change_due_date(payable_view)

    def on_BillCheckSearch__activate(self, action):
        self._run_bill_check_search()
