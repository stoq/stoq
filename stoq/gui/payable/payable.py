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
## Author(s):       Evandro Vale Miquelito      <evandro@async.com.br>
##                  Fabio Morbec                <fabio@async.com.br>
##
"""
stoq/gui/payable/payable.py:

    Implementation of payable application.
"""

import datetime
import gettext

import gtk
from kiwi.datatypes import currency
from kiwi.enums import SearchFilterPosition
from kiwi.python import all
from kiwi.ui.search import DateSearchFilter, ComboSearchFilter
from kiwi.ui.widgets.list import Column
from stoqlib.database.runtime import new_transaction, finish_transaction
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.payment.views import OutPaymentView
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.dialogs.purchasedetails import PurchaseDetailsDialog
from stoqlib.gui.dialogs.saledetails import SaleDetailsDialog
from stoqlib.gui.printing import print_report
from stoqlib.reporting.payment import PayablePaymentReport
from stoqlib.reporting.payment_receipt import PaymentReceipt

from stoq.gui.application import SearchableAppWindow
from stoqlib.gui.slaves.installmentslave import PurchaseInstallmentConfirmationSlave

_ = gettext.gettext


class PayableApp(SearchableAppWindow):

    app_name = _('Accounts Payable')
    app_icon_name = 'stoq-payable-app'
    gladefile = 'payable'
    search_table = OutPaymentView
    search_label = _('matching:')
    klist_selection_mode = gtk.SELECTION_MULTIPLE

    def __init__(self, app):
        SearchableAppWindow.__init__(self, app)
        self._setup_widgets()
        self._update_widgets()
        self.pay_order_button.set_sensitive(False)
        self.Receipt.set_sensitive(False)
        self.results.connect('has-rows', self._has_rows)

    #
    # SearchableAppWindow
    #

    def create_filters(self):
        self.set_text_field_columns(['description', 'supplier_name'])
        date_filter = DateSearchFilter(_('Paid or due date:'))
        self.add_filter(
            date_filter, columns=['paid_date', 'due_date'])
        self.add_filter(
            ComboSearchFilter(_('Show payments with status'),
                              self._get_status_values()),
            SearchFilterPosition.TOP, ['status'])

    def _has_rows(self, result_list, has_rows):
        self.print_button.set_sensitive(has_rows)

    def get_columns(self):
        return [Column('id', title=_('Number'), width=80,
                       data_type=str, sorted=True, format='%03d'),
                Column('description', title=_('Description'), width=190,
                       data_type=str, expand=True),
                Column('supplier_name', title=_('Supplier'), data_type=str,
                       width=170),
                Column('due_date', title=_('Due Date'),
                       data_type=datetime.date, width=90),
                Column('paid_date', title=_('Paid Date'),
                        data_type=datetime.date, width=90),
                Column('status_str', title=_('Status'), width=70,
                       data_type=str),
                Column('value', title=_('Value'), data_type=currency,
                       width=80)]

    #
    # Private
    #

    def _show_details(self, payable_view):
        if payable_view.purchase:
            run_dialog(PurchaseDetailsDialog, self,
                       self.conn, payable_view.purchase)
        elif payable_view.sale:
            run_dialog(SaleDetailsDialog, self,
                       self.conn, payable_view.sale)
        else:
            raise AssertionError

    def _can_show_details(self, payable_views):
        """
        Determines if we can show details for a list of payables
        """
        return (self._same_purchase(payable_views) or
                self._same_sale(payable_views))

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

        purchase = payable_views[0].purchase
        if purchase is None:
            return False
        return all(view.purchase == purchase and
                   view.status == Payment.STATUS_PENDING
                   for view in payable_views)

    def _are_paid(self, payable_views):
        """
        Determines if a list of payables_views are paid.
        To do so they must meet the following conditions:
          - Be in the same purchase order
          - The payment status needs to be set to PAID
        """
        if not payable_views:
            return False

        purchase = payable_views[0].purchase
        if purchase is None:
            return False
        return all(view.purchase == purchase and
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
        self.search.set_summary_label(column='value',
                                      label='<b>Total:</b>',
                                      format='<b>%s</b>')

    def _update_widgets(self):
        selected = self.results.get_selected_rows()
        self.details_button.set_sensitive(self._can_show_details(selected))
        self.pay_order_button.set_sensitive(self._same_purchase(selected))
        self.pay_order_button.set_sensitive(self._can_pay(selected))
        self.print_button.set_sensitive(bool(self.results))
        self.Receipt.set_sensitive(self._are_paid(selected))

    def _get_status_values(self):
        items = [(value, key) for key, value in Payment.statuses.items()]
        items.insert(0, (_('Any'), None))
        return items

    #
    # Kiwi callbacks
    #

    def on_results__row_activated(self, klist, payable_view):
        if self._can_show_details([payable_view]):
            self._show_details(payable_view)

    def on_details_button__clicked(self, button):
        payable_view = self.results.get_selected_rows()[0]
        self._show_details(payable_view)

    def on_pay_order_button__clicked(self, button):
        self._pay(self.results.get_selected_rows())

    def on_results__selection_changed(self, results, selected):
        self._update_widgets()

    def on_print_button__clicked(self, button):
        print_report(PayablePaymentReport, list(self.results),do_footer=False)

    def on_Receipt__activate(self, action):
        payment_views = self.results.get_selected_rows()
        payments = [v.payment for v in payment_views]
        print_report(PaymentReceipt, payments=payments,
                     purchase=payment_views[0].purchase)
