# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008 Async Open Source <http://www.async.com.br>
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
""" Slaves for Cash Change """

from kiwi import ValueUnset
from kiwi.datatypes import currency, ValidationError
from kiwi.python import Settable

from stoqlib.domain.sale import Sale
from stoqlib.domain.payment.renegotiation import PaymentRenegotiation
from stoqlib.gui.editors.baseeditor import BaseEditorSlave
from stoqlib.lib.formatters import get_formatted_price
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class CashChangeSlave(BaseEditorSlave):
    """This slave is responsible to calculate paybacks"""

    gladefile = 'CashChangeSlave'
    model_type = object
    proxy_widgets = ('received_value', )

    def __init__(self, conn, model):
        BaseEditorSlave.__init__(self, conn, model)
        self._setup_widgets()

    def _setup_widgets(self):
        self.title_lbl.set_underline(True)
        self.change_value_lbl.set_bold(True)
        self.update_total_sale_amount()

    def _get_total_amount(self):
        if isinstance(self.model, Sale):
            return self.model.get_total_sale_amount()
        elif isinstance(self.model, PaymentRenegotiation):
            return self.model.total
        else:
            raise TypeError

    def setup_proxies(self):
        # Add a proxy just so the validation disables the wizard/editor
        fake_model = Settable(received_value=self._get_total_amount())
        self._proxy = self.add_proxy(fake_model, self.proxy_widgets)

    #
    # Public API
    #

    def enable_cash_change(self):
        self.received_value.set_sensitive(True)
        self.update_total_sale_amount()

    def disable_cash_change(self):
        self.update_total_sale_amount()
        self.received_value.set_sensitive(False)

    def update_total_sale_amount(self):
        value = self._get_total_amount()
        self.received_value.set_text(get_formatted_price(value))

    def get_received_value(self):
        return currency(self.received_value.read())

    def can_finish(self):
        return self.received_value.validate(True) is not ValueUnset

    #
    # Kiwi callbacks
    #

    def on_received_value__validate(self, widget, value):
        sale_amount = self._get_total_amount()
        if value < sale_amount:
            return ValidationError(_(u"The received value must be greater "
                                      "or equal than the sale value."))

    def on_received_value__content_changed(self, widget):
        #XXX: The 'validate' signal was not emitted when there's no
        # proxy attaching widget/model. By calling the validate method
        # works as shortcut to emit the signal properly:
        value = self.received_value.validate(force=True)
        if value is ValueUnset:
            value = '0.0'

        sale_amount = self._get_total_amount()
        change_value = currency(value) - sale_amount
        self.change_value_lbl.set_text(get_formatted_price(change_value))
