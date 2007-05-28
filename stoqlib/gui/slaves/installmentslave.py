# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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
## Author(s):   Johan Dahlin      <jdahlin@async.com.br>
##              Fabio Morbec      <fabio@async.com.br>
##
##
""" Installment confirmation slave """

import datetime

from kiwi.datatypes import currency, ValidationError
from kiwi.ui.objectlist import Column
from kiwi import ValueUnset

from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.domain.sale import Sale

_ = stoqlib_gettext

class _ConfirmationModel(object):
    def __init__(self, payments):
        self.payments = payments
        self.pay_penalty = True
        self.pay_interest = True
        self.close_date = datetime.date.today()

    def get_installment_value(self):
        return currency(sum(p.value for p in self.payments))

    def get_discount(self):
        return currency(0)

    def get_interest(self):
        if not self.pay_interest:
            return currency(0)
        return currency(sum(p.get_interest(self.close_date)
                            for p in self.payments))

    def get_penalty(self):
        if not self.pay_penalty:
            return currency(0)
        return currency(sum(p.get_penalty(self.close_date)
                            for p in self.payments))

    def get_total_value(self):
        return currency(self.get_installment_value() +
                        self.get_penalty() +
                        self.get_interest())

    def get_payment_total_value(self, payment):
        value = payment.value
        if self.pay_penalty:
            value += payment.get_penalty(self.close_date)
        if self.pay_interest:
            value += payment.get_interest(self.close_date)
        return value

    def calculate_paid_value(self, payments):
        installments_number = len(payments)
        for payment in payments:
            payment.paid_value = self.get_payment_total_value(payment)


class _SaleConfirmationModel(_ConfirmationModel):
    def __init__(self, payments, sale):
        if not isinstance(sale, Sale):
            raise TypeError("sale must be a Sale")
        _ConfirmationModel.__init__(self, payments)
        self.calculate_paid_value(payments)
        self._sale = sale
        self.open_date = self._sale.open_date.date()

    def get_order_number(self):
        return self._sale.id

    def get_person_name(self):
        if self._sale.client:
            return self._sale.client.person.name


class _PurchaseConfirmationModel(_ConfirmationModel):
    def __init__(self, payments, purchase):
        if not isinstance(purchase, PurchaseOrder):
            raise TypeError("purchase must be a PurchaseOrder")
        _ConfirmationModel.__init__(self, payments)
        self._purchase = purchase
        self.open_date = purchase.open_date.date()

    def get_order_number(self):
        return self._purchase.id

    def get_person_name(self):
        if self._purchase.supplier:
            return self._purchase.supplier.person.name

    def get_penalty(self):
        return currency(0)

    def get_interest(self):
        return currency(0)

    def get_payment_total_value(self, payment):
        return currency(0)


class _InstallmentConfirmationSlave(BaseEditor):
    """
    This slave is responsible for confirming a list of payments and
    applying the necessary interests and fines.

    """
    gladefile = 'InstallmentConfirmation'
    model_type = _ConfirmationModel
    size = (640, 420)
    title = _("Confirm payment")

    def __init__(self, conn, payments):
        """
        @param conn: a database connection
        @param payments: a list of payments
        """
        self._payments = payments
        self._proxy = None
        BaseEditor.__init__(self, conn)
        self._setup_widgets()

    proxy_widgets = ('order_number',
                     'installment_value',
                     'interest',
                     'penalty',
                     'discount',
                     'total_value',
                     'person_name',
                     'pay_penalty',
                     'pay_interest',
                     'close_date')

    # Private

    def _get_columns(self):
        return [Column('id', data_type=int, visible=False,
                       sorted=True),
                Column('description', _("Description"), data_type=str),
                Column('due_date', _("Due"), data_type=datetime.date),
                Column('paid_date', _("Paid date"), data_type=datetime.date),
                Column('base_value', _("Value"), data_type=currency),
                Column('paid_value', _("Paid value"), data_type=currency)]

    def _setup_widgets(self):
        self.installments.set_columns(self._get_columns())
        self.installments.extend(self._payments)

    #
    # BaseEditorSlave hooks
    #

    def create_model(self, conn):
        return _SaleConfirmationModel(self._payments,
                                      self._payments[0].group.get_adapted())

    def setup_proxies(self):
        self._proxy = self.add_proxy(
            self.model, _InstallmentConfirmationSlave.proxy_widgets)

    def on_confirm(self):
        pay_date = self.close_date.get_date()
        for payment in self._payments:
            payment.pay(pay_date,
                        self.model.get_payment_total_value(payment))
        return True

    #
    # Callbacks
    #

    def on_close_date__validate(self, widget, date):
        if date > datetime.date.today() or date < self.model.open_date:
            return ValidationError(_("Paid date must be between "
                                     "%s and today") % (self.model.open_date,))

    def on_pay_penalty__toggled(self, toggle):
        self.penalty.set_sensitive(toggle.get_active())
        self.model.calculate_paid_value(self._payments)
        self.installments.refresh()
        self._proxy.update('total_value')

    def on_pay_interest__toggled(self, toggle):
        self.interest.set_sensitive(toggle.get_active())
        self.model.calculate_paid_value(self._payments)
        self.installments.refresh()
        self._proxy.update('total_value')

class SaleInstallmentConfirmationSlave(_InstallmentConfirmationSlave):
    model_type = _SaleConfirmationModel

    def on_close_date__changed(self, proxy_date_entry):
        self._proxy.update('total_value')
        self._proxy.update('penalty')
        self._proxy.update('interest')

class PurchaseInstallmentConfirmationSlave(_InstallmentConfirmationSlave):
    model_type = _PurchaseConfirmationModel

    def _setup_widgets(self):
        _InstallmentConfirmationSlave._setup_widgets(self)
        self.discount_label.show()
        self.discount.show()
        self.person_label.set_text(_("Supplier: "))
        self.expander.hide()
        self.discount_value = currency(0)
        self.penalty_value = currency(0)
        self.interest_value = currency(0)
        self.installments_number = len(self._payments)

    def _calculate_payment(self):
        total = self.penalty_value - self.discount_value + self.interest_value
        value = total/self.installments_number
        for payment in self._payments:
            payment.value = payment.base_value + value
            self.installments.update(payment)
        self._proxy.update('total_value')

    def _read_widget_value(self, proxy_entry):
        try:
            value = proxy_entry.read()
        except ValidationError:
            value = currency(0)
        if value == ValueUnset:
            value = currency(0)
        return value

    def after_discount__content_changed(self, proxy_entry):
        self.discount_value = self._read_widget_value(proxy_entry)
        self._calculate_payment()

    def on_discount__validate(self, entry, value):
        if value >= self._payments[0].base_value:
            return ValidationError(_("Discount can not be greater than value"))

    def after_penalty__content_changed(self, proxy_entry):
        self.penalty_value = self._read_widget_value(proxy_entry)
        self._calculate_payment()

    def on_penalty__validate(self, entry, value):
        if value < 0:
            return ValidationError(_("Penalty can not be less than zero"))

    def after_interest__content_changed(self, proxy_entry):
        self.interest_value = self._read_widget_value(proxy_entry)
        self._calculate_payment()

    def on_interest__validate(self, entry, value):
        if value < 0:
            return ValidationError(_("Penalty can not be less than zero"))

    def create_model(self, conn):
        return _PurchaseConfirmationModel(self._payments,
                                          self._payments[0].group.get_adapted())
