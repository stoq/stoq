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
from kiwi.currency import currency
from kiwi.datatypes import converter

from kiwi.ui.delegates import GladeSlaveDelegate
from kiwi.utils import gsignal

from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.lib.translation import stoqlib_gettext

N_ = _ = stoqlib_gettext


class SelectPaymentMethodSlave(GladeSlaveDelegate):
    gladefile = 'SelectPaymentMethodSlave'
    gsignal('method-changed', object)

    def __init__(self, store=None,
                 payment_type=None,
                 methods=None,
                 default_method=None):
        methods = methods or []
        self._widgets = {}
        self._methods = {}
        self._selected_method = None

        if payment_type is None:
            raise ValueError("payment_type must be set")
        GladeSlaveDelegate.__init__(self, gladefile=self.gladefile)

        self.store = store
        self._setup_payment_methods(payment_type)

        if default_method is None:
            default_method = 'money'
        self._default_method = default_method
        self._select_default_method()

    def _setup_payment_methods(self, payment_type):
        methods = PaymentMethod.get_creatable_methods(
            self.store, payment_type, separate=False)
        group = None
        for method in methods:
            method_name = method.method_name
            widget = gtk.RadioButton(group, N_(method.description))
            widget.connect('toggled', self._on_method__toggled)
            widget.set_data('method', method)
            if group is None:
                group = widget
            self.methods_box.pack_start(widget, False, False, 6)
            widget.show()

            self._methods[method_name] = method
            self._widgets[method_name] = widget
            self.method_set_sensitive(method_name, True)

        # Don't allow the user to change the kind of payment method if
        # there's only one
        if len(methods) == 1:
            self._widgets[methods[0].method_name].set_sensitive(False)
        else:
            # Money should be the first
            widget = self._widgets.get(u'money')
            if widget is not None:
                self.methods_box.reorder_child(widget, 0)

            # Multiple should be the last
            widget = self._widgets.get(u'multiple')
            if widget is not None:
                self.methods_box.reorder_child(
                    widget, len(self.methods_box) - 1)

    def _select_default_method(self):
        method = self._methods.get(self._default_method)
        # Fallback in case the requested method is not available
        if not method:
            self._default_method, method = self._methods.items()[0]
        self._selected_method = method
        self._widgets[self._default_method].set_active(True)

    #
    #   Public API
    #

    def get_method(self, name):
        return self._methods[name]

    def get_selected_method(self):
        return self._selected_method

    def select_method(self, method_name):
        widget = self._widgets[method_name]
        widget.set_active(True)

    def method_set_sensitive(self, method_name, sensitive):
        if method_name in self._widgets:
            widget = self._widgets[method_name]
            widget.set_visible(sensitive)

        # This method was select, but is no longer available. Select the default
        # method instead.
        selected_method = self.get_selected_method()
        if selected_method and selected_method.method_name == method_name:
            self._select_default_method()

    def set_client(self, client, total_amount):
        self.select_method(u'credit')
        if client and client.credit_account_balance > 0:
            client_credit = converter.as_string(
                currency, client.credit_account_balance)
            self._widgets[u'credit'].set_label(
                _("Credit (%s)") % client_credit)
            has_enough_credit = client.credit_account_balance >= total_amount
            if has_enough_credit:
                self.select_method(u'credit')
            else:
                self.select_method(u'money')
            self._widgets[u'credit'].set_sensitive(has_enough_credit)
        else:
            self.select_method(u'money')
        self._client = client

    #
    # Kiwi callbacks
    #

    def _on_method__toggled(self, radio):
        if not radio.get_active():
            return

        self._selected_method = radio.get_data('method')
        self.emit('method-changed', self._selected_method)
