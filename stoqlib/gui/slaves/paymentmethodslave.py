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
## Author(s):    Evandro Vale Miquelito      <evandro@async.com.br>
##               Johan Dahlin                <jdahlin@async.com.br>
##
##
""" Slaves for payment methods management"""

import gtk

from kiwi.ui.delegates import GladeSlaveDelegate
from kiwi.utils import gsignal

from stoqlib.database.runtime import get_connection
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.exceptions import StoqlibError
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class SelectPaymentMethodSlave(GladeSlaveDelegate):
    """ This slave show a radion button group with three payment method options:
    Money and Other (any other method supported by the system).
    The visibility of these buttons are directly related to payment method
    availability in the company.
    """
    gladefile = 'SelectPaymentMethodSlave'
    gsignal('method-changed', object)

    def __init__(self):
        GladeSlaveDelegate.__init__(self, gladefile=self.gladefile)
        self._options = {}

        self.conn = get_connection()
        self._setup_widgets()
        self.cash_check.set_active(True)
        self._setup_payment_methods()

    def _setup_payment_methods(self):
        self._selected_method = PaymentMethod.get_by_name(self.conn, 'money')
        self.cash_check.connect('toggled', self._on_method__toggled)
        self.cash_check.set_data('method', self._selected_method)

        self._add_payment_method('card')
        self._add_payment_method('bill')
        self._add_payment_method('check')
        self._add_payment_method('store_credit')
        self._add_payment_method('multiple')

    def _add_payment_method(self, method_name):
        method = PaymentMethod.get_by_name(self.conn, method_name)
        if not method.is_active:
            return

        radio = gtk.RadioButton(self.cash_check, method.description)
        self.methods_box.pack_start(radio)
        radio.connect('toggled', self._on_method__toggled)
        radio.set_data('method', method)
        radio.show()

        self._options[method_name] = radio

    def _setup_widgets(self):
        money_method = PaymentMethod.get_by_name(self.conn, 'money')
        if not money_method.is_active:
            raise StoqlibError("The money payment method should be always "
                               "available")

    #
    #   Public API
    #

    def get_selected_method(self):
        return self._selected_method

    def method_set_sensitive(self, method_name, sensitive):
        if method_name in self._options.keys():
            self._options[method_name].set_sensitive(sensitive)

    #
    # Kiwi callbacks
    #
    def _on_method__toggled(self, radio):
        if not radio.get_active():
            return

        self._selected_method = radio.get_data('method')
        self.emit('method-changed', self._selected_method)

