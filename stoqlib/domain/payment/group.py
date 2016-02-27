# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2013 Async Open Source <http://www.async.com.br>
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

The five use cases for payment groups are:

  - Sale
  - Purchase
  - Renegotiation
  - Stockdecreae
  - Lonely payments

All of them contains a set of payments and they behaves slightly
differently
"""

# pylint: enable=E1101

from kiwi.currency import currency
from storm.expr import And, In, Not
from storm.references import Reference
from zope.interface import implementer

from stoqlib.database.properties import IdCol
from stoqlib.domain.base import Domain
from stoqlib.domain.events import PaymentGroupGetOrderEvent
from stoqlib.domain.interfaces import IContainer
from stoqlib.domain.payment.payment import Payment
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


@implementer(IContainer)
class PaymentGroup(Domain):
    """A set of |payments|, all related to the same
    |sale|, |purchase|, |paymentrenegotiation| or |stockdecrease|.
    The set of payments can also be lonely, eg not associated with one of
    objects mentioned above.

    A payer is paying the recipient who's receiving the |payments|.
    """

    __storm_table__ = 'payment_group'

    payer_id = IdCol(default=None)

    #: the |person| who is paying this group
    payer = Reference(payer_id, 'Person.id')

    recipient_id = IdCol(default=None)

    #: the |person| who is receiving this group
    recipient = Reference(recipient_id, 'Person.id')

    # XXX: Rename to renegotiated
    renegotiation_id = IdCol(default=None)

    #: the payment renegotation this group belongs to
    renegotiation = Reference(renegotiation_id, 'PaymentRenegotiation.id')

    #: The |sale| if this group is part of one
    sale = Reference('id', 'Sale.group_id', on_remote=True)

    #: The |purchase| if this group is part of one
    purchase = Reference('id', 'PurchaseOrder.group_id', on_remote=True)

    #: the payment renegotation the |payments| of this group belongs to
    _renegotiation = Reference('id', 'PaymentRenegotiation.group_id', on_remote=True)

    #: The |stockdecrease| if this group is part of one
    stock_decrease = Reference('id', 'StockDecrease.group_id', on_remote=True)

    #
    # IContainer implementation
    #

    def add_item(self, payment):
        payment.group = self

    def remove_item(self, payment):
        assert payment.group == self, payment.group
        payment.group = None

    def get_items(self):
        store = self.store
        return store.find(Payment, group=self).order_by(
            Payment.due_date, Payment.identifier)

    #
    # Properties
    #

    @property
    def payments(self):
        """Returns all payments of this group

        :returns: a list of |payments|
        """
        return self.get_items()

    @property
    def installments_number(self):
        """The number of installments(|payments|) that are part of this group."""
        return self.payments.count()

    #
    # Private
    #

    def _get_paid_payments(self):
        return self.store.find(Payment,
                               And(Payment.group_id == self.id,
                                   In(Payment.status,
                                      [Payment.STATUS_PAID,
                                       Payment.STATUS_REVIEWING,
                                       Payment.STATUS_CONFIRMED])))

    def _get_preview_payments(self):
        return self.store.find(Payment,
                               status=Payment.STATUS_PREVIEW,
                               group=self)

    def _get_payments_sum(self, payments, attr):
        in_payments_value = payments.find(
            Payment.payment_type == Payment.TYPE_IN).sum(attr) or 0
        out_payments_value = payments.find(
            Payment.payment_type == Payment.TYPE_OUT).sum(attr) or 0

        if self.sale or self._renegotiation:
            return currency(in_payments_value - out_payments_value)
        elif self.purchase:
            return currency(out_payments_value - in_payments_value)

        # FIXME: Is this right for payments not linked to a
        #        sale/purchase/renegotiation?
        return currency(payments.sum(attr) or 0)

    #
    # Public API
    #

    def get_order_object(self):
        """Get the order object related to this payment group"""
        for obj in [self.sale, self.purchase, self._renegotiation,
                    self.stock_decrease]:
            if obj is not None:
                return obj

        return PaymentGroupGetOrderEvent.emit(self, self.store)

    def confirm(self):
        """Confirms all |payments| in this group

        Confirming the payment group means that the customer has
        confirmed the payments. All individual payments are set to
        pending.
        """
        for payment in self._get_preview_payments():
            payment.set_pending()

    def pay(self):
        """Pay all |payments| in this group
        """
        for payment in self.get_valid_payments():
            if payment.is_paid():
                continue
            payment.pay()

    def pay_method_payments(self, method_name):
        """Pay all |payments| of a method in this group

        :param method_name: the method of the payments to be paid
        """
        for payment in self.get_valid_payments():
            if payment.is_of_method(method_name) and not payment.is_paid():
                payment.pay()

    def cancel(self):
        """Cancel all pending |payments| in this group
        """
        for payment in self.get_pending_payments():
            if not payment.is_cancelled():
                payment.cancel()

    def get_total_paid(self):
        """Returns the sum of all paid |payment| values within this group.

        :returns: the total paid value
        """
        return self._get_payments_sum(self._get_paid_payments(),
                                      Payment.value)

    def get_total_value(self):
        """Returns the sum of all |payment| values.

        This will consider all payments ignoring just the cancelled ones.

        If you want to ignore preview payments too, use
        :meth:`.get_total_confirmed_value` instead

        :returns: the total payment value or zero.
        """
        return self._get_payments_sum(self.get_valid_payments(),
                                      Payment.value)

    def get_total_to_pay(self):
        """Returns the total amount to be paid to have the group fully paid.
        """
        payments = self.store.find(
            Payment,
            And(Payment.group_id == self.id,
                Payment.status == Payment.STATUS_PENDING))

        return self._get_payments_sum(payments, Payment.value)

    def get_total_confirmed_value(self):
        """Returns the sum of all confirmed payments values

        This will consider all payments ignoring cancelled and preview
        ones, that is, if a payment is confirmed/reviewing/paid it will
        be summed.

        If you want to consider the preview ones too, use
        :meth:`.get_total_value` instead

        :returns: the total confirmed payments value
        """
        payments = self.store.find(
            Payment,
            And(Payment.group_id == self.id,
                Not(In(Payment.status,
                       [Payment.STATUS_CANCELLED, Payment.STATUS_PREVIEW]))))

        return self._get_payments_sum(payments, Payment.value)

    # FIXME: with proper database transactions we can probably remove this
    def clear_unused(self):
        """Delete payments of preview status associated to the current
        payment_group. It can happen if user open and cancel this wizard.
        """
        for payment in self._get_preview_payments():
            self.remove_item(payment)
            payment.delete()

    def get_description(self):
        """Returns a small description for the payment group which will be
        used in payment descriptions

        :returns: the description
        """
        # FIXME: Now that we have a get_order_object, we can ask each of
        # those objects (Sale, PurchaseOrder, etc) to describe themselves
        # and remove those if/elifs bellow
        if self.sale:
            return _(u'sale %s') % self.sale.identifier
        elif self.purchase:
            return _(u'order %s') % self.purchase.identifier
        elif self._renegotiation:
            return _(u'renegotiation %s') % self._renegotiation.identifier
        elif self.stock_decrease:
            return _(u'stock decrease %s') % self.stock_decrease.identifier

        order_obj = self.get_order_object()
        # FIXME: Add a proper description when there's no order_obj
        return order_obj.payment_description if order_obj else u''

    def get_pending_payments(self):
        """Returns a list of pending |payments|
        :returns: list of |payments|
        """
        return self.store.find(Payment, group=self,
                               status=Payment.STATUS_PENDING)

    def get_parent(self):
        """Return the |sale|, |purchase|, |paymentrenegotiation| or
        |stockdecrease| this group is part of.

        :returns: the object this group is part of or ``None``
        """
        if self.sale:
            return self.sale
        elif self.purchase:
            return self.purchase
        elif self._renegotiation:
            return self._renegotiation
        elif self.stock_decrease:
            return self.stock_decrease
        return None

    def get_total_discount(self):
        """Returns the sum of all |payment| discounts.

        :returns: the total payment discount or zero.
        """
        return self._get_payments_sum(self.get_valid_payments(),
                                      Payment.discount)

    def get_total_interest(self):
        """Returns the sum of all |payment| interests.

        :returns: the total payment interest or zero.
        """
        return self._get_payments_sum(self.get_valid_payments(),
                                      Payment.interest)

    def get_total_penalty(self):
        """Returns the sum of all |payment| penalties.

        :returns: the total payment penalty or zero.
        """
        return self._get_payments_sum(self.get_valid_payments(),
                                      Payment.penalty)

    def get_valid_payments(self):
        """Returns all |payments| that are not cancelled.

        :returns: list of |payments|
        """
        return self.store.find(Payment,
                               And(Payment.group_id == self.id,
                                   Payment.status != Payment.STATUS_CANCELLED))

    def get_payments_by_method_name(self, method_name):
        """Returns all |payments| of a specific |paymentmethod| within this group.

        :param unicode method_name: the name of the method
        :returns: list of |payments|
        """
        from stoqlib.domain.payment.method import PaymentMethod
        return self.store.find(
            Payment,
            And(Payment.group_id == self.id,
                Payment.method_id == PaymentMethod.id,
                PaymentMethod.method_name == method_name))
