# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2008 Async Open Source <http://www.async.com.br>
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
##
""" Slaves for payment management """

import gtk


from copy import deepcopy
import datetime
from dateutil.relativedelta import relativedelta
from decimal import Decimal

from kiwi import ValueUnset
from kiwi.component import get_utility
from kiwi.datatypes import format_price, currency, ValidationError
from kiwi.python import Settable
from kiwi.utils import gsignal
from kiwi.ui.delegates import GladeSlaveDelegate
from kiwi.ui.objectlist import Column

from stoqlib.api import api
from stoqlib.domain.events import CreatePaymentEvent
from stoqlib.domain.interfaces import IInPayment, IOutPayment
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.domain.payment.method import PaymentMethod, CreditCardData
from stoqlib.domain.payment.payment import Payment, PaymentChangeHistory
from stoqlib.domain.payment.renegotiation import PaymentRenegotiation
from stoqlib.domain.person import PersonAdaptToCreditProvider
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.domain.sale import Sale
from stoqlib.drivers.cheque import get_current_cheque_printer_settings
from stoqlib.enums import CreatePaymentStatus
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.baseeditor import BaseEditorSlave, BaseEditor
from stoqlib.gui.interfaces import IDomainSlaveMapper
from stoqlib.lib.defaults import (interval_types, INTERVALTYPE_MONTH,
                                  DECIMAL_PRECISION)
from stoqlib.lib.message import info, warning
from stoqlib.lib.payment import (generate_payments_values,
                                          generate_payments_due_dates)
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

#
# Temporary Objects
#

DEFAULT_INSTALLMENTS_NUMBER = 1
DEFAULT_INTERVALS = 1
DEFAULT_INTERVAL_TYPE = INTERVALTYPE_MONTH


class _BaseTemporaryMethodData(object):
    def __init__(self, first_duedate=None,
                 installments_number=None):
        self.first_duedate = first_duedate or datetime.date.today()
        self.installments_number = (installments_number or
                                    DEFAULT_INSTALLMENTS_NUMBER)
        self.intervals = DEFAULT_INTERVALS
        self.interval_type = DEFAULT_INTERVAL_TYPE


class _TemporaryCreditProviderGroupData(_BaseTemporaryMethodData):
    def __init__(self, provider=None):
        self.provider = provider
        _BaseTemporaryMethodData.__init__(self)


class _TemporaryPaymentData(object):
    def __init__(self, description, value, due_date,
                 payment_number=None, bank_account=None):
        self.description = description
        self.value = value
        self.due_date = due_date
        self.payment_number = payment_number
        self.bank_account = bank_account


class _TemporaryBankData(object):
    def __init__(self, bank_number=None, bank_branch=None, bank_account=None):
        self.bank_number = bank_number
        self.bank_branch = bank_branch
        self.bank_account = bank_account


#
# Editors
#

class BasePaymentDataEditor(BaseEditor):
    """A base editor to set payment information.
    """

    gladefile = 'BasePaymentDataEditor'
    model_type = _TemporaryPaymentData
    payment_widgets = ('due_date', 'value', 'payment_number')
    slave_holder = 'bank_data_slave'

    def __init__(self, model):
        BaseEditor.__init__(self, None, model)

    #
    # Private Methods
    #

    def _setup_widgets(self):
        self.payment_number.grab_focus()

    #
    # BaseEditorSlave hooks
    #

    def get_title(self, model):
        return _(u"Edit '%s'") % model.description

    def setup_proxies(self):
        self._setup_widgets()
        self.add_proxy(self.model, self.payment_widgets)

    #
    # Kiwi callbacks
    #

    def on_due_date__validate(self, widget, value):
        if sysparam(self.conn).ALLOW_OUTDATED_OPERATIONS:
            return

        if value < datetime.date.today():
            return ValidationError(_(u"Expected installment due date "
                                      "must be set to a future date"))

    def on_value__validate(self, widget, value):
        if value < currency(0):
            return ValidationError(_(u"The value must be "
                                      "a positive number"))


class CheckDataEditor(BasePaymentDataEditor):
    """An editor to set payment information of check payment method.
    """

    #
    # BaseEditorSlave hooks
    #

    def setup_slaves(self):
        bank_data_slave = BankDataSlave(self.model.bank_account)

        if self.get_slave(self.slave_holder):
            self.detach_slave(self.slave_holder)
        self.attach_slave(self.slave_holder, bank_data_slave)


class BankDataSlave(BaseEditorSlave):
    """A simple slave that contains only a hbox with fields to bank name and
    its branch. This slave is used by payment method slaves that has reference
    to a BankAccount object.
    """

    gladefile = 'BankDataSlave'
    model_type = _TemporaryBankData
    proxy_widgets = ('bank_number', 'bank_branch', 'bank_account')

    def __init__(self, model):
        self.model = model
        BaseEditorSlave.__init__(self, None, self.model)

    #
    # BaseEditorSlave hooks
    #

    def setup_proxies(self):
        self.add_proxy(self.model, self.proxy_widgets)


class PaymentListSlave(GladeSlaveDelegate):
    """A slave to manage payments with one/multiple installment(s)"""

    gladefile = 'PaymentListSlave'
    gsignal('payment-edited')

    def __init__(self, iface, group, method, total_value, editor_class, parent):
        self.parent = parent
        self.iface = iface
        self.group = group
        self.total_value = total_value
        self.editor_class = editor_class
        self.method = method

        GladeSlaveDelegate.__init__(self, gladefile=self.gladefile)
        self._setup_widgets()

    #
    # Private Methods
    #

    def _can_edit_payments(self):
        return self.method.method_name != 'money'

    def _has_bank_account(self):
        return self.method.method_name == 'check'

    def _get_columns(self):
        columns = [Column('description', title=_('Description'),
                          expand=True, data_type=str)]

        if self._has_bank_account():
            columns.extend([Column('bank_account.bank_number',
                                   title=_('Bank ID'),
                                   data_type=str, justify=gtk.JUSTIFY_RIGHT),
                            Column('bank_account.bank_branch',
                                   title=_('Bank branch'),
                                   data_type=str, justify=gtk.JUSTIFY_RIGHT),
                            Column('bank_account.bank_account',
                                   title=_('Bank account'),
                                   data_type=str, justify=gtk.JUSTIFY_RIGHT)])

        # Money methods doesn't have a payment_number related with it.
        if self.method.method_name != 'money':
            columns.append(Column('payment_number', title=_('Number'),
                                  data_type=str, justify=gtk.JUSTIFY_RIGHT))

        columns.extend([Column('due_date', title=_('Due date'),
                               data_type=datetime.date),
                        Column('value', title=_('Value'), data_type=currency,
                               justify=gtk.JUSTIFY_RIGHT)])

        return columns

    def _setup_widgets(self):
        self.payment_list.set_columns(self._get_columns())
        self.total_label.set_text(format_price(self.total_value, True,
                                               DECIMAL_PRECISION))

    def _update_difference_label(self):
        difference = self.get_total_difference()
        if not difference:
            label_name = _('Difference')
        elif difference > 0:
            label_name = _('Overpaid:')
        elif difference < 0:
            label_name = _('Outstanding:')
            difference *= -1
        difference = format_price(difference, True, DECIMAL_PRECISION)
        self.difference_label.set_text(difference)
        self.difference_status_label.set_text(label_name)

    def _run_edit_payment_dialog(self):
        if not self._can_edit_payments():
            return

        payment = self.payment_list.get_selected()
        old = deepcopy(payment)
        retval = run_dialog(self.editor_class, self.parent, payment)
        if not retval:
            # Remove the changes if dialog was canceled.
            pos = self.payment_list.get_selected_row_number()
            self.payment_list.remove(payment)
            self.payment_list.insert(pos, old)
        self.emit('payment-edited')

    #
    # Public API
    #

    def update_view(self):
        self.payment_list.refresh()
        self._update_difference_label()

    def add_payment(self, description, value, due_date, payment_number=None,
                    bank_account=None, refresh=True):
        """Add a payment to the list"""
        payment = _TemporaryPaymentData(description,
                                        value,
                                        due_date,
                                        payment_number,
                                        bank_account)
        self.payment_list.append(payment)

        if refresh:
            self.update_view()

    def add_payments(self, installments_number, first_due_date,
                     interval, interval_type):
        values = generate_payments_values(self.total_value,
                                          installments_number)
        due_dates = generate_payments_due_dates(installments_number,
                                                first_due_date, interval,
                                                interval_type)
        bank_account = None

        self.clear_payments()
        for i in range(installments_number):
            description = self.method.describe_payment(self.group, i + 1,
                                                       installments_number)
            if self._has_bank_account():
                bank_account = _TemporaryBankData()

            self.add_payment(description, currency(values[i]), due_dates[i],
                             None, bank_account, False)

        self.update_view()

    def create_payments(self):
        """Commit the payments on the list to the database"""
        if not self.is_payment_list_valid():
            return []

        payments = []
        for p in self.payment_list:
            # FIXME: The create_payment API has an argcheck on due_date
            #        forcing it to be datetime.datetime, so we need to
            #        make this conversion.
            due_date = datetime.datetime(p.due_date.year,
                                         p.due_date.month,
                                         p.due_date.day)
            payment = self.method.create_payment(iface=self.iface,
                                                 payment_group=self.group,
                                                 value=p.value,
                                                 due_date=due_date,
                                                 description=p.description,
                                                 payment_number=p.payment_number)
            if p.bank_account:
                # Add the bank_account into the payment, if any.
                adapted = payment.get_adapted()
                bank_account = adapted.check_data.bank_account
                bank_account.bank_number = p.bank_account.bank_number
                bank_account.bank_branch = p.bank_account.bank_branch
                bank_account.bank_account = p.bank_account.bank_account
            payments.append(payment)

        return payments

    def clear_payments(self):
        self.payment_list.clear()
        self.update_view()

    def get_total_difference(self):
        total_payments = Decimal(0)
        for payment in self.payment_list:
            total_payments += payment.value
        return (total_payments - self.total_value)

    def are_due_dates_valid(self):
        if sysparam(self.method.get_connection()).ALLOW_OUTDATED_OPERATIONS:
            return True

        previous_date = datetime.date.today() + datetime.timedelta(days=-1)
        for payment in self.payment_list:
            if payment.due_date <= previous_date:
                warning(_(u"Payment dates can't repeat or be lower than "
                           "previous dates."))
                return False
            previous_date = payment.due_date
        return True

    def are_payment_values_valid(self):
        return not self.get_total_difference()

    def is_payment_list_valid(self):
        if not self.are_due_dates_valid():
            return False
        if not self.are_payment_values_valid():
            return False
        return True

    #
    # Kiwi Callbacks
    #

    def on_payment_list__row_activated(self, *args):
        self._run_edit_payment_dialog()
        self.update_view()


#
# Payment Method Slaves
#

class BasePaymentMethodSlave(BaseEditorSlave):
    """A base payment method slave for Bill and Check methods."""

    gladefile = 'BasePaymentMethodSlave'
    model_type = _BaseTemporaryMethodData
    slave_holder = 'slave_holder'
    proxy_widgets = ('interval_type_combo',
                     'intervals',
                     'first_duedate',
                     'installments_number')

    # This attribute must be defined in child.
    # Use BasePaymentDataEditor or one of it's children.
    _data_editor_class = None

    def __init__(self, wizard, parent, conn, order_obj, payment_method,
                 outstanding_value=currency(0), first_duedate=None,
                 installments_number=None):
        self.wizard = wizard
        self.parent = parent
        # Note that 'order' may be a Sale or a PurchaseOrder object
        self.order = order_obj
        self.method = payment_method
        self.method_iface = self._get_payment_method_iface()
        self.total_value = outstanding_value or self._get_total_amount()
        self.payment_group = self.order.group
        self.payment_list = None
        # This is very useful when calculating the total amount outstanding
        # or overpaid of the payments
        self.interest_total = currency(0)

        self._first_duedate = first_duedate
        self._installments_number = installments_number

        BaseEditorSlave.__init__(self, conn)
        self.register_validate_function(self._refresh_next)

    #
    # Private Methods
    #

    def _refresh_next(self, validation_ok=True):
        if not self.payment_list:
            validation_ok = False
        if validation_ok:
            validation_ok = self.payment_list.is_payment_list_valid()

        self.wizard.refresh_next(validation_ok)

    def _setup_payment_list(self):
        self.payment_list = PaymentListSlave(self.method_iface,
                                             self.payment_group,
                                             self.method,
                                             self.total_value,
                                             self._data_editor_class,
                                             self.wizard)
        if self.get_slave(BasePaymentMethodSlave.slave_holder):
            self.detach_slave(BasePaymentMethodSlave.slave_holder)
        self.attach_slave(BasePaymentMethodSlave.slave_holder,
                          self.payment_list)
        self.setup_payments()
        self.payment_list.connect('payment-edited',
                                  self._on_payment_list__edit_payment)

    def _setup_widgets(self):
        max_installments = self.method.max_installments
        self.installments_number.set_range(1, max_installments)
        has_installments = (self._installments_number and
                            self._installments_number > 1 or False)

        self.intervals.set_range(1, 99)
        self.intervals.set_sensitive(has_installments)

        items = [(label, constant)
                 for constant, label in interval_types.items()]
        self.interval_type_combo.prefill(items)
        self.interval_type_combo.select_item_by_data(INTERVALTYPE_MONTH)
        self.interval_type_combo.set_sensitive(has_installments)

        # PaymentListSlave setup
        self._setup_payment_list()

    def _get_total_amount(self):
        """Returns the order total amount """
        if isinstance(self.order, Sale):
            return self.order.get_total_sale_amount()
        elif isinstance(self.order, PurchaseOrder):
            return self.order.get_purchase_total()
        elif isinstance(self.order, PaymentRenegotiation):
            return self.order.total
        else:
            raise TypeError

    def _get_payment_method_iface(self):
        if isinstance(self.order, Sale):
            return IInPayment
        elif isinstance(self.order, PurchaseOrder):
            return IOutPayment
        elif isinstance(self.order, PaymentRenegotiation):
            return IInPayment
        else:
            raise TypeError

    def _create_payments(self):
        """Insert the payment_list's payments in the base."""
        return self.payment_list.create_payments()

    #
    # Public API
    #

    def setup_payments(self):
        """Setup the payments in PaymentList.

        Note: The payments are not inserted into the db until self.finish()
        is called. The wizard is responsable for that"""
        if not self.model.first_duedate:
            return
        if self.payment_list:
            self.payment_list.add_payments(self.model.installments_number,
                                           self.model.first_duedate,
                                           self.model.intervals,
                                           self.model.interval_type)
        self.update_view()

    def update_view(self):
        self._refresh_next()

    def get_interest_total(self):
        return self.interest_total

    #
    # PaymentMethodStep hooks
    #

    def finish(self):
        """This method is called by the wizard when going to a next step.
        If it returns False, the wizard can't go on."""
        if (not self.payment_list or
            not self.payment_list.is_payment_list_valid()):
            return False
        self._create_payments()

        return True

    #
    # BaseEditor Slave hooks
    #

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model,
                                    BasePaymentMethodSlave.proxy_widgets)

    def create_model(self, conn):
        return _BaseTemporaryMethodData(self._first_duedate,
                                        self._installments_number)

    #
    # Kiwi callbacks
    #

    def _on_payment_list__edit_payment(self, *args):
        """Callback for the 'payment-edited' signal on PaymentListSlave"""
        self.update_view()

    def after_installments_number__changed(self, *args):
        has_installments = self.model.installments_number > 1

        self.interval_type_combo.set_sensitive(has_installments)
        self.intervals.set_sensitive(has_installments)
        self.setup_payments()

    def after_intervals__changed(self, *args):
        self.setup_payments()

    def after_interval_type_combo__changed(self, *args):
        self.setup_payments()

    def after_first_duedate__changed(self, *args):
        self.setup_payments()

    def on_installments_number__validate(self, widget, value):
        if not value:
            return ValidationError(_("The number of installments "
                                     "cannot be 0"))

        max_installments = self.method.max_installments
        if value > max_installments:
            return ValidationError(_("The number of installments "
                                     "must be less then %d") %
                                     max_installments)

    def on_first_duedate__validate(self, widget, value):
        if sysparam(self.conn).ALLOW_OUTDATED_OPERATIONS:
            return

        if value < datetime.date.today():
            self.payment_list.clear_payments()
            return ValidationError(_("Expected first installment date must be "
                                     "set to a future date"))


class BillMethodSlave(BasePaymentMethodSlave):
    _data_editor_class = BasePaymentDataEditor

    def __init__(self, wizard, parent, conn, sale, payment_method,
                 outstanding_value=currency(0),
                 first_duedate=None, installments_number=None):
        BasePaymentMethodSlave.__init__(self, wizard, parent, conn,
                                        sale, payment_method,
                                        outstanding_value=outstanding_value,
                                        installments_number=installments_number,
                                        first_duedate=first_duedate)
        self.bank_label.hide()
        self.bank_combo.hide()


class CheckMethodSlave(BasePaymentMethodSlave):
    _data_editor_class = CheckDataEditor

    def _setup_widgets(self):
        printer = get_current_cheque_printer_settings(self.conn)
        if not printer:
            self.bank_combo.hide()
            self.bank_label.hide()
        else:
            banks = printer.get_banks()
            items = [("%s - %s" % (code, bank.name), code)
                     for code, bank in banks.items()]
            self.bank_combo.prefill(items)
        BasePaymentMethodSlave._setup_widgets(self)


class MoneyMethodSlave(BasePaymentMethodSlave):
    model_type = _BaseTemporaryMethodData
    _data_editor_class = BasePaymentDataEditor

    def __init__(self, wizard, parent, conn, sale, payment_method,
                 outstanding_value=currency(0),
                 first_duedate=None, installments_number=None):
        BasePaymentMethodSlave.__init__(self, wizard, parent, conn,
                                        sale, payment_method,
                                        outstanding_value=outstanding_value,
                                        installments_number=installments_number,
                                        first_duedate=first_duedate)
        self.bank_label.hide()
        self.bank_combo.hide()
        self.first_duedate_lbl.hide()
        self.first_duedate.hide()
        self.intervals_lbl.hide()
        self.intervals.hide()
        self.interval_type_combo.hide()
        self.installments_number_lbl.hide()
        self.installments_number.hide()


class DepositMethodSlave(BasePaymentMethodSlave):
    model_type = _BaseTemporaryMethodData
    _data_editor_class = BasePaymentDataEditor

    def __init__(self, wizard, parent, conn, sale, payment_method,
                 outstanding_value=currency(0),
                 first_duedate=None, installments_number=None):
        BasePaymentMethodSlave.__init__(self, wizard, parent, conn,
                                        sale, payment_method,
                                        outstanding_value=outstanding_value,
                                        installments_number=installments_number,
                                        first_duedate=first_duedate)
        self.bank_combo.hide()
        self.bank_label.hide()


class StoreCreditMethodSlave(BasePaymentMethodSlave):
    model_type = _BaseTemporaryMethodData
    _data_editor_class = BasePaymentDataEditor

    def __init__(self, wizard, parent, conn, total_amount,
                 payment_method, outstanding_value=currency(0),
                 first_duedate=None, installments_number=None):
        BasePaymentMethodSlave.__init__(self, wizard, parent, conn,
                                        total_amount, payment_method,
                                        outstanding_value=outstanding_value,
                                        installments_number=installments_number,
                                        first_duedate=first_duedate)
        self.bank_label.hide()
        self.bank_combo.hide()
        self.first_duedate_lbl.hide()
        self.first_duedate.hide()


class CardMethodSlave(BaseEditorSlave):
    """A base payment method slave for card and finance methods.
    Available slaves are: CardMethodSlave
    """

    gladefile = 'CreditProviderMethodSlave'
    model_type = _TemporaryCreditProviderGroupData
    proxy_widgets = ('credit_provider', 'installments_number')

    def __init__(self, wizard, parent, conn, order, payment_method,
                 outstanding_value=currency(0), first_duedate=None,
                 installments_number=None):
        self.model = order
        self.wizard = wizard
        self.method = payment_method
        self._payment_group = self.model.group
        self.total_value = (outstanding_value or
                            self._get_total_amount())
        self.providers = self._get_credit_providers()
        self._selected_type = CreditCardData.TYPE_CREDIT
        BaseEditorSlave.__init__(self, conn)
        self.register_validate_function(self._refresh_next)
        self.parent = parent
        self._order = order

        # this will change after the payment type is changed
        self.installments_number.set_range(1, 1)
        self._refresh_next(False)

    #
    # PaymentMethodStep hooks
    #

    def finish(self):
        self._setup_payments()
        return True

    def update_view(self):
        pass

    #
    # BaseEditor Slave hooks
    #

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)

        # Workaround for a kiwi bug. report me
        self.credit_provider.select_item_by_position(1)
        self.credit_provider.select_item_by_position(0)

    def create_model(self, conn):
        if not self.providers:
            raise ValueError('You must have credit providers information '
                             'stored in the database before start doing '
                             'sales')
        return _TemporaryCreditProviderGroupData(provider=None)

    # Private

    def _get_total_amount(self):
        if isinstance(self.model, Sale):
            return self.model.get_total_sale_amount()
        elif isinstance(self.model, PaymentRenegotiation):
            return self.model.total
        else:
            raise TypeError

    def _setup_widgets(self):
        provider_items = [(p.short_name, p) for p in self.providers]
        self.credit_provider.prefill(provider_items)

        self._radio_group = None

        for ptype, name in CreditCardData.types.items():
            self._add_card_type(name, ptype)

    def _add_card_type(self, name, payment_type):
        radio = gtk.RadioButton(self._radio_group, name)
        radio.set_data('type', payment_type)
        radio.connect('toggled', self._on_card_type_radio_toggled)
        self.types_box.pack_start(radio)
        radio.show()

        if self._radio_group is None:
            self._radio_group = radio

    def _on_card_type_radio_toggled(self, radio):
        if not radio.get_active():
            return

        self._selected_type = radio.get_data('type')
        self._setup_max_installments()

    def _refresh_next(self, validation_ok=True):
        validation_ok = validation_ok and self.model.installments_number
        self.wizard.refresh_next(validation_ok)

    def _setup_max_installments(self):
        type = self._selected_type
        maximum = 1

        if type == CreditCardData.TYPE_CREDIT_INSTALLMENTS_STORE:
            maximum = self.method.max_installments
        elif type == CreditCardData.TYPE_CREDIT_INSTALLMENTS_PROVIDER:
            maximum = self.model.provider.max_installments

        if maximum > 1:
            minimum = 2
        else:
            minimum = 1

        self.installments_number.set_range(minimum, maximum)
        self.installments_number.set_sensitive(maximum != 1)

    def _setup_payments(self):
        provider = self.model.provider
        payment_type = self._selected_type
        due_dates = []
        first_duedate = datetime.datetime.today()
        for i in range(self.model.installments_number):
            if first_duedate.day > provider.closing_day:
                first_duedate += relativedelta(months=+1)
            due_dates.append(first_duedate.replace(day=provider.payment_day))
            first_duedate += relativedelta(months=+1)

        if isinstance(self._order, PurchaseOrder):
            payments = self.method.create_outpayments(self._payment_group,
                                                     self.total_value, due_dates)
        else:
            payments = self.method.create_inpayments(self._payment_group,
                                                     self.total_value, due_dates)

        operation = self.method.operation
        for payment in payments:
            adapted = payment.get_adapted()
            data = operation.get_card_data_by_payment(adapted)
            data.card_type = payment_type
            data.provider = provider
            data.fee = provider.get_fee_for_payment(provider, data)
            data.fee_value = data.fee * adapted.value / 100

    def _get_credit_providers(self):
        return PersonAdaptToCreditProvider.get_card_providers(
            self.method.get_connection())

    #
    #   Callbacks
    #

    def on_credit_provider__changed(self, combo):
        self._setup_max_installments()

    def on_installments_number__validate(self, entry, installments):
        max_installments = self.installments_number.get_range()[1]
        min_installments = self.installments_number.get_range()[0]
        if not min_installments <= installments <= max_installments:
            return ValidationError(_(u'Number of installments must be greater '
                                      'than %d and lower than %d')
                                      % (min_installments, max_installments))


class _MultipleMethodEditor(BaseEditor):
    """A generic editor that attaches a payment method slave in a toplevel
    window.
    """

    gladefile = 'HolderTemplate'
    model_type = PaymentGroup
    model_name = _(u'Payment')
    size = (600, 375)

    def __init__(self, wizard, parent, conn, order, payment_method,
                 outstanding_value=currency(0)):
        BaseEditor.__init__(self, conn, order.group)

        self._method = payment_method
        dsm = get_utility(IDomainSlaveMapper)
        slave_class = dsm.get_slave_class(self._method)
        assert slave_class

        self.conn.savepoint('before_payment_creation')

        #FIXME: This is a workaround to make the slave_class to ignore the
        #       payments created previously.
        class _InnerSlaveClass(slave_class):
            def get_created_adapted_payments(self):
                return []

        self.slave = _InnerSlaveClass(wizard, parent, self.conn, order,
                                      self._method, outstanding_value)
        #FIXME: We need to control how many payments could be created, since
        #       we are ignoring the payments created previously.
        payments = order.group.get_valid_payments().filter(
                                        Payment.q.methodID == self._method.id)
        max_installments = self._method.max_installments - payments.count()
        self.slave.installments_number.set_range(1, max_installments)

        self.attach_slave('place_holder', self.slave)

    def validate_confirm(self):
        return self.slave.finish()

    def on_cancel(self):
        self.conn.rollback_to_savepoint('before_payment_creation')
        return False


class MultipleMethodSlave(BaseEditorSlave):
    """A base payment method slave for multiple payments."""
    gladefile = 'MultipleMethodSlave'
    model_type = object

    def __init__(self, wizard, parent, conn, order, payment_method,
                 outstanding_value=currency(0), finish_on_total=True):
        """
        @param finish_on_total: finalize the payment when the total value is
                                reached.
        """
        self.finish_on_total = finish_on_total
        # We need a temporary object to hold the value that will be read from
        # the user. We will set a proxy with this temporary object to help
        # with the validation.
        self._holder = Settable(value=Decimal(0))
        self._wizard = wizard
        # 'money' is the default payment method and it is always avaliable.
        self._method = PaymentMethod.get_by_name(conn, 'money')

        BaseEditorSlave.__init__(self, conn, order)
        self._outstanding_value = (outstanding_value or
                                   self._get_total_amount())
        self._total_value = self._outstanding_value
        self._setup_widgets()

    def setup_proxies(self):
        self._proxy = self.add_proxy(self._holder, ['base_value'])

    # The two methods below are required to be a payment method slave without
    # inheriting BasePaymentMethodSlave.

    def update_view(self):
        # The user can only confirm the payments if there is no value left.
        can_confirm = self.can_confirm()

        self._wizard.refresh_next(can_confirm)
        # If this is a sale wizard, we cannot go back after payments have
        # started being created.
        if len(self.payments) > 0:
            self._wizard.disable_back()

    def finish(self):
        # All the payments are created in slaves. We still need to return
        # True so the wizard can finish
        return True

    #
    # Private
    #

    def _get_total_amount(self):
        if isinstance(self.model, Sale):
            return self.model.get_total_sale_amount()
        elif isinstance(self.model, PaymentRenegotiation):
            return self.model.total
        elif isinstance(self.model, PurchaseOrder):
            # If it is a purchase, consider the total amount as the total of
            # payments, since it includes surcharges and discounts, and may
            # include the freight (the freight can also be in a different
            # payment group - witch should not be considered here.)
            return self.model.group.get_total_value()
        else:
            raise TypeError

    def _setup_widgets(self):
        self.remove_button.hide()
        self.cash_radio.connect('toggled', self._on_method__toggled)
        self.cash_radio.set_data('method', self._method)
        for method in ['bill', 'check', 'card', 'store_credit',
                       'deposit']:
            self._add_method(PaymentMethod.get_by_name(self.conn, method))

        self.payments.set_columns(self._get_columns())
        self.payments.add_list(self.model.group.get_items())

        self.total_value.set_bold(True)
        self.received_value.set_bold(True)
        self.missing_value.set_bold(True)
        self.total_value.update(self._total_value)
        self.remove_button.set_sensitive(False)
        self._update_values()

    def toggle_new_payments(self):
        """Toggle new payments addition interface.

        This method verifies if its possible to add more payments (if the
        total value is already reached), and enables or disables the value
        entry and add button.
        """
        self.base_value.set_sensitive(not self.can_confirm())
        self.add_button.set_sensitive(not self.can_confirm())

    def _update_values(self):
        payments = self.model.group.get_valid_payments()
        total_payments = payments.sum('base_value') or Decimal(0)
        self._outstanding_value = self._total_value - total_payments
        self.toggle_new_payments()

        if self._outstanding_value > 0:
            self.base_value.update(self._outstanding_value)
        else:
            self.base_value.update(0)
            self._outstanding_value = 0

        self.received_value.update(total_payments)
        self._update_missing_or_change_value()
        self.base_value.grab_focus()

    def _update_missing_or_change_value(self):
        received = self.received_value.read()
        if received == ValueUnset:
            received = currency(0)

        new_payment = self.base_value.read()
        if new_payment == ValueUnset:
            new_payment = currency(0)

        total_received = received + new_payment

        # The total value may be less than total received.
        value = self._total_value - total_received
        self.missing_value.update(abs(value))
        if value > 0:
            self.missing_change.set_text(_(u'Missing:'))
        else:
            self.missing_change.set_text(_(u'Change:'))

    def _get_columns(self):
        return [Column('description', title=_(u'Description'), data_type=str,
                        expand=True, sorted=True),
                Column('status_str', title=_('Status'), data_type=str,
                       width=80),
                Column('value', title=_(u'Value'), data_type=currency),
                Column('due_date', title=_('Due date'),
                        data_type=datetime.date)]

    def _add_method(self, payment_method):
        if not payment_method.is_active:
            return

        # bill and store_credit payment method is not allowed without a client.
        if (payment_method.method_name == 'bill' or
            payment_method.method_name == 'store_credit'):
            if (not isinstance(self.model, PurchaseOrder) and
                self.model.client is None):
                return
            elif (isinstance(self.model, PurchaseOrder) and
                  payment_method.method_name == 'store_credit'):
                return

        radio = gtk.RadioButton(self.cash_radio,
                                payment_method.get_description())
        self.methods_box.pack_start(radio)
        radio.connect('toggled', self._on_method__toggled)
        radio.set_data('method', payment_method)
        radio.show()

    def _can_add_payment(self):
        if self.base_value.read() is ValueUnset:
            return False

        if self._outstanding_value <= 0:
            return False

        payments = self.model.group.get_valid_payments()
        payment_count = payments.filter(
            Payment.q.methodID == self._method.id).count()
        if payment_count >= self._method.max_installments:
            info(_(u'You can not add more payments using the %s '
                   'payment method.') % self._method.description)
            return False

        if self._method.method_name == 'store_credit':
            client = self.model.client
            credit = client.remaining_store_credit
            total = self._holder.value

            if credit < total:
                info(_(u"Client %s does not have enought credit left.") % \
                     client.person.name)
                return False

        return True

    def _add_payment(self):
        assert self._method

        if not self._can_add_payment():
            return

        if self._method.method_name == 'money':
            self._setup_cash_payment()

        # We are about to create payments, so we need to consider the fiscal
        # printer and its operations.
        # See salewizard.SalesPersonStep.on_next_step for details.
        # (We only emit this event for sales.)
        if not isinstance(self.model, PurchaseOrder):
            retval = CreatePaymentEvent.emit(self._method, self.model,
                                             self.conn, self._holder.value)
        else:
            retval = None

        if retval is None or retval == CreatePaymentStatus.UNHANDLED:
            if not self._method.method_name == 'money':
                self._run_payment_editor()

        self._update_payment_list()
        # Exigência do TEF: Deve finalizar ao chegar no total da venda.
        if self.finish_on_total and self._outstanding_value == 0:
            self._wizard.finish()
        # Keep update_view after force_validation, since it can disable
        # next/finish even if validation is ok
        self.force_validation()
        self.update_view()

    def _remove_payment(self, payment):
        if payment.is_preview():
            payment.group.remove_item(payment)
            Payment.delete(payment.id, connection=self.conn)
        elif payment.is_paid():
            entry = PaymentChangeHistory(payment=payment,
                             change_reason=_('Payment renegotiated'),
                             connection=self.conn)
            payment.set_not_paid(entry)
            entry.new_status = Payment.STATUS_CANCELLED
            payment.cancel()
        else:
            payment.cancel()

        self._update_payment_list()
        # Keep update_view after force_validation, since it can disable
        # next/finish even if validation is ok
        self.force_validation()
        self.update_view()

    def _setup_cash_payment(self):
        has_change_value = self._holder.value - self._outstanding_value > 0
        if has_change_value:
            payment_value = self._outstanding_value
        else:
            payment_value = self._holder.value

        if isinstance(self.model, PurchaseOrder):
            payment = self._method.create_outpayment(
                self.model.group, payment_value).get_adapted()
        else:
            payment = self._method.create_inpayment(
                self.model.group, payment_value).get_adapted()
        # We have to modify the payment, so the fiscal printer can calculate
        # and print the change.
        payment.base_value = self._holder.value

        return True

    def _update_payment_list(self):
        # We reload all the payments each time we update the list. This will
        # avoid the validation of each payment (add or update) and allow us to
        # rename the payments at runtime.
        self.payments.clear()
        payment_group = self.model.group
        payments = payment_group.get_items()
        npayments = payments.count()

        for i, payment in enumerate(payments.orderBy('id')):
            description = payment.method.describe_payment(payment_group, i + 1,
                                                          npayments)
            payment.description = description
            self.payments.append(payment)

        self._update_values()

    def _run_payment_editor(self):
        if self._wizard:
            toplevel = self._wizard.get_toplevel()
        else:
            toplevel = None
        retval = run_dialog(_MultipleMethodEditor, toplevel, self._wizard,
                            self, self.conn, self.model, self._method,
                            self._holder.value)
        return retval

    #
    #   Public API
    #

    def enable_remove(self):
        self.remove_button.show()

    def can_confirm(self):
        return self._outstanding_value == 0

    #
    # Callbacks
    #

    def _on_method__toggled(self, radio):
        if not radio.get_active():
            return

        self._method = radio.get_data('method')
        self.base_value.validate(force=True)
        self.base_value.grab_focus()

    def on_add_button__clicked(self, widget):
        self._add_payment()

    def on_remove_button__clicked(self, button):
        payments = self.payments.get_selected_rows()
        for payment in payments:
            if not payment.is_cancelled():
                self._remove_payment(payment)

    def on_payments__selection_changed(self, objectlist, payment):
        has_payments = len(objectlist) > 0
        self.remove_button.set_sensitive(has_payments)

    def on_base_value__activate(self, entry):
        if self.add_button.get_sensitive():
            self._add_payment()

    def on_base_value__changed(self, entry):
        try:
            entry.read()
        except ValidationError, e:
            self.add_button.set_sensitive(False)
            return e
        self._update_missing_or_change_value()

    def on_base_value__validate(self, entry, value):
        retval = None
        if value < 0:
            retval = ValidationError(_(u'The value must be greater than zero.'))

        if self._outstanding_value < 0:
            self._outstanding_value = 0

        is_money_method = self._method and self._method.method_name == 'money'
        if self._outstanding_value - value < 0 and not is_money_method:
            retval = ValidationError(_(u'The value must be lesser than the '
                                       'missing value.'))

        if not value and self._outstanding_value > 0:
            retval = ValidationError(_(u'You must provide a payment value.'))

        self._holder.value = value
        self.toggle_new_payments()
        if not self.can_confirm():
            self.add_button.set_sensitive(not bool(retval))

        return retval


def register_payment_slaves():
    dsm = get_utility(IDomainSlaveMapper)
    conn = api.get_connection()
    for method_name, slave_class in [
        ('bill', BillMethodSlave),
        ('check', CheckMethodSlave),
        ('card', CardMethodSlave),
        ('store_credit', StoreCreditMethodSlave),
        ('multiple', MultipleMethodSlave),
        ('deposit', DepositMethodSlave)]:

        method = PaymentMethod.get_by_name(conn, method_name)
        dsm.register(method, slave_class)
