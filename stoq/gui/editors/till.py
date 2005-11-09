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

from stoqlib.gui.editors import BaseEditor, BaseEditorSlave
from kiwi.datatypes import ValidationError

from stoq.domain.sellable import get_formatted_price
from stoq.domain.interfaces import (IPaymentGroup, IInPayment, IEmployee, 
                                    IBranch)
from stoq.domain.till import Till, get_current_till_operation
from stoq.domain.payment.base import Payment, CashAdvanceInfo
from stoq.domain.person import Person
from stoq.lib.parameters import sysparam
from stoq.lib.validators import get_price_format_str

_ = gettext.gettext

class TillOpeningEditor(BaseEditor):
    model_name = _('Till Opening')
    model_type = Till
    gladefile = 'TillOpening'
    widgets = ('open_date', 
               'initial_cash_amount')

    def __init__(self, conn, model):
        BaseEditor.__init__(self, conn, model)

    def _setup_widgets(self):
        self.initial_cash_amount.set_data_format(get_price_format_str())

    #
    # BaseEditor hooks
    # 

    def get_title_model_attribute(self, model):
        return self.model_name

    def setup_proxies(self):
        self.model.open_till()
        self._setup_widgets()
        self.add_proxy(self.model, self.widgets)


class TillClosingEditor(BaseEditor):
    model_name = _('Till Closing')
    model_type = Till
    gladefile = 'TillClosing'
    widgets = ('closing_date_lbl',
               'final_cash_amount',
               'balance_to_send',
               'total_balance_lbl')
    size = (350, 210)

    def __init__(self, conn, model):
        BaseEditor.__init__(self, conn, model)
        self.total_balance = model.get_balance()
        self._update_widgets()

    def _setup_widgets(self):
        for widget in (self.balance_to_send, self.final_cash_amount):
            widget.set_data_format(get_price_format_str())

    def _update_widgets(self):
        closing_date = self.model.closing_date.strftime('%x') 
        self.closing_date_lbl.set_text(closing_date)
        total_balance = get_formatted_price(self.total_balance)
        self.total_balance_lbl.set_text(total_balance)
  
    def update_final_cash_amount(self):
        balance_to_send = self.model.balance_sent or 0.0
        self.model.final_cash_amount = self.total_balance - balance_to_send
        self.proxy.update('final_cash_amount')

    def update_balance_to_send(self):
        final_cash_amount = self.model.final_cash_amount or 0.0
        self.model.balance_sent = self.total_balance - final_cash_amount 
        self.proxy.update('balance_sent')

    #
    # BaseEditor hooks
    # 

    def get_title(self, *args):
        return _('Closing current till')

    def setup_proxies(self):
        self.model.close_till()
        self.final_cash = self.model.final_cash_amount
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model, self.widgets)

    #
    # Kiwi handlers
    #

    def after_final_cash_amount__validate(self, widget, value):
        if value <= self.final_cash:
            return
        return ValidationError(_("You can not specifiy a final"
                                 " cash amount greater than the "
                                 "calculated value."))

    def after_balance_to_send__changed(self, *args):
        self.handler_block(self.final_cash_amount, 'changed')
        self.update_final_cash_amount()
        self.handler_unblock(self.final_cash_amount, 'changed')

    def after_final_cash_amount__changed(self, *args):
        self.handler_block(self.balance_to_send, 'changed')
        self.update_balance_to_send()
        self.handler_unblock(self.balance_to_send, 'changed')


class BaseCashSlave(BaseEditorSlave):
    model_type = Payment
    gladefile = 'BaseCashSlave'
    proxy_widgets = ('cash_amount',)
    label_widgets = ('date',
                     'date_lbl',
                     'cash_amount_lbl')
    widgets = proxy_widgets + label_widgets

    def __init__(self, conn, payment_description):
        self.payment_description = payment_description
        BaseEditorSlave.__init__(self, conn)

    def _setup_widgets(self):
        self.date.set_text(datetime.datetime.now().strftime('%x'))
        self.cash_amount.set_text('') 

    # 
    # BaseEditorSlave Hooks
    # 

    def create_model(self, conn):
        status = Payment.STATUS_TO_PAY
        now = datetime.datetime.now()
        method = sysparam(conn).METHOD_MONEY
        current_till = get_current_till_operation(conn)
        group = IPaymentGroup(current_till, connection=conn)
        if not group:
            ValueError('Till object must have a IPaymentGroup facet' 
                       'defined at this point')
        destination= sysparam(conn).DEFAULT_PAYMENT_DESTINATION
        description = self.payment_description
        model = Payment(status=status, due_date=now, value=0.0, 
                        method=method, group=group, 
                        destination=destination, 
                        description=description,
                        connection=conn)
        model.addFacet(IInPayment, connection=conn)
        return model

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)
        self._setup_widgets()

    #
    # Kiwi handlers
    #
    
    def on_cash_amount__validate(self, entry, value):
        if value <= 0.0:
            return ValidationError(_("Value Must be greater than zero"))


class CashAdvanceEditor(BaseEditor): 
    model_name = _('Cash Advance')
    model_type = CashAdvanceInfo
    gladefile = 'CashAdvanceEditor'
    size = (340, 180)
    label_widgets = ('employee_lbl',)
    entry_widgets = ('employee_combo',)


    def _setup_size_group(self, size_group, widgets, obj):
        for widget_name in widgets:
            widget = getattr(obj, widget_name)
            size_group.add_widget(widget)
                            
    def _setup_widgets(self):
        self.entry_size_group = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        self._setup_size_group(self.entry_size_group, self.entry_widgets,
                               self)
        self._setup_size_group(self.entry_size_group,
                               self.cash_slave.proxy_widgets, 
                               self.cash_slave)
        self.label_size_group = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        self._setup_size_group(self.label_size_group, self.label_widgets,
                               self)
        self._setup_size_group(self.label_size_group, 
                               self.cash_slave.label_widgets,
                               self.cash_slave)
        employees_table = Person.getAdapterClass(IEmployee)
        employees = [(p.get_adapted().name, p) for p in
                          employees_table.select(connection=self.conn)]
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
        self.cash_slave = BaseCashSlave(payment_description=None,
                                        conn=self.conn)
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
    size = (300, 150)

    # 
    # BaseEditorSlave Hooks
    # 
 
    def setup_slaves(self):
        current_till = get_current_till_operation(self.conn)
        branch_table = Person.getAdapterClass(IBranch)
        branch = branch_table.get(current_till.branch.id, connection=self.conn)
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
    widgets = label_widgets + entry_widgets
    title = _('Reverse Payment')
    size = (350, 195)
    
    def _setup_size_group(self, size_group, widgets, obj):
        for widget_name in widgets:
            widget = getattr(obj, widget_name)
            size_group.add_widget(widget)
        
    def _setup_widgets(self):
        self.entry_size_group = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        self._setup_size_group(self.entry_size_group, self.entry_widgets,
                               self)
        self._setup_size_group(self.entry_size_group,
                               self.cash_slave.proxy_widgets, 
                               self.cash_slave)
        self.label_size_group = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        self._setup_size_group(self.label_size_group, self.label_widgets,
                               self)
        self._setup_size_group(self.label_size_group, 
                               self.cash_slave.label_widgets,
                               self.cash_slave)
    
    # 
    # BaseEditorSlave Hooks
    # 
    
    def setup_slaves(self):
        self.cash_slave = BaseCashSlave(payment_description=None,
                                        conn=self.conn)
        self.attach_slave("base_cash_holder", self.cash_slave)
        self._setup_widgets()

    def on_confirm(self):
        payment_description = self.reason.get_text()
        self.cash_slave.model.description = payment_description
        value = self.cash_slave.model.value
        value *= -1
        self.cash_slave.model.value = value
        return self.cash_slave.on_confirm()
