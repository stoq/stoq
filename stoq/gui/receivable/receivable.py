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

import gtk
from kiwi.datatypes import currency
from kiwi.python import all
from kiwi.ui.widgets.list import Column, SummaryLabel
from stoqlib.database.database import finish_transaction
from stoqlib.database.runtime import new_transaction
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.sale import SaleView
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.dialogs.saledetails import SaleDetailsDialog
from stoqlib.lib.defaults import ALL_ITEMS_INDEX

from stoq.gui.application import SearchableAppWindow
from stoq.gui.receivable.view import ReceivableView
from stoqlib.gui.slaves.installmentslave import SaleInstallmentConfirmationSlave

_ = gettext.gettext


class ReceivableApp(SearchableAppWindow):

    app_name = _('Receivable')
    app_icon_name = 'stoq-bills'
    gladefile = 'receivable'
    searchbar_table = ReceivableView
    searchbar_use_dates = True
    searchbar_result_strings = (_('payment'), _('payments'))
    searchbar_labels = (_('matching:'),)
    filter_slave_label = _('Show payments with status')
    klist_name = 'receivables'
    klist_selection_mode = gtk.SELECTION_MULTIPLE

    def __init__(self, app):
        SearchableAppWindow.__init__(self, app)
        self._setup_widgets()
        self._update_widgets()

    def _setup_widgets(self):
        value_format = '<b>%s</b>'
        self.summary_label = SummaryLabel(klist=self.receivables,
                                          column='value',
                                          label='<b>Total:</b>',
                                          value_format=value_format)
        self.summary_label.show()
        self.list_vbox.pack_start(self.summary_label, False)

    def _update_widgets(self):
        self._update_total_label()

    def _update_total_label(self):
        self.summary_label.update_total()

    def on_searchbar_activate(self, slave, objs):
        SearchableAppWindow.on_searchbar_activate(self, slave, objs)
        self._update_widgets()

    def get_filter_slave_items(self):
        items = [(value, key) for key, value in Payment.statuses.items()]
        items.insert(0, (_('Any'), ALL_ITEMS_INDEX))
        return items

    #
    # SearchBar hooks
    #

    def get_columns(self):
        return [Column('id', title=_('Number'), width=80,
                       data_type=str, sorted=True, format='%03d'),
                Column('description', title=_('Description'), width=190,
                       data_type=str, expand=True),
                Column('thirdparty_name', title=_('Drawee'), data_type=str,
                       width=170),
                Column('due_date', title=_('Due Date'),
                       data_type=datetime.date, width=90),
                Column('paid_date', title=_('Paid Date'),
                        data_type=datetime.date, width=90),
                Column('status_str', title=_('Status'), width=70,
                       data_type=str),
                Column('value', title=_('Value'), data_type=currency,
                       width=80)]

    def get_extra_query(self):
        status = self.filter_slave.get_selected_status()
        if status != ALL_ITEMS_INDEX:
            return Payment.q.status == status

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
                self.receivables.update(view)

        trans.close()

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

    def on_receivables__row_activated(self, klist, receivable_view):
        self._show_details(receivable_view)

    def on_details_button__clicked(self, button):
        selected = self.receivables.get_selected_rows()[0]
        self._show_details(selected)

    def on_receive_button__clicked(self, button):
        self._receive(self.receivables.get_selected_rows())

    def on_receivables__selection_changed(self, receivables, selected):
        self.receive_button.set_sensitive(self._can_receive(selected))
        self.details_button.set_sensitive(self._same_sale(selected))
