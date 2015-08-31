# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007-2010 Async Open Source <http://www.async.com.br>
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

# pylint: enable=E1101

import datetime

from dateutil.relativedelta import relativedelta
from kiwi.datatypes import converter
from storm.expr import (And, Count, Join, LeftJoin, Or, Sum, Alias,
                        Select, Cast)
from storm.info import ClassAlias

from stoqlib.database.expr import Date, Field
from stoqlib.database.viewable import Viewable
from stoqlib.domain.account import BankAccount
from stoqlib.domain.payment.card import (CreditProvider,
                                         CreditCardData, CardPaymentDevice)
from stoqlib.domain.payment.category import PaymentCategory
from stoqlib.domain.payment.comment import PaymentComment
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.domain.payment.method import CheckData, PaymentMethod
from stoqlib.domain.payment.operation import get_payment_operation
from stoqlib.domain.payment.payment import Payment, PaymentChangeHistory
from stoqlib.domain.payment.renegotiation import PaymentRenegotiation
from stoqlib.domain.person import Person, Branch
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.domain.sale import Sale
from stoqlib.lib.dateutils import localtoday
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext


_ = stoqlib_gettext


_CommentsSummary = Select(columns=[PaymentComment.payment_id,
                                   Alias(Count(PaymentComment.id), 'comments_number')],
                          tables=[PaymentComment],
                          group_by=[PaymentComment.payment_id]),
CommentsSummary = Alias(_CommentsSummary, '_comments')


class BasePaymentView(Viewable):
    PaymentGroup_Sale = ClassAlias(PaymentGroup, 'payment_group_sale')
    PaymentGroup_Purchase = ClassAlias(PaymentGroup, 'payment_group_purchase')

    payment = Payment
    group = PaymentGroup
    purchase = PurchaseOrder
    sale = Sale
    method = PaymentMethod
    branch = Branch

    card_data = CreditCardData
    check_data = CheckData

    # Payment
    id = Payment.id
    identifier = Payment.identifier
    identifier_str = Cast(Payment.identifier, 'text')
    description = Payment.description
    due_date = Payment.due_date
    status = Payment.status
    paid_date = Payment.paid_date
    value = Payment.value
    paid_value = Payment.paid_value
    payment_number = Payment.payment_number
    group_id = Payment.group_id

    branch_id = Payment.branch_id

    # PaymentGroup
    renegotiated_id = PaymentGroup.renegotiation_id

    # PaymentMethod
    method_name = PaymentMethod.method_name
    method_id = PaymentMethod.id

    # PaymentCategory
    color = PaymentCategory.color
    category = PaymentCategory.name

    # PaymentComment
    comments_number = Field('_comments', 'comments_number')

    # Sale
    sale_id = Sale.id

    # Purchase
    purchase_id = PurchaseOrder.id

    _count_tables = [
        Payment,
        Join(Branch, Payment.branch_id == Branch.id),
        LeftJoin(PaymentGroup, PaymentGroup.id == Payment.group_id),
        LeftJoin(PaymentCategory, PaymentCategory.id == Payment.category_id),
        Join(PaymentMethod, Payment.method_id == PaymentMethod.id),
        LeftJoin(CreditCardData, Payment.id == CreditCardData.payment_id),
        LeftJoin(CheckData, Payment.id == CheckData.payment_id),

        # Purchase
        LeftJoin(PaymentGroup_Purchase, PaymentGroup_Purchase.id == Payment.group_id),
        LeftJoin(PurchaseOrder, PurchaseOrder.group_id == PaymentGroup_Purchase.id),

        # Sale
        LeftJoin(PaymentGroup_Sale, PaymentGroup_Sale.id == Payment.group_id),
        LeftJoin(Sale, Sale.group_id == PaymentGroup_Sale.id),
    ]

    tables = _count_tables + [
        LeftJoin(CommentsSummary, Field('_comments', 'payment_id') == Payment.id),
    ]

    #
    # Private
    #

    def _get_due_date_delta(self):
        if self.status in [Payment.STATUS_PAID, Payment.STATUS_CANCELLED]:
            return datetime.timedelta(0)

        return localtoday().date() - self.due_date.date()

    #
    # Public API
    #

    @classmethod
    def post_search_callback(cls, sresults):
        select = sresults.get_select_expr(Count(1), Sum(cls.value))
        return ('count', 'sum'), select

    def can_change_due_date(self):
        return self.status not in [Payment.STATUS_PAID,
                                   Payment.STATUS_CANCELLED]

    def can_cancel_payment(self):
        """Only  lonely payments and pending can be cancelled
        """
        if self.sale_id or self.purchase_id:
            return False

        return self.status == Payment.STATUS_PENDING

    @property
    def method_description(self):
        return self.method.description

    @property
    def status_str(self):
        return Payment.statuses[self.status]

    def is_late(self):
        return self._get_due_date_delta().days > 0

    def get_days_late(self):
        return max(self._get_due_date_delta().days, 0)

    def is_paid(self):
        return self.status == Payment.STATUS_PAID

    @property
    def operation(self):
        return self.method.operation

    @classmethod
    def find_pending(cls, store, due_date=None):
        query = cls.status == Payment.STATUS_PENDING

        if due_date:
            if isinstance(due_date, tuple):
                date_query = And(Date(cls.due_date) >= due_date[0],
                                 Date(cls.due_date) <= due_date[1])
            else:
                date_query = Date(cls.due_date) == due_date

            query = And(query, date_query)

        return store.find(cls, query)


class InPaymentView(BasePaymentView):
    drawee = Person.name
    person_id = Person.id
    renegotiated_id = PaymentGroup.renegotiation_id
    renegotiation_id = PaymentRenegotiation.id

    _count_tables = BasePaymentView._count_tables[:]
    _count_tables.append(
        LeftJoin(Person,
                 PaymentGroup.payer_id == Person.id))

    tables = BasePaymentView.tables[:]
    tables.extend([
        LeftJoin(Person, PaymentGroup.payer_id == Person.id),
        LeftJoin(PaymentRenegotiation,
                 PaymentRenegotiation.group_id == PaymentGroup.id),
    ])

    clause = (Payment.payment_type == Payment.TYPE_IN)

    @property
    def renegotiation(self):
        if self.renegotiation_id:
            return self.store.get(PaymentRenegotiation, self.renegotiation_id)

    @property
    def renegotiated(self):
        if self.renegotiated_id:
            return self.store.get(PaymentRenegotiation, self.renegotiated_id)

    def get_parent(self):
        return self.sale or self.renegotiation

    @classmethod
    def has_late_payments(cls, store, person):
        """Checks if the provided person has unpaid payments that are overdue

        :param person: A :class:`person <stoqlib.domain.person.Person>` to
          check if has late payments
        :returns: True if the person has overdue payments. False otherwise
        """
        tolerance = sysparam.get_int('TOLERANCE_FOR_LATE_PAYMENTS')

        query = And(
            cls.person_id == person.id,
            cls.status == Payment.STATUS_PENDING,
            cls.due_date < localtoday() - relativedelta(days=tolerance))

        for late_payments in store.find(cls, query):
            sale = late_payments.sale
            # Exclude payments for external sales as they are handled by an
            # external entity (e.g. a payment gateway) meaning that they be
            # out of sync with the Stoq database.
            if not sale or not sale.is_external():
                return True

        return False


class OutPaymentView(BasePaymentView):
    supplier_name = Person.name

    _count_tables = BasePaymentView._count_tables[:]
    _count_tables.append(
        LeftJoin(Person,
                 BasePaymentView.PaymentGroup_Sale.recipient_id == Person.id))

    tables = BasePaymentView.tables[:]
    tables.extend([
        LeftJoin(Person,
                 Person.id == BasePaymentView.PaymentGroup_Sale.recipient_id),
    ])

    clause = (Payment.payment_type == Payment.TYPE_OUT)


class CardPaymentView(Viewable):
    """A view for credit providers."""
    _DraweePerson = ClassAlias(Person, "drawee_person")

    payment = Payment
    credit_card_data = CreditCardData

    #: the branch this payment was created on
    branch = Branch

    # Payment Columns
    id = Payment.id
    identifier = Payment.identifier
    identifier_str = Cast(Payment.identifier, 'text')
    description = Payment.description
    due_date = Payment.due_date
    paid_date = Payment.paid_date
    status = Payment.status
    value = Payment.value

    # CreditCardData
    fare = CreditCardData.fare
    fee = CreditCardData.fee
    fee_calc = CreditCardData.fee_value
    card_type = CreditCardData.card_type
    auth = CreditCardData.auth

    device_id = CardPaymentDevice.id
    device_name = CardPaymentDevice.description

    drawee_name = _DraweePerson.name
    provider_name = CreditProvider.short_name
    sale_id = Sale.id
    renegotiation_id = PaymentRenegotiation.id

    tables = [
        Payment,
        Join(PaymentMethod, PaymentMethod.id == Payment.method_id),
        Join(CreditCardData, CreditCardData.payment_id == Payment.id),
        Join(CreditProvider, CreditProvider.id == CreditCardData.provider_id),
        Join(Branch, Branch.id == Payment.branch_id),
        LeftJoin(CardPaymentDevice, CardPaymentDevice.id == CreditCardData.device_id),
        LeftJoin(PaymentGroup, PaymentGroup.id == Payment.group_id),
        LeftJoin(_DraweePerson, _DraweePerson.id == PaymentGroup.payer_id),
        LeftJoin(Sale, Sale.group_id == PaymentGroup.id),
        LeftJoin(PaymentRenegotiation,
                 PaymentRenegotiation.group_id == PaymentGroup.id),
    ]

    @property
    def status_str(self):
        return Payment.statuses[self.status]

    @property
    def renegotiation(self):
        if self.renegotiation_id:
            return self.store.get(PaymentRenegotiation, self.renegotiation_id)


class _BillandCheckPaymentView(Viewable):
    """A base view for check and bill payments."""

    payment = Payment

    #: The branch this paymet was created on
    branch = Branch

    id = Payment.id
    identifier = Payment.identifier
    due_date = Payment.due_date
    paid_date = Payment.paid_date
    status = Payment.status
    value = Payment.value
    payment_number = Payment.payment_number
    method_name = PaymentMethod.method_name
    bank_number = BankAccount.bank_number
    bank_branch = BankAccount.bank_branch
    bank_account = BankAccount.bank_account

    tables = [
        Payment,
        Join(Branch, Payment.branch_id == Branch.id),
        LeftJoin(CheckData, Payment.id == CheckData.payment_id),
        Join(PaymentMethod, Payment.method_id == PaymentMethod.id),
        LeftJoin(BankAccount, BankAccount.id == CheckData.bank_account_id),
    ]

    clause = Or(PaymentMethod.method_name == u'bill',
                PaymentMethod.method_name == u'check')

    @property
    def status_str(self):
        return Payment.statuses[self.status]

    @property
    def method_description(self):
        return get_payment_operation(self.method_name).description


class InCheckPaymentView(_BillandCheckPaymentView):
    """Stores information about bill and check receivings.
    """
    clause = And(_BillandCheckPaymentView.clause,
                 Payment.payment_type == Payment.TYPE_IN)


class OutCheckPaymentView(_BillandCheckPaymentView):
    """Stores information about bill and check payments.
    """
    bill_received = Payment.bill_received

    clause = And(_BillandCheckPaymentView.clause,
                 Payment.payment_type == Payment.TYPE_OUT)


class PaymentChangeHistoryView(Viewable):
    """Holds information about changes to a payment.
    """

    id = PaymentChangeHistory.id
    description = Payment.description
    reason = PaymentChangeHistory.change_reason
    change_date = PaymentChangeHistory.change_date
    last_due_date = PaymentChangeHistory.last_due_date
    new_due_date = PaymentChangeHistory.new_due_date
    last_status = PaymentChangeHistory.last_status
    new_status = PaymentChangeHistory.new_status

    tables = [
        PaymentChangeHistory,
        Join(Payment, Payment.id == PaymentChangeHistory.payment_id)
    ]

    @classmethod
    def find_by_group(cls, store, group):
        return store.find(cls, Payment.group_id == group.id)

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
