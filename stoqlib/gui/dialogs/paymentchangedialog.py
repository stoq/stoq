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
##

from kiwi.datatypes import ValidationError

from stoqlib.domain.payment.payment import Payment, PaymentChangeHistory
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.domain.sale import Sale
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.dateutils import localtoday
from stoqlib.lib.message import warning
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class _BasePaymentChangeDialog(BaseEditor):
    """This dialog is responsible to change a payment"""

    title = _(u"Change Payment")
    size = (-1, 250)
    model_type = PaymentChangeHistory
    gladefile = "PaymentChangeDialog"
    history_widgets = ('change_reason', )
    payment_widgets = ()

    def __init__(self, store, payment, order=None):
        self._order = order
        self._payment = payment
        BaseEditor.__init__(self, store)
        self._setup_widgets()

    def _setup_widgets(self):
        self.identifier.set_text(self._get_identifier())
        self.name_lbl.set_text(self._get_person_name())
        self.status_lbl2.hide()
        self.target_status_combo.hide()

    def _get_identifier(self):
        if self._order:
            return unicode(self._order.identifier)
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
        # Lonely payments case
        if self._order is None:
            group = self._payment.group
            if group.payer is not None:
                return group.payer.name
            elif group.recipient is not None:
                return group.recipient.name
        # Fallback
        return _(u"No client or supplier")

    #
    # BaseEditor Hooks
    #

    def create_model(self, store):
        return PaymentChangeHistory(payment=self._payment,
                                    store=store)

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

    def get_payment(self):
        return self._payment

    def get_validate_message(self):  # pragma: no cover
        """Defines a message to pop out to the user when the
        validation fails.
        """
        raise NotImplementedError


class _TempDateModel(object):
    due_date = None


class PaymentDueDateChangeDialog(_BasePaymentChangeDialog):
    """This dialog is responsible to change a payment due date"""
    title = _(u"Change payment due date")

    def _setup_widgets(self):
        _BasePaymentChangeDialog._setup_widgets(self)
        self.status_box.hide()
        # There was a bug wher payment.due_date was set to None :(
        if self._payment.due_date:
            due_date_str = self._payment.due_date.strftime("%x")
        msg = _(u"Set current due date (%s) to:") % due_date_str
        self.due_date_lbl.set_text(msg)

    #
    # _BasePaymentChangeDialog
    #

    def get_validate_message(self):
        return _(u'You can not change the due date without a reason!')

    #
    # BaseEditor Hooks
    #

    def setup_proxies(self):
        _BasePaymentChangeDialog.setup_proxies(self)

        self._temp_model = _TempDateModel()
        self._date_proxy = self.add_proxy(self._temp_model, ('due_date', ))

    def create_model(self, store):
        model = _BasePaymentChangeDialog.create_model(self, store)
        model.last_due_date = self._payment.due_date
        return model

    def on_confirm(self):
        self._payment.change_due_date(self._temp_model.due_date)
        self.model.new_due_date = self._payment.due_date

    #
    # Kiwi callbacks
    #

    def on_due_date__validate(self, widget, value):
        if value < localtoday().date():
            msg = _(u"The due date must be set to today or a future date.")
            return ValidationError(msg)


class PaymentStatusChangeDialog(_BasePaymentChangeDialog):
    """This dialog is responsible to change a payment status"""

    title = _(u"Change Payment Status")
    payment_widgets = ('status_combo', )

    def __init__(self, store, payment, target_status, order=None):
        self._target_status = target_status
        assert self._target_status in Payment.statuses, self._target_status

        _BasePaymentChangeDialog.__init__(self, store, payment, order)

    def _setup_widgets(self):
        _BasePaymentChangeDialog._setup_widgets(self)
        self.due_date_box.hide()
        self.status_combo.set_sensitive(False)

        self.target_status_combo.select_item_by_data(self._target_status)
        self.target_status_combo.set_sensitive(False)
        self.target_status_combo.show()
        self.status_lbl2.show()

    def setup_proxies(self):
        self._setup_combo()
        _BasePaymentChangeDialog.setup_proxies(self)

    def _setup_combo(self):
        items = [(Payment.statuses[id], id) for id in Payment.statuses]
        self.status_combo.prefill(items)
        self.target_status_combo.prefill(items)

    #
    # BaseEditor Hooks
    #
    def create_model(self, store):
        return _BasePaymentChangeDialog.create_model(self, store)

    def on_confirm(self):
        payment = self.get_payment()

        if self._target_status == Payment.STATUS_CANCELLED:
            payment.cancel(self.model)
        elif self._target_status == Payment.STATUS_PENDING:
            payment.set_not_paid(self.model)
        else:
            raise AssertionError("status change not implemented")

    #
    # _BasePaymentChangeDialog
    #

    def get_validate_message(self):
        return _(u'You can not change the payment status without '
                 'a reason!')
