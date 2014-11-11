# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2007 Async Open Source <http://www.async.com.br>
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
""" Editors implementation for open/close operation on till operation"""

from datetime import timedelta

from kiwi.currency import currency
from kiwi.datatypes import ValidationError
from kiwi.python import Settable
from kiwi.ui.objectlist import Column, ColoredColumn, SummaryLabel

from stoqdrivers.exceptions import DriverError

from stoqlib.api import api
from stoqlib.database.expr import TransactionTimestamp
from stoqlib.domain.account import AccountTransaction
from stoqlib.domain.events import (TillOpenEvent, TillCloseEvent,
                                   TillAddTillEntryEvent,
                                   TillAddCashEvent, TillRemoveCashEvent)
from stoqlib.domain.person import Employee
from stoqlib.domain.till import Till
from stoqlib.exceptions import DeviceError, TillError
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.slaves.tillslave import RemoveCashSlave, BaseCashSlave
from stoqlib.lib.dateutils import localnow
from stoqlib.lib.message import warning
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


def _create_transaction(store, till_entry):
    if till_entry.value > 0:
        operation_type = AccountTransaction.TYPE_IN
        source_account = sysparam.get_object_id('IMBALANCE_ACCOUNT')
        dest_account = sysparam.get_object_id('TILLS_ACCOUNT')
    else:
        operation_type = AccountTransaction.TYPE_OUT
        source_account = sysparam.get_object_id('TILLS_ACCOUNT')
        dest_account = sysparam.get_object_id('IMBALANCE_ACCOUNT')

    AccountTransaction(description=till_entry.description,
                       source_account_id=source_account,
                       account_id=dest_account,
                       value=abs(till_entry.value),
                       code=unicode(till_entry.identifier),
                       date=TransactionTimestamp(),
                       store=store,
                       payment=till_entry.payment,
                       operation_type=operation_type)


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
        # self.till is None only in the special case that the user added the ECF
        # to Stoq with a pending reduce Z, so we need to close the till on the
        # ECF, but not on Stoq.
        # Return a date in the past
        if not self.till:
            return localnow() - timedelta(1)
        return self.till.opening_date

    def get_cash_amount(self):
        if not self.till:
            return currency(0)
        return currency(self.till.get_cash_amount() - self.value)

    def get_balance(self):
        if not self.till:
            return currency(0)
        return currency(self.till.get_balance() - self.value)


class TillOpeningEditor(BaseEditor):
    """An editor to open a till.
    You can add cash to the till in the editor and it also shows
    the balance of the till, after the cash has been added.

    Callers of this editor are responsible for sending in a valid Till object,
    which the method open_till() can be called.
    """
    title = _(u'Till Opening')
    model_type = _TillOpeningModel
    gladefile = 'TillOpening'
    confirm_widgets = ['value']
    proxy_widgets = ('value',
                     'balance')

    help_section = 'till-open'

    #
    # BaseEditorSlave
    #

    def create_model(self, store):
        till = Till(store=store, station=api.get_current_station(store))
        till.open_till()

        return _TillOpeningModel(till=till, value=currency(0))

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model, TillOpeningEditor.proxy_widgets)

    def on_confirm(self):
        till = self.model.till
        # Using api.get_default_store instead of self.store
        # or it will return self.model.till
        last_opened = Till.get_last_opened(api.get_default_store())
        if (last_opened and
            last_opened.opening_date.date() == till.opening_date.date()):
            warning(_("A till was opened earlier this day."))
            self.retval = False
            return

        try:
            TillOpenEvent.emit(till=till)
        except (TillError, DeviceError) as e:
            warning(str(e))
            self.retval = False
            return

        value = self.proxy.model.value
        if value:
            TillAddCashEvent.emit(till=till, value=value)
            till_entry = till.add_credit_entry(value, _(u'Initial Cash amount'))
            _create_transaction(self.store, till_entry)
            # The callsite is responsible for interacting with
            # the fiscal printer

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
    size = (500, 440)
    title = _(u'Closing Opened Till')
    model_type = _TillClosingModel
    gladefile = 'TillClosing'
    confirm_widgets = ['value']
    proxy_widgets = ('value',
                     'balance',
                     'opening_date',
                     'observations')

    help_section = 'till-close'

    def __init__(self, store, model=None, previous_day=False, close_db=True,
                 close_ecf=True):
        """
        Create a new TillClosingEditor object.
        :param previous_day: If the till wasn't closed previously
        """
        self._previous_day = previous_day
        self.till = Till.get_last(store)
        if close_db:
            assert self.till
        self._close_db = close_db
        self._close_ecf = close_ecf
        BaseEditor.__init__(self, store, model)
        self._setup_widgets()

    def _setup_widgets(self):
        # We cant remove cash if closing till from a previous day
        self.value.set_sensitive(not self._previous_day)
        if self._previous_day:
            value = 0
        else:
            value = self.model.get_balance()
        self.value.update(value)

        self.day_history.set_columns(self._get_columns())
        self.day_history.connect('row-activated', lambda olist, row: self.confirm())
        self.day_history.add_list(self._get_day_history())
        summary_day_history = SummaryLabel(
            klist=self.day_history,
            column='value',
            label='<b>%s</b>' % api.escape(_(u'Total balance:')))
        summary_day_history.show()
        self.day_history_box.pack_start(summary_day_history, False)

    def _get_day_history(self):
        if not self.till:
            assert self._close_ecf and not self._close_db
            return

        day_history = {}
        day_history[_(u'Initial Amount')] = self.till.initial_cash_amount

        for entry in self.till.get_entries():
            payment = entry.payment
            if payment is not None:
                desc = payment.method.get_description()
            else:
                if entry.value > 0:
                    desc = _(u'Cash In')
                else:
                    desc = _(u'Cash Out')

            if desc in day_history.keys():
                day_history[desc] += entry.value
            else:
                day_history[desc] = entry.value

        for description, value in day_history.items():
            yield Settable(description=description, value=value)

    def _get_columns(self):
        return [Column('description', title=_('Description'), data_type=str,
                       width=300, sorted=True),
                ColoredColumn('value', title=_('Amount'), data_type=currency,
                              color='red', data_func=lambda x: x < 0)]

    #
    # BaseEditorSlave
    #

    def create_model(self, trans):
        return _TillClosingModel(till=self.till, value=currency(0))

    def setup_proxies(self):
        if self.till and not self.till.get_balance():
            self.value.set_sensitive(False)
        self.proxy = self.add_proxy(self.model,
                                    TillClosingEditor.proxy_widgets)

    def validate_confirm(self):
        till = self.model.till
        removed = abs(self.model.value)
        if removed and removed > till.get_balance():
            warning(_("The amount that you want to remove is "
                      "greater than the current balance."))
            return False
        return True

    def on_confirm(self):
        till = self.model.till
        removed = abs(self.model.value)
        if removed:
            # We need to do this inside a new transaction, because if the
            # till closing fails further on, this still needs to be recorded
            # in the database
            store = api.new_store()
            t_till = store.fetch(till)
            TillRemoveCashEvent.emit(till=t_till, value=removed)

            reason = _('Amount removed from Till by %s') % (
                api.get_current_user(self.store).get_description(), )
            till_entry = t_till.add_debit_entry(removed, reason)

            # Financial transaction
            _create_transaction(store, till_entry)
            # DB transaction
            store.confirm(True)
            store.close()

        if self._close_ecf:
            try:
                retval = TillCloseEvent.emit(till=till,
                                             previous_day=self._previous_day)
            except (TillError, DeviceError) as e:
                warning(str(e))
                return None

            # If the event was captured and its return value is False, then we
            # should not close the till.
            if retval is False:
                return False

        if self._close_db:
            try:
                till.close_till(observations=self.model.observations)
            except ValueError as err:
                warning(str(err))
                return

        # The callsite is responsible for interacting with
        # the fiscal printer
        return self.model

    #
    # Kiwi handlers
    #

    def after_value__validate(self, widget, value):
        if not hasattr(self, 'proxy'):
            return
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


class TillVerifyEditor(TillClosingEditor):
    title = _('Till verification')
    help_section = 'till-verify'

    def __init__(self, store, model=None, previous_day=False,
                 close_db=False, close_ecf=False):
        assert not close_db and not close_ecf
        super(TillVerifyEditor, self).__init__(store, model=model,
                                               previous_day=previous_day,
                                               close_db=close_db,
                                               close_ecf=close_ecf)
        self.set_message(
            _("Use this to adjust the till for the next user.\n"
              "Note that this will not really close the till or ecf."))


class CashAdvanceEditor(BaseEditor):
    """An editor which extends BaseCashSlave to include.
    It extends BaseCashSlave to include an employee combobox
    """

    model_name = _(u'Cash Advance')
    model_type = Settable
    gladefile = 'CashAdvanceEditor'

    def _get_employee(self):
        return self.employee_combo.get_selected_data()

    def _get_employee_name(self):
        return self.employee_combo.get_selected_label()

    def _setup_widgets(self):
        employees = self.store.find(Employee)
        self.employee_combo.prefill(api.for_person_combo(employees))
        self.employee_combo.set_active(0)

    #
    # BaseEditorSlave
    #

    def create_model(self, store):
        till = Till.get_current(self.store)
        return Settable(employee=None,
                        payment=None,
                        # FIXME: should send in consts.now()
                        open_date=None,
                        till=till,
                        balance=till.get_balance(),
                        value=currency(0))

    def setup_slaves(self):
        self.cash_slave = RemoveCashSlave(self.store,
                                          self.model)
        self.cash_slave.value.connect('content-changed',
                                      self._on_cash_slave__value_changed)
        self.attach_slave("base_cash_holder", self.cash_slave)
        self._setup_widgets()

    def on_confirm(self):
        till = self.model.till
        value = abs(self.model.value)
        assert till
        try:
            TillRemoveCashEvent.emit(till=till, value=value)
        except (TillError, DeviceError, DriverError) as e:
            warning(str(e))
            self.retval = False
            return
        till_entry = till.add_debit_entry(
            value, (_(u'Cash advance paid to employee: %s') % (
                    self._get_employee_name(), )))

        TillAddTillEntryEvent.emit(till_entry, self.store)
        _create_transaction(self.store, till_entry)

    #
    # Callbacks
    #

    def _on_cash_slave__value_changed(self, entry):
        self.cash_slave.model.value = -abs(self.cash_slave.model.value)


class BaseCashEditor(BaseEditor):
    model_type = Settable
    gladefile = 'BaseCashEditor'

    def __init__(self, store):
        BaseEditor.__init__(self, store)
        self.set_confirm_widget(self.reason)
        self.set_confirm_widget(self.cash_slave.value)

    #
    # BaseEditorSlave
    #

    def create_model(self, store):
        till = Till.get_current(store)
        return Settable(value=currency(0),
                        reason=u'',
                        till=till,
                        balance=till.get_balance())

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model, [u'reason'])

    def setup_slaves(self):
        self.cash_slave = self.cash_slave_class(self.store, self.model)
        self.attach_slave("base_cash_holder", self.cash_slave)

    def on_confirm(self):
        value = abs(self.model.value)
        till = self.model.till
        assert till
        try:
            self.event.emit(till=till, value=value)
        except (TillError, DeviceError, DriverError) as e:
            warning(str(e))
            self.retval = False
            return

        till_entry = self.create_entry(till, value, self.model.reason)

        TillAddTillEntryEvent.emit(till_entry, self.store)
        _create_transaction(self.store, till_entry)


class CashOutEditor(BaseCashEditor):
    """An editor to Remove cash from the Till
    """

    model_name = _(u'Cash Out')
    title = _(u'Reverse Payment')
    cash_slave_class = RemoveCashSlave
    event = TillRemoveCashEvent
    help_section = 'till-remove-money'

    def create_entry(self, till, value, reason):
        return till.add_debit_entry(value, (_(u'Cash out: %s') % (reason, )))


class CashInEditor(BaseCashEditor):
    """An editor to Add cash to the Till
    """

    model_name = _(u'Cash In')
    cash_slave_class = BaseCashSlave
    event = TillAddCashEvent
    help_section = 'till-add-money'

    def create_entry(self, till, value, reason):
        return till.add_credit_entry(value, (_(u'Cash in: %s') % (reason, )))
