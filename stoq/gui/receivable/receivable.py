# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005 Async Open Source <http://www.async.com.br>
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
##
"""
stoq/gui/receivable/receivable.py:

    Implementation of receivable application.
"""

import datetime
import gettext

import gtk
from kiwi.datatypes import currency
from kiwi.ui.widgets.list import Column, SummaryLabel
from sqlobject.sqlbuilder import AND
from stoqlib.domain.payment.payment import Payment, PaymentAdaptToInPayment
from stoqlib.domain.sale import SaleView, SaleAdaptToPaymentGroup
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.dialogs.saledetails import SaleDetailsDialog
from stoqlib.lib.defaults import ALL_ITEMS_INDEX

from stoq.gui.application import SearchableAppWindow

_ = gettext.gettext

class ReceivableApp(SearchableAppWindow):

    app_name = _('Receivable')
    app_icon_name = 'stoq-bills'
    gladefile = 'receivable'
    searchbar_table = Payment
    searchbar_use_dates = True
    searchbar_result_strings = (_('payment'), _('payments'))
    searchbar_labels = (_('matching:'),)
    filter_slave_label = _('Show payments with status')
    klist_selection_mode = gtk.SELECTION_MULTIPLE
    klist_name = 'receivables'

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
        has_sales = len(self.receivables) > 0
        self.details_button.set_sensitive(has_sales)
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
        return [Column('identifier', title=_('Number'), width=100,
                       data_type=str, sorted=True, format='%03d'),
                Column('description', title=_('Description'), width=220,
                       data_type=str, expand=True),
                Column('thirdparty_name', title=_('Drawee'), data_type=str,
                       width=170),
                Column('due_date', title=_('Due Date'),
                       data_type=datetime.date, width=90),
                Column('status_str', title=_('Status'), width=80,
                       data_type=str),
                Column('value', title=_('Value'), data_type=currency,
                       width=100)]

    def get_extra_query(self):
        status = self.filter_slave.get_selected_status()
        query = AND(Payment.q.groupID == SaleAdaptToPaymentGroup.q.id,
                    Payment.q.id == PaymentAdaptToInPayment.q._originalID)
        if status != ALL_ITEMS_INDEX:
            query = AND(query, Payment.q.status == status)
        return query

    #
    # Private
    #


    # This list operates on payments, but SaleDetailsDialog expects a
    # SaleView object, so we have to fetch the sale via the payment group.
    # We have to assure that the selected Payment group refers to a
    # SaleAdaptToPaymentGroup, and not to a PurchaseOrderAdaptToPaymentGroup.
    def _show_details(self, payment):
        assert isinstance(payment.group, SaleAdaptToPaymentGroup)
        sale_view = SaleView.get(payment.group.sale.id)
        run_dialog(SaleDetailsDialog, self, self.conn, sale_view)


    #
    # Kiwi callbacks
    #

    def on_details_button__clicked(self, button):
        if len(self.receivables):
            if not self.receivables.get_selected_rows():
                self.receivables.select(self.receivables[0])
            self._show_details(self.receivables.get_selected_rows()[0])


