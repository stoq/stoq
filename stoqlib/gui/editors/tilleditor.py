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
##                   Johan Dahlin               <jdahlin@async.com.br>
##
""" Editors implementation for open/close operation on till operation"""

from datetime import datetime
from decimal import Decimal

from kiwi.datatypes import ValidationError, currency
from kiwi.python import Settable

from stoqlib.database.runtime import get_current_station
from stoqlib.domain.interfaces import IEmployee
from stoqlib.domain.person import Person
from stoqlib.domain.till import Till, TillEntry
from stoqlib.gui.editors.baseeditor import BaseEditor, BaseEditorSlave
from stoqlib.lib.drivers import till_add_cash, till_remove_cash
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class _TillOpeningModel(object):
    def __init__(self, till, value):
        self.till = till
        self.value = value

    def get_balance(self):
        return currency(self.till.get_balance() + self.value)

class _TillClosingModel(object):
    def __init__(self, till, value):
        self.till = till
        self.value = value

    def get_opening_date(self):
        return self.till.opening_date

    def get_balance(self):
        return currency(self.till.get_balance() - self.value)

    def get_total_balance(self):
        return self.till.get_balance()

class CashAdvanceInfo(Settable):
    employee = None
    payment = None
    open_date = None

class _BaseCashModel(object):
    def __init__(self, entry):
        self.entry = entry

    def get_balance(self):
        return currency(self.entry.till.get_balance())

    def _get_value(self):
        return self.entry.value

    def _set_value(self, value):
        self.entry.value = value
    value = property(_get_value, _set_value)

class TillOpeningEditor(BaseEditor):
    """
    An editor to open a till.
    You can add cash to the till in the editor and it also shows
    the balance of the till, after the cash has been added.

    Callers of this editor are responsible for sending in a valid Till object,
    which the method open_till() can be called.
    """
    title = _(u'Till Opening')
    model_type = _TillOpeningModel
    gladefile = 'TillOpening'
    proxy_widgets = ('value',
                     'balance')

    def __init__(self, conn, model=None, visual_mode=False):
        BaseEditor.__init__(self, conn, model, visual_mode=visual_mode)
        self.main_dialog.set_confirm_widget(self.value)

    #
    # BaseEditorSlave
    #

    def create_model(self, conn):
        till = Till(connection=conn, station=get_current_station(conn))
        till.open_till()

        return _TillOpeningModel(till=till, value=currency(0))

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model, TillOpeningEditor.proxy_widgets)

    def on_confirm(self):
        till = self.model.till

        value = self.proxy.model.value
        if value:
            till.create_credit(value,
                               (_(u'Initial Cash amount of %s')
                                % till.opening_date.strftime('%x')))

        return till

    #
    # Kiwi callbacks
    #

    def on_value__validate(self, entry, data):
        if data < currency(0):
            self.proxy.update('balance', currency(0))
            return ValidationError(
                _("You cannot add a negative amount when opening the till."))

    def after_value__content_changed(self, entry):
        self.proxy.update('balance')

class TillClosingEditor(BaseEditor):
    title = _(u'Closing Opened Till')
    model_type = _TillClosingModel
    gladefile = 'TillClosing'
    proxy_widgets = ('value',
                     'balance',
                     'total_balance',
                     'opening_date')

    def __init__(self, conn, model=None, visual_mode=False):
        self.till = Till.get_last_opened(conn)
        assert self.till
        BaseEditor.__init__(self, conn, model, visual_mode=visual_mode)

        self.main_dialog.set_confirm_widget(self.value)

    #
    # BaseEditorSlave
    #

    def create_model(self, trans):
        return _TillClosingModel(till=self.till, value=currency(0))

    def on_confirm(self):
        self.till.close_till(self.model.value)
        return True

    def setup_proxies(self):
        if not self.till.get_balance():
            self.value.set_sensitive(False)
        self.proxy = self.add_proxy(self.model,
                                    TillClosingEditor.proxy_widgets)


    #
    # Kiwi handlers
    #

    def after_value__validate(self, widget, value):
        if value < currency(0):
            self.proxy.update('balance', currency(0))
            return ValidationError(_("Value cannot be less than zero"))
        if value > self.till.get_balance():
            self.proxy.update('balance', currency(0))
            return ValidationError(_("You can not specify an amount "
                                     "removed greater than the "
                                     "till balance."))

    def after_value__content_changed(self, entry):
        self.proxy.update('balance')


class BaseCashSlave(BaseEditorSlave):
    """
    A slave representing two fields, which is used by Cash editors:

    Date:        YYYY-MM-DD
    Cash Amount: [        ]
    """

    model_type = _BaseCashModel
    gladefile = 'BaseCashSlave'
    proxy_widgets = ('value', 'balance')

    #
    # BaseEditorSlave
    #

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model, BaseCashSlave.proxy_widgets)
        self.date.set_text(str(datetime.today().date()))
        self.proxy.update('value', Decimal('0.01'))

    #
    # Kiwi handlers
    #

    def on_value__validate(self, widget, value):
        zero = currency(0)
        if value <= zero:
            return ValidationError(_("Value cannot be zero or less than zero"))

    def on_value__content_changed(self, entry):
        self.proxy.update('balance')

class RemoveCashSlave(BaseCashSlave):

    def on_value__validate(self, widget, value):
        retval = BaseCashSlave.on_value__validate(self, widget, value)
        if retval:
            return retval
        if value > self.model.get_balance():
            return ValidationError(_("Value cannot be more than the total Till balance"))

class CashAdvanceEditor(BaseEditor):
    """
    An editor which extends BashCashSlave to include.
    It extends BashCashSlave to include an employee combobox
    """

    model_name = _(u'Cash Advance')
    model_type = CashAdvanceInfo
    gladefile = 'CashAdvanceEditor'

    def _get_employee(self):
        return self.employee_combo.get_selected_data()

    def _get_employee_name(self):
        return self.employee_combo.get_selected_label()

    def _setup_widgets(self):
        # FIXME: Implement and use IDescribable on PersonAdaptToEmployee
        employees = [(e.person.name, e)
                     for e in Person.iselect(IEmployee, connection=self.conn)]
        self.employee_combo.prefill(employees)
        self.employee_combo.set_active(0)

    #
    # BaseEditorSlave
    #

    def create_model(self, conn):
        till = Till.get_current(conn)
        assert till
        self.payment = till.create_debit(currency(0))

        return CashAdvanceInfo(payment=self.payment)

    def setup_slaves(self):
        self.cash_slave = RemoveCashSlave(self.conn, _BaseCashModel(self.payment))
        self.cash_slave.value.connect('content-changed', self._on_cash_slave__value_changed)
        self.attach_slave("base_cash_holder", self.cash_slave)
        self._setup_widgets()

    def validate_confirm(self):
        return self.cash_slave.validate_confirm()

    def on_confirm(self):
        valid = self.cash_slave.on_confirm()
        if valid:
            self.model.description = (_(u'Cash advance paid to employee: %s')
                                     % self._get_employee_name())
            self.payment.description = self.model.description
            self.model.employee = self._get_employee()
            self.payment.value = self.payment.value
            self.model.value = abs(self.payment.value)

            till_remove_cash(self.conn, self.model.value)
            return self.model

        return valid

    #
    # Callbacks
    #

    def _on_cash_slave__value_changed(self, entry):
        self.cash_slave.model.value = -abs(self.cash_slave.model.value)


class CashOutEditor(BaseEditor):
    """
    An editor to Remove cash from the Till
    It extends BashCashSlave to include a reason entry.
    """

    model_name = _(u'Cash Out')
    model_type = TillEntry
    gladefile = 'CashOutEditor'
    title = _(u'Reverse Payment')

    def __init__(self, conn):
        BaseEditor.__init__(self, conn)
        self.main_dialog.set_confirm_widget(self.reason)
        self.main_dialog.set_confirm_widget(self.cash_slave.value)

    #
    # BaseEditorSlave
    #

    def create_model(self, conn):
        till = Till.get_current(conn)
        assert till

        # FIXME: Implement and use IDescribable on PersonAdaptToBranch
        description = (_(u'Cash out for station "%s" of branch "%s"')
                       % (till.station.name,
                          till.station.branch.person.name))
        return till.create_debit(currency(0), description)

    def setup_slaves(self):
        self.cash_slave = RemoveCashSlave(
            self.conn, _BaseCashModel(self.model))
        self.cash_slave.value.connect('content-changed', self._on_cash_slave__value_changed)
        self.attach_slave("base_cash_holder", self.cash_slave)

    def validate_confirm(self):
        return self.cash_slave.validate_confirm()

    def on_confirm(self):
        valid = self.cash_slave.on_confirm()
        if valid:
            reason = self.reason.get_text()
            if reason:
                # %s is the description used when removing money
                payment_description = _(u'Cash out: %s') % reason
            else:
                payment_description = _(u'Cash out')
            self.model.description = payment_description

        till_remove_cash(self.conn, abs(self.cash_slave.model.value))
        return valid

    #
    # Callbacks
    #

    def _on_cash_slave__value_changed(self, entry):
        self.cash_slave.model.value = -abs(self.cash_slave.model.value)

class CashInEditor(BaseEditor):
    """
    An editor to Add cash to the Till
    It uses BashCashSlave without any extensions
    """

    model_name = _(u'Cash In')
    model_type = TillEntry
    gladefile = 'CashOutEditor'

    def __init__(self, conn):
        BaseEditor.__init__(self, conn)
        self.main_dialog.set_confirm_widget(self.reason)
        self.main_dialog.set_confirm_widget(self.cash_slave.value)

    #
    # BaseEditorSlave
    #

    def create_model(self, conn):
        till = Till.get_current(conn)
        assert till

        # FIXME: Implement and use IDescribable on PersonAdaptToBranch
        description = (_(u'Cash in for station "%s" of branch "%s"')
                       % (till.station.name,
                          till.station.branch.person.name))
        return till.create_credit(currency(0), description)

    def setup_slaves(self):
        self.cash_slave = BaseCashSlave(
            self.conn, _BaseCashModel(self.model))
        self.attach_slave("base_cash_holder", self.cash_slave)

    def validate_confirm(self):
        return self.cash_slave.validate_confirm()

    def on_confirm(self):
        valid = self.cash_slave.on_confirm()
        if valid:
            reason = self.reason.get_text()
            if reason:
                # %s is the description used when removing money
                payment_description = _(u'Cash in: %s') % reason
            else:
                payment_description = _(u'Cash in')
            self.model.description = payment_description

        till_add_cash(self.conn, self.cash_slave.model.value)
        return valid
