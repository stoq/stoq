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
## Author(s):       Henrique Romano     <henrique@async.com.br>
##                  Bruno Rafael Garcia <brg@async.com.br>
##
"""
stoq/gui/till/operations.py:

    Implementation of classes related to till operations.
"""


import gettext
import datetime

import gtk
import gobject
from kiwi.utils import gsignal
from sqlobject.sqlbuilder import AND, IN
from kiwi.ui.delegates import SlaveDelegate
from kiwi.ui.widgets.list import Column, ColoredColumn
from stoqlib.gui.search import SearchBar
from stoqlib.gui.dialogs import BasicWrappingDialog
from stoqlib.database import rollback_and_begin
from stoqlib.exceptions import DatabaseInconsistency

from stoq.domain.interfaces import IPaymentGroup
from stoq.domain.sale import Sale
from stoq.domain.till import get_current_till_operation
from stoq.domain.payment.base import Payment
from stoq.domain.sellable import get_formatted_price


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
               'debit_total_label',
               'klist',
               'credit_total_label',)

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
        self._update_totals()
        self.main_dialog.set_title(self.get_title())
    
    def on_cancel(self):
        # XXX We need a proper base class in stoqlib to avoid redefining this
        # method here. bug 2217
        self.main_dialog.close()

    def get_title(self):
        today_format = _('%d of %B')
        today_str = datetime.date.today().strftime(today_format)
        return _('Stoq - %s of %s') % (self.app_name, today_str)

    def colorize(self, column_data):
        return column_data < 0


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
        q1 = IN(Payment.q.groupID, group_ids)
        q2 = Payment.q.status == Payment.STATUS_TO_PAY
        return AND(q1, q2)
       
       
    def filter_results(self, payments): 
        # XXX We need some refactoring in SearchBar to avoid this hook
        return payments

    def _update_totals(self):    
        credit_total = 0.0
        debit_total = 0.0
        self.balance_total = 0.0
        for item in self.klist: 
            if item.value > 0.00:
                credit_total += item.value
            else:
                debit_total += item.value
            self.balance_total += item.value

        for widget, value in ((self.debit_total_label, debit_total),
                              (self.credit_total_label, credit_total)):
            widget.set_text(get_formatted_price(value))
        total_balance_str = get_formatted_price(self.balance_total)
        self.total_balance_label.set_text('Balance: %s' % total_balance_str)

    def update_klist(self, items):
        self.klist.clear()
        rollback_and_begin(self.conn)
        for item in items: 
            item = Payment.get(item.id, connection=self.conn)
            self.klist.append(item)
        self._update_totals()

    def _get_columns(self, *args):
        return [Column('payment_id', _('Number'), data_type=int, width=100,
                       justify=gtk.JUSTIFY_RIGHT, sorted=True,
                       format='%03d'),
                Column('due_date', _('Due Date'), 
                       data_type=datetime.date, width=120, 
                       justify=gtk.JUSTIFY_RIGHT),
                Column('description', _('Description'), data_type=str, 
                       expand=True),
                ColoredColumn('value', _('Value'), data_type=float, 
                              color='red', data_func=self.colorize,
                              width=120, justify=gtk.JUSTIFY_RIGHT)]

    def _setup_slaves(self):
        self.search_bar = SearchBar(self, Payment, self._get_columns(), 
                                    searching_by_date=True)
        self.search_bar.set_searchbar_labels(_('Payments Matching'))
        self.search_bar.set_result_strings(_('payment'), _('payments'))
        self.attach_slave('searchbar_holder', self.search_bar)

    def _update_widgets(self):
        selected_item = len(self.klist.get_selected_rows()) > 0
        #This button will be implemented on bug #2197
        #self.reverse_selection_button.set_sensitive(selected_item)

    def _setup_widgets(self):      
        self.klist.set_columns(self._get_columns())
        self.klist.set_selection_mode(gtk.SELECTION_MULTIPLE)
        #These buttons will be implemented on bug #2197
        self.cash_out_button.set_sensitive(False)
        self.cash_in_button.set_sensitive(False)
        self.cash_advance_button.set_sensitive(False)
        self.reverse_selection_button.set_sensitive(False)



    #
    # Kiwi handlers
    #



    def on_klist__selection_changed(self, *args):
        self._update_widgets()

    def on_cash_out_button__clicked(self, button):
        #This button will be implemented on bug #2197
        raise NotImplementedError

    def on_cash_in_button__clicked(self, button):
        #This button will be implemented on bug #2197
        raise NotImplementedError

    def on_cash_advance_button__clicked(self, button):
        #This button will be implemented on bug #2197
        raise NotImplementedError

    def on_reverse_selection_button__clicked(self, button):
        #This button will be implemented on bug #2197
        raise NotImplementedError

    def on_close_till_button__clicked(self, button):
        self.emit('close-till')
        if get_current_till_operation(self.conn) is None:
            self.main_dialog.close()

gobject.type_register(TillOperationDialog)
