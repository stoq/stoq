# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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
from kiwi.ui.search import ComboSearchFilter
from kiwi.ui.objectlist import Column, SearchColumn
from stoqlib.database.runtime import new_transaction, finish_transaction
from stoqlib.domain.payment.operation import register_payment_operations
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.payment.views import OutPaymentView
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.gtkadds import render_pixbuf
from stoqlib.gui.dialogs.paymentchangedialog import (PaymentDueDateChangeDialog,
                                                     PaymentStatusChangeDialog)
from stoqlib.gui.dialogs.paymentcommentsdialog import PaymentCommentsDialog
from stoqlib.gui.dialogs.paymentflowhistorydialog import PaymentFlowHistoryDialog
from stoqlib.gui.editors.paymenteditor import OutPaymentEditor
from stoqlib.gui.editors.paymentseditor import PaymentsEditor
from stoqlib.gui.printing import print_report
from stoqlib.gui.search.paymentsearch import OutPaymentBillCheckSearch
from stoqlib.reporting.payment import PayablePaymentReport
from stoqlib.reporting.payment_receipt import PaymentReceipt

from stoq.gui.application import SearchableAppWindow
from stoqlib.gui.slaves.installmentslave import PurchaseInstallmentConfirmationSlave

_ = gettext.gettext
LAUNCHER_EMBEDDED = True

class PayableApp(SearchableAppWindow):

    # TODO: Change all widget.set_sensitive to self.set_sensitive([widget])

    app_name = _('Accounts payable')
    app_icon_name = 'stoq-payable-app'
    gladefile = 'payable'
    search_table = OutPaymentView
    search_label = _('matching:')

    def __init__(self, app):
        SearchableAppWindow.__init__(self, app)
        self._setup_widgets()
        self._update_widgets()
        self.Pay.set_sensitive(False)
        self.PrintReceipt.set_sensitive(False)
        self.results.connect('has-rows', self._has_rows)

    #
    # Application
    #

    def activate(self):
        self.search.refresh()

    def deactivate(self):
        self.uimanager.remove_ui(self.payable_ui)
        self.uimanager.remove_ui(self.payable_help_ui)

    def create_actions(self):
        ui_string = """<ui>
          <menubar action="menubar">
            <menu action="StoqMenu">
              <menu action="NewMenu">
                <placeholder name="NewMenuItemPH">
                  <menuitem action="AddPayment"/>
                </placeholder>
              </menu>
              <placeholder name="StoqMenuPH">
                <menuitem action="ExportCSV"/>
              </placeholder>
            </menu>
            <menu action="EditMenu">
              <placeholder name="EditMenuPH">
                <menuitem action="CancelPayment"/>
                <menuitem action="SetNotPaid"/>
                <menuitem action="ChangeDueDate"/>
                <menuitem action="Comments"/>
                <menuitem action="PrintReceipt"/>
                <menuitem action="PaymentFlowHistory"/>
              </placeholder>
            </menu>
            <placeholder name="AppMenubarPH">
              <menu action="SearchMenu">
                <menuitem action="BillCheckSearch"/>
              </menu>
            </placeholder>
          </menubar>
      <toolbar action="toolbar">
        <placeholder name="NewToolItemPH">
          <toolitem action="NewToolItem">
            <menu action="NewMenu">
              <menuitem action="AddPayment"/>
            </menu>
          </toolitem>
        </placeholder>
        <toolitem action="PrintReport"/>
        <separator/>
        <toolitem action="Pay"/>
        <toolitem action="Edit"/>
        <toolitem action="Details"/>
        </toolbar>
    </ui>"""

        actions = [
            ('menubar', None, ''),

            # Payable
            ('AddPayment', gtk.STOCK_ADD, _('Accounts payable'), '<Control>p'),
            ('CancelPayment', gtk.STOCK_REMOVE, _('Cancel payment...')),
            ('SetNotPaid', gtk.STOCK_UNDO, _('Set as not paid...')),
            ('ChangeDueDate', gtk.STOCK_REFRESH, _('Change due date...')),
            ('Comments', None, _('Comments...')),

            ('PrintReceipt', None, _('Print _receipt'), '<Control>r'),
            ('PaymentFlowHistory', None, _('Payment _flow history...'),
             '<Control>f'),

            ('ExportCSV', gtk.STOCK_SAVE_AS, _('Export CSV...')),
            ("Quit", gtk.STOCK_QUIT),

            # Search
            ('SearchMenu', None, _('_Search')),
            ('BillCheckSearch', None, _('Bill and check...')),

            # Toolbar
            ('PrintReport', gtk.STOCK_PRINT, _('Print'), '',
              _('Print a report for the payment')),
            ('Pay', gtk.STOCK_APPLY, _('Pay'), '',
              _('Pay the order assoicated with the payment')),
            ('Edit', gtk.STOCK_EDIT, _('Edit'), '',
              _('Edit the payment')),
            ('Details', gtk.STOCK_FIND, _('Details'), '',
              _('Show details for the payment')),
        ]
        self.payable_ui = self.add_ui_actions(ui_string, actions)
        self.payable_help_ui = self.add_help_ui(_("Accounts payable help"),
                                                  'pagar-inicio')
        self.Pay.props.is_important = True

    def new_activate(self):
        self._add_payment()

    #
    # SearchableAppWindow
    #

    def create_filters(self):
        self.set_text_field_columns(['description', 'supplier_name'])
        self.add_filter(
            ComboSearchFilter(_('Show payments'),
                              self._get_status_values()),
            SearchFilterPosition.TOP, ['status'])

    def _has_rows(self, result_list, has_rows):
        self.PrintReport.set_sensitive(has_rows)

    def get_columns(self):
        return [SearchColumn('id', title=_('#'), long_title='Payment ID',
                             width=60, data_type=int, sorted=True,
                             format='%04d'),
                Column('color', title=_('Description'), width=20,
                       data_type=gtk.gdk.Pixbuf, format_func=render_pixbuf),
                Column('payment.comments_number', title=_(u'Comments'),
                        visible=False),
                SearchColumn('description', title=_('Description'),
                              data_type=str, ellipsize=pango.ELLIPSIZE_END,
                              expand=True, column='color'),
                SearchColumn('supplier_name', title=_('Supplier'),
                             data_type=str, width=140,
                             ellipsize=pango.ELLIPSIZE_END),
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
                SearchColumn('paid_value', title=_('Paid'), data_type=currency,
                              long_title='Paid value', width=90)]

    #
    # Private
    #

    def _show_details(self, payable_view):
        trans = new_transaction()
        payment = trans.get(payable_view.payment)
        retval = run_dialog(OutPaymentEditor, self, trans, payment)
        if finish_transaction(trans, retval):
            self.search.refresh()
        trans.close()

    def _show_comments(self, payable_view):
        trans = new_transaction()
        retval = run_dialog(PaymentCommentsDialog, self, trans,
                            payable_view.payment)
        finish_transaction(trans, retval)

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

        status = payable_views[0].purchase.status
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
        trans = new_transaction()
        payment = trans.get(payable_view.payment)
        order = trans.get(payable_view.sale)

        if order is None:
            order = trans.get(payable_view.purchase)

        retval = run_dialog(PaymentDueDateChangeDialog, self, trans,
                            payment, order)

        if finish_transaction(trans, retval):
            payable_view.sync()
            self.results.update(payable_view)

        trans.close()

    def _change_status(self, payable_view, status):
        """Show a dialog do enter a reason for status change
        @param payable_view: a OutPaymentView instance
        """
        trans = new_transaction()
        payment = trans.get(payable_view.payment)
        order = trans.get(payable_view.sale)

        if order is None:
            order = trans.get(payable_view.purchase)

        retval = run_dialog(PaymentStatusChangeDialog, self, trans,
                            payment, status, order)

        if finish_transaction(trans, retval):
            payable_view.sync()
            self.results.update(payable_view)
            self.results.unselect_all()

        trans.close()

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
        trans = new_transaction()
        order = trans.get(payable_views[0].purchase)
        model = run_dialog(PaymentsEditor, self, trans, order)
        finish_transaction(trans, model)
        trans.close()

    def _pay(self, payable_views):
        """
        Pay a list of items from a payable_views, note that
        the list of payable_views must reference the same order
        @param payables_views: a list of payable_views
        """
        assert self._can_pay(payable_views)

        trans = new_transaction()

        payments = [trans.get(view.payment) for view in payable_views]

        retval = run_dialog(PurchaseInstallmentConfirmationSlave, self, trans,
                            payments=payments)

        if finish_transaction(trans, retval):
            for view in payable_views:
                view.sync()
                self.results.update(view)

        trans.close()
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

        purchase = payable_views[0].purchase
        if purchase is None:
            return False
        return all(view.purchase == purchase and
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

        purchase = payable_views[0].purchase
        if purchase is None and respect_purchase:
            return False

        return all((view.purchase == purchase or not respect_purchase) and
                   view.payment.is_paid() for view in payable_views)

    def _same_purchase(self, payable_views):
        """Determines if a list of payable_views are in the same purchase"""
        if not payable_views:
            return False

        purchase = payable_views[0].purchase
        if purchase is None:
            return False
        return all(view.purchase == purchase for view in payable_views)

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
                                      format='<b>%s</b>')

    def _update_widgets(self):
        selected = self.results.get_selected_rows()
        self.Details.set_sensitive(self._can_show_details(selected))
        self.Comments.set_sensitive(self._can_show_comments(selected))
        self.ChangeDueDate.set_sensitive(self._can_change_due_date(selected))
        self.CancelPayment.set_sensitive(self._can_cancel_payment(selected))
        self.Edit.set_sensitive(self._can_edit(selected))
        self.Pay.set_sensitive(self._can_pay(selected))
        self.Edit.set_sensitive(bool(len(self.results)))
        self.PrintReceipt.set_sensitive(self._are_paid(selected,
                                                       respect_purchase=True))
        self.SetNotPaid.set_sensitive(self._are_paid(selected, respect_purchase=False))

    def _get_status_values(self):
        items = [(value, key) for key, value in Payment.statuses.items()]
        items.insert(0, (_('Any'), None))
        return items

    def _add_payment(self):
        trans = new_transaction()
        retval = self.run_dialog(OutPaymentEditor, trans)
        if finish_transaction(trans, retval):
            self.results.refresh()
        trans.close()
        self.search.refresh()

    def _run_bill_check_search(self):
        run_dialog(OutPaymentBillCheckSearch, self, self.conn)

    #
    # Kiwi callbacks
    #

    def on_results__row_activated(self, klist, payable_view):
        if self._can_show_details([payable_view]):
            self._show_details(payable_view)

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

    def on_PrintReport__activate(self, action):
        payments = self.results.get_selected_rows() or list(self.results)
        self.print_report(PayablePaymentReport, self.results,
                          payments, do_footer=False)

    def on_PrintReceipt__activate(self, action):
        register_payment_operations()
        payment_views = self.results.get_selected_rows()
        payments = [v.payment for v in payment_views]
        print_report(PaymentReceipt, payments=payments,
                     purchase=payment_views[0].purchase)

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
