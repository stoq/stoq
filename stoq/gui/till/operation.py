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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s):       Henrique Romano         <henrique@async.com.br>
##                  Bruno Rafael Garcia     <brg@async.com.br>
##                  Evandro Vale Miquelito  <evandro@async.com.br>
##
"""
stoq/gui/till/operations.py:

    Implementation of classes related to till operations.
"""


import gettext
import datetime

import gtk
from kiwi.datatypes import currency
from kiwi.utils import gsignal
from kiwi.ui.delegates import SlaveDelegate
from kiwi.ui.widgets.list import Column, ColoredColumn
from sqlobject.sqlbuilder import AND, IN
from stoqlib.gui.search import SearchBar
from stoqlib.gui.dialogs import (BasicWrappingDialog, run_dialog,
                                 confirm_dialog, notify_dialog)
from stoqlib.database import finish_transaction, rollback_and_begin
from stoqlib.exceptions import DatabaseInconsistency

from stoq.domain.interfaces import IPaymentGroup
from stoq.domain.sale import Sale
from stoq.domain.till import get_current_till_operation
from stoq.domain.payment.base import Payment
from stoq.domain.sellable import get_formatted_price
from stoq.gui.editors.till import (CashAdvanceEditor, CashInEditor, 
                                   CashOutEditor)                                   

_ = gettext.gettext


class TillOperationDialog(SlaveDelegate):
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
        SlaveDelegate.__init__(self, gladefile=self.gladefile,
                               widgets=self.widgets)
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

    def _colorize(self, column_data):
        return column_data < 0

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
            if item.status == Payment.STATUS_TO_PAY:
                self.selected += 1
        self.reverse_selection_button.set_sensitive(self.selected > 0)

    def _setup_widgets(self):      
        self.payments.set_columns(self._get_columns())
        self.payments.set_selection_mode(gtk.SELECTION_MULTIPLE)
        self._update_total()

    def _run_editor(self, editor_class):
        model = run_dialog(editor_class, self, self.conn)
        if finish_transaction(self.conn, model, keep_transaction=True):
            self.search_bar.search_items()
            self.payments.unselect_all()
            self._select_last_item()

    def _select_last_item(self): 
        inserted_item_position = len(self.payments) - 1 
        self.payments.select(self.payments[inserted_item_position])
        
    def _update_list(self, slave, objs):
        self.payments.add_list(objs)
        self._update_total()
        
    def _update_total(self, *args):
        total_balance = 0.0
        for item in self.payments: 
            total_balance += item.value
        total_balance_str = get_formatted_price(total_balance)
        self.total_balance_label.set_text(total_balance_str)
        if total_balance < 0:
            self.total_balance_label.set_color('red')
        else:
            self.total_balance_label.set_color('black')

    def _get_payment_id(self, value):
        # Attribute payment_id will be mandatory soon. 
        # Waiting for bug 2214.
        if not value:
            return 0
        return '%03d' % value

    def _get_columns(self, *args):
        return [Column('payment_id', _('Number'), data_type=int, width=100,
                        format_func=self._get_payment_id, sorted=True),
                       # XXX Waiting for bug 2214
                       # format='%03d'),
                Column('due_date', _('Due Date'), 
                       data_type=datetime.date, width=120),
                Column('description', _('Description'), data_type=str, 
                       expand=True),
                ColoredColumn('value', _('Value'), data_type=currency, 
                              color='red', data_func=self._colorize,
                              width=120)]

    def _reverse_selection(self):
        title = _('Reverse Selection')
        size = (360, 150)
        if self.selected > 1:
            transaction_string = _('transactions')
        else:
            transaction_string = _('transaction')
            self.selected = ''
        text = _('Are you sure you want to reverse the \n%s selected '
                 '%s?') % (self.selected, transaction_string) 
        if self.canceled_items > 1:
            item_string = _('items')
        else:
            item_string = _('item')
        if self.canceled_items > 0:
            text += _('\nWarning: It has %d cancelled %s in your ' 
                      'selection.') % (self.canceled_items, item_string)
        is_initial_cash = self._check_initial_cash_amount()
        if is_initial_cash:
            text = _("Your selection contains the initial cash amount "
                     "payment."
                     "\nIt's not possible to cancel this payment.")
            size = (430, 150)
            notify_dialog(text, size=size)
            return
        if confirm_dialog(text, title=title, size=size):
            for item in self.selected_item:
                item.cancel_payment()
            self.conn.commit()
        self.search_bar.search_items()
        self._select_last_item()

    def _check_initial_cash_amount(self):
        # This method is wrong.
        # A good way to get the initial cash amount payment would be to 
        # use the payment_id.
        # Waiting for bug 2214.
        for item in self.selected_item:
            if item.description == _('Initial cash amount'):
                return True
        return False

    #
    # Searchbar callbacks
    # 

    def get_extra_query(self):
        current_till = get_current_till_operation(self.conn)
        group = IPaymentGroup(current_till, connection=self.conn)
        if not group:
            raise DatabaseInconsistency("Till instance must have a"
                                        "IPaymentGroup facet")
        group_ids = [group.id]
        for sale in Sale.selectBy(till=current_till, connection=self.conn):
            group = IPaymentGroup(sale, connection=self.conn)
            if not group:
                raise DatabaseInconsistency("Sale instance must have a" 
                                            "IPaymentGroup facet")
            group_ids.append(group.id)
        statuses = [Payment.STATUS_TO_PAY, Payment.STATUS_CANCELLED]
        q1 = IN(Payment.q.groupID, group_ids)
        q2 = IN(Payment.q.status, statuses)
        return AND(q1, q2)
       
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
        if get_current_till_operation(self.conn) is None:
            self.main_dialog.close()
