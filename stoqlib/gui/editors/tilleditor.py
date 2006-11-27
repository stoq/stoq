# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source <http://www.async.com.br>
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
## Author(s):        Henrique Romano            <henrique@async.com.br>
##                   Evandro Vale Miquelito     <evandro@async.com.br>
##
""" Editors implementation for open/close operation on till operation"""

from datetime import datetime

from kiwi.datatypes import ValidationError, currency
from kiwi.python import Settable

from stoqlib.database.runtime import get_current_station
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.base.editors import BaseEditor, BaseEditorSlave
from stoqlib.domain.till import Till, TillEntry
from stoqlib.domain.payment.base import CashAdvanceInfo
from stoqlib.domain.person import Person
from stoqlib.domain.interfaces import IInPayment, IEmployee, IOutPayment

_ = stoqlib_gettext


class TillOpeningEditor(BaseEditor):
    title = _(u'Till Opening')
    model_type = Till
    gladefile = 'TillOpening'

    #
    # BaseEditor hooks
    #

    def create_model(self, conn):
        model = Till(connection=conn, station=get_current_station(conn))
        model.open_till()
        return model

    def setup_proxies(self):
        self.till_proxy = self.add_proxy(self.model, ['opening_date'])

        model = Settable(initial_cash_amount=currency(0))
        self.settable_proxy = self.add_proxy(model, ['initial_cash_amount'])

    def on_confirm(self):
        initial_cash = self.settable_proxy.model.initial_cash_amount
        if initial_cash > 0:
            reason = (_(u'Initial Cash amount of %s')
                        % self.model.opening_date.strftime('%x'))
            self.model.create_credit(initial_cash, reason)
        return self.model

    def on_initial_cash_amount__validate(self, entry, data):
        if data < currency(0):
            return ValidationError(
                _("You cannot open the till with a negative amount."))

class TillClosingEditor(BaseEditor):
    title = _(u'Closing Opened Till')
    model_type = Till
    gladefile = 'TillClosing'
    size = (350, 290)
    proxy_widgets = ('float_remaining',
                     'balance_sent',
                     'closing_date',
                     'opening_date',
                     'cash_total',
                     'balance')

    #
    # BaseEditor hooks
    #

    def on_confirm(self):
        self.model.close_till()
        return self.model

    def setup_proxies(self):
        self.model.closing_date = datetime.now()
        self.total_cash = self.model.get_cash_total()
        if not self.total_cash:
            self.balance_sent.set_sensitive(False)
        self.proxy = self.add_proxy(self.model,
                                    TillClosingEditor.proxy_widgets)

    #
    # Kiwi handlers
    #

    def after_balance_sent__validate(self, widget, value):
        if value < currency(0):
            return ValidationError(_("Value cannot be lesser that zero"))
        if value <= self.total_cash:
            return
        return ValidationError(_("You can not specifiy an amount "
                                 "removed greater than the "
                                 "till balance."))

    def after_balance_sent__changed(self, *args):
        self.proxy.update('balance')
        self.proxy.update('float_remaining')


class BaseCashSlave(BaseEditorSlave):
    model_type = TillEntry
    gladefile = 'BaseCashSlave'
    proxy_widgets = ('cash_amount',)

    def __init__(self, conn, payment_description,
                 payment_iface=IInPayment):
        self.payment_description = payment_description
        self.payment_iface = payment_iface
        BaseEditorSlave.__init__(self, conn)

    def _setup_widgets(self):
        self.date.set_text(datetime.now().strftime('%x'))

    #
    # BaseEditorSlave Hooks
    #

    def create_model(self, conn):
        till = Till.get_current(conn)
        assert till, "till must be open"

        if self.payment_iface == IInPayment:
            return till.create_credit(currency(0), self.payment_description)
        elif self.payment_iface == IOutPayment:
            return till.create_debit(currency(0), self.payment_description)
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

    def validate_confirm(self):
        if self.model.value <= 0:
            self.cash_amount.set_invalid( _("Value Must be greater than zero"))
            return False
        return True


class CashAdvanceEditor(BaseEditor):
    model_name = _(u'Cash Advance')
    model_type = CashAdvanceInfo
    gladefile = 'CashAdvanceEditor'

    payment_iface = IOutPayment

    def _setup_widgets(self):
        # FIXME: Implement and use IDescribable on PersonAdaptToEmployee
        employees = [(e.person.name, e)
                     for e in Person.iselect(IEmployee, connection=self.conn)]
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
                                        payment_description=u"",
                                        payment_iface=self.payment_iface)
        self.attach_slave("base_cash_holder", self.cash_slave)
        self._setup_widgets()

    def validate_confirm(self):
        return self.cash_slave.validate_confirm()

    def on_confirm(self):
        self.model.employee = self.employee_combo.get_selected_data()
        self.model.payment = self.cash_slave.model
        employee_name = self.employee_combo.get_selected_label()
        payment_description = (_(u'Cash advance paid to employee: %s')
                                 % employee_name)
        self.cash_slave.model.description = payment_description

        value = self.cash_slave.model.value
        value *= -1
        self.cash_slave.model.value = value
        return self.model


class CashInEditor(BaseEditor):
    model_name = _(u'Cash In')
    model_type = TillEntry
    gladefile = 'BaseTemplate'

    #
    # BaseEditorSlave Hooks
    #

    def setup_slaves(self):
        if not self.cash_slave:
            raise ValueError("The cash_slave attribute should be defined at "
                             "this point")
        self.attach_slave("main_holder", self.cash_slave)

    def create_model(self, conn):
        current_till = Till.get_current(conn)
        # FIXME: Implement and use IDescribable on PersonAdaptToBranch
        description = (_(u'Cash in for station "%s" of branch "%s"')
                       % (current_till.station.name,
                          current_till.station.branch.person.name))
        self.cash_slave = BaseCashSlave(payment_description=description,
                                        conn=conn)
        return self.cash_slave.model

    def validate_confirm(self):
        return self.cash_slave.validate_confirm()

    def on_confirm(self):
        return self.cash_slave.on_confirm()


class CashOutEditor(BaseEditor):
    model_name = _(u'Cash Out')
    model_type = TillEntry
    gladefile = 'CashOutEditor'
    title = _(u'Reverse Payment')

    payment_iface = IOutPayment

    #
    # BaseEditorSlave Hooks
    #

    def create_model(self, conn):
        self.cash_slave = BaseCashSlave(self.conn, payment_description=u"",
                                        payment_iface=self.payment_iface)
        return self.cash_slave.model

    def setup_slaves(self):
        if not self.cash_slave:
            raise ValueError("The cash_slave attribute should be defined at "
                             "this point")
        self.attach_slave("base_cash_holder", self.cash_slave)

    def validate_confirm(self):
        return self.cash_slave.validate_confirm()

    def on_confirm(self):
        reason = self.reason.get_text()
        if reason:
            # %s is the description used when removing money
            payment_description = _(u'Cash out: %s') % reason
        else:
            payment_description = _(u'Cash out')
        self.model.description = payment_description
        self.model.value = -self.model.value

        return self.cash_slave.on_confirm()
