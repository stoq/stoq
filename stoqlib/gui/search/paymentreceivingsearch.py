# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import datetime
import gtk

from kiwi.currency import currency

from stoqdrivers.exceptions import DriverError
from storm.expr import And

from stoqlib.api import api
from stoqlib.domain.events import (TillAddCashEvent, TillAddTillEntryEvent)
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.payment.views import InPaymentView
from stoqlib.domain.till import Till
from stoqlib.exceptions import DeviceError, TillError
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.gtkadds import change_button_appearance
from stoqlib.gui.slaves.paymentconfirmslave import SalePaymentConfirmSlave
from stoqlib.gui.search.searchcolumns import SearchColumn, IdentifierColumn
from stoqlib.gui.search.searchdialog import SearchDialog, SearchDialogButtonSlave
from stoqlib.gui.search.searchfilters import DateSearchFilter
from stoqlib.lib.message import warning
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class PaymentReceivingSearch(SearchDialog):
    title = _('Payments to Receive Search')
    size = (775, 450)
    search_spec = InPaymentView

    def __init__(self, store):
        SearchDialog.__init__(self, store)
        self.results.connect('selection-changed', self._on_selection_changed)
        self._setup_button_slave()

    def _setup_button_slave(self):
        self._button_slave = SearchDialogButtonSlave()
        change_button_appearance(self._button_slave.button,
                                 gtk.STOCK_APPLY, _("Receive"))
        self.attach_slave('print_holder', self._button_slave)
        self._button_slave.connect('click', self.on_receive_button_clicked)
        self._button_slave.button.set_sensitive(False)

    def _receive(self):
        with api.new_store() as store:
            till = Till.get_current(store)
            assert till

            in_payment = self.results.get_selected()
            payment = store.fetch(in_payment.payment)
            assert self._can_receive(payment)

            retval = run_dialog(SalePaymentConfirmSlave, self, store,
                                payments=[payment], show_till_info=False)
            if not retval:
                return

            try:
                TillAddCashEvent.emit(till=till, value=payment.value)
            except (TillError, DeviceError, DriverError) as e:
                warning(str(e))
                return

            till_entry = till.add_credit_entry(payment.value,
                                               _(u'Received payment: %s') % payment.description)

            TillAddTillEntryEvent.emit(till_entry, store)

        if store.committed:
            self.search.refresh()

    def _can_receive(self, payment):
        if not payment:
            return False

        return payment.status == Payment.STATUS_PENDING

    #
    # SearchDialog Hooks
    #

    def create_filters(self):
        self.set_text_field_columns(['description', 'identifier_str'])
        self.search.set_query(self.executer_query)

        # Date
        date_filter = DateSearchFilter(_('Date:'))
        date_filter.select(0)
        columns = [Payment.due_date,
                   Payment.open_date,
                   Payment.paid_date]
        self.add_filter(date_filter, columns=columns)
        self.date_filter = date_filter

    def get_columns(self):
        return [IdentifierColumn('identifier', title=_('Payment #'), sorted=True),
                SearchColumn('description', title=_('Description'),
                             data_type=str, expand=True),
                SearchColumn('drawee', title=_('Drawee'),
                             data_type=str, width=200),
                SearchColumn('due_date', title=_('Due Date'),
                             data_type=datetime.date, width=100),
                SearchColumn('value', title=_('Value'),
                             data_type=currency, width=145), ]

    def executer_query(self, store):
        store_credit_method = PaymentMethod.get_by_name(
            self.store, u'store_credit')
        query = And(Payment.status == Payment.STATUS_PENDING,
                    Payment.method == store_credit_method)
        return store.find(self.search_spec, query)

    #
    # Callbacks
    #

    def _on_selection_changed(self, results, selected):
        can_click = bool(selected)
        self._button_slave.button.set_sensitive(can_click)

    def on_receive_button_clicked(self, button):
        self._receive()
