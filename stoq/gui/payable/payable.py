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
from kiwi.ui.widgets.list import Column, SummaryLabel
from stoqlib.domain.payment.payment import Payment
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.dialogs.purchasedetails import PurchaseDetailsDialog
from stoqlib.lib.defaults import ALL_ITEMS_INDEX

from stoq.gui.application import SearchableAppWindow
from stoq.gui.payable.view import PayableView

_ = gettext.gettext


class PayableApp(SearchableAppWindow):

    app_name = _('Payable')
    app_icon_name = 'stoq-payable-app'
    gladefile = 'payable'
    searchbar_table = PayableView
    searchbar_use_dates = True
    searchbar_result_strings = (_('payment'), _('payments'))
    searchbar_labels = (_('matching:'),)
    filter_slave_label = _('Show payments with status')
    klist_selection_mode = gtk.SELECTION_MULTIPLE
    klist_name = 'payables'

    def __init__(self, app):
        SearchableAppWindow.__init__(self, app)
        self._setup_widgets()
        self._update_widgets()

    def _setup_widgets(self):
        value_format = '<b>%s</b>'
        self.summary_label = SummaryLabel(klist=self.payables,
                                          column='value',
                                          label='<b>Total:</b>',
                                          value_format=value_format)
        self.summary_label.show()
        self.list_vbox.pack_start(self.summary_label, False)

    def _update_widgets(self):
        has_sales = len(self.payables) > 0
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
                Column('supplier_name', title=_('Supplier'), data_type=str,
                       width=170),
                Column('due_date', title=_('Due Date'),
                       data_type=datetime.date, width=90),
                Column('status_str', title=_('Status'), width=80,
                       data_type=str),
                Column('value', title=_('Value'), data_type=currency,
                       width=100)]

    def get_extra_query(self):
        status = self.filter_slave.get_selected_status()
        if status != ALL_ITEMS_INDEX:
            return Payment.q.status == status

    #
    # Private
    #

    def _show_details(self, payable_view):
        run_dialog(PurchaseDetailsDialog, self, self.conn,
                   payable_view.purchase)


    #
    # Kiwi callbacks
    #

    def on_payables__row_activated(self, klist, payable_view):
        self._show_details(payable_view)

    def on_details_button__clicked(self, button):
        if len(self.payables):
            if not self.payables.get_selected_rows():
                self.payables.select(self.payables[0])
            self._show_details(self.payables.get_selected_rows()[0])
