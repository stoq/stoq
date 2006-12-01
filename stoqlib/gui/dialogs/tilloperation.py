# -*- coding: utf-8 -*-
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
## Author(s):       Henrique Romano         <henrique@async.com.br>
##                  Bruno Rafael Garcia     <brg@async.com.br>
##                  Evandro Vale Miquelito  <evandro@async.com.br>
##
""" Implementation of classes related to till operations.  """


import datetime

import gtk
from kiwi.datatypes import currency
from kiwi.utils import gsignal
from kiwi.ui.delegates import GladeSlaveDelegate
from kiwi.ui.widgets.list import Column, ColoredColumn
from sqlobject.sqlbuilder import IN

from stoqlib.database.database import finish_transaction, rollback_and_begin
from stoqlib.exceptions import TillError
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.defaults import payment_value_colorize
from stoqlib.lib.message import warning, yesno
from stoqlib.lib.validators import get_formatted_price
from stoqlib.domain.interfaces import IPaymentGroup
from stoqlib.domain.sale import Sale
from stoqlib.domain.till import Till
from stoqlib.domain.payment.base import Payment
from stoqlib.gui.base.search import SearchBar
from stoqlib.gui.base.dialogs import BasicWrappingDialog, run_dialog
from stoqlib.gui.editors.tilleditor import (CashAdvanceEditor, CashInEditor,
                                            CashOutEditor)
from stoqlib.gui.editors.tilleditor import TillOpeningEditor, TillClosingEditor

_ = stoqlib_gettext


def verify_and_open_till(till, conn):
    if Till.get_current(conn) is not None:
        raise TillError("You already have a till operation opened. "
                        "Close the current Till and open another one.")

    try:
        model = till.run_dialog(TillOpeningEditor, conn)
    except TillError, e:
        warning(e)
        model = None

    if finish_transaction(till.conn, model):
        return True

    return False

def verify_and_close_till(till, conn, *args):
    till = Till.get_last_opened(conn)
    assert till

    model = till.run_dialog(TillClosingEditor, conn)

    # TillClosingEditor closes the till
    if not finish_transaction(till.conn, model):
        return False

    opened_sales = Sale.select(Sale.q.status == Sale.STATUS_OPENED,
                               connection=till.conn)
    if not opened_sales:
        return False

    # A new till object to "store" the sales that weren't
    # confirmed. Note that this new till operation isn't
    # opened yet, but it will be considered when opening a
    # new operation
    branch_station = opened_sales[0].till.station
    new_till = Till(connection=till.conn,
                    station=branch_station)
    for sale in opened_sales:
        sale.till = new_till

class TillOperationDialog(GladeSlaveDelegate):
    app_name = _('Till Operations')
    gladefile = 'TillOperationDialog'
    widgets = ('cash_out_button',
               'cash_advance_button',
               'cash_in_button',
               'reverse_selection_button',
               'close_till_button',
               'total_balance_label',
               'payments')

    title = _('Current Till Operation')
    size = (800, 500)

    gsignal('close-till')

    def __init__(self, conn):
        GladeSlaveDelegate.__init__(self, gladefile=self.gladefile)
        self.main_dialog = BasicWrappingDialog(self, self.title, size=self.size,
                                               hide_footer=True)
        self.conn = conn
        self._setup_widgets()
        self._setup_slaves()
        self._update_widgets()
        self.main_dialog.set_title(self._get_title())
        self.search_bar.search_items()
        self._check_initial_cash_amount()

    def on_cancel(self):
        # XXX We need a proper base class in stoqlib to avoid redefining this
        # method here. bug 2217
        self.main_dialog.close()

    def _get_title(self):
        today_format = _('%d of %B')
        today_str = datetime.date.today().strftime(today_format)
        return _('Stoq - %s of %s') % (self.app_name, today_str)

    def _sync(self, *args):
        rollback_and_begin(self.conn)

    def _setup_slaves(self):
        self.search_bar = SearchBar(self.conn, Payment,
                                    self._get_columns(),
                                    searching_by_date=True)
        self.search_bar.register_extra_query_callback(self.get_extra_query)
        self.search_bar.set_searchbar_labels(_('Payments Matching'))
        self.search_bar.set_result_strings(_('payment'), _('payments'))
        self.search_bar.connect('search-activate', self._update_list)
        self.search_bar.connect('before-search-activate', self._sync)
        self.attach_slave('searchbar_holder', self.search_bar)

    def _update_widgets(self):
        self.selected_item = self.payments.get_selected_rows()
        self.canceled_items = 0
        self.selected = 0
        for item in self.selected_item:
            if item.status == Payment.STATUS_CANCELLED:
                self.canceled_items += 1
            if item.status == Payment.STATUS_PENDING:
                self.selected += 1
        self.reverse_selection_button.set_sensitive(self.selected > 0)

    def _setup_widgets(self):
        self.payments.set_columns(self._get_columns())
        self.payments.set_selection_mode(gtk.SELECTION_MULTIPLE)
        self._update_total()

    def _run_editor(self, editor_class):
        model = run_dialog(editor_class, self, self.conn)
        if finish_transaction(self.conn, model):
            self.search_bar.search_items()
            self.payments.unselect_all()
            self._select_last_item()

    def _select_last_item(self):
        if len(self.payments):
            self.payments.select(self.payments[-1])

    def _update_list(self, slave, objs):
        self.payments.add_list(objs)
        self._update_total()

    def _update_total(self, *args):
        total_balance = currency(0)
        for item in self.payments:
            total_balance += item.value
        total_balance_str = get_formatted_price(total_balance)
        self.total_balance_label.set_text(total_balance_str)
        if total_balance < 0:
            self.total_balance_label.set_color('red')
        else:
            self.total_balance_label.set_color('black')

    def _get_columns(self, *args):
        return [Column('identifier', _('Number'), data_type=int, width=100,
                        format='%03d', sorted=True),
                Column('due_date', _('Due Date'),
                       data_type=datetime.date, width=120),
                Column('description', _('Description'), data_type=str,
                       expand=True),
                ColoredColumn('value', _('Value'), data_type=currency,
                              color='red', data_func=payment_value_colorize,
                              width=120)]

    def _reverse_selection(self):
        if self.selected > 1:
            transaction_string = _(u'transactions')
        else:
            transaction_string = _(u'transaction')
            self.selected = ''
        text = _(u'Are you sure you want to reverse the \n%s selected '
                 '%s?') % (self.selected, transaction_string)
        if self.canceled_items > 1:
            item_string = _('items')
        else:
            item_string = _('item')
        if self.canceled_items > 0:
            text += _(u'\nWarning: It has %d cancelled %s in your '
                      'selection.') % (self.canceled_items, item_string)
        is_initial_cash = self._check_initial_cash_amount()
        if is_initial_cash:
            text = _(u"Your selection contains the initial cash amount "
                     "payment."
                     "\nIt's not possible to cancel this payment.")
            warning(text)
            return
        if not yesno(text, gtk.RESPONSE_YES, _(u"Cancel"), _(u"Reverse Items")):
            for item in self.selected_item:
                item.cancel_till_entry()
            self.conn.commit()
        self.search_bar.search_items()
        self._select_last_item()

    def _check_initial_cash_amount(self):
        # This method is wrong.
        # A good way to get the initial cash amount payment would be to
        # use the payment_id.
        # Waiting for bug 2524
        for item in self.selected_item:
            if item.description == _('Initial cash amount'):
                return True
        return False

    #
    # Searchbar callbacks
    #

    def get_extra_query(self):
        current_till = Till.get_current(self.conn)
        assert current_till
        group = IPaymentGroup(current_till)
        group_ids = [group.id]
        for sale in Sale.get_available_sales(self.conn, current_till):
            group = IPaymentGroup(sale)
            group_ids.append(group.id)
        return IN(Payment.q.groupID, group_ids)

    #
    # Kiwi handlers
    #

    def on_payments__selection_changed(self, *args):
        self._update_widgets()

    def on_cash_out_button__clicked(self, button):
        self._run_editor(CashOutEditor)

    def on_cash_in_button__clicked(self, button):
        self._run_editor(CashInEditor)

    def on_cash_advance_button__clicked(self, button):
        self._run_editor(CashAdvanceEditor)

    def on_reverse_selection_button__clicked(self, button):
        self._reverse_selection()

    def on_close_till_button__clicked(self, button):
        self.emit('close-till')
        if Till.get_current(self.conn) is None:
            self.main_dialog.close()
