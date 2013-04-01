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

from kiwi.currency import currency
from storm.expr import And, In
from storm.references import Reference
from zope.interface import implements

from stoqlib.database.properties import IntCol
from stoqlib.domain.base import Domain
from stoqlib.domain.interfaces import IContainer
from stoqlib.domain.payment.payment import Payment
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class PaymentGroup(Domain):
    """A base class for payment group adapters. """

    implements(IContainer)

    __storm_table__ = 'payment_group'

    payer_id = IntCol(default=None)
    payer = Reference(payer_id, 'Person.id')
    recipient_id = IntCol(default=None)
    recipient = Reference(recipient_id, 'Person.id')
    # This is where this payment group was renegotiated, ie, this payments
    # wore renegotiated in this renegotiation.
    # XXX: Rename to renegotiated
    renegotiation_id = IntCol(default=None)
    renegotiation = Reference(renegotiation_id, 'PaymentRenegotiation.id')

    sale = Reference('id', 'Sale.group_id', on_remote=True)
    purchase = Reference('id', 'PurchaseOrder.group_id', on_remote=True)
    # This is the payment group's renegotiation, ie, this payments are part
    # of this renegotiation.
    _renegotiation = Reference('id', 'PaymentRenegotiation.group_id', on_remote=True)
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
        return store.find(Payment, group=self).order_by(Payment.id)

    #
    # Properties
    #

    @property
    def payments(self):
        """Returns all payments of this group

        :returns: a list of :class:`stoqlib.domain.payment.payment.Payment`
        """
        return self.get_items()

    @property
    def installments_number(self):
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

    def confirm(self):
        """Confirms all payments in this payment group

        Confirming the payment group means that the customer has
        confirmed the payments. All individual payments are set to
        pending.
        """
        for payment in self.get_valid_payments():
            if payment.is_pending() or payment.is_paid():
                continue
            payment.set_pending()

    def pay(self):
        """Pay all payments in this payment group
        """
        for payment in self.get_valid_payments():
            if payment.is_paid():
                continue
            payment.pay()

    def pay_money_payments(self):
        """Pay all money payments in this payment group
        """
        for payment in self.get_valid_payments():
            if payment.is_money() and not payment.is_paid():
                payment.pay()

    def cancel(self):
        """Cancel all pending payments in this payment group
        """
        for payment in self.get_pending_payments():
            if payment.is_cancelled():
                continue
            payment.cancel()

    def get_total_paid(self):
        return self._get_payments_sum(self._get_paid_payments(),
                                      Payment.value)

    def get_total_value(self):
        """Returns the sum of all payment values.
        :returns: the total payment value or zero.
        """
        return self._get_payments_sum(self.get_valid_payments(),
                                      Payment.value)

    def clear_unused(self):
        """Delete payments of preview status associated to the current
        payment_group. It can happen if user open and cancel this wizard.
        """
        payments = self.store.find(Payment, status=Payment.STATUS_PREVIEW,
                                   group=self)
        for payment in payments:
            self.remove_item(payment)
            payment.delete()

    def get_description(self):
        """Returns a small description for the payment group which will be
        used in payment descriptions
        """

        # FIXME: This is hack which won't scale. But I don't know
        #        a better solution right now. Johan 2008-09-25
        if self.sale:
            return _(u'sale %s') % self.sale.identifier
        elif self.purchase:
            return _(u'order %s') % self.purchase.identifier
        elif self._renegotiation:
            return _(u'renegotiation %s') % self._renegotiation.identifier
        elif self.stock_decrease:
            return _(u'stock decrease %s') % self.stock_decrease.identifier
        # FIXME: Add a proper description
        else:
            return u''

    def get_pending_payments(self):
        return self.store.find(Payment, group=self,
                               status=Payment.STATUS_PENDING)

    def get_parent(self):
        """Return the sale, purchase or renegotiation this group is part of.
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
        """Returns the sum of all payment discounts.
        :returns: the total payment discount or zero.
        """
        return self._get_payments_sum(self.get_valid_payments(),
                                      Payment.discount)

    def get_total_interest(self):
        """Returns the sum of all payment interests.
        :returns: the total payment interest or zero.
        """
        return self._get_payments_sum(self.get_valid_payments(),
                                      Payment.interest)

    def get_total_penalty(self):
        """Returns the sum of all payment penalties.
        :returns: the total payment penalty or zero.
        """
        return self._get_payments_sum(self.get_valid_payments(),
                                      Payment.penalty)

    def get_valid_payments(self):
        """Returns all payments that are not cancelled.
        """
        return self.store.find(Payment,
                               And(Payment.group_id == self.id,
                                   Payment.status != Payment.STATUS_CANCELLED))

    def get_payments_by_method_name(self, method_name):
        from stoqlib.domain.payment.method import PaymentMethod
        return self.store.find(
            Payment,
            And(Payment.group_id == self.id,
                Payment.method_id == PaymentMethod.id,
                PaymentMethod.method_name == method_name))
