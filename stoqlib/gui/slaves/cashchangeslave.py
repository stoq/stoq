# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008-2013 Async Open Source <http://www.async.com.br>
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
from kiwi.currency import currency
from kiwi.datatypes import ValidationError

from stoqlib.enums import ReturnPolicy
from stoqlib.gui.editors.baseeditor import BaseEditorSlave
from stoqlib.lib.formatters import get_formatted_price
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class CashChangeSlave(BaseEditorSlave):
    """This slave is responsible to calculate paybacks"""

    gladefile = 'CashChangeSlave'
    model_type = object

    def __init__(self, store, model, wizard):
        self.wizard = wizard
        BaseEditorSlave.__init__(self, store, model)
        self._setup_widgets()

    def _setup_widgets(self):
        self.change_value_lbl.set_bold(True)
        self.update_total_sale_amount(self.wizard.get_total_amount())
        self._update_change()

    #
    # Public API
    #

    def enable_cash_change(self):
        self.received_value.set_sensitive(True)
        self._update_change()

    def disable_cash_change(self):
        self.received_value.set_sensitive(False)
        self._update_change()

    def update_total_sale_amount(self, value):
        if value < 0:
            # Setting this to 0 will make it be considered a change,
            # since the client can't pay a negative amount of money
            value = 0
        self.received_value.set_text(get_formatted_price(value))

    def get_received_value(self):
        return currency(self.received_value.read())

    def can_finish(self):
        return self.received_value.validate(True) is not ValueUnset

    #
    # Kiwi callbacks
    #

    def on_received_value__validate(self, widget, value):
        sale_amount = currency(self.wizard.get_total_amount() -
                               self.wizard.get_total_paid())
        if value < sale_amount:
            return ValidationError(_(u"The received value must be greater "
                                     "or equal than the sale value."))

    def on_received_value__content_changed(self, widget):
        self._update_change()

    def _update_change(self):
        # XXX: The 'validate' signal was not emitted when there's no
        # proxy attaching widget/model. By calling the validate method
        # works as shortcut to emit the signal properly:
        value = self.received_value.validate(force=True)
        if value is ValueUnset:
            value = '0.0'

        sale_amount = (self.wizard.get_total_amount() -
                       self.wizard.get_total_paid())
        change_value = currency(value) - sale_amount
        self.change_value_lbl.set_text(get_formatted_price(change_value))

        # There is some change for the clientchange, but we cannot edit the
        # received value. This means that the client has already paid more than
        # the total sale amount.
        if change_value > 0 and not self.received_value.get_sensitive():
            self.credit_checkbutton.set_visible(True)
            policy = sysparam.get_int('RETURN_POLICY_ON_SALES')
            self.credit_checkbutton.set_sensitive(policy == ReturnPolicy.CLIENT_CHOICE)
            self.credit_checkbutton.set_active(policy == ReturnPolicy.RETURN_CREDIT)
        else:
            self.credit_checkbutton.set_visible(False)
