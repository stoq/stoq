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
## Author(s):        Henrique Romano            <henrique@async.com.br>
##                   Evandro Vale Miquelito     <evandro@async.com.br>
##
"""
stoq/gui/editors/till.py:

    Editors implementation for open/close operation on till operation.
"""

import gtk
import gettext
import datetime

from sqlobject.sqlbuilder import AND, IN
from stoqlib.gui.editors import BaseEditor, BaseEditorSlave
from kiwi.datatypes import ValidationError

from stoq.domain.sellable import get_formatted_price
from stoq.domain.interfaces import (IPaymentGroup, IInPayment, IEmployee, 
                                    IBranch, IOutPayment)
from stoq.domain.till import Till, get_current_till_operation
from stoq.domain.payment.base import Payment, CashAdvanceInfo
from stoq.domain.person import Person
from stoq.lib.validators import get_price_format_str

_ = gettext.gettext


class TillOpeningEditor(BaseEditor):
    model_name = _('Till Opening')
    model_type = Till
    gladefile = 'TillOpening'
    proxy_widgets = ('open_date', 
                     'initial_cash_amount')

    def __init__(self, conn, model):
        BaseEditor.__init__(self, conn, model)

    def _setup_widgets(self):
        self.initial_cash_amount.set_data_format(get_price_format_str())

    def _initialize_till_operation(self):
        if self.model.initial_cash_amount > 0:
            current_till = get_current_till_operation(self.conn)
            value = self.model.initial_cash_amount
            reason = _('Initial cash amount')
            current_till.create_credit(value, reason)
            self.conn.commit()

    #
    # BaseEditor hooks
    # 

    def get_title_model_attribute(self, model):
        return self.model_name

    def setup_proxies(self):
        self.model.open_till()
        self._setup_widgets()
        self._initialize_till_operation()
        self.add_proxy(self.model,
                       TillOpeningEditor.proxy_widgets)


class TillClosingEditor(BaseEditor):
    model_name = _('Till Closing')
    model_type = Till
    gladefile = 'TillClosing'
    proxy_widgets = ('final_cash_amount',
                     'balance_to_send')
    size = (350, 290)

    def __init__(self, conn, model):
        BaseEditor.__init__(self, conn, model)
        self.total_balance = model.get_balance()
        self._update_widgets()

    def _setup_widgets(self):
        for widget in (self.balance_to_send, self.final_cash_amount):
            widget.set_data_format(get_price_format_str())
    
    def _payment_query(self): 
        current_till = get_current_till_operation(self.conn)
        group = IPaymentGroup(current_till, connection=self.conn)
        statuses = [Payment.STATUS_TO_PAY, Payment.STATUS_CANCELLED]
        query = AND(IN(Payment.q.status, statuses), 
                    Payment.q.groupID == group.id)
        payments = Payment.select(query, connection=self.conn)
        self.debits = 0
        self.credits = 0
        for payment in payments:
            if payment.value < 0:
                self.debits += payment.value
            else:
                self.credits += payment.value
        if current_till.initial_cash_amount < 0:
            raise ValueError(_('Initial cash amount cannot be lesser than ' 
                               'zero'))
        self.credits -= current_till.initial_cash_amount
         
    def _update_widgets(self):
        closing_date = self.model.closing_date.strftime('%x') 
        self.closing_date_lbl.set_text(closing_date)
        initial_cash = self.model.initial_cash_amount
        initial_cash_str = get_formatted_price(initial_cash)
        self.initial_cash_amount_lbl.set_text(initial_cash_str)
        debits = get_formatted_price(self.debits)
        self.debits_lbl.set_text(debits)
        self.debits_lbl.set_color('red')
        credits = get_formatted_price(self.credits)
        self.credits_lbl.set_text(credits)
        total_balance = get_formatted_price(self.total_balance)
        self.total_balance_lbl.set_text(total_balance)
        if self.total_balance < 0:
            self.total_balance_lbl.set_color('red')
  
    def _update_final_cash_amount(self):
        balance_to_send = self.model.balance_sent or 0.0
        self.model.final_cash_amount = self.total_balance - balance_to_send
        self.proxy.update('final_cash_amount')

    def _update_balance_to_send(self):
        final_cash_amount = self.model.final_cash_amount or 0.0
        self.model.balance_sent = self.total_balance - final_cash_amount 
        self.proxy.update('balance_sent')

    #
    # BaseEditor hooks
    # 

    def get_title(self, *args):
        return _('Closing current till')

    def setup_proxies(self):
        self._payment_query()
        self.model.close_till()
        self.final_cash = self.model.final_cash_amount
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model,
                                    TillClosingEditor.proxy_widgets)

    #
    # Kiwi handlers
    #

    def after_final_cash_amount__validate(self, widget, value):
        if value < 0.0:
            return ValidationError(_("Value cannot be lesser that zero"))
        if value <= self.final_cash:
            return
        return ValidationError(_("You can not specifiy a final"
                                 " cash amount greater than the "
                                 "calculated value."))

    def after_balance_to_send__changed(self, *args):
        self.handler_block(self.final_cash_amount, 'changed')
        self._update_final_cash_amount()
        self.handler_unblock(self.final_cash_amount, 'changed')

    def after_final_cash_amount__changed(self, *args):
        self.handler_block(self.balance_to_send, 'changed')
        self._update_balance_to_send()
        self.handler_unblock(self.balance_to_send, 'changed')


class BaseCashSlave(BaseEditorSlave):
    model_type = Payment
    gladefile = 'BaseCashSlave'
    proxy_widgets = ('cash_amount',)
    label_widgets = ('date',
                     'date_lbl',
                     'cash_amount_lbl')

    def __init__(self, conn, payment_description, 
                 payment_iface=IInPayment):
        self.payment_description = payment_description
        self.payment_iface = payment_iface
        BaseEditorSlave.__init__(self, conn)

    def _setup_widgets(self):
        self.date.set_text(datetime.datetime.now().strftime('%x'))
        self.cash_amount.set_text('') 

    # 
    # BaseEditorSlave Hooks
    # 

    def create_model(self, conn):
        reason = self.payment_description
        current_till = get_current_till_operation(conn)
        payment_value = 0.0
        args = [payment_value, reason]
        if self.payment_iface is IInPayment:
            return current_till.create_credit(*args)
        elif self.payment_iface is IOutPayment:
            return current_till.create_debit(*args)
        else:
            raise ValueError('Invalid interface, got %s' 
                             % self.payment_iface)

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model,
                                    BaseCashSlave.proxy_widgets)
        self._setup_widgets()

    #
    # Kiwi handlers
    #
    
    def on_cash_amount__validate(self, entry, value):
        if value < 0.0:
            return ValidationError(_("Value Must be greater than zero"))


class CashAdvanceEditor(BaseEditor): 
    model_name = _('Cash Advance')
    model_type = CashAdvanceInfo
    gladefile = 'CashAdvanceEditor'
    label_widgets = ('employee_lbl',)
    entry_widgets = ('employee_combo',)

    payment_iface = IOutPayment

    def _setup_size_group(self, size_group, widgets, obj):
        for widget_name in widgets:
            widget = getattr(obj, widget_name)
            size_group.add_widget(widget)
                            
    def _setup_widgets(self):
        self.entry_size_group = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        self._setup_size_group(self.entry_size_group,
                               CashAdvanceEditor.entry_widgets,
                               self)
        self._setup_size_group(self.entry_size_group,
                               self.cash_slave.proxy_widgets, 
                               self.cash_slave)
        self.label_size_group = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        self._setup_size_group(self.label_size_group,
                               CashAdvanceEditor.label_widgets,
                               self)
        self._setup_size_group(self.label_size_group, 
                               self.cash_slave.label_widgets,
                               self.cash_slave)
        employees = [(p.get_adapted().name, p) 
                     for p in Person.iselect(IEmployee, connection=self.conn)]
        self.employee_combo.prefill(employees)
        self.employee_combo.set_active(0)
        
    # 
    # BaseEditorSlave Hooks
    # 
    
    def create_model(self, conn):
        # XXX We should not need to set None values here. 
        # Waiting for bug 2163.
        model = CashAdvanceInfo(employee=None, payment=None, 
                                connection=conn)
        return model
        
    def setup_slaves(self):
        self.cash_slave = BaseCashSlave(conn=self.conn,
                                        payment_description=None,
                                        payment_iface=self.payment_iface)
        self.attach_slave("base_cash_holder", self.cash_slave)
        self._setup_widgets()

    def on_confirm(self):
        self.model.employee = self.employee_combo.get_selected_data()
        self.model.payment = self.cash_slave.model
        employee_name = self.employee_combo.get_selected_label()
        payment_description = (_('Cash advance paid to employee: %s') 
                               % employee_name)
        self.cash_slave.model.description = payment_description
        value = self.cash_slave.model.value
        value *= -1
        self.cash_slave.model.value = value
        return self.model


class CashInEditor(BaseEditor):
    model_name = _('Cash In')
    gladefile = 'BaseTemplate'

    # 
    # BaseEditorSlave Hooks
    # 
 
    def setup_slaves(self):
        current_till = get_current_till_operation(self.conn)
        branch = Person.iget(IBranch, current_till.branch.id, 
                             connection=self.conn)
        branch_name = branch.get_adapted().name 
        payment_description = (_('Cash in for branch: %s') %
                               branch_name)
        self.cash_slave = BaseCashSlave(payment_description=payment_description,
                                        conn=self.conn)
        self.attach_slave("main_holder", self.cash_slave)

    def on_confirm(self):
        value = self.cash_slave.model.value
        self.cash_slave.model.value = value
        return self.cash_slave.on_confirm()


class CashOutEditor(BaseEditor):
    model_name = _('Cash Out')
    gladefile = 'CashOutEditor'
    label_widgets = ('reason_lbl',)
    entry_widgets = ('reason',)
    title = _('Reverse Payment')
    
    payment_iface = IOutPayment
    
    def _setup_size_group(self, size_group, widgets, obj):
        for widget_name in widgets:
            widget = getattr(obj, widget_name)
            size_group.add_widget(widget)
        
    def _setup_widgets(self):
        self.entry_size_group = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        self._setup_size_group(self.entry_size_group,
                               CashOutEditor.entry_widgets,
                               self)
        self._setup_size_group(self.entry_size_group,
                               self.cash_slave.proxy_widgets, 
                               self.cash_slave)
        self.label_size_group = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        self._setup_size_group(self.label_size_group,
                               CashOutEditor.label_widgets,
                               self)
        self._setup_size_group(self.label_size_group, 
                               self.cash_slave.label_widgets,
                               self.cash_slave)
    
    # 
    # BaseEditorSlave Hooks
    # 
    
    def setup_slaves(self):
        self.cash_slave = BaseCashSlave(self.conn, payment_description=None,
                                        payment_iface=self.payment_iface)
        self.attach_slave("base_cash_holder", self.cash_slave)
        self._setup_widgets()

    def on_confirm(self):
        reason = self.reason.get_text()
        if reason:
            # %s is the description used when removing money
            payment_description = _('Cash out: %s') % reason
        else:
            payment_description = _('Cash out')
        self.cash_slave.model.description = payment_description
        model = self.cash_slave.model
        model.value = -model.value
        return self.cash_slave.on_confirm()
