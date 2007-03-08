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
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.defaults import payment_value_colorize
from stoqlib.lib.validators import get_formatted_price
from stoqlib.domain.interfaces import IPaymentGroup
from stoqlib.domain.sale import Sale
from stoqlib.domain.till import TillEntryAndPaymentView, Till
from stoqlib.domain.payment.payment import Payment
from stoqlib.gui.base.searchbar import SearchBar
from stoqlib.gui.base.dialogs import BasicWrappingDialog, run_dialog
from stoqlib.gui.editors.tilleditor import (CashAdvanceEditor, CashInEditor,
                                            CashOutEditor)

_ = stoqlib_gettext


class TillHistoryDialog(GladeSlaveDelegate):
    app_name = _('Till History')
    gladefile = 'TillHistoryDialog'
    widgets = ('cash_out_button',
               'cash_advance_button',
               'cash_in_button',
               'close_till_button',
               'total_balance_label',
               'payments')

    title = _('Current Till History')
    size = (750, -1)

    gsignal('close-till')

    def __init__(self, conn):
        GladeSlaveDelegate.__init__(self, gladefile=self.gladefile)
        self.main_dialog = BasicWrappingDialog(self, self.title,
                                               size=self.size,
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
        self.search_bar = SearchBar(self.conn, TillEntryAndPaymentView,
                                    self._get_columns(),
                                    searching_by_date=True)
        self.search_bar.register_extra_query_callback(self.get_extra_query)
        self.search_bar.set_searchbar_labels(_('Items Matching'))
        self.search_bar.set_result_strings(_('item'), _('items'))
        self.search_bar.connect('search-activate', self._update_list)
        self.search_bar.connect('before-search-activate', self._sync)
        self.attach_slave('searchbar_holder', self.search_bar)

    def _update_widgets(self):
        self.selected_item = self.payments.get_selected_rows()
        self.canceled_items = 0
        self.selected = 0

    def _setup_widgets(self):
        self.payments.set_columns(self._get_columns())
        self.payments.set_visible_rows(10)
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
        return [Column('identifier', _('Number'), data_type=int, width=80,
                        format='%03d', sorted=True),
                Column('date', _('Due Date'),
                       data_type=datetime.date, width=110),
                Column('description', _('Description'), data_type=str,
                       expand=True,
                       width=300),
                ColoredColumn('value', _('Value'), data_type=currency,
                              color='red', data_func=payment_value_colorize,
                              width=140)]

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

    def on_close_till_button__clicked(self, button):
        self.emit('close-till')
        if Till.get_current(self.conn) is None:
            self.main_dialog.close()
