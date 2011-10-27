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
"""Payment groups, a set of payments

The two use cases for payment groups are:

  - Sale
  - Purchase

Both of them contains a list of payments and they behaves slightly
differently
"""

from kiwi.argcheck import argcheck
from kiwi.datatypes import currency
from zope.interface import implements

from stoqlib.database.orm import IntCol, ForeignKey
from stoqlib.database.orm import SingleJoin
from stoqlib.database.orm import AND, IN
from stoqlib.domain.base import Domain
from stoqlib.domain.interfaces import IContainer
from stoqlib.domain.payment.payment import Payment
from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class PaymentGroup(Domain):
    """A base class for payment group adapters. """

    (STATUS_INITIAL,
     STATUS_CONFIRMED,
     STATUS_PAID,
     STATUS_CANCELLED) = range(4)

    statuses = {
        STATUS_INITIAL: _(u"Preview"),
        STATUS_CONFIRMED: _(u"Confirmed"),
        STATUS_PAID: _(u"Closed"),
        STATUS_CANCELLED: _(u"Cancelled"),
        }

    implements(IContainer)

    status = IntCol(default=STATUS_INITIAL)
    payer = ForeignKey('Person', default=None)
    recipient = ForeignKey('Person', default=None)
    # This is where this payment group was renegotiated, ie, this payments
    # wore renegotiated in this renegotaition.
    # XXX: Rename to renegotiated
    renegotiation = ForeignKey('PaymentRenegotiation', default=None)

    sale = SingleJoin('Sale', joinColumn='group_id')
    purchase = SingleJoin('PurchaseOrder', joinColumn='group_id')
    # This is the payment group's renegotiation, ie, this payments are part
    # of this renegotiation.
    _renegotiation = SingleJoin('PaymentRenegotiation', joinColumn='group_id')

    #
    # IContainer implementation
    #

    @argcheck(Payment)
    def add_item(self, payment):
        payment.group = self

    @argcheck(Payment)
    def remove_item(self, payment):
        assert payment.group == self, payment.group
        payment.group = None

    def get_items(self):
        conn = self.get_connection()
        return Payment.selectBy(group=self,
                                connection=conn).orderBy(Payment.q.id)

    #
    # Properties
    #

    @property
    def payments(self):
        return self.get_items()

    @property
    def installments_number(self):
        return self.payments.count()

    #
    # Fiscal methods
    #

    def _get_paid_payments(self):
        return Payment.select(AND(Payment.q.groupID == self.id,
                                  IN(Payment.q.status,
                                     [Payment.STATUS_PAID,
                                      Payment.STATUS_REVIEWING,
                                      Payment.STATUS_CONFIRMED])),
                              connection=self.get_connection())

    #
    # Public API
    #

    def can_cancel(self):
        """Everything can be called
        @returns: True if the payment group can be cancelled, otherwise False
        """
        return self.status != PaymentGroup.STATUS_CANCELLED

    def can_confirm(self):
        """Newly created payment groups can be confirmed
        @returns: True if the payment group can be confirmed, otherwise False
        """
        return self.status == PaymentGroup.STATUS_INITIAL

    def can_pay(self):
        """Confirmed payment groups can be paid
        @returns: True if the payment group can be paid, otherwise False
        """
        return self.status == PaymentGroup.STATUS_CONFIRMED

    def confirm(self):
        """Confirms the payment group
        Confirming the payment group means that the customer has
        confirmed the transactions. All individual payments are set to
        pending.
        """
        assert self.can_confirm(), self.get_status_string()

        for payment in self.get_valid_payments():
            payment.set_pending()

        self.status = PaymentGroup.STATUS_CONFIRMED

    def pay(self):
        """Pay all payments in the payment group
        """
        assert self.can_pay(), self.get_status_string()

        for payment in self.get_valid_payments():
            payment.pay()

        self.status = PaymentGroup.STATUS_PAID

    def pay_money_payments(self):
        """Pay all money payments in the payment group
        """
        assert self.can_pay(), self.get_status_string()

        for payment in self.get_valid_payments():
            if payment.method.method_name == 'money':
                payment.pay()

    def cancel(self):
        """Cancel all payments in the payment group
        """
        assert self.can_cancel(), self.get_status_string()

        for payment in self.get_pending_payments():
            payment.cancel()

        self.status = PaymentGroup.STATUS_CANCELLED

    def get_total_paid(self):
        return currency(self._get_paid_payments().sum('value') or 0)

    def get_total_value(self):
        """Returns the sum of all payment values.
        @returns: the total payment value or zero.
        """
        return currency(self.get_valid_payments().sum('value') or 0)

    def clear_unused(self):
        """Delete payments of preview status associated to the current
        payment_group. It can happen if user open and cancel this wizard.
        """
        payments = Payment.selectBy(
            connection=self.get_connection(),
            status=Payment.STATUS_PREVIEW,
            group=self)
        for payment in payments:
            self.remove_item(payment)
            Payment.delete(payment.id, connection=self.get_connection())

    def get_description(self):
        """Returns a small description for the payment group which will be
        used in payment descriptions
        """

        # FIXME: This is hack which won't scale. But I don't know
        #        a better solution right now. Johan 2008-09-25
        if self.sale:
            return _(u'sale %s') % self.sale.get_order_number_str()
        elif self.purchase:
            return _(u'order %s') % self.purchase.id
        elif self._renegotiation:
            return _(u'renegotiation %s') % self._renegotiation.id
        # This breakes the tests.
        #else:
        #    raise AssertionError

    def get_pending_payments(self):
        return Payment.selectBy(group=self,
                                status=Payment.STATUS_PENDING,
                                connection=self.get_connection())

    def get_parent(self):
        """Return the sale, purchase or renegotiation this group is part of"""
        if self.sale:
            return self.sale
        elif self.purchase:
            return self.purchase
        elif self._renegotiation:
            return self._renegotiation
        else:
            raise AssertionError
    #
    # Accessors
    #

    def get_status_string(self):
        if not self.status in PaymentGroup.statuses.keys():
            raise DatabaseInconsistency("Invalid status, got %d"
                                        % self.status)
        return self.statuses[self.status]

    def get_total_discount(self):
        """Returns the sum of all payment discounts.
        @returns: the total payment discount or zero.
        """
        discount = Payment.selectBy(
            group=self, connection=self.get_connection()).sum('discount')

        return currency(discount or 0)

    def get_total_interest(self):
        """Returns the sum of all payment interests.
        @returns: the total payment interest or zero.
        """
        interest = Payment.selectBy(
            group=self, connection=self.get_connection()).sum('interest')

        return currency(interest or 0)

    def get_total_penalty(self):
        """Returns the sum of all payment penalties.
        @returns: the total payment penalty or zero.
        """
        penalty = Payment.selectBy(
            group=self, connection=self.get_connection()).sum('penalty')

        return currency(penalty or 0)

    def get_valid_payments(self):
        """Returns all payments that are not cancelled.
        """
        return Payment.select(AND(Payment.q.groupID == self.id,
                                  Payment.q.status != Payment.STATUS_CANCELLED),
                              connection=self.get_connection())
