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

from stoqlib.api import api
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.lib.translation import stoqlib_gettext

N_ = _ = stoqlib_gettext


class SelectPaymentMethodSlave(GladeSlaveDelegate):
    domain = 'stoq'
    gladefile = 'SelectPaymentMethodSlave'
    gsignal('method-changed', object)

    def __init__(self, store=None, payment_type=None, default_method=None,
                 no_payments=False):
        """
        :param no_payments: if ``True``, add the option "No payments" that
        doesn't create any payments.
        """
        self._default_method = default_method
        self._no_payments = no_payments
        self._widgets = {}
        self._methods = {}
        self._selected_method = None

        if payment_type is None:
            raise ValueError("payment_type must be set")
        GladeSlaveDelegate.__init__(self, gladefile=self.gladefile)

        self.store = store
        self._setup_payment_methods(payment_type)

    def _add_method(self, method, group):
        if method:
            method_name = method.method_name
            description = method.description
        else:
            method_name = None
            description = _("No payments")
        widget = gtk.RadioButton(group, N_(description))
        widget.connect('toggled', self._on_method__toggled)
        widget.set_data('method', method)
        self.methods_box.pack_start(widget, False, False, 6)
        widget.show()

        self._methods[method_name] = method
        self._widgets[method_name] = widget
        self.method_set_visible(method_name, True)
        return widget

    def _setup_payment_methods(self, payment_type):
        methods = PaymentMethod.get_creatable_methods(
            self.store, payment_type, separate=False)
        group = None
        for method in methods:
            widget = self._add_method(method, group)
            if group is None:
                group = widget

        if self._no_payments:
            self._add_method(None, group)

        if len(methods) == 1:
            self._default_method = methods[0].method_name
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

        # The default method could not have been passed to the constructor,
        # or if it was, it could not be active. Fallback to the parameters'
        # one or money in case it's not active too
        if (self._default_method is None or
            self._default_method not in self._widgets):
            default = api.sysparam.get_object(self.store,
                                              "DEFAULT_PAYMENT_METHOD")
            if default.method_name in self._widgets:
                self._default_method = default.method_name
            else:
                self._default_method = u'money'

        self._select_default_method()

    def _select_method(self, method_name):
        method = self._methods.get(method_name)
        method_widget = self._widgets[method_name]

        # In case method_name is not visible/sensitive, fallback to money.
        # It's the only method that we can be sure is always active
        if (not method_widget.get_visible() or
            not method_widget.get_sensitive()):
            self._select_method(u'money')
            return

        self._selected_method = method
        method_widget.set_active(True)

    def _select_default_method(self):
        self._select_method(self._default_method)

    def _set_credit_visible(self, client, total_amount):
        if client is None:
            self.method_set_visible(u'credit', False)
            return

        credit_widget = self._widgets.get(u'credit', None)
        if credit_widget:
            credit_balance = client.credit_account_balance
            credit_widget.set_label(_("Credit (%s)") % (
                converter.as_string(currency, credit_balance)))
            self.method_set_visible(u'credit', bool(credit_balance))
            self.method_set_sensitive(u'credit',
                                      credit_balance >= total_amount)

    def _set_store_credit_visible(self, client, total_amount):
        if client is None:
            self.method_set_visible(u'store_credit', False)
            return

        store_credit_widget = self._widgets.get(u'store_credit', None)
        if store_credit_widget:
            store_credit_balance = client.credit_limit
            self.method_set_visible(u'store_credit',
                                    bool(store_credit_balance))
            self.method_set_sensitive(u'store_credit',
                                      store_credit_balance >= total_amount)

    #
    #   Public API
    #

    def get_selected_method(self):
        return self._selected_method

    def method_set_sensitive(self, method_name, sensitive):
        if method_name not in self._widgets:
            return

        widget = self._widgets[method_name]
        widget.set_sensitive(sensitive)

        # This method was select, but is no longer available.
        # Select the default method instead.
        if widget.get_active() and not sensitive:
            self._select_default_method()

    def method_set_visible(self, method_name, visible):
        if method_name not in self._widgets:
            return

        widget = self._widgets[method_name]
        widget.set_visible(visible)

        # This method was select, but is no longer available.
        # Select the default method instead.
        if widget.get_active() and not visible:
            self._select_default_method()

    def set_client(self, client, total_amount):
        self.method_set_visible(u'bill', bool(client))
        self._set_credit_visible(client, total_amount)
        self._set_store_credit_visible(client, total_amount)

    #
    # Kiwi callbacks
    #

    def _on_method__toggled(self, radio):
        if not radio.get_active():
            return

        self._selected_method = radio.get_data('method')
        self.emit('method-changed', self._selected_method)
