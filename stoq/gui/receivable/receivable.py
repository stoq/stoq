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
## Author(s):       Evandro Vale Miquelito      <evandro@async.com.br>
##                  Johan Dahlin                <jdahlin@async.com.br>
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
from kiwi.ui.search import (DateSearchFilter, ComboSearchFilter,
                            DateSearchOption)
from kiwi.ui.widgets.list import Column
from stoqlib.database.runtime import new_transaction, finish_transaction
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.payment.views import InPaymentView
from stoqlib.domain.sale import SaleView
from stoqlib.reporting.payment import ReceivablePaymentReport
from stoqlib.reporting.receival_receipt import ReceivalReceipt
from stoqlib.gui.printing import print_report
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.dialogs.saledetails import SaleDetailsDialog
from stoqlib.gui.slaves.installmentslave import SaleInstallmentConfirmationSlave

from stoq.gui.application import SearchableAppWindow

_ = gettext.gettext

class NextMonthOption(DateSearchOption):
    name = _('Next month')
    def get_interval(self):
        today = datetime.date.today()
        year = today.year
        month = today.month + 1
        if month > 12:
            month = 1
            year += 1
        # Try 31 first then add one until date() does not complain.
        day = today.day
        while True:
            try:
                end_date = datetime.date(year, month, day)
                break
            except ValueError:
                day += 1
        return datetime.date.today(), end_date

class ReceivableApp(SearchableAppWindow):

    app_name = _('Accounts Receivable')
    app_icon_name = 'stoq-bills'
    gladefile = 'receivable'

    search_table = InPaymentView
    search_label = _('matching:')
    klist_selection_mode = gtk.SELECTION_MULTIPLE

    def __init__(self, app):
        SearchableAppWindow.__init__(self, app)
        self._setup_widgets()
        self._update_widgets()
        self.results.connect('has-rows', self._has_rows)

    def _setup_widgets(self):
        self.search.set_summary_label(
            'value', '<b>Total:</b>', '<b>%s</b>')

    def _update_widgets(self):
        selected = self.results.get_selected_rows()
        self.receive_button.set_sensitive(self._can_receive(selected))
        self.details_button.set_sensitive(self._same_sale(selected))
        self.Receipt.set_sensitive(self._can_emit_receipt(selected))

    def _has_rows(self, result_list, has_rows):
        self.print_button.set_sensitive(has_rows)

    def _get_status_values(self):
        values = [(v, k) for k, v in Payment.statuses.items()]
        values.insert(0, (_("Any"), None))
        return values

    #
    # SearchableAppWindow hooks
    #

    def create_filters(self):
        self.set_text_field_columns(['description', 'drawee'])
        date_filter = DateSearchFilter(_('Paid or due date:'))
        date_filter.add_option(NextMonthOption)
        self.add_filter(
            date_filter, columns=['paid_date', 'due_date'])
        self.add_filter(
            ComboSearchFilter(_('Show payments with status'),
                              self._get_status_values()),
            SearchFilterPosition.TOP, ['status'])

    def get_columns(self):
        return [Column('id', title=_('#'), width=46,
                       data_type=int, sorted=True, format='%04d'),
                Column('description', title=_('Description'), width=170,
                       data_type=str, expand=True,
                       ellipsize=pango.ELLIPSIZE_END),
                Column('drawee', title=_('Drawee'), data_type=str,
                       width=160, ellipsize=pango.ELLIPSIZE_END),
                Column('due_date', title=_('Due Date'),
                       data_type=datetime.date, width=100),
                Column('paid_date', title=_('Paid Date'),
                        data_type=datetime.date, width=100),
                Column('status_str', title=_('Status'), width=80,
                       data_type=str),
                Column('value', title=_('Value'), data_type=currency,
                       width=80)]

    #
    # Private
    #

    def _show_details(self, receivable_view):
        sale_view = SaleView.get(receivable_view.sale_id)
        run_dialog(SaleDetailsDialog, self, self.conn, sale_view)


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

    def _can_emit_receipt(self, receivable_views):
        """
        Determines if we can emit the receipt for a list of
        receivable views.
        To do so they must meet the following conditions:
          - Be in the same sale
          - The payment status needs to be set to PAID
        """
        if not receivable_views:
            return False

        sale = receivable_views[0].sale
        if sale is None:
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

        sale = receivable_views[0].sale
        if sale is None:
            return False
        return all(view.sale == sale and
                   view.status == Payment.STATUS_PENDING
                   for view in receivable_views)

    def _same_sale(self, receivable_views):
        """
        Determines if a list of receivable_views are in the same sale
        To do so they must meet the following conditions:
          - Be in the same sale
        """

        if not receivable_views:
            return False

        sale = receivable_views[0].sale
        return all(view.sale == sale for view in receivable_views[1:])

    #
    # Kiwi callbacks
    #

    def on_results__row_activated(self, klist, receivable_view):
        self._show_details(receivable_view)

    def on_results__selection_changed(self, receivables, selected):
        self._update_widgets()

    def on_details_button__clicked(self, button):
        selected = self.results.get_selected_rows()[0]
        self._show_details(selected)

    def on_receive_button__clicked(self, button):
        self._receive(self.results.get_selected_rows())

    def on_print_button__clicked(self, button):
        print_report(ReceivablePaymentReport, list(self.results))

    def on_Receipt__activate(self, action):
        receivable_views = self.results.get_selected_rows()
        payments = [v.payment for v in receivable_views]
        print_report(ReceivalReceipt, payments=payments,
                     sale=receivable_views[0].sale)
