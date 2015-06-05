# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2009 Async Open Source
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU Lesser General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
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
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

from kiwi.currency import currency

from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.domain.sale import Sale
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.slaves.paymentslave import (register_payment_slaves,
                                             MultipleMethodSlave)
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class _PaymentsEditor(BaseEditor):
    """Editor that offers a generic entry to input a string value."""
    gladefile = "HolderTemplate"
    title = _('Payments Editor')
    model_type = object
    size = (-1, 400)

    def __init__(self, store, model):
        BaseEditor.__init__(self, store, model)
        self.update_fully_paid(self._slave_valid)

    def update_fully_paid(self, fully_paid):  # pragma no cover
        """This gets called every time the user creates or removes a payment

        Subclasses can override this method if the model requires aditional
        decision if the model is fully paid or not
        """
        pass

    def setup_slaves(self):
        register_payment_slaves()
        self.slave = MultipleMethodSlave(self, self, self.store,
                                         order=self.model,
                                         outstanding_value=currency(0),
                                         finish_on_total=False)
        self.slave.enable_remove()
        self.attach_slave('place_holder', self.slave)

    def on_confirm(self):
        for payment in self.slave.payments:
            if payment.is_preview():
                payment.set_pending()
            # Set the payment status to paid for credit method.
            # This avoid the credit to be used on another sale.
            if payment.is_pending() and payment.method.method_name == u'credit':
                payment.pay()

    # Mimic a Wizard, so that we can use the payment slaves
    def refresh_next(self, valid):
        # setup_slaves gets called before BaseEditor is finished constructing
        # itself. If this is the case, save the valid state so we can refresh
        # later
        if not hasattr(self, 'main_dialog'):
            self._slave_valid = valid
            return

        self.update_fully_paid(valid)

    def disable_back(self):
        pass


class PurchasePaymentsEditor(_PaymentsEditor):
    model_type = PurchaseOrder


class SalePaymentsEditor(_PaymentsEditor):
    model_type = Sale

    def update_fully_paid(self, fully_paid):
        # If the model is not confirmed yet, let the payments be partial.
        # Otherwise, we should require the sale to be fully paid
        if self.model.confirm_date is None or fully_paid:
            self.enable_ok()
        else:
            self.disable_ok()
