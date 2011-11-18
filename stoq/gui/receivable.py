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
"""
stoq/gui/receivable/receivable.py:

    Implementation of receivable application.
"""

import datetime
import gettext

import pango
import gtk
from kiwi.datatypes import currency
from kiwi.enums import SearchFilterPosition
from kiwi.python import all
from kiwi.ui.search import ComboSearchFilter
from kiwi.ui.objectlist import SearchColumn, Column
from stoqlib.database.runtime import new_transaction, finish_transaction
from stoqlib.domain.payment.operation import register_payment_operations
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.payment.views import InPaymentView
from stoqlib.domain.till import Till
from stoqlib.exceptions import TillError
from stoqlib.reporting.payment import ReceivablePaymentReport
from stoqlib.reporting.receival_receipt import ReceivalReceipt
from stoqlib.gui.printing import print_report
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.gtkadds import render_pixbuf
from stoqlib.gui.dialogs.paymentchangedialog import (PaymentDueDateChangeDialog,
                                                     PaymentStatusChangeDialog)
from stoqlib.gui.dialogs.paymentcommentsdialog import PaymentCommentsDialog
from stoqlib.gui.dialogs.paymentflowhistorydialog import PaymentFlowHistoryDialog
from stoqlib.gui.editors.paymenteditor import InPaymentEditor
from stoqlib.gui.search.paymentsearch import InPaymentBillCheckSearch
from stoqlib.gui.search.paymentsearch import CardPaymentSearch
from stoqlib.gui.slaves.installmentslave import SaleInstallmentConfirmationSlave
from stoqlib.gui.wizards.renegotiationwizard import PaymentRenegotiationWizard
from stoqlib.lib.boleto import BillReport, can_generate_bill
from stoqlib.lib.message import warning

from stoq.gui.application import SearchableAppWindow

_ = gettext.gettext

class ReceivableApp(SearchableAppWindow):

    # TODO: Change all widget.set_sensitive to self.set_sensitive([widget])

    app_name = _('Accounts receivable')
    app_icon_name = 'stoq-bills'
    gladefile = 'receivable'
    search_table = InPaymentView
    search_label = _('matching:')
    launcher_embedded = True

    def __init__(self, app):
        SearchableAppWindow.__init__(self, app)
        self.results.connect('has-rows', self._has_rows)

    #
    # Application
    #

    def create_actions(self):
        actions = [
            ('menubar', None, ''),

            # Payable
            ('AddReceiving', gtk.STOCK_ADD,
             _('Accounts receivable'), '<Control>p'),
            ('CancelPayment', gtk.STOCK_REMOVE, _('Cancel payment...')),
            ('SetNotPaid', gtk.STOCK_UNDO, _('Set as not paid...')),
            ('ChangeDueDate', gtk.STOCK_REFRESH, _('Change due date...')),
            ('PrintBill', gtk.STOCK_PRINT, _('Print bill')),
            ('Comments', None, _('Comments...')),

            ('Renegotiate', None, _('Renegotiate payments...')),
            ('PrintReceipt', None, _('Print _receipt'), '<Control>r'),
            ('PaymentFlowHistory', None,
             _('Payment _flow history...'), '<Control>f'),

            ('ExportCSV', gtk.STOCK_SAVE_AS, _('Export CSV...')),

            # Search
            ('SearchMenu', None, _('_Search')),
            ('BillCheckSearch', None, _('Bill and check...')),
            ('CardPaymentSearch', None, _('Card payment...')),

            ('PrintToolMenu', _('Print')),
            ('PrintList', gtk.STOCK_PRINT, _('Payment List'), '',
             _('Print a report for this payment list'),),

            ('Receive', gtk.STOCK_APPLY, _('Receive'), '',
             _('Receive the selected payments')),
            ('Details', gtk.STOCK_INFO, _('Details'), '',
             _('Show details for the payment'),)
        ]
        self.receivable_ui = self.add_ui_actions(None, actions,
                                                 filename='receivable.xml')
        self.set_help_section(_("Accounts receivable help"), 'receber-inicio')

        self.add_tool_menu_actions([
                            ("Print", _("Print"), None,
                            gtk.STOCK_PRINT)])

        self.Receive.props.is_important = True

    def create_ui(self):
        self.app.launcher.add_new_items([self.AddReceiving])
        self.results.set_selection_mode(gtk.SELECTION_MULTIPLE)
        parent = self.app.launcher.statusbar.get_message_area()
        self.search.set_summary_label(column='value',
            label='<b>%s</b>' % (_("Total")),
            format='<b>%s</b>',
            parent=parent)

    def activate(self):
        self._update_widgets()
        self.search.refresh()

    def deactivate(self):
        self.uimanager.remove_ui(self.receivable_ui)

    def new_activate(self):
        self._add_receiving()

    #
    # SearchableAppWindow hooks
    #

    def create_filters(self):
        self.set_text_field_columns(['description', 'drawee'])
        self.add_filter(
            ComboSearchFilter(_('Show payments'),
                              self._get_status_values()),
            SearchFilterPosition.TOP, ['status'])

    def get_columns(self):
        return [SearchColumn('id', title=_('#'), long_title="Payment ID",
                             width=60, data_type=int, sorted=True,
                             format='%04d'),
                Column('color', title=_('Description'), width=20,
                       data_type=gtk.gdk.Pixbuf, format_func=render_pixbuf),
                Column('payment.comments_number', title=_(u'Comments'),
                        visible=False),
                SearchColumn('description', title=_('Description'),
                              data_type=str, ellipsize=pango.ELLIPSIZE_END,
                             column='color', expand=True),
                SearchColumn('drawee', title=_('Drawee'), data_type=str,
                             ellipsize=pango.ELLIPSIZE_END, width=140),
                SearchColumn('due_date', title=_('Due date'),
                             data_type=datetime.date, width=100),
                SearchColumn('paid_date', title=_('Paid date'),
                             data_type=datetime.date, width=100),
                SearchColumn('status_str', title=_('Status'), width=100,
                             data_type=str, search_attribute='status',
                             valid_values=self._get_status_values(),
                             visible=False),
                SearchColumn('value', title=_('Value'), data_type=currency,
                             width=90),
                SearchColumn('paid_value', title=_('Paid'),
                             long_title='Paid value',
                             data_type=currency, width=90)]

    #
    # Private
    #

    def _update_widgets(self):
        selected = self.results.get_selected_rows()
        self.Receive.set_sensitive(self._can_receive(selected))
        self.Details.set_sensitive(self._can_show_details(selected))
        self.Comments.set_sensitive(self._can_show_comments(selected))
        self.Renegotiate.set_sensitive(self._can_renegotiate(selected))
        self.ChangeDueDate.set_sensitive(self._can_change_due_date(selected))
        self.CancelPayment.set_sensitive(self._can_cancel_payment(selected))
        self.PrintReceipt.set_sensitive(self._are_paid(selected,
                                                       respect_sale=True))
        self.SetNotPaid.set_sensitive(self._are_paid(selected,
                                                     respect_sale=False))
        self.PrintBill.set_sensitive(self._can_print_bill(selected))

    def _has_rows(self, result_list, has_rows):
        self.Print.set_sensitive(has_rows)

    def _get_status_values(self):
        values = [(v, k) for k, v in Payment.statuses.items()]
        values.insert(0, (_("Any"), None))
        return values

    def _show_details(self, receivable_view):
        trans = new_transaction()
        payment = trans.get(receivable_view.payment)
        retval = run_dialog(InPaymentEditor, self, trans, payment)
        if finish_transaction(trans, retval):
            self.search.refresh()
        trans.close()
        return retval


    def _show_comments(self, receivable_view):
        trans = new_transaction()
        retval = run_dialog(PaymentCommentsDialog, self, trans,
                            receivable_view.payment)
        finish_transaction(trans, retval)

    def _receive(self, receivable_views):
        """
        Receives a list of items from a receivable_views, note that
        the list of receivable_views must reference the same sale
        @param receivable_views: a list of receivable_views
        """
        assert self._can_receive(receivable_views)

        trans = new_transaction()

        payments = [trans.get(view.payment) for view in receivable_views]

        retval = run_dialog(SaleInstallmentConfirmationSlave, self, trans,
                            payments=payments)

        if finish_transaction(trans, retval):
            for view in receivable_views:
                view.sync()
                self.results.update(view)

        trans.close()
        self._update_widgets()

    def _add_receiving(self):
        trans = new_transaction()
        retval = self.run_dialog(InPaymentEditor, trans)
        if finish_transaction(trans, retval):
            self.search.refresh()

    def _change_due_date(self, receivable_view):
        """ Receives a receivable_view and change the payment due date
        related to the view.
        @param receivable_view: a InPaymentView instance
        """
        assert receivable_view.can_change_due_date()
        trans = new_transaction()
        payment = trans.get(receivable_view.payment)
        sale = trans.get(receivable_view.sale)
        retval = run_dialog(PaymentDueDateChangeDialog, self,
                            trans, payment, sale)

        if finish_transaction(trans, retval):
            receivable_view.sync()
            self.results.update(receivable_view)

        trans.close()

    def _change_status(self, receivable_view, status):
        """Show a dialog do enter a reason for status change
        @param receivable_view: a InPaymentView instance
        """
        trans = new_transaction()
        payment = trans.get(receivable_view.payment)
        order = trans.get(receivable_view.sale)
        retval = run_dialog(PaymentStatusChangeDialog, self, trans,
                            payment, status, order)

        if finish_transaction(trans, retval):
            receivable_view.sync()
            self.results.update(receivable_view)
            self.results.unselect_all()

        trans.close()

    def _are_paid(self, receivable_views, respect_sale=True):
        """
        Determines if a list of receivable_views are paid.
        To do so they must meet the following conditions:
          - Be in the same sale
            (This will be satistied only if respect_sale is True)
          - The payment status needs to be set to PAID
        """
        if not receivable_views:
            return False

        sale = receivable_views[0].sale
        if sale is None and respect_sale:
            return False
        return all(view.sale == sale and view.payment.is_paid()
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

        # Until we fix bug 3703, don't allow receiving store credit payments
        if any(view.method_name == 'store_credit'
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
        """whether or not we can renegotiate this payments"""
        if not len(receivable_views):
            return False

        # Parent is a Sale or a PaymentRenegotiation
        parent = receivable_views[0].get_parent()

        if not parent:
            return False

        client = parent.client

        if not client:
            return False

        return all(view.get_parent() and
                   view.get_parent().client is client and
                   view.get_parent().can_set_renegotiated()
                   for view in receivable_views)

    def _can_cancel_payment(self, receivable_views):
        """whether or not we can cancel the receiving.
        """
        if len(receivable_views) != 1:
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

        sale = receivable_views[0].sale
        if sale is None:
            if len(receivable_views) == 1:
                return True
            else:
                return False

        return all(view.sale == sale for view in receivable_views[1:])

    def _can_show_comments(self, receivable_views):
        return len(receivable_views) == 1

    def _can_print_bill(self, receivable_views):
        return (len(receivable_views) == 1 and
                receivable_views[0].method_name == 'bill' and
                receivable_views[0].status == Payment.STATUS_PENDING)

    def _run_card_payment_search(self):
        run_dialog(CardPaymentSearch, self, self.conn)

    def _run_bill_check_search(self):
        run_dialog(InPaymentBillCheckSearch, self, self.conn)

    def _print_payment_list(self):
        payments = self.results.get_selected_rows() or list(self.results)
        self.print_report(ReceivablePaymentReport, self.results, payments)

    #
    # Kiwi callbacks
    #

    def on_results__row_activated(self, klist, receivable_view):
        self._show_details(receivable_view)

    def on_results__selection_changed(self, receivables, selected):
        self._update_widgets()

    def on_Details__activate(self, button):
        selected = self.results.get_selected_rows()[0]
        self._show_details(selected)

    def on_Receive__activate(self, button):
        self._receive(self.results.get_selected_rows())

    def on_Print__activate(self, button):
        self._print_payment_list()

    def on_PrintList__activate(self, action):
        self._print_payment_list()

    def on_Comments__activate(self, action):
        receivable_view = self.results.get_selected_rows()[0]
        self._show_comments(receivable_view)

    def on_PrintReceipt__activate(self, action):
        register_payment_operations()
        receivable_views = self.results.get_selected_rows()
        payments = [v.payment for v in receivable_views]
        print_report(ReceivalReceipt, payments=payments,
                     sale=receivable_views[0].sale)

    def on_PaymentFlowHistory__activate(self, action):
        self.run_dialog(PaymentFlowHistoryDialog, self.conn)

    def on_AddReceiving__activate(self, action):
        self._add_receiving()

    def on_CancelPayment__activate(self, action):
        receivable_view = self.results.get_selected_rows()[0]
        self._change_status(receivable_view, Payment.STATUS_CANCELLED)

    def on_SetNotPaid__activate(self, action):
        receivable_view = self.results.get_selected_rows()[0]
        self._change_status(receivable_view, Payment.STATUS_PENDING)

    def on_ChangeDueDate__activate(self, action):
        receivable_view = self.results.get_selected_rows()[0]
        self._change_due_date(receivable_view)

    def on_BillCheckSearch__activate(self, action):
        self._run_bill_check_search()

    def on_CardPaymentSearch__activate(self, action):
        self._run_card_payment_search()

    def on_Renegotiate__activate(self, action):
        try:
            Till.get_current(self.conn)
        except TillError, e:
            warning(str(e))
            return
        receivable_views = self.results.get_selected_rows()
        trans = new_transaction()
        groups = list(set([trans.get(v.group) for v in receivable_views]))
        retval = run_dialog(PaymentRenegotiationWizard, self, trans,
                            groups)
        if finish_transaction(trans, retval):
            self.search.refresh()

    def on_PrintBill__activate(self, action):
        if not can_generate_bill():
            return

        item = self.results.get_selected_rows()[0]
        payment = item.payment
        print_report(BillReport, [payment])
