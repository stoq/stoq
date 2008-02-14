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
##
##

import datetime

from kiwi.datatypes import ValidationError

from stoqlib.database.runtime import get_current_user
from stoqlib.domain.payment.payment import PaymentDueDateInfo
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.domain.sale import Sale
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.message import warning
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class PaymentDueDateChangeDialog(BaseEditor):
    """ This dialog is responsible to change a payment due date """

    title = _(u"Change Due Date")
    size = (450, 250)
    model_type = PaymentDueDateInfo
    gladefile = "PaymentDueDateChangeDialog"
    payment_widgets = ('due_date',)
    due_date_info_widgets = ('due_date_change_reason',)

    def __init__(self, conn, payment, order=None):
        self._order = order
        self._payment = payment
        BaseEditor.__init__(self, conn)
        self._setup_widgets()

    def _setup_widgets(self):
        self.order_number_lbl.set_text(self._get_order_number())

        self.name_lbl.set_text(self._get_person_name())

        due_date_str = self._payment.due_date.strftime("%x")
        msg = _(u"Set current due date (%s) to:") % due_date_str
        self.due_date_lbl.set_text(msg)

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
        user = get_current_user(conn)
        model = self._payment.get_due_date_info()
        if model is not None:
            model.last_due_date = self._payment.due_date
            model.change_date = datetime.date.today()
            model.responsible = user
            return model

        return PaymentDueDateInfo(last_due_date=self._payment.due_date,
                                  payment=self._payment,
                                  responsible=user,
                                  connection=conn)

    def setup_proxies(self):
        self.add_proxy(self._payment, self.payment_widgets)
        self.add_proxy(self.model, self.due_date_info_widgets)

    def validate_confirm(self):
        if not self.model.due_date_change_reason:
            msg = _(u'You can not change the due date without a reason!')
            warning(msg)
            return False
        return True

    #
    # Kiwi callbacks
    #

    def on_due_date__validate(self, widget, value):
        if value <= datetime.date.today():
            msg = _(u"The due date must be set to a future date.")
            return ValidationError(msg)
