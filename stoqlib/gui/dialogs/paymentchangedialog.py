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
## Author(s):   George Kussumoto        <george@async.com.br>
##              Ronaldo Maia            <romaia@async.com.br>
##
##

import datetime

from kiwi.datatypes import ValidationError

from stoqlib.domain.payment.payment import Payment, PaymentChangeHistory
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.domain.sale import Sale
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.message import warning
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class BasePaymentChangeDialog(BaseEditor):
    """This dialog is responsible to change a payment"""

    title = _(u"Change Payment")
    size = (450, 250)
    model_type = PaymentChangeHistory
    gladefile = "PaymentChangeDialog"
    history_widgets = ('change_reason',)

    def __init__(self, conn, payment, order=None):
        self._order = order
        self._payment = payment
        BaseEditor.__init__(self, conn)
        self._setup_widgets()

    def _setup_widgets(self):
        self.order_number_lbl.set_text(self._get_order_number())
        self.name_lbl.set_text(self._get_person_name())

    def _get_order_number(self):
        if self._order:
            return u"%05d" % self._order.id
        else:
            return self._payment.description

    def _get_person_name(self):
        someone = None
        if isinstance(self._order, Sale):
            someone = self._order.client
        elif isinstance(self._order, PurchaseOrder):
            self.client_supplier_lbl.set_text(_(u"Supplier:"))
            someone = self._order.supplier

        if someone is not None:
            return someone.person.name
        return _(u"No client or supplier")

    #
    # BaseEditor Hooks
    #

    def create_model(self, conn):
        return PaymentChangeHistory(payment=self._payment,
                                    connection=conn)

    def setup_proxies(self):
        self.add_proxy(self._payment, self.payment_widgets)
        self.add_proxy(self.model, self.history_widgets)

    def validate_confirm(self):
        if not self.model.change_reason:
            msg = self.get_validate_message()
            if bool(msg):
                warning(msg)
            return False
        return True

    #
    # Public API
    #

    def get_validate_message(self):
        """Defines a message to pop out to the user when the
        validation fails.
        """
        pass


class PaymentDueDateChangeDialog(BasePaymentChangeDialog):
    """This dialog is responsible to change a payment due date"""
    title = _(u"Change Payment Due Date")
    payment_widgets = ('due_date',)

    def _setup_widgets(self):
        BasePaymentChangeDialog._setup_widgets(self)
        self.status_box.hide()
        due_date_str = self._payment.due_date.strftime("%x")
        msg = _(u"Set current due date (%s) to:") % due_date_str
        self.due_date_lbl.set_text(msg)

    #
    # BasePaymentChangeDialog
    #

    def get_validate_message(self):
        return _(u'You can not change the due date without a reason!')

    #
    # BaseEditor Hooks
    #

    def create_model(self, conn):
        model = BasePaymentChangeDialog.create_model(self, conn)
        model.last_due_date = self._payment.due_date
        return model

    def on_confirm(self):
        self.model.new_due_date = self._payment.due_date
        return self.model

    #
    # Kiwi callbacks
    #

    def on_due_date__validate(self, widget, value):
        if value < datetime.date.today():
            msg = _(u"The due date must be set to today or a future date.")
            return ValidationError(msg)


class PaymentStatusChangeDialog(BasePaymentChangeDialog):
    """This dialog is responsible to change a payment status"""

    title = _(u"Change Payment Status")
    payment_widgets = ('status_combo',)

    def _setup_widgets(self):
        BasePaymentChangeDialog._setup_widgets(self)
        self.due_date_box.hide()
        self.status_combo.set_sensitive(False)

    def setup_proxies(self):
        self._setup_combo()
        BasePaymentChangeDialog.setup_proxies(self)

    def _setup_combo(self):
        items = [(Payment.statuses[id], id) for id in Payment.statuses]
        self.status_combo.prefill(items)

    #
    # BaseEditor Hooks
    #
    def create_model(self, conn):
        change_entry = BasePaymentChangeDialog.create_model(self, conn)
        self._payment.set_not_paid(change_entry)
        return change_entry

    #
    # BasePaymentChangeDialog
    #

    def get_validate_message(self):
        return _(u'You can not change the payment status without '
                 'a reason!')
