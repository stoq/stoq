# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007,2008 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s):   Johan Dahlin <jdahlin@async.com.br>
##              Fabio Morbec <fabio@async.com.br>
##

import datetime

from kiwi.datatypes import converter

from stoqlib.database.orm import AND
from stoqlib.database.orm import Alias, LEFTJOINOn, INNERJOINOn
from stoqlib.database.orm import Viewable
from stoqlib.domain.account import BankAccount
from stoqlib.domain.payment.category import PaymentCategory
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.domain.payment.method import CheckData, PaymentMethod
from stoqlib.domain.payment.payment import (Payment, PaymentAdaptToInPayment,
                                            PaymentAdaptToOutPayment,
                                            PaymentChangeHistory)
from stoqlib.domain.payment.renegotiation import PaymentRenegotiation
from stoqlib.domain.person import Person
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.domain.sale import Sale, SaleView
from stoqlib.lib.translation import stoqlib_gettext


_ = stoqlib_gettext

class InPaymentView(Viewable):
    columns = dict(
        id=Payment.q.id,
        description=Payment.q.description,
        drawee=Person.q.name,
        due_date=Payment.q.due_date,
        status=Payment.q.status,
        paid_date=Payment.q.paid_date,
        value=Payment.q.value,
        paid_value=Payment.q.paid_value,
        sale_id=Sale.q.id,
        color=PaymentCategory.q.color,
        payment_number=Payment.q.payment_number,
        person_id=Person.q.id,
        group_id=Payment.q.groupID,
        method_name=PaymentMethod.q.method_name,
        renegotiation_id=PaymentRenegotiation.q.id,
        renegotiated_id=PaymentGroup.q.renegotiationID,
        )

    joins = [
        INNERJOINOn(None, PaymentAdaptToInPayment,
                    PaymentAdaptToInPayment.q._originalID == Payment.q.id),
        LEFTJOINOn(None, PaymentGroup,
                   PaymentGroup.q.id == Payment.q.groupID),
        LEFTJOINOn(None, Person,
                    PaymentGroup.q.payerID == Person.q.id),
        LEFTJOINOn(None, Sale,
                   Sale.q.groupID == PaymentGroup.q.id),
        LEFTJOINOn(None, PaymentRenegotiation,
                   PaymentRenegotiation.q.groupID == PaymentGroup.q.id),
        LEFTJOINOn(None, PaymentCategory,
                   PaymentCategory.q.id == Payment.q.categoryID),
        INNERJOINOn(None, PaymentMethod,
                    Payment.q.methodID == PaymentMethod.q.id),
        ]

    def can_change_due_date(self):
        return not (self.payment.is_paid() or self.payment.is_cancelled())

    def can_change_payment_status(self):
        # cash receivings can't be changed
        return (self.payment.method.method_name != 'money' and
                self.payment.is_paid())

    def get_status_str(self):
        return Payment.statuses[self.status]

    @property
    def sale(self):
        if self.sale_id:
            return Sale.get(self.sale_id)

    @property
    def payment(self):
        return Payment.get(self.id, connection=self.get_connection())

    @property
    def group(self):
        return PaymentGroup.get(self.group_id, connection=self.get_connection())

    @property
    def renegotiation(self):
        if self.renegotiation_id:
            return PaymentRenegotiation.get(self.renegotiation_id,
                                            connection=self.get_connection())

    @property
    def renegotiated(self):
        if self.renegotiated_id:
            return PaymentRenegotiation.get(self.renegotiated_id,
                                            connection=self.get_connection())

    def get_parent(self):
        return self.sale or self.renegotiation


class OutPaymentView(Viewable):

    columns = dict(
        id=Payment.q.id,
        description=Payment.q.description,
        supplier_name=Person.q.name,
        due_date=Payment.q.due_date,
        status=Payment.q.status,
        paid_date=Payment.q.paid_date,
        value=Payment.q.value,
        paid_value=Payment.q.paid_value,
        purchase_id=PurchaseOrder.q.id,
        sale_id=Sale.q.id,
        color=PaymentCategory.q.color,
        )

    PaymentGroup_Sale = Alias(PaymentGroup, 'payment_group_sale')
    PaymentGroup_Purchase = Alias(PaymentGroup, 'payment_group_purchase')

    joins = [
        INNERJOINOn(None, PaymentAdaptToOutPayment,
                    PaymentAdaptToOutPayment.q._originalID == Payment.q.id),
        LEFTJOINOn(None, PaymentGroup_Purchase,
                   PaymentGroup_Purchase.q.id == Payment.q.groupID),
        LEFTJOINOn(None, PurchaseOrder,
                   PurchaseOrder.q.groupID == PaymentGroup_Purchase.q.id),
        LEFTJOINOn(None, PaymentGroup_Sale,
                   PaymentGroup_Sale.q.id == Payment.q.groupID),
        LEFTJOINOn(None, Sale,
                   Sale.q.groupID == PaymentGroup_Sale.q.id),
        LEFTJOINOn(None, Person,
                   Person.q.id == PaymentGroup_Sale.q.recipientID),
        LEFTJOINOn(None, PaymentCategory,
                   PaymentCategory.q.id == Payment.q.categoryID),
        ]

    def get_status_str(self):
        return Payment.statuses[self.status]

    def can_change_due_date(self):
        return not (self.payment.is_paid() or self.payment.is_cancelled())

    @property
    def purchase(self):
        if self.purchase_id:
            return PurchaseOrder.get(self.purchase_id)

    @property
    def sale(self):
        if self.sale_id:
            return SaleView.select(SaleView.q.id == self.sale_id)[0]

    @property
    def payment(self):
        return Payment.get(self.id, connection=self.get_connection())


class _CheckPaymentView(Viewable):
    """A base view for check and bill payments."""
    columns = dict(
        id=Payment.q.id,
        due_date=Payment.q.due_date,
        paid_date=Payment.q.paid_date,
        status=Payment.q.status,
        value=Payment.q.value,
        payment_number=Payment.q.payment_number,
        bank_id=BankAccount.q.bank_id,
        branch=BankAccount.q.branch,
        account=BankAccount.q.account,
    )

    joins = [
        LEFTJOINOn(None, CheckData, Payment.q.id == CheckData.q.paymentID),
        LEFTJOINOn(None, BankAccount,
                   BankAccount.q.id == CheckData.q.bank_dataID),
    ]

    def get_status_str(self):
        return Payment.statuses[self.status]

    @property
    def payment(self):
        return Payment.get(self.id, connection=self.get_connection())


class InCheckPaymentView(_CheckPaymentView):
    """Stores information about bill and check receivings.
    """
    columns = _CheckPaymentView.columns
    joins = _CheckPaymentView.joins
    clause = AND(PaymentAdaptToInPayment.q._originalID == Payment.q.id)


class OutCheckPaymentView(_CheckPaymentView):
    """Stores information about bill and check payments.
    """
    columns = _CheckPaymentView.columns
    joins = _CheckPaymentView.joins
    clause = AND(PaymentAdaptToOutPayment.q._originalID == Payment.q.id)


class PaymentChangeHistoryView(Viewable):
    """Holds information about changes to a payment.
    """

    columns = dict(
        id=PaymentChangeHistory.q.id,
        description=Payment.q.description,
        reason=PaymentChangeHistory.q.change_reason,
        change_date=PaymentChangeHistory.q.change_date,
        last_due_date=PaymentChangeHistory.q.last_due_date,
        new_due_date=PaymentChangeHistory.q.new_due_date,
        last_status=PaymentChangeHistory.q.last_status,
        new_status=PaymentChangeHistory.q.new_status,
    )

    joins = [
        INNERJOINOn(None, Payment,
                    Payment.q.id == PaymentChangeHistory.q.paymentID)
    ]


    @classmethod
    def select_by_group(cls, group, connection):
        return PaymentChangeHistoryView.select((Payment.q.groupID == group.id),
                                           connection=connection)

    @property
    def changed_field(self):
        """Return the name of the changed field."""

        if self.last_due_date:
            return _('Due Date')
        elif self.last_status:
            return _('Status')

    @property
    def from_value(self):
        if self.last_due_date:
            return converter.as_string(datetime.date, self.last_due_date)
        elif self.last_status:
            return Payment.statuses[self.last_status]

    @property
    def to_value(self):
        if self.new_due_date:
            return converter.as_string(datetime.date, self.new_due_date)
        elif self.new_status:
            return Payment.statuses[self.new_status]

