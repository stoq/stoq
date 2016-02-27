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
"""Slaves for payment creation

This slaves will be used when payments are being created.
"""

from copy import deepcopy
import datetime
from decimal import Decimal

from dateutil.relativedelta import relativedelta
import gtk
from kiwi import ValueUnset
from kiwi.component import get_utility
from kiwi.currency import format_price, currency
from kiwi.datatypes import ValidationError, converter
from kiwi.python import Settable
from kiwi.utils import gsignal
from kiwi.ui.delegates import GladeSlaveDelegate
from kiwi.ui.objectlist import Column

from stoqlib.api import api
from stoqlib.domain.events import CreatePaymentEvent
from stoqlib.domain.payment.card import CreditProvider, CreditCardData
from stoqlib.domain.payment.card import CardPaymentDevice
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment, PaymentChangeHistory
from stoqlib.domain.payment.renegotiation import PaymentRenegotiation
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.domain.returnedsale import ReturnedSale
from stoqlib.domain.sale import Sale
from stoqlib.domain.stockdecrease import StockDecrease
from stoqlib.enums import CreatePaymentStatus
from stoqlib.exceptions import SellError, PaymentMethodError
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.baseeditor import BaseEditorSlave, BaseEditor
from stoqlib.gui.interfaces import IDomainSlaveMapper
from stoqlib.lib.dateutils import (INTERVALTYPE_MONTH,
                                   get_interval_type_items,
                                   create_date_interval,
                                   localdatetime,
                                   localtoday,
                                   localnow)
from stoqlib.lib.defaults import DECIMAL_PRECISION
from stoqlib.lib.message import info, warning
from stoqlib.lib.payment import generate_payments_values
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.pluginmanager import get_plugin_manager
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
        self.first_duedate = first_duedate or localtoday().date()
        self.installments_number = (installments_number or
                                    DEFAULT_INSTALLMENTS_NUMBER)
        self.intervals = DEFAULT_INTERVALS
        self.interval_type = DEFAULT_INTERVAL_TYPE
        self.auth_number = None
        self.bank_id = None
        self.bank_branch = None
        self.bank_account = None
        self.bank_first_check_number = None


class _TemporaryCreditProviderGroupData(_BaseTemporaryMethodData):
    def __init__(self, provider=None, device=None):
        self.provider = provider
        self.device = device
        _BaseTemporaryMethodData.__init__(self)


class _TemporaryPaymentData(object):
    def __init__(self, description, value, due_date,
                 payment_number=None, bank_account=None):
        self.description = description
        self.value = value
        self.due_date = due_date
        self.payment_number = payment_number
        self.bank_account = bank_account

    def __repr__(self):
        return '<_TemporaryPaymentData>'


class _TemporaryBankData(object):
    def __init__(self, bank_number=None, bank_branch=None, bank_account=None):
        self.bank_number = bank_number
        self.bank_branch = bank_branch
        self.bank_account = bank_account


#
# Editors
#

class _BasePaymentDataEditor(BaseEditor):
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
        if sysparam.get_bool('ALLOW_OUTDATED_OPERATIONS'):
            return

        if value < localtoday().date():
            return ValidationError(_(u"Expected installment due date "
                                     "must be set to a future date"))

    def on_value__validate(self, widget, value):
        if value < currency(0):
            return ValidationError(_(u"The value must be "
                                     "a positive number"))


class CheckDataEditor(_BasePaymentDataEditor):
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

    domain = 'stoq'
    gladefile = 'PaymentListSlave'
    gsignal('payment-edited')

    def __init__(self, payment_type, group, branch, method, total_value,
                 editor_class, parent, temporary_identifiers=False):
        self.parent = parent
        self.branch = branch
        self.payment_type = payment_type
        self.group = group
        self.total_value = total_value
        self.editor_class = editor_class
        self.method = method
        self.temporary_identifiers = temporary_identifiers

        GladeSlaveDelegate.__init__(self, gladefile=self.gladefile)
        self._setup_widgets()

    #
    # Private Methods
    #

    def _can_edit_payments(self):
        return self.method.method_name != 'money'

    def _has_bank_account(self):
        return self.method.method_name == u'check'

    def _is_check_number_mandatory(self):
        return (api.sysparam.get_bool('MANDATORY_CHECK_NUMBER') and
                self._has_bank_account())

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
        if self.method.method_name != u'money':
            title = _('Number')
            # Add (*) to indicate on column Number that this information is
            # mandatory
            if self._is_check_number_mandatory():
                title += ' (*)'
            columns.append(Column('payment_number',
                                  title=title,
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
        # FIXME: Workaround to allow the check_number to be automatically added.
        # payment_number is unicode in domain, on wizard we treat it as an int
        # so we can automatically increment it and before we actually create
        # the payment it is converted to unicode. Shouldn't it be int
        # on domain?
        if payment_number is not None:
            payment_number = unicode(payment_number)

        payment = _TemporaryPaymentData(description,
                                        value,
                                        due_date.date(),
                                        payment_number,
                                        bank_account)

        self.payment_list.append(payment)

        if refresh:
            self.update_view()

    def add_payments(self, installments_number, start_date,
                     interval, interval_type, bank_id=None, bank_branch=None,
                     bank_account=None, bank_first_number=None):
        values = generate_payments_values(self.total_value,
                                          installments_number)
        due_dates = create_date_interval(interval_type=interval_type,
                                         interval=interval,
                                         count=installments_number,
                                         start_date=start_date)

        self.clear_payments()
        bank_check_number = bank_first_number

        for i in range(installments_number):

            bank_data = None
            if self._has_bank_account():
                bank_data = _TemporaryBankData(bank_id, bank_branch,
                                               bank_account)

            description = self.method.describe_payment(self.group, i + 1,
                                                       installments_number)

            self.add_payment(description, currency(values[i]), due_dates[i],
                             bank_check_number, bank_data, False)

            if bank_check_number is not None:
                bank_check_number += 1

        self.update_view()

    def create_payments(self):
        """Commit the payments on the list to the database"""
        if not self.is_payment_list_valid():
            return []

        payments = []
        for p in self.payment_list:
            due_date = localdatetime(p.due_date.year,
                                     p.due_date.month,
                                     p.due_date.day)
            try:
                # When creating temporary identifiers, we should use negative
                # values, but we need to get the next negative value before
                # creating the payment, otherwise there may be a conflict in the
                # database, since the payment identifier for the other branch
                # may already exist
                if self.temporary_identifiers:
                    tmp_identifier = Payment.get_temporary_identifier(self.method.store)
                else:
                    tmp_identifier = None

                payment = self.method.create_payment(
                    payment_type=self.payment_type, payment_group=self.group,
                    branch=self.branch, value=p.value, due_date=due_date,
                    description=p.description, payment_number=p.payment_number)
                if tmp_identifier:
                    payment.identifier = tmp_identifier
            except PaymentMethodError as err:
                warning(str(err))
                return

            if p.bank_account:
                # Add the bank_account into the payment, if any.
                bank_account = payment.check_data.bank_account
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
        if sysparam.get_bool('ALLOW_OUTDATED_OPERATIONS'):
            return True

        previous_date = localtoday().date() + datetime.timedelta(days=-1)
        for payment in self.payment_list:
            if payment.due_date <= previous_date:
                warning(_(u"Payment dates can't repeat or be lower than "
                          "previous dates."))
                return False
            previous_date = payment.due_date
        return True

    def are_payment_values_valid(self):
        return not self.get_total_difference()

    def is_check_number_valid(self):
        """Verify if check number is set"""
        if not self._is_check_number_mandatory():
            return True

        for p in self.payment_list:
            if p.payment_number is None or p.payment_number == u'':
                return False
        return True

    def is_payment_list_valid(self):
        if not self.are_due_dates_valid():
            return False
        if not self.are_payment_values_valid():
            return False
        if not self.is_check_number_valid():
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
    data_editor_class = _BasePaymentDataEditor
    slave_holder = 'slave_holder'
    proxy_widgets = ('interval_type_combo',
                     'intervals',
                     'first_duedate',
                     'installments_number',
                     'bank_id',
                     'bank_branch',
                     'bank_account',
                     'bank_first_check_number')

    def __init__(self, wizard, parent, store, order_obj, payment_method,
                 outstanding_value=currency(0), first_duedate=None,
                 installments_number=None, temporary_identifiers=False):
        self.wizard = wizard
        self.parent = parent
        # Note that 'order' may be a Sale or a PurchaseOrder object
        self.order = order_obj
        self.method = payment_method
        self.payment_type = self._get_payment_type()
        self.total_value = outstanding_value or self._get_total_amount()
        self.payment_group = self.order.group
        self.payment_list = None
        self.temporary_identifiers = temporary_identifiers

        # This is very useful when calculating the total amount outstanding
        # or overpaid of the payments
        self.interest_total = currency(0)

        self._first_duedate = first_duedate
        self._installments_number = installments_number

        BaseEditorSlave.__init__(self, store)
        self.register_validate_function(self._refresh_next)

        # Most of slaves don't have bank information
        self._set_bank_widgets_visible(False)

        self.bank_first_check_number.set_sensitive(True)

    #
    # Private Methods
    #

    def _set_bank_widgets_visible(self, visible=True):
        self.bank_info_box.set_visible(visible)

    def _clear_if_unset(self, widget, attr):
        # FIXME: When the widget goes from not empty and valid to empty, its
        # .read() method returns ValueUnset (int datatype behaviour), which
        # makes the proxy not update the model, leaving the old value behind
        try:
            is_unset = widget.read() == ValueUnset
        except ValidationError:
            is_unset = True

        if is_unset:
            setattr(self.model, attr, None)
            self.setup_payments()

    def _refresh_next(self, validation_ok=True):
        if not self.payment_list:
            validation_ok = False
        if validation_ok:
            validation_ok = self.payment_list.is_payment_list_valid()

        self.wizard.refresh_next(validation_ok)

    def _setup_payment_list(self):
        self.payment_list = PaymentListSlave(self.payment_type,
                                             self.payment_group,
                                             self.order.branch,
                                             self.method,
                                             self.total_value,
                                             self.data_editor_class,
                                             self.wizard,
                                             self.temporary_identifiers)
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

        interval_types = get_interval_type_items(plural=True)
        self.interval_type_combo.prefill(interval_types)
        self.interval_type_combo.select_item_by_data(INTERVALTYPE_MONTH)
        self.interval_type_combo.set_sensitive(has_installments)
        if self.method.method_name == 'check':
            check_mandatory = sysparam.get_bool('MANDATORY_CHECK_NUMBER')
            self.bank_first_check_number.set_property('mandatory', check_mandatory)

        # PaymentListSlave setup
        self._setup_payment_list()

    def _get_total_amount(self):
        """Returns the order total amount """
        if isinstance(self.order, Sale):
            return self.order.get_total_sale_amount()
        elif isinstance(self.order, ReturnedSale):
            return self.model.sale_total
        elif isinstance(self.order, PurchaseOrder):
            return self.order.purchase_total
        elif isinstance(self.order, PaymentRenegotiation):
            return self.order.total
        else:
            raise TypeError

    def _get_payment_type(self):
        # FIXME: Is it right to consider only PurchaseOrder as TYPE_OUT?
        # Maybe we should add an interface on order objects for them to
        # decide which type of payment would be created here
        if isinstance(self.order, PurchaseOrder):
            return Payment.TYPE_OUT
        else:
            return Payment.TYPE_IN

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
                                           self.model.interval_type,
                                           self.model.bank_id,
                                           self.model.bank_branch,
                                           self.model.bank_account,
                                           self.model.bank_first_check_number)
        self.update_view()

    def update_view(self):
        self._refresh_next()

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

    def has_next_step(self):
        return False

    def next_step(self):
        return None

    #
    # BaseEditor Slave hooks
    #

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model,
                                    BasePaymentMethodSlave.proxy_widgets)

    def create_model(self, store):
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

    def after_bank_id__changed(self, widget):
        self._clear_if_unset(widget, 'bank_id')
        self.setup_payments()

    def after_bank_branch__changed(self, widget):
        self._clear_if_unset(widget, 'bank_branch')
        self.setup_payments()

    def after_bank_account__changed(self, widget):
        self._clear_if_unset(widget, 'bank_account')
        self.setup_payments()

    def after_bank_first_check_number__changed(self, widget):
        self._clear_if_unset(widget, 'bank_first_check_number')
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
        if sysparam.get_bool('ALLOW_OUTDATED_OPERATIONS'):
            return

        if value < datetime.date.today():
            self.payment_list.clear_payments()
            return ValidationError(_("Expected first installment date must be "
                                     "set to a future date"))


class BillMethodSlave(BasePaymentMethodSlave):
    """Bill method slave"""


class CheckMethodSlave(BasePaymentMethodSlave):
    """Check method slave"""

    data_editor_class = CheckDataEditor

    def __init__(self, wizard, parent, store, total_amount,
                 payment_method, outstanding_value=currency(0),
                 first_duedate=None, installments_number=None,
                 temporary_identifiers=False):
        BasePaymentMethodSlave.__init__(self, wizard, parent, store,
                                        total_amount, payment_method,
                                        outstanding_value=outstanding_value,
                                        installments_number=installments_number,
                                        first_duedate=first_duedate,
                                        temporary_identifiers=temporary_identifiers)
        self._set_bank_widgets_visible(True)


class DepositMethodSlave(BasePaymentMethodSlave):
    """Deposit method slave"""


class StoreCreditMethodSlave(BasePaymentMethodSlave):
    """Store credit method slave"""


class MoneyMethodSlave(BasePaymentMethodSlave):
    """Money method slave"""


class CreditMethodSlave(BasePaymentMethodSlave):
    """Credit method slave"""


class CardMethodSlave(BaseEditorSlave):
    """A base payment method slave for card and finance methods.
    Available slaves are: CardMethodSlave
    """

    gladefile = 'CreditProviderMethodSlave'
    model_type = _TemporaryCreditProviderGroupData
    proxy_widgets = ('card_device', 'credit_provider', 'installments_number',
                     'auth_number')

    def __init__(self, wizard, parent, store, order, payment_method,
                 outstanding_value=currency(0)):
        self.order = order
        self.wizard = wizard
        self.method = payment_method
        self._payment_group = self.order.group
        self.total_value = (outstanding_value or
                            self._get_total_amount())
        self._selected_type = CreditCardData.TYPE_CREDIT
        BaseEditorSlave.__init__(self, store)
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
        self._refresh_next()

    def has_next_step(self):
        return False

    #
    # BaseEditor Slave hooks
    #

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)

        # Workaround for a kiwi bug. report me
        self.credit_provider.select_item_by_position(1)
        self.credit_provider.select_item_by_position(0)

        is_mandatory = sysparam.get_bool('MANDATORY_CARD_AUTH_NUMBER')
        self.auth_number.set_property('mandatory', is_mandatory)

    def create_model(self, store):
        if store.find(CardPaymentDevice).is_empty():
            raise ValueError('You must have card devices registered '
                             'before start doing sales')

        providers = CreditProvider.get_card_providers(
            self.method.store)
        if providers.count() == 0:
            raise ValueError('You must have credit providers information '
                             'stored in the database before start doing '
                             'sales')
        return _TemporaryCreditProviderGroupData(provider=None)

    # Private

    def _get_total_amount(self):
        if isinstance(self.order, Sale):
            return self.order.get_total_sale_amount()
        elif isinstance(self.order, ReturnedSale):
            return self.model.sale_total
        elif isinstance(self.order, PaymentRenegotiation):
            return self.order.total
        else:
            raise TypeError

    def _setup_widgets(self):
        devices = CardPaymentDevice.get_devices(self.method.store)
        self.card_device.prefill(api.for_combo(devices))

        providers = CreditProvider.get_card_providers(
            self.method.store)
        self.credit_provider.prefill(api.for_combo(providers))

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

    def _validate_auth_number(self):
        is_auth_number_mandatory = sysparam.get_bool('MANDATORY_CARD_AUTH_NUMBER')
        if is_auth_number_mandatory and self.auth_number.read() == ValueUnset:
            return False
        return True

    def _refresh_next(self, validation_ok=True):
        validation_ok = (validation_ok and self.model.installments_number and
                         self._validate_auth_number())

        self.wizard.refresh_next(validation_ok)

    def _setup_max_installments(self):
        type = self._selected_type
        maximum = 1

        if type == CreditCardData.TYPE_CREDIT_INSTALLMENTS_STORE:
            maximum = self.method.max_installments
        elif type == CreditCardData.TYPE_CREDIT_INSTALLMENTS_PROVIDER:
            provider = self.credit_provider.read()
            if self.credit_provider is not None:
                # If we have a credit provider, use the limit from that provider,
                # otherwise fallback to the payment method.
                maximum = provider.max_installments
            else:
                maximum = self.method.max_installments

        if maximum > 1:
            minimum = 2
        else:
            minimum = 1

        # Use set_editable instead of set_sensitive so that the invalid state
        # disables the finish
        self.installments_number.set_editable(maximum != 1)

        # TODO: Prevent validation signal here to avoid duplicate effort
        self.installments_number.set_range(minimum, maximum)
        self.installments_number.validate(force=True)

    def _update_card_device(self):
        provider = self.credit_provider.get_selected()
        if provider and provider.default_device:
            self.card_device.update(provider.default_device)

    def _get_payment_details(self, cost=None):
        """Given the current state of this slave, this method will return a
        tuple containing:

        - The due date of the first payment. All other payments will have a one
          month delta
        - The fee (percentage) of the payments
        - The fare (fixed cost) of the payments

        The state considered is:

        - Selected card device
        - Selected card provider
        - Selected card type
        - Number of installments
        """
        # If its a purchase order, the due date is today, and there is no fee
        # and fare
        if isinstance(self._order, PurchaseOrder):
            return localnow(), 0, 0

        # If there is no configuration for this payment settings, still let the
        # user sell, but there will be no automatic calculation of the first due
        # date and any other cost related to the payment.
        if cost:
            payment_days = cost.payment_days
        else:
            payment_days = 0

        today = localnow()
        first_duedate = today + relativedelta(days=payment_days)
        return first_duedate

    def _setup_payments(self):

        device = self.card_device.read()
        cost = device.get_provider_cost(provider=self.model.provider,
                                        card_type=self._selected_type,
                                        installments=self.model.installments_number)

        first_duedate = self._get_payment_details(cost)
        due_dates = []
        for i in range(self.model.installments_number):
            due_dates.append(first_duedate + relativedelta(months=i))

        if isinstance(self._order, PurchaseOrder):
            payments = self.method.create_payments(Payment.TYPE_OUT,
                                                   self._payment_group,
                                                   self.order.branch,
                                                   self.total_value, due_dates)
            return

        payments = self.method.create_payments(Payment.TYPE_IN,
                                               self._payment_group,
                                               self.order.branch,
                                               self.total_value, due_dates)

        operation = self.method.operation
        for payment in payments:
            data = operation.get_card_data_by_payment(payment)
            data.installments = self.model.installments_number
            data.auth = self.model.auth_number
            data.update_card_data(device=device,
                                  provider=self.model.provider,
                                  card_type=self._selected_type,
                                  installments=data.installments)

    #
    #   Callbacks
    #
    def on_credit_provider__changed(self, combo):
        self._setup_max_installments()
        self._update_card_device()

    def on_card_device__changed(self, combo):
        self.installments_number.validate(force=True)

    def on_installments_number__validate(self, entry, installments):
        provider = self.credit_provider.read()
        device = self.card_device.read()
        # Prevent validating in case the dialog is still beeing setup
        if ValueUnset in (device, provider, installments):
            return

        max_installments = self.installments_number.get_range()[1]
        min_installments = self.installments_number.get_range()[0]
        if not min_installments <= installments <= max_installments:
            return ValidationError(_(u'Number of installments must be greater '
                                     'than %d and lower than %d')
                                   % (min_installments, max_installments))

    def on_auth_number__validate(self, entry, value):
        if entry.get_text_length() > 6:
            return ValidationError(_("Authorization number must have 6 digits or less."))


class _MultipleMethodEditor(BaseEditor):
    """A generic editor that attaches a payment method slave in a toplevel
    window.
    """

    gladefile = 'HolderTemplate'
    model_type = PaymentGroup
    model_name = _(u'Payment')
    size = (-1, 375)

    def __init__(self, wizard, parent, store, order, payment_method,
                 outstanding_value=currency(0)):
        BaseEditor.__init__(self, store, order.group)

        self._method = payment_method
        dsm = get_utility(IDomainSlaveMapper)
        slave_class = dsm.get_slave_class(self._method)
        assert slave_class

        self.store.savepoint('before_payment_creation')

        # FIXME: This is a workaround to make the slave_class to ignore the
        #       payments created previously.
        class _InnerSlaveClass(slave_class):
            def get_created_adapted_payments(self):
                return []

        self.slave = _InnerSlaveClass(wizard, parent, self.store, order,
                                      self._method, outstanding_value)
        # FIXME: We need to control how many payments could be created, since
        #       we are ignoring the payments created previously.
        payments = order.group.get_valid_payments().find(
            Payment.method_id == self._method.id)
        max_installments = self._method.max_installments - payments.count()
        if hasattr(self.slave, 'installments_number'):
            self.slave.installments_number.set_range(1, max_installments)

        self.attach_slave('place_holder', self.slave)

    def validate_confirm(self):
        return self.slave.finish()

    def on_cancel(self):
        self.store.rollback_to_savepoint('before_payment_creation')


class MultipleMethodSlave(BaseEditorSlave):
    """A base payment method slave for multiple payments

    This slave is used to create/edit payments for an order in
    a wizard and should be attached to a step. It will have a
    list with all the order's payments and the possibility to
    remove each of them and add new ones.

    Useful to create payments in any method you want where their
    sums with the existing payments should match the total (that is,
    the ``outstanding_value`` or the model's total value). Note that
    some arguments passed to __init__ will drastically modify the
    behaviour of this slave.

    Hint: When adding an amount of money greater than the actual
    outstanding value, the actual value that will be added is
    the outstanding value, so be prepared to give some change
    """

    gladefile = 'MultipleMethodSlave'
    model_type = object

    # FIXME: Remove payment_method arg as it's not used
    def __init__(self, wizard, parent, store, order, payment_method=None,
                 outstanding_value=currency(0), finish_on_total=True,
                 allow_remove_paid=True, require_total_value=True):
        """Initializes the slave

        :param wizard: a :class:`stoqlib.gui.base.wizards.BaseWizard`
            instance
        :param parent: the parent of this slave (normally the one
            who is attaching it)
        :param store: a :class:`stoqlib.database.runtime.StoqlibStore`
            instance
        :param order: the order in question. This slave is prepared to
            handle a |sale|, |purchase|, |returnedsale|,
            |stockdecrease| and |paymentrenegotiation|
        :param payment_method: Not used. Just ignore or pass None
        :param outstanding_value: the outstanding value, that is
            the quantity still missing in payments. If not passed,
            it will be retrieved from the order directly
        :param finish_on_total: if we should finish the ``wizard`` when
            the total is reached. Note that it will finish as soon as
            payment (that reached the total) is added
        :param allow_remove_paid: if we should allow to remove (cancel)
            paid payments from the list
        :param require_total_value: if ``True``, we can only finish
            the wizard if there's no outstanding value (that is, the
            sum of all payments is equal to the total). Useful to allow
            the partial payments creation
        """
        self._require_total_value = require_total_value
        self._has_modified_payments = False
        self._allow_remove_paid = allow_remove_paid
        self.finish_on_total = finish_on_total
        # We need a temporary object to hold the value that will be read from
        # the user. We will set a proxy with this temporary object to help
        # with the validation.
        self._holder = Settable(value=Decimal(0))
        self._wizard = wizard
        # 'money' is the default payment method and it is always avaliable.
        self._method = PaymentMethod.get_by_name(store, u'money')

        self._outstanding_value = outstanding_value
        BaseEditorSlave.__init__(self, store, order)
        self._outstanding_value = (self._outstanding_value or
                                   self._get_total_amount())
        self._total_value = self._outstanding_value
        self._setup_widgets()

        self.register_validate_function(self._refresh_next)
        self.force_validation()

    def setup_proxies(self):
        self._proxy = self.add_proxy(self._holder, ['value'])

    # The two methods below are required to be a payment method slave without
    # inheriting BasePaymentMethodSlave.

    def update_view(self):
        self.force_validation()
        # If this is a sale wizard, we cannot go back after payments have
        # started being created.
        if self._has_modified_payments:
            self._wizard.disable_back()

    def finish(self):
        # All the payments are created in slaves. We still need to return
        # True so the wizard can finish
        return True

    def has_next_step(self):
        return False

    #
    # Private
    #

    def _get_total_amount(self):
        if isinstance(self.model, Sale):
            sale_total = self.model.get_total_sale_amount()
            # When editing the payments of a returned sale, we should deduct the
            # value that was already returned.
            returned_total = self.model.get_returned_value()
            return sale_total - returned_total
        elif isinstance(self.model, ReturnedSale):
            return self.model.sale_total
        elif isinstance(self.model, PaymentRenegotiation):
            return self.model.total
        elif isinstance(self.model, PurchaseOrder):
            # If it is a purchase, consider the total amount as the total of
            # payments, since it includes surcharges and discounts, and may
            # include the freight (the freight can also be in a different
            # payment group - witch should not be considered here.)
            return self.model.group.get_total_value()
        elif isinstance(self.model, StockDecrease):
            return self.model.get_total_cost()
        else:
            raise AssertionError

    def _setup_widgets(self):
        # Removing payments should only be disable when using the tef plugin
        manager = get_plugin_manager()
        if manager.is_active('tef'):
            self.remove_button.hide()

        # FIXME: Is it right to consider only PurchaseOrder as TYPE_OUT?
        # Maybe we should add an interface on order objects for them to
        # decide which type of payment would be created here
        if isinstance(self.model, PurchaseOrder):
            payment_type = Payment.TYPE_OUT
        else:
            payment_type = Payment.TYPE_IN

        # FIXME: All this code is duplicating SelectPaymentMethodSlave.
        # Replace this with it
        money_method = PaymentMethod.get_by_name(self.store, u'money')
        self._add_method(money_method, payment_type)
        for method in PaymentMethod.get_creatable_methods(
                self.store, payment_type, separate=False):
            if method.method_name in [u'multiple', u'money']:
                continue
            self._add_method(method, payment_type)

        self.payments.set_columns(self._get_columns())
        self.payments.add_list(self.model.group.payments)

        self.total_value.set_bold(True)
        self.received_value.set_bold(True)
        self.missing_value.set_bold(True)
        self.change_value.set_bold(True)
        self.total_value.update(self._total_value)
        self.remove_button.set_sensitive(False)
        self._update_values()

    def toggle_new_payments(self):
        """Toggle new payments addition interface.

        This method verifies if its possible to add more payments (if the
        total value is already reached), and enables or disables the value
        entry and add button.
        """
        can_add = self._outstanding_value != 0
        for widget in [self.value, self.add_button]:
            widget.set_sensitive(can_add)

    def _update_values(self):
        total_payments = self.model.group.get_total_value()
        self._outstanding_value = self._total_value - total_payments
        self.toggle_new_payments()

        if self.value.validate() is ValueUnset:
            self.value.update(self._outstanding_value)
        elif self._outstanding_value > 0:
            method_name = self._method.method_name
            if method_name == u'credit':
                # Set value to client's current credit or outstanding value, if
                # it's less than the available credit.
                value = min(self._outstanding_value,
                            self.model.client.credit_account_balance)
            elif method_name == u'store_credit':
                # Set value to client's current credit or outstanding value, if
                # it's less than the available credit.
                value = min(self._outstanding_value,
                            self.model.client.remaining_store_credit)
            elif method_name == 'money':
                # If the user changes method to money, keep the value he
                # already typed.
                value = self.value.read() or self._outstanding_value
            else:
                # Otherwise, default to the outstanding value.
                value = self._outstanding_value

            self.value.update(value)
        else:
            self.value.update(0)
            self._outstanding_value = 0

        self.received_value.update(total_payments)
        self._update_missing_or_change_value()
        self.value.grab_focus()

    def _update_missing_or_change_value(self):
        # The total value may be less than total received.

        value = self._get_missing_change_value(with_new_payment=True)
        missing_value = self._get_missing_change_value(with_new_payment=False)

        self.missing_value.update(abs(missing_value))

        change_value = currency(0)
        if value < 0:
            change_value = abs(value)
        self.change_value.update(change_value)

        if missing_value > 0:
            self.missing.set_text(_('Missing:'))
        elif missing_value < 0 and isinstance(self.model, ReturnedSale):
            self.missing.set_text(_('Overpaid:'))
        else:
            self.missing.set_text(_('Difference:'))

    def _get_missing_change_value(self, with_new_payment=False):
        received = self.received_value.read()

        if received == ValueUnset:
            received = currency(0)
        if with_new_payment:
            new_payment = self.value.read()
            if new_payment == ValueUnset:
                new_payment = currency(0)
            received += new_payment

        return self._total_value - received

    def _get_columns(self):
        return [Column('description', title=_(u'Description'), data_type=str,
                       expand=True, sorted=True),
                Column('status_str', title=_('Status'), data_type=str,
                       width=80),
                Column('value', title=_(u'Value'), data_type=currency),
                Column('due_date', title=_('Due date'),
                       data_type=datetime.date)]

    def _add_method(self, payment_method, payment_type):
        if not payment_method.is_active:
            return

        # some payment methods are not allowed without a client.
        if payment_method.operation.require_person(payment_type):
            if isinstance(self.model, StockDecrease):
                return
            elif (not isinstance(self.model, PurchaseOrder) and
                  self.model.client is None):
                return
            elif (isinstance(self.model, PurchaseOrder) and
                            (payment_method.method_name == 'store_credit' or
                             payment_method.method_name == 'credit')):
                return

        if (self.model.group.payer and
                (payment_method.method_name == 'store_credit' or
                 payment_method.method_name == 'credit')):
            try:
                # FIXME: If the client can pay at least 0.01 with
                # store_credit/credit, allow those methods. This is not an
                # "all or nothing" situation, since the value is being divided
                # between multiple payments
                self.model.client.can_purchase(payment_method, Decimal('0.01'))
            except SellError:
                return

        children = self.methods_box.get_children()
        if children:
            group = children[0]
        else:
            group = None
        if (payment_method.method_name == 'credit' and
            self.model.client and
            self.model.client.credit_account_balance > 0):
            credit = converter.as_string(
                currency, self.model.client.credit_account_balance)
            description = u"%s (%s)" % (payment_method.get_description(),
                                        credit)
        else:
            description = payment_method.get_description()

        radio = gtk.RadioButton(group, description)
        self.methods_box.pack_start(radio)
        radio.connect('toggled', self._on_method__toggled)
        radio.set_data('method', payment_method)
        radio.show()

        if api.sysparam.compare_object("DEFAULT_PAYMENT_METHOD",
                                       payment_method):
            radio.set_active(True)

    def _can_add_payment(self):
        if self.value.read() is ValueUnset:
            return False

        if self._outstanding_value <= 0:
            return False

        payments = self.model.group.get_valid_payments()
        payment_count = payments.find(
            Payment.method_id == self._method.id).count()
        if payment_count >= self._method.max_installments:
            info(_(u'You can not add more payments using the %s '
                   'payment method.') % self._method.description)
            return False

        # If we are creaing out payments (PurchaseOrder) or the Sale does not
        # have a client, assume all options available are creatable.
        if (isinstance(self.model, (PurchaseOrder, StockDecrease))
            or not self.model.client):
            return True

        method_values = {self._method: self._holder.value}
        for i, payment in enumerate(self.model.group.payments):
            # Cancelled payments doesn't count, and paid payments have already
            # been validated.
            if payment.is_cancelled() or payment.is_paid():
                continue
            method_values.setdefault(payment.method, 0)
            method_values[payment.method] += payment.value
        for method, value in method_values.items():
            try:
                self.model.client.can_purchase(method, value)
            except SellError as e:
                warning(str(e))
                return False

        return True

    def _add_payment(self):
        assert self._method

        if not self._can_add_payment():
            return

        if self._method.method_name == u'money':
            self._setup_cash_payment()
        elif self._method.method_name == u'credit':
            self._setup_credit_payment()

        # We are about to create payments, so we need to consider the fiscal
        # printer and its operations.
        # See salewizard.SalesPersonStep.on_next_step for details.
        # (We only emit this event for sales.)
        if not isinstance(self.model, PurchaseOrder):
            retval = CreatePaymentEvent.emit(self._method, self.model,
                                             self.store, self._holder.value)
        else:
            retval = None

        if retval is None or retval == CreatePaymentStatus.UNHANDLED:
            if not (self._method.method_name == u'money' or
                    self._method.method_name == u'credit'):
                self._run_payment_editor()

        self._has_modified_payments = True

        self._update_payment_list()
        # Exigência do TEF: Deve finalizar ao chegar no total da venda.
        if self.finish_on_total and self.can_confirm():
            self._wizard.finish()
        self.update_view()

    def _remove_payment(self, payment):
        if payment.is_preview():
            payment.group.remove_item(payment)
            payment.delete()
        elif payment.is_paid():
            if not self._allow_remove_paid:
                return
            entry = PaymentChangeHistory(payment=payment,
                                         change_reason=_(
                                             u'Payment renegotiated'),
                                         store=self.store)
            payment.set_not_paid(entry)
            entry.new_status = Payment.STATUS_CANCELLED
            payment.cancel()
        else:
            payment.cancel()

        self._has_modified_payments = True

        self._update_payment_list()
        self.update_view()

    def _setup_credit_payment(self):
        payment_value = self._holder.value

        assert isinstance(self.model, Sale)

        try:
            payment = self._method.create_payment(
                Payment.TYPE_IN, self.model.group, self.model.branch, payment_value)
        except PaymentMethodError as err:
            warning(str(err))

        payment.base_value = self._holder.value

        return True

    def _setup_cash_payment(self):
        has_change_value = self._holder.value - self._outstanding_value > 0
        if has_change_value:
            payment_value = self._outstanding_value
        else:
            payment_value = self._holder.value

        if isinstance(self.model, PurchaseOrder):
            p_type = Payment.TYPE_OUT
        else:
            p_type = Payment.TYPE_IN

        try:
            payment = self._method.create_payment(
                p_type, self.model.group, self.model.branch, payment_value)
        except PaymentMethodError as err:
            warning(str(err))

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
        payments = list(payment_group.payments.order_by(Payment.identifier))
        preview_payments = [p for p in payments if p.is_preview()]
        len_preview_payments = len(preview_payments)

        for payment in payments:
            if payment.is_preview():
                continue
            self.payments.append(payment)

        for i, payment in enumerate(preview_payments):
            payment.description = payment.method.describe_payment(
                payment_group, i + 1, len_preview_payments)
            self.payments.append(payment)

        self._update_values()

    def _run_payment_editor(self):
        if self._wizard:
            toplevel = self._wizard.get_current_toplevel()
        else:
            toplevel = None
        retval = run_dialog(_MultipleMethodEditor, toplevel, self._wizard,
                            self, self.store, self.model, self._method,
                            self._holder.value)
        return retval

    def _refresh_next(self, value):
        self._wizard.refresh_next(value and self.can_confirm())

    #
    #   Public API
    #

    def enable_remove(self):
        self.remove_button.show()

    def can_confirm(self):
        if not self.is_valid:
            return False

        missing_value = self._get_missing_change_value()
        if self._require_total_value and missing_value != 0:
            return False

        assert missing_value >= 0, missing_value

        return True

    #
    # Callbacks
    #

    def _on_method__toggled(self, radio):
        if not radio.get_active():
            return

        self._method = radio.get_data('method')
        self._update_values()
        self.value.validate(force=True)
        self.value.grab_focus()

    def on_add_button__clicked(self, widget):
        self._add_payment()

    def on_remove_button__clicked(self, button):
        payment = self.payments.get_selected()
        if not payment:
            return
        if payment.is_cancelled():
            return

        self._remove_payment(payment)

    def on_payments__selection_changed(self, objectlist, payment):
        if not payment:
            # Nothing selected
            can_remove = False
        elif not self._allow_remove_paid and payment.is_paid():
            can_remove = False
        elif (isinstance(self.model, PurchaseOrder) and
              payment.payment_type == Payment.TYPE_IN):
            # Do not allow to remove inpayments on orders, as only
            # outpayments can be added
            can_remove = False
        elif (isinstance(self.model,
                         (PaymentRenegotiation, Sale, ReturnedSale)) and
              payment.payment_type == Payment.TYPE_OUT):
            # Do not allow to remove outpayments on orders, as only
            # inpayments can be added
            can_remove = False
        else:
            can_remove = True

        self.remove_button.set_sensitive(can_remove)

    def on_value__activate(self, entry):
        if self.add_button.get_sensitive():
            self._add_payment()

    def on_value__changed(self, entry):
        try:
            value = entry.read()
        except ValidationError as e:
            self.add_button.set_sensitive(False)
            return e

        self.add_button.set_sensitive(value and
                                      value is not ValueUnset)
        self._update_missing_or_change_value()

    def on_value__validate(self, entry, value):
        retval = None
        if value < 0:
            retval = ValidationError(_(u'The value must be greater than zero.'))

        if self._outstanding_value < 0:
            self._outstanding_value = 0

        is_money_method = self._method and self._method.method_name == u'money'
        if self._outstanding_value - value < 0 and not is_money_method:
            retval = ValidationError(_(u'The value must be lesser than the '
                                       'missing value.'))

        if not value and self._outstanding_value > 0:
            retval = ValidationError(_(u'You must provide a payment value.'))

        if not isinstance(self.model, StockDecrease):
            if (self._method.method_name == 'store_credit' and
                value > self.model.client.remaining_store_credit):
                fmt = _(u'Client does not have enough credit. '
                        u'Client store credit: %s.')
                retval = ValidationError(
                    fmt % currency(self.model.client.remaining_store_credit))
            if (self._method.method_name == u'credit' and
                value > self.model.client.credit_account_balance):
                fmt = _(u'Client does not have enough credit. '
                        u'Client credit: %s.')
                retval = ValidationError(
                    fmt % currency(self.model.client.credit_account_balance))

        self._holder.value = value
        self.toggle_new_payments()
        if self._outstanding_value != 0:
            self.add_button.set_sensitive(not bool(retval))

        return retval


def register_payment_slaves():
    dsm = get_utility(IDomainSlaveMapper)
    default_store = api.get_default_store()
    for method_name, slave_class in [
        (u'money', MoneyMethodSlave),
        (u'bill', BillMethodSlave),
        (u'check', CheckMethodSlave),
        (u'card', CardMethodSlave),
        (u'credit', CreditMethodSlave),
        (u'store_credit', StoreCreditMethodSlave),
        (u'multiple', MultipleMethodSlave),
        (u'deposit', DepositMethodSlave)]:
        method = PaymentMethod.get_by_name(default_store, method_name)
        dsm.register(method, slave_class)
