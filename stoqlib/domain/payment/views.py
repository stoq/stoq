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

from stoqlib.domain.payment.category import PaymentCategory
from stoqlib.domain.payment.methods import MoneyPM
from stoqlib.domain.payment.payment import (Payment, PaymentAdaptToInPayment,
                                            PaymentAdaptToOutPayment,
                                            PaymentChangeHistory)
from stoqlib.domain.person import (Person, PersonAdaptToClient,
                                   PersonAdaptToSupplier)
from stoqlib.domain.purchase import (PurchaseOrder,
                                     PurchaseOrderAdaptToPaymentGroup)
from stoqlib.domain.sale import Sale, SaleAdaptToPaymentGroup, SaleView
from stoqlib.lib.translation import stoqlib_gettext

from sqlobject.sqlbuilder import LEFTJOINOn, INNERJOINOn
from sqlobject.viewable import Viewable

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
        sale_id=Sale.q.id,
        color=PaymentCategory.q.color,
        )

    joins = [
        INNERJOINOn(None, PaymentAdaptToInPayment,
                    PaymentAdaptToInPayment.q._originalID == Payment.q.id),
        LEFTJOINOn(None, SaleAdaptToPaymentGroup,
                   SaleAdaptToPaymentGroup.q.id == Payment.q.groupID),
        LEFTJOINOn(None, Sale,
                   Sale.q.id == SaleAdaptToPaymentGroup.q._originalID),
        LEFTJOINOn(None, PersonAdaptToClient,
                   PersonAdaptToClient.q.id == Sale.q.clientID),
        LEFTJOINOn(None, Person,
                   Person.q.id == PersonAdaptToClient.q._originalID),
        LEFTJOINOn(None, PaymentCategory,
                   PaymentCategory.q.id == Payment.q.categoryID),
        ]

    def can_change_due_date(self):
        return not self.payment.is_paid()

    def can_change_payment_status(self):
        # cash receivings can't be changed
        use_money_method = isinstance(self.payment.method, MoneyPM)
        return not use_money_method and self.payment.is_paid()

    def get_status_str(self):
        return Payment.statuses[self.status]

    @property
    def sale(self):
        if self.sale_id:
            return Sale.get(self.sale_id)

    @property
    def payment(self):
        return Payment.get(self.id, connection=self.get_connection())


class OutPaymentView(Viewable):
    columns = dict(
        id=Payment.q.id,
        description=Payment.q.description,
        supplier_name=Person.q.name,
        due_date=Payment.q.due_date,
        status=Payment.q.status,
        paid_date=Payment.q.paid_date,
        value=Payment.q.value,
        purchase_id=PurchaseOrder.q.id,
        sale_id=Sale.q.id,
        color=PaymentCategory.q.color,
        )

    joins = [
        INNERJOINOn(None, PaymentAdaptToOutPayment,
                    PaymentAdaptToOutPayment.q._originalID == Payment.q.id),
        LEFTJOINOn(None, PurchaseOrderAdaptToPaymentGroup,
                   PurchaseOrderAdaptToPaymentGroup.q.id == Payment.q.groupID),
        LEFTJOINOn(None, PurchaseOrder,
                   PurchaseOrder.q.id == PurchaseOrderAdaptToPaymentGroup.q._originalID),
        LEFTJOINOn(None, SaleAdaptToPaymentGroup,
                   SaleAdaptToPaymentGroup.q.id == Payment.q.groupID),
        LEFTJOINOn(None, Sale,
                   Sale.q.id == SaleAdaptToPaymentGroup.q._originalID),
        LEFTJOINOn(None, PersonAdaptToSupplier,
                    PersonAdaptToSupplier.q.id == PurchaseOrder.q.supplierID),
        LEFTJOINOn(None, Person,
                   Person.q.id == PersonAdaptToSupplier.q._originalID),
        LEFTJOINOn(None, PaymentCategory,
                   PaymentCategory.q.id == Payment.q.categoryID),
        ]

    def get_status_str(self):
        return Payment.statuses[self.status]

    def can_change_due_date(self):
        return not self.payment.is_paid()

    @property
    def purchase(self):
        if self.purchase_id:
            return PurchaseOrder.get(self.purchase_id)

    @property
    def sale(self):
        if self.sale_id:
            return SaleView.get(self.sale_id)

    @property
    def payment(self):
        return Payment.get(self.id, connection=self.get_connection())

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

