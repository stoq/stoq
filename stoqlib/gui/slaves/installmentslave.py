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
##
##
""" Installment confirmation slave """

import datetime
import gettext

from kiwi.datatypes import currency
from kiwi.ui.objectlist import Column

from stoqlib.gui.base.editors import BaseEditor

_ = gettext.gettext

class _ConfirmationModel(object):
    def __init__(self, payments):
        self.payments = payments
        self.pay_penalty = True
        self.pay_interest = True

    def get_installment_value(self):
        return currency(sum(p.value for p in self.payments))

    def get_interest(self):
        if not self.pay_interest:
            return currency(0)
        return currency(sum(p.get_interest() for p in self.payments))

    def get_penalty(self):
        if not self.pay_penalty:
            return currency(0)
        return currency(sum(p.get_penalty() for p in self.payments))

    def get_total_value(self):
        return currency(self.get_installment_value() +
                        self.get_penalty() +
                        self.get_interest())

    def get_payment_total_value(self, payment):
        value = payment.value
        if self.pay_penalty:
            value += payment.get_penalty()
        if self.pay_interest:
            value += payment.get_interest()
        return value

class _SaleConfirmationModel(_ConfirmationModel):
    def __init__(self, payments):
        _ConfirmationModel.__init__(self, payments)
        self._sale = payments[0].group.get_adapted()

    def get_order_number(self):
        return self._sale.id

    def get_client_name(self):
        if self._sale.client:
            return self._sale.client.person.name

class _InstallmentConfirmationSlave(BaseEditor):
    """
    This slave is responsible for confirming a list of payments and
    applying the necessary interests and fines.

    """
    gladefile = 'InstallmentConfirmation'
    model_type = _ConfirmationModel
    size = (640, 420)

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
                     'total_value',
                     'client_name',
                     'pay_penalty',
                     'pay_interest')

    # Private

    def _get_columns(self):
        return [Column('id', data_type=int, visible=False,
                       sorted=True),
                Column('description', _("Description"), data_type=str),
                Column('due_date', _("Due"), data_type=datetime.date),
                Column('paid_date', _("Paid date"), data_type=datetime.date),
                Column('value', _("Value"), data_type=currency),
                Column('paid_value', _("Paid value"), data_type=currency)]

    def _setup_widgets(self):
        self.installments.set_columns(self._get_columns())
        self.installments.extend(self._payments)

    #
    # BaseEditorSlave hooks
    #

    def create_model(self, conn):
        return _SaleConfirmationModel(self._payments)

    def setup_proxies(self):
        self._proxy = self.add_proxy(
            self.model, _InstallmentConfirmationSlave.proxy_widgets)

    def on_confirm(self):
        today = datetime.date.today()
        for payment in self._payments:
            payment.pay(today, self.model.get_payment_total_value(payment))
        return True

    #
    # Callbacks
    #

    def on_pay_penalty__toggled(self, toggle):
        self.penalty.set_sensitive(toggle.get_active())
        self._proxy.update('total_value')

    def on_pay_interest__toggled(self, toggle):
        self.interest.set_sensitive(toggle.get_active())
        self._proxy.update('total_value')

class SaleInstallmentConfirmationSlave(_InstallmentConfirmationSlave):
    model_type = _SaleConfirmationModel

