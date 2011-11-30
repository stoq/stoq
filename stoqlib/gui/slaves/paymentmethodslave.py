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
""" Slaves for payment methods management"""

import gtk

from kiwi.ui.delegates import GladeSlaveDelegate
from kiwi.utils import gsignal

from stoqlib.domain.payment.views import PaymentMethodView
from stoqlib.exceptions import StoqlibError
from stoqlib.lib.translation import stoqlib_gettext

N_ = _ = stoqlib_gettext


class SelectPaymentMethodSlave(GladeSlaveDelegate):
    """ This slave show a radion button group with three payment method options:
    Money and Other (any other method supported by the system).
    The visibility of these buttons are directly related to payment method
    availability in the company.
    """
    gladefile = 'SelectPaymentMethodSlave'
    gsignal('method-changed', object)

    AVAILABLE_METHODS = ['money', 'card', 'bill', 'check',
                         'store_credit', 'multiple']

    def __init__(self, connection=None, available_methods=[],
                 default_method=None):
        GladeSlaveDelegate.__init__(self, gladefile=self.gladefile)

        self.conn = connection
        self._options = {}
        self._methods = {}
        for method in list(PaymentMethodView.select(connection=self.conn)):
            self._methods[method.method_name] = method

        self._setup_widgets()
        self.cash_check.set_active(True)
        self._setup_payment_methods(available_methods, default_method)

    def _setup_payment_methods(self, available_methods, default_method):
        self._selected_method = self._methods['money']
        self.cash_check.connect('toggled', self._on_method__toggled)
        self.cash_check.set_data('method', self._selected_method)
        self.cash_check.set_sensitive('money' in available_methods)

        methods = [method for method
                   in SelectPaymentMethodSlave.AVAILABLE_METHODS
                   if method != 'money']
        for method_name in methods:
            set_active = method_name == default_method
            self._add_payment_method(method_name,
                                     set_active=set_active)
            self.method_set_sensitive(method_name,
                                      method_name in available_methods)

    def _add_payment_method(self, method_name, set_active=False):
        method = self._methods[method_name]
        if not method.is_active:
            return

        radio = gtk.RadioButton(self.cash_check, N_(method.description))
        self.methods_box.pack_start(radio)
        radio.connect('toggled', self._on_method__toggled)
        radio.set_data('method', method)
        radio.set_active(set_active)
        radio.show()

        self._options[method_name] = radio

    def _setup_widgets(self):
        money_method = self._methods['money']
        if not money_method.is_active:
            raise StoqlibError("The money payment method should be always "
                               "available")

    #
    #   Public API
    #

    def get_method(self, name):
        return self._methods[name]

    def get_selected_method(self):
        return self._selected_method.method

    def method_set_sensitive(self, method_name, sensitive):
        if method_name in self._options.keys():
            self._options[method_name].set_sensitive(sensitive)

            if self._options[method_name].get_active():
                # Active the money method as a fallback.
                self.cash_check.set_active(True)

    #
    # Kiwi callbacks
    #
    def _on_method__toggled(self, radio):
        if not radio.get_active():
            return

        self._selected_method = radio.get_data('method')
        self.emit('method-changed', self._selected_method)
