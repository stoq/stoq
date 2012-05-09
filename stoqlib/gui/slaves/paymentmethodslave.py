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

from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.lib.translation import stoqlib_gettext

N_ = _ = stoqlib_gettext


class SelectPaymentMethodSlave(GladeSlaveDelegate):
    gladefile = 'SelectPaymentMethodSlave'
    gsignal('method-changed', object)

    def __init__(self, connection=None,
                 payment_type=None,
                 methods=[],
                 default_method=None):
        self._widgets = {}
        self._methods = {}
        self._selected_method = None

        if payment_type is None:
            raise ValueError("payment_type must be set")
        GladeSlaveDelegate.__init__(self, gladefile=self.gladefile)

        self.conn = connection
        self._setup_payment_methods(payment_type)

        if default_method is None:
            default_method = 'money'
        self._select_default_method(default_method)

    def _setup_payment_methods(self, payment_type):
        methods = PaymentMethod.get_creatable_methods(
            self.conn, payment_type, separate=False)
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
            widget = self._widgets.get('money')
            if widget is not None:
                self.methods_box.reorder_child(widget, 0)

            # Multiple should be the last
            widget = self._widgets.get('multiple')
            if widget is not None:
                self.methods_box.reorder_child(
                    widget, len(self.methods_box) - 1)

    def _select_default_method(self, method_name):
        method = self._methods.get(method_name)
        # Fallback in case the requested method is not available
        if not method:
            method_name, method = self._methods.items()[0]
        self._selected_method = method
        self._widgets[method_name].set_active(True)

    #
    #   Public API
    #

    def get_method(self, name):
        return self._methods[name]

    def get_selected_method(self):
        return self._selected_method

    def method_set_sensitive(self, method_name, sensitive):
        if method_name in self._widgets:
            widget = self._widgets[method_name]
            widget.set_visible(sensitive)

    #
    # Kiwi callbacks
    #
    def _on_method__toggled(self, radio):
        if not radio.get_active():
            return

        self._selected_method = radio.get_data('method')
        self.emit('method-changed', self._selected_method)
