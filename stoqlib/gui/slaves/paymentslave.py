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
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##              Johan Dahlin                <jdahlin@async.com.br>
##              George Kussumoto            <george@async.com.br>
##
##
""" Slaves for payment management """

from decimal import Decimal
import datetime
from dateutil.relativedelta import relativedelta

from kiwi.datatypes import format_price, currency, ValidationError
from kiwi.utils import gsignal
from kiwi.ui.views import SlaveView

from stoqlib.domain.account import BankAccount
from stoqlib.domain.interfaces import IInPayment, IOutPayment
from stoqlib.domain.payment.methods import (BillCheckGroupData, CheckData,
                                            CreditProviderGroupData,
                                            DebitCardDetails,
                                            CreditCardDetails,
                                            CardInstallmentsStoreDetails,
                                            CardInstallmentsProviderDetails,
                                            FinanceDetails,
                                            PaymentMethodDetails,
                                            APaymentMethod,
                                            CheckPM, BillPM, MoneyPM)
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.sale import Sale
from stoqlib.drivers.cheque import get_current_cheque_printer_settings
from stoqlib.gui.editors.baseeditor import BaseEditorSlave
from stoqlib.lib.defaults import (interval_types, INTERVALTYPE_MONTH,
     DECIMAL_PRECISION, calculate_interval)
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

class PaymentListSlave(BaseEditorSlave):
    """A basic payment list slave. Each element of this list is a payment
    method slave which hold informations about payments. Available slaves
    are: BillDataSlave and CheckDataSlave

    Notes:
        - get_payment_slave: is a hook method which must be defined in
                             parents. The result of this function must
                             be a BaseEditorSlave instance.
    """

    gladefile = 'PaymentListSlave'
    model_type = APaymentMethod

    gsignal('remove-slave')
    gsignal('add-slave')
    gsignal('remove-item', SlaveView)

    def __init__(self, parent, conn, payment_method, total_amount):
        self.parent = parent
        self.total_amount = total_amount
        self.max_installments_number = None
        # This dict stores a reference of each toplevel widget with its own
        # kiwi object, the slave.
        self.payment_slaves = {}
        BaseEditorSlave.__init__(self, conn, payment_method)
        self._update_view()

    def _update_view(self):
        children_number = self.get_children_number()
        can_remove = children_number > 1
        max = self.max_installments_number or 0
        can_add = children_number < max
        self.remove_button.set_sensitive(can_remove)
        self.add_button.set_sensitive(can_add)
        self.update_total_label()

    def _remove_payment_slave(self, widget):
        slave = self.payment_slaves[widget]
        del self.payment_slaves[widget]
        self.list_vbox.remove(widget)
        self._update_view()
        self.emit("remove-item", slave)

    def get_total_difference(self):
        """Get the difference for the total of check payments invoiced. If
        the difference is zero the entire sale total value is invoiced.
        If the difference is greater than zero, there is an outstanding
        amount to invoice. If the value is negative, there is a overpaid
        value.
        """
        slaves = self.payment_slaves.values()
        values = [s.get_payment_value() for s in slaves
                        if s.get_payment_value() is not None]
        total = sum(values, currency(0))
        slaves_total = Decimal(str(total))
        slaves_total -= self.parent.get_interest_total()
        if slaves_total == self.total_amount:
            return currency(0)
        return currency(self.total_amount - slaves_total)

    def update_total_label(self):
        difference = self.get_total_difference()
        if not round(difference, DECIMAL_PRECISION):
            label_name = difference = ''
        elif difference < 0:
            difference *= -1
            label_name = _('Overpaid:')
        else:
            label_name = _('Outstanding:')
        if difference:
            difference = format_price(difference)
        self.total_label.set_text(difference)
        self.status_label.set_text(label_name)

    def get_children_number(self):
        vbox_children = self.list_vbox.get_children()
        return len(vbox_children)

    def register_max_installments_number(self, inst_number):
        self.max_installments_number = inst_number

    def clear_list(self):
        for widget in self.list_vbox.get_children()[:]:
            self._remove_payment_slave(widget)

    def update_payment_list(self, installments_number):
        installments_number = installments_number or 0
        children_number = self.get_children_number()
        difference = installments_number - children_number
        if not difference:
            return
        if difference > 0:
            for unused in range(difference):
                self.add_slave()
        else:
            difference *= -1
            for unused in range(difference):
                self.remove_last_payment_slave()

    def add_slave(self, slave=None):
        if not self.max_installments_number:
            raise ValueError('You call register_max_installments_number '
                             'before start adding slaves')
        if self.get_children_number() > self.max_installments_number:
            return
        slave = slave or self.parent.get_payment_slave()
        widget = slave.get_toplevel()
        self.payment_slaves[widget] = slave
        children_number = self.get_children_number() + 1
        slave.set_frame_label('# %d' % children_number)
        self.list_vbox.pack_start(widget, False)
        # Scroll to the bottom of the scrolled window
        vadj = self.scrolled_window.get_vadjustment()
        vadj.set_value(vadj.upper)
        widget.show()
        self._update_view()

    def remove_last_payment_slave(self):
        vbox_children = self.list_vbox.get_children()
        if not vbox_children:
            return
        widget = vbox_children[-1]
        self._remove_payment_slave(widget)

    def is_all_due_dates_valid(self):
        today = datetime.date.today()
        for slave in self.payment_slaves.values():
            if slave.due_date.read() < today:
                return False
        return True

    #
    # Kiwi callbacks
    #

    def on_add_button__clicked(self, *args):
        self.add_slave()
        self.emit('add-slave')

    def on_remove_button__clicked(self, *args):
        self.remove_last_payment_slave()
        self.emit('remove-slave')


class BankDataSlave(BaseEditorSlave):
    """  A simple slave that contains only a hbox with fields to bank name and
    its branch. This slave is used by payment method slaves that has reference
    to a BankAccount object.
    """
    gladefile = 'BankDataSlave'
    model_type = BankAccount
    proxy_widgets = ('bank',
                     'branch')

    #
    # BaseEditorSlave hooks
    #

    def setup_proxies(self):
        self.add_proxy(self.model, BankDataSlave.proxy_widgets)

class BillDataSlave(BaseEditorSlave):
    """ A slave to set payment information of bill payment method.
    """

    gladefile = 'BillDataSlave'
    model_type = Payment
    payment_widgets = ('due_date',
                       'value',
                       'payment_number')
    gsignal('paymentvalue-changed')
    gsignal('duedate-validate')

    def __init__(self, conn, payment_group, due_date, value,
                 method_iface, model=None):
        self._payment_group = payment_group
        self._due_date = due_date
        self._value = value
        self._method_iface = method_iface
        BaseEditorSlave.__init__(self, conn, model)

    def _setup_widgets(self):
        self.payment_number_label.set_bold(True)
        self.payment_number_label.set_size('small')

    def set_frame_label(self, label_name):
        self.payment_number_label.set_text(label_name)

    def get_payment_value(self):
        return self.model.value

    #
    # BaseEditorSlave hooks
    #

    def create_model(self, conn):
        bill_method = BillPM.selectOne(connection=conn)
        apayment = bill_method.create_payment(self._method_iface,
                                              self._payment_group,
                                              self._value,
                                              self._due_date)
        return apayment.get_adapted()

    def setup_proxies(self):
        self._setup_widgets()
        self.add_proxy(self.model, BillDataSlave.payment_widgets)

    #
    # Kiwi callbacks
    #

    def after_value__changed(self, *args):
        self.emit('paymentvalue-changed')

    def on_due_date__validate(self, widget, value):
        self.emit('duedate-validate')
        if value < datetime.date.today():
            return ValidationError(_(u"Expected installment due date "
                                      "must be set to a future date"))

class CheckDataSlave(BillDataSlave):
    """A slave to set payment information of check payment method."""
    slave_holder = 'bank_data_slave'
    model_type = CheckData

    def __init__(self, conn, payment_group, due_date, value,
                 is_sale_payment, model=None, default_bank=None):
        self._default_bank = default_bank
        BillDataSlave.__init__(self, conn, payment_group, due_date,
                               value, is_sale_payment, model)

    #
    # BaseEditorSlave hooks
    #

    def get_payment_value(self):
        return self.model.payment.value

    def create_model(self, conn):
        check_method = CheckPM.selectOne(connection=conn)
        apayment = check_method.create_payment(self._method_iface,
                                               self._payment_group,
                                               self._value, self._due_date)
        adapted = apayment.get_adapted()
        return check_method.get_check_data_by_payment(adapted)

    def setup_slaves(self):
        if self._default_bank and not self.model.bank_data.bank_id:
            self.model.bank_data.bank_id = self._default_bank
        bank_data_slave = BankDataSlave(self.conn, self.model.bank_data)
        if self.get_slave(self.slave_holder):
            self.detach_slave(self.slave_holder)
        self.attach_slave(self.slave_holder, bank_data_slave)

    def setup_proxies(self):
        self._setup_widgets()
        self.add_proxy(self.model.payment, BillDataSlave.payment_widgets)

class BasePaymentMethodSlave(BaseEditorSlave):
    """A base payment method slave for Bill and Check methods."""

    gladefile = 'BillCheckMethodSlave'
    model_type = BillCheckGroupData
    slave_holder = 'bill_check_data_list'
    proxy_widgets = ('interval_type_combo',
                     'intervals',
                     'first_duedate',
                     'installments_number')
    # This attribute must be defined in child. It can assume two
    # value: CheckDataSlave, BillDataSlave
    _data_slave_class = None

    def __init__(self, wizard, parent, conn, order_obj, payment_method,
                 outstanding_value=currency(0)):
        # Note that 'order' may be a Sale or a PurchaseOrder object
        self.order = order_obj
        self.wizard = wizard
        self.method = payment_method
        self.method_iface = self._get_payment_method_iface()
        # This is very useful when calculating the total amount outstanding
        # or overpaid of the payments
        self.interest_total = currency(0)
        self.payment_group = self.wizard.payment_group
        self.payment_list = None
        self.reset_btn_validation_ok = True
        self.total_value = outstanding_value or self._get_total_amount()
        BaseEditorSlave.__init__(self, conn)
        self.register_validate_function(self._refresh_next)
        self.parent = parent
        self.interval_type_combo.set_sensitive(False)
        self.intervals.set_sensitive(False)
        self.update_view()

    def _refresh_next(self, validation_ok=True):
        if validation_ok and self.payment_list:
            total_difference = self.payment_list.get_total_difference()
            validation_ok = (total_difference == currency(0) and
                             self.payment_list.is_all_due_dates_valid())
        self.wizard.refresh_next(validation_ok)

    def update_view(self):
        attrs = [self.model.installments_number, self.model.first_duedate,
                 self.model.intervals]
        self.reset_button.set_sensitive((None not in attrs) and
                                        self.reset_btn_validation_ok)
        self._refresh_next()

    def _setup_widgets(self):
        max = self.method.get_max_installments_number()
        self.installments_number.set_range(1, max)
        self.installments_number.set_value(1)
        items = [(label, constant) for constant, label
                                in interval_types.items()]
        self.interval_type_combo.prefill(items)
        self.payment_list = PaymentListSlave(self, self.conn,
                                             self.method, self.total_value)
        self.payment_list.connect('add-slave',
                                  self.update_installments_number)
        self.payment_list.connect('remove-slave',
                                  self.update_installments_number)
        self.payment_list.connect("remove-item",
                                  self._on_payment_list__remove_item)
        self.payment_list.register_max_installments_number(max)
        if self.get_slave(BasePaymentMethodSlave.slave_holder):
            self.detach_slave(BasePaymentMethodSlave.slave_holder)
        self.attach_slave(BasePaymentMethodSlave.slave_holder,
                          self.payment_list)
        created_adapted_payments = self.get_created_adapted_payments()
        if created_adapted_payments:
            self.fill_slave_list(created_adapted_payments)
        else:
            # Adding the first payment
            slave = self.get_payment_slave()
            self.payment_list.add_slave(slave)

    def get_created_adapted_payments(self):
        for payment in Payment.selectBy(group=self.wizard.payment_group,
                                        method=self.method,
                                        status=Payment.STATUS_PREVIEW,
                                        connection=self.conn):
            yield self.method_iface(payment, None)

    def _is_sale(self):
        """"Returns if our order object is a Sale instance"""
        return isinstance(self.order, Sale)

    def _get_total_amount(self):
        """Returns the order total amount """
        if self._is_sale():
            return self.order.get_total_sale_amount()
        # else self.order is purchase order object
        return self.order.get_purchase_total()

    def _get_payment_method_iface(self):
        if self._is_sale():
            return IInPayment
        else:
            return IOutPayment

    #
    # General methods
    #
    def _setup_payments(self):
        self.payment_list.clear_list()
        due_dates = []
        interval = calculate_interval(self.model.interval_type,
                                      self.model.intervals)
        installments_number = self.model.installments_number
        self.payment_group.installments_number = installments_number
        for i in range(installments_number):
            due_dates.append(self.model.first_duedate +
                             datetime.timedelta(i * interval))

        payments = self.method.create_payments(self.method_iface,
                                               self.wizard.payment_group,
                                               self.total_value,
                                               due_dates)
        interest = Decimal(0)

        # This is very useful when calculating the total amount outstanding
        # or overpaid of the payments
        self.interest_total = interest
        self.fill_slave_list(payments)

    def fill_slave_list(self, adapted_payments):
        for adapted in adapted_payments:
            slave = self.get_slave_by_adapted_payment(adapted)
            self.payment_list.add_slave(slave)

    def get_slave_by_adapted_payment(self, adapted_payment):
        raise NotImplementedError

    def get_interest_total(self):
        return self.interest_total

    def get_extra_slave_args(self):
        """  This method can be redefined in child when extra parameters needs
        to be passed to the slave class. This method must return always a list
        with the parameters.
        """
        return []

    #
    #  Callbacks
    #

    def _on_payment_list__remove_item(self, payment_list, slave):
        if not isinstance(slave.model, slave.model_type):
            raise TypeError('Slave model attribute should be of type '
                            '%s, got %s' % (slave.model_type,
                                            type(slave.model)))

        if isinstance(slave.model, CheckData):
            payment = slave.model.payment
        else:
            payment = slave.model

        self.method.delete_payment(self.method_iface, payment)

    #
    # PaymentListSlave hooks and callbacks
    #

    def get_payment_slave(self, model=None):
        if not self._data_slave_class:
            raise ValueError('Child classes must define a data_slave_class '
                             'attribute')
        group = self.wizard.payment_group
        due_date = datetime.datetime.today()
        if not self.payment_list.get_children_number():
            total = self.total_value
        else:
            total = currency(0)
        extra_params = self.get_extra_slave_args()
        slave = self._data_slave_class(self.conn, group, due_date, total,
                                       self.method_iface, model, *extra_params)
        slave.connect('paymentvalue-changed',
                      self._on_slave__paymentvalue_changed)
        slave.connect('duedate-validate',
                      self._on_slave__duedate_validate)
        return slave

    def _on_slave__paymentvalue_changed(self, slave):
        self.update_view()
        self.payment_list.update_total_label()

    def _on_slave__duedate_validate(self, slave):
        self.update_view()

    def update_installments_number(self, *args):
        inst_number = self.payment_list.get_children_number()
        self.model.installments_number = inst_number
        self.proxy.update('installments_number')

    #
    # PaymentMethodStep hooks
    #

    def finish(self):
        # Since payments are created during this step there is no need to
        # perform tasks here
        return

    #
    # BaseEditor Slave hooks
    #

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model,
                                    BasePaymentMethodSlave.proxy_widgets)
        self.interval_type_combo.select_item_by_data(INTERVALTYPE_MONTH)

    def create_model(self, conn):
        group = self.wizard.payment_group
        check_group = self.method.get_check_group_data(group)
        if check_group:
            return check_group
        return BillCheckGroupData(connection=conn, group=group,
                                  first_duedate=datetime.datetime.today())

    #
    # Kiwi callbacks
    #

    def on_installments_number__changed(self, proxyspinbutton):
        # Call this callback *on* the value changed because we need to
        # have the same value for the length of the payments list and
        # validate the installments_number
        inst_number = self.model.installments_number
        max = self.method.get_max_installments_number()
        if inst_number > max:
            self.installments_number.set_invalid(_("The number of installments "
                "must be less then %d" % max))
            self._refresh_next(False)
            return
        if self.payment_list:
            self.payment_list.update_payment_list(inst_number)
        has_installments = inst_number > 1
        self.interval_type_combo.set_sensitive(has_installments)
        self.intervals.set_sensitive(has_installments)
        self._refresh_next(False)

    def on_first_duedate__validate(self, widget, value):
        if value < datetime.date.today():
            return ValidationError(_("Expected first installment date must be set "
                "to a future date"))
        self._refresh_next(False)

    def on_intervals__value_changed(self, *args):
        self.update_view()
        self._refresh_next(False)

    def on_interval_type_combo__changed(self, *args):
        self.update_view()
        self._refresh_next(False)

    def on_reset_button__clicked(self, *args):
        self._setup_payments()
        self.update_view()

    def on_intervals__validation_changed(self, widget, is_valid):
        self.reset_btn_validation_ok = is_valid
        self.update_view()

    def on_first_duedate__validation_changed(self, widget, is_valid):
        self.reset_btn_validation_ok = is_valid
        self.update_view()

    def on_installments_number__validation_changed(self, widget, is_valid):
        self.reset_btn_validation_ok = is_valid
        self.update_view()

class CheckMethodSlave(BasePaymentMethodSlave):
    _data_slave_class = CheckDataSlave

    def get_slave_by_adapted_payment(self, adapted_payment):
        payment = adapted_payment.get_adapted()
        check_data = self.method.get_check_data_by_payment(payment)
        return self.get_payment_slave(check_data)

    def get_extra_slave_args(self):
        """ If there is any selected item in the banks combo, return this
        as extra parameter to the slave (CheckDataSlave). """
        if (self.bank_combo.get_property("visible")
            and len(self.bank_combo.get_model())):
            bank_id = self.bank_combo.get_selected()
            if bank_id:
                return [bank_id]
        return []

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

class BillMethodSlave(BasePaymentMethodSlave):
    _data_slave_class = BillDataSlave

    def __init__(self, wizard, parent, conn, sale, payment_method,
                 outstanding_value=currency(0)):
        BasePaymentMethodSlave.__init__(self, wizard, parent, conn,
                                        sale, payment_method,
                                        outstanding_value=outstanding_value)
        self.bank_label.hide()
        self.bank_combo.hide()

    def get_slave_by_adapted_payment(self, adapted_payment):
        payment = adapted_payment.get_adapted()
        return self.get_payment_slave(payment)


class _MoneyData(BillDataSlave):

    def create_model(self, conn):
        money_method = MoneyPM.selectOne(connetion=conn)
        apayment = money_method.create_payment(self._payment_group,
                                               self._value,
                                               self._due_date)
        return apayment.get_adapted()


class _TemporaryMoneyData:
    installments_number = 1
    intervals = 1

    def __init__(self):
        self.first_duedate = datetime.datetime.today()


class MoneyMethodSlave(BasePaymentMethodSlave):
    model_type = _TemporaryMoneyData
    _data_slave_class = _MoneyData

    def __init__(self, wizard, parent, conn, total_amount,
                 payment_method, outstanding_value=currency(0)):
        BasePaymentMethodSlave.__init__(self, wizard, parent, conn,
                                        total_amount, payment_method,
                                        outstanding_value=outstanding_value)
        self.bank_label.hide()
        self.bank_combo.hide()
        self.first_duedate_lbl.hide()
        self.first_duedate.hide()

    def get_slave_by_adapted_payment(self, adapted_payment):
        return self.get_payment_slave(adapted_payment.get_adapted())

    def create_model(self, conn):
        return _TemporaryMoneyData()


#
# Classes related to "credit provider" payment method
#

class _CreditProviderMethodSlave(BaseEditorSlave):
    """A base payment method slave for card and finance methods.
    Available slaves are: CardMethodSlave, FinanceMethodSlave
    """
    gladefile = 'CreditProviderMethodSlave'
    model_type = CreditProviderGroupData
    proxy_widgets = ('payment_type',
                     'credit_provider',
                     'installments_number')
    _payment_types = None

    def __init__(self, wizard, parent, conn, sale_obj, payment_method,
                 outstanding_value=currency(0)):
        self.sale = sale_obj
        self.wizard = wizard
        self.method = payment_method
        self.payment_group = self.wizard.payment_group
        self._pmdetails_objs = None
        self.total_value = (outstanding_value or
                            self.sale.get_total_sale_amount())
        self.providers = self._get_credit_providers()
        BaseEditorSlave.__init__(self, conn)
        self.parent = parent
        # this will be properly updated after changing data in payment_type
        # widget
        self.installments_number.set_range(1, 1)
        self.payment_type.set_sensitive(False)
        self._refresh_next(False)

    def _refresh_next(self, validation_ok=True):
        validation_ok = validation_ok and self.model.installments_number
        self.wizard.refresh_next(validation_ok)

    def _setup_max_installments(self):
        selected = self.payment_type.get_selected_data()
        max = selected.get_max_installments_number()
        if max > 1:
            min = 2
        else:
            min = 1
        self.installments_number.set_range(min, max)

    def update_view(self):
        # This is for PaymentMethodStep compatibility.
        # FIXME We need to change PaymentMethodDetails to use signals
        # instead of calling methods of parents and slaves directly
        self.payment_type.set_sensitive(True)

    def _get_credit_providers(self):
        raise NotImplementedError

    def _get_payment_types(self, credit_provider):
        if self._pmdetails_objs:
            return self._pmdetails_objs
        objs = PaymentMethodDetails.selectBy(providerID=credit_provider.id,
                                             is_active=True,
                                             connection=self.conn)
        if not objs:
            raise ValueError('You must have payment information objs '
                             'stored in the database before start doing '
                             'sales')
        pmdetails_objs = [obj for obj in objs
                                if obj.is_active and
                                    isinstance(obj, self._payment_types)]
        if not pmdetails_objs:
            raise ValueError('You must have payment_types information '
                             'stored in the database before start doing '
                             'sales')
        # This is useful to avoid multiple database selects when calling
        # kiwi combobox content changed signal
        self._pmdetails_objs = pmdetails_objs
        self.update_view()
        return self._pmdetails_objs

    def _setup_payment_types(self):
        raise NotImplementedError

    def _setup_widgets(self):
        provider_items = [(p.short_name, p) for p in self.providers]
        self.credit_provider.prefill(provider_items)
        self._setup_payment_types()

    def _setup_payments(self):
        payment_type = self.model.payment_type
        due_dates = []
        start_due_date = datetime.datetime.today()
        for i in range(self.model.installments_number):
            due_dates.append(payment_type.calculate_payment_duedate(
                start_due_date))
            start_due_date += relativedelta(months=+1)

        self.method.create_inpayments(self.wizard.payment_group,
                                      self.total_value, due_dates)

    #
    # PaymentMethodStep hooks
    #

    def finish(self):
        self._setup_payments()
        self.update_view()

    #
    # BaseEditor Slave hooks
    #

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model,
                                    _CreditProviderMethodSlave.proxy_widgets)

    def create_model(self, conn):
        if not self.providers:
            raise ValueError('You must have credit providers information '
                             'stored in the database before start doing '
                             'sales')
        group = self.wizard.payment_group
        return CreditProviderGroupData(connection=conn, group=group,
                                       payment_type=None,
                                       provider=None)

    #
    # Kiwi callbacks
    #

    def on_payment_type__content_changed(self, *args):
        self._setup_max_installments()
        self._refresh_next()
        self.credit_provider.set_sensitive(False)

    def on_credit_provider__content_changed(self, *args):
        self._setup_payment_types()
        self.update_view()


class CardMethodSlave(_CreditProviderMethodSlave):

    _payment_types = (CardInstallmentsStoreDetails,
                      CardInstallmentsProviderDetails, DebitCardDetails,
                      CreditCardDetails)

    def _get_credit_providers(self):
        return self.method.get_credit_card_providers()

    def _setup_payment_types(self):
        selected = self.credit_provider.get_selected_data()
        if not selected:
            return
        payment_types = self._get_payment_types(selected)
        self.ptypes_items = [(p.payment_type_name, p) for p in payment_types]
        self.payment_type.prefill(self.ptypes_items)

class FinanceMethodSlave(_CreditProviderMethodSlave):
    _payment_types = FinanceDetails,

    def _get_credit_providers(self):
        return self.method.get_finance_companies()

    def _setup_payment_types(self):
        payment_types = self._get_payment_types(self.providers[0])
        if len(payment_types) != 1:
            raise ValueError('It should have only one payment type for '
                             'finance payment method. Found %d' %
                             len(payment_types))
        payment_type = payment_types[0]
        names = payment_type.payment_type_names
        self.ptypes_items = [(name, payment_type) for name in names]
        self.payment_type.prefill(self.ptypes_items)


class MultipleMethodSlave:
    gladefile = 'MultipleMethodSlave'
    # Bug 2161 will implement this class
    # XXX We must clean all the payments created for this payment group when
    # creating this slave since there is no way to filter them by payment
    # method after create payments here.
