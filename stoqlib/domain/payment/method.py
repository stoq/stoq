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
"""Payment methods"""

from decimal import Decimal
import datetime

from kiwi.argcheck import argcheck
from kiwi.component import get_utility
from zope.interface import implements

from stoqlib.database.orm import PercentCol, PriceCol
from stoqlib.database.orm import IntCol, ForeignKey, BoolCol, StringCol, UnicodeCol
from stoqlib.database.orm import const, AND
from stoqlib.domain.base import Domain
from stoqlib.domain.interfaces import (IInPayment, IActive, IOutPayment,
                                       IDescribable)
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.domain.payment.payment import Payment, PaymentAdaptToInPayment
from stoqlib.domain.till import Till
from stoqlib.exceptions import DatabaseInconsistency, PaymentMethodError
from stoqlib.lib.defaults import quantize
from stoqlib.lib.interfaces import IPaymentOperationManager
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

#
# Domain Classes
#


class CheckData(Domain):
    """Stores check informations and also a history of possible
    devolutions.

    @ivar bank_data: information about the bank account of this check.
    @ivar payment: the payment object.
    """
    payment = ForeignKey('Payment')
    bank_account = ForeignKey('BankAccount')


class CreditCardData(Domain):
    """Stores CreditCard specific state related to a payment

    @ivar payment: the payment
    @type payment: L{Payment}
    @ivar card_type:
    @type card_type: int, > 0, < 3
    @ivar provider:
    @type provider: L{PersonAdaptToCreditProvider}
    @ivar installments: the installments number
    @type installments: int, >= 1
    @ivar entrance_value: the value of the first installment
                          (when installments > 1)
    @type entrance_value: currency
    """
    (TYPE_CREDIT,
     TYPE_DEBIT,
     TYPE_CREDIT_INSTALLMENTS_STORE,
     TYPE_CREDIT_INSTALLMENTS_PROVIDER,
     TYPE_DEBIT_PRE_DATED) = range(5)

    types = {
        TYPE_CREDIT: _('Credit Card'),
        TYPE_DEBIT: _('Debit Card'),
        TYPE_CREDIT_INSTALLMENTS_STORE: _('Credit Card Installments Store'),
        TYPE_CREDIT_INSTALLMENTS_PROVIDER: _('Credit Card Installments '
                                             'Provider'),
        TYPE_DEBIT_PRE_DATED: _('Debit Card Pre-dated'),
        }

    payment = ForeignKey('Payment')
    card_type = IntCol(default=TYPE_CREDIT)
    provider = ForeignKey('PersonAdaptToCreditProvider', default=None)
    fee = PercentCol(default=0)
    fee_value = PriceCol(default=0)
    nsu = IntCol(default=None)
    auth = IntCol(default=None)
    installments = IntCol(default=1)
    entrance_value = PriceCol(default=0)


class PaymentMethod(Domain):
    """A PaymentMethod controls how a payments is paid. Example of payment
    methods are: money, bill, check and credit card.
    This class consists of the persistent part of a payment method.
    The logic itself for the various different methods are in the
    PaymentMethodOperation classes. Each PaymentMethod has a PaymentMethodOperation
    associated.
    @ivar name:
    @ivar description:
    @ivar is_active:
    @ivar daily_penalty:
    @ivar interest: a value for the interest. It must always be in the format:
       0 <= interest <= 100
    @ivar payment_day: which day in the month is the credit provider going
      to pay the store? Usually they pay in the same day
      every month.
    @ivar closing_day: which day the credit provider stoq counting sales
      to pay in the payment_day? Sales after this day
      will be paid only in the next month.
    @ivar account_destination: destination account for payment
      methods which creates transactions
    """

    implements(IActive, IDescribable)

    method_name = StringCol()
    is_active = BoolCol(default=True)
    description = UnicodeCol()
    daily_penalty = PercentCol(default=0)
    interest = PercentCol(default=0)
    payment_day = IntCol(default=None)
    closing_day = IntCol(default=None)
    max_installments = IntCol(default=1)
    destination_account = ForeignKey('Account', default=None)

    #
    # IActive implementation
    #

    def inactivate(self):
        assert self.is_active, ('This provider is already inactive')
        self.is_active = False

    def activate(self):
        assert not self.is_active, ('This provider is already active')
        self.is_active = True

    def get_status_string(self):
        if self.is_active:
            return _(u'Active')
        return _(u'Inactive')

    #
    # IDescribable implementation
    #

    def get_description(self):
        return _(self.description)

    #
    # Properties
    #

    @property
    def operation(self):
        """Get the operation for this method.
        The operation contains method specific logic when
        creating/deleting a payment.
        @return: the operation associated with the method
        @rtype: object implementing IPaymentOperation
        """
        return get_utility(IPaymentOperationManager).get(self.method_name)

    #
    # Private API
    #

    def _check_installments_number(self, installments_number, maximum=None):
        if maximum is None:
            maximum = self.max_installments
        if installments_number > maximum:
            raise ValueError(
                _('The number of installments can not be greater than %d '
                  'for payment method %r') % (maximum, self))

    def _check_interest_value(self, interest):
        interest = interest or Decimal(0)
        if not isinstance(interest, (int, Decimal)):
            raise TypeError('interest argument must be integer '
                            'or Decimal, got %s instead'
                            % type(interest))
        if not (0 <= interest <= 100):
            raise ValueError(_("Argument interest must be "
                               "between 0 and 100, got %s")
                             % interest)

    def _calculate_payment_value(self, total_value, installments_number,
                                iface, interest=None):
        if not installments_number:
            raise ValueError(_('The payment_qty argument must be greater '
                               'than zero'))

        if iface is IInPayment:
            self._check_installments_number(installments_number)

        self._check_interest_value(interest)

        if not interest:
            return total_value / installments_number

        interest_rate = interest / 100 + 1
        return (total_value / installments_number) * interest_rate

    #
    # Public API
    #

    # FIXME All create_* methods should be moved to a separate class,
    #       they don't really belong to the method itself.
    #       They should either go into the group or to a separate payment
    #       factory singleton.
    @argcheck(object, PaymentGroup, Decimal, datetime.datetime,
              basestring, basestring, Till, basestring)
    def create_payment(self, iface, payment_group, value, due_date=None,
                       description=None, base_value=None, till=None,
                       payment_number=None):
        """Creates a new payment according to a payment method interface
        @param iface: a payment method interface eg L{IOutPayment} or
        L{IInPayment}
        @param payment_group: a L{PaymentGroup} subclass
        @param value: value of payment
        @param due_date: optional, due date of payment
        @param details: optional
        @param description: optional, description of the payment
        @param base_value: optional
        @param till: optional
        @param payment_number: optional
        @returns: a L{PaymentAdaptToOutPayment} or L{PaymentAdaptToInPayment}
        """
        conn = self.get_connection()

        if due_date is None:
            due_date = const.NOW()

        if iface is IInPayment:
            query = AND(Payment.q.groupID == payment_group.id,
                        Payment.q.methodID == self.id,
                        Payment.q.id == PaymentAdaptToInPayment.q.originalID)
            payment_count = Payment.select(query,
                                connection=self.get_connection()).count()
            if payment_count == self.max_installments:
                raise PaymentMethodError(
                    _('You can not create more inpayments for this payment '
                      'group since the maximum allowed for this payment '
                      'method is %d') % self.max_installments)
            elif payment_count > self.max_installments:
                raise DatabaseInconsistency(
                    _('You have more inpayments in database than the maximum '
                      'allowed for this payment method'))

        if not description:
            description = self.describe_payment(payment_group)

        # If till is unset, do some clever guessing
        if till is None:
            # We only need a till for inpayments
            if iface is IInPayment:
                till = Till.get_current(conn)
            elif iface is IOutPayment:
                till = None
            else:
                raise AssertionError(iface)

        payment = Payment(connection=conn,
                          due_date=due_date,
                          value=value,
                          base_value=base_value,
                          group=payment_group,
                          method=self,
                          category=None,
                          till=till,
                          description=description,
                          payment_number=payment_number)
        facet = payment.addFacet(iface, connection=conn)
        self.operation.payment_create(payment)
        return facet

    @argcheck(object, PaymentGroup, Decimal, object)
    def create_payments(self, iface, group, value, due_dates):
        """Creates new payments according to a payment method interface.
        The values of the individual payments are calculated by taking
        the value and dividing it by the number of payments.
        The number of payments is determined by the length of the due_dates
        sequence.
        @param iface: a payment method interface eg L{IOutPayment} or
        L{IInPayment}
        @param payment_group: a L{PaymentGroup} subclass
        @param value: value of payment
        @param due_dates: a list of datetime objects
        @returns: a list of L{PaymentAdaptToOutPayment} or
        L{PaymentAdaptToInPayment}
        """
        installments = len(due_dates)
        interest = Decimal(0)

        normalized_value = self._calculate_payment_value(
            value, installments, iface, interest)

        normalized_value = quantize(normalized_value)
        if interest:
            interest_total = normalized_value * installments - value
        else:
            interest_total = Decimal(0)

        payments = []
        payments_total = Decimal(0)
        for i, due_date in enumerate(due_dates):
            payment = self.create_payment(iface,
                group, normalized_value, due_date,
                description=self.describe_payment(group, i + 1, installments))
            payments.append(payment)
            payments_total += normalized_value

        # Adjust the last payment so it the total will sum up nicely.
        difference = -(payments_total - interest_total - value)
        if difference:
            adapted = payment.get_adapted()
            adapted.value += difference
        return payments

    def describe_payment(self, payment_group, installment=1, installments=1):
        """ Returns a string describing payment, in the following
        format: current_installment/total_of_installments payment_description
        for payment_group_description

        @param payment_group: a L{PaymentGroup}
        @param installment: current installment
        @param installments: total installments
        @returns: a payment description
        """
        assert installment > 0
        assert installments > 0
        assert installments >= installment
        return _(u'%s/%s %s for %s') % (installment, installments,
                                        self.get_description(),
                                        payment_group.get_description())

    @argcheck(PaymentGroup, Decimal, datetime.datetime,
              basestring, Decimal, Till)
    def create_inpayment(self, payment_group, value, due_date=None,
                         description=None, base_value=None, till=None):
        """Creates a new inpayment
        @param payment_group: a L{PaymentGroup} subclass
        @param value: value of payment
        @param due_date: optional, due date of payment
        @param description: optional, description of the payment
        @param base_value: optional
        @param till: optional
        @returns: a L{PaymentAdaptToInPayment}
        """
        return self.create_payment(IInPayment, payment_group,
                                   value, due_date,
                                   description, base_value, till)

    @argcheck(PaymentGroup, Decimal, datetime.datetime,
              basestring, Decimal, Till)
    def create_outpayment(self, payment_group, value, due_date=None,
                          description=None, base_value=None, till=None):
        """Creates a new outpayment
        @param payment_group: a L{PaymentGroup} subclass
        @param value: value of payment
        @param due_date: optional, due date of payment
        @param description: optional, description of the payment
        @param base_value: optional
        @param till: optional
        @returns: a L{PaymentAdaptToOutPayment}
        """
        return self.create_payment(IOutPayment, payment_group,
                                   value, due_date,
                                   description, base_value, till)

    @argcheck(PaymentGroup, Decimal, object)
    def create_inpayments(self, payment_group, value, due_dates):
        """Creates a list of new inpayments, the values of the individual
        payments are calculated by taking the value and dividing it by
        the number of payments.
        The number of payments is determined by the length of the due_dates
        sequence.
        @param payment_group: a L{PaymentGroup} subclass
        @param value: total value of all payments
        @param due_dates: a list of datetime objects
        @returns: a list of L{PaymentAdaptToInPayment}
        """
        return self.create_payments(IInPayment, payment_group,
                                    value, due_dates)

    @argcheck(PaymentGroup, Decimal, object)
    def create_outpayments(self, payment_group, value, due_dates):
        """Creates a list of new outpayments, the values of the individual
        payments are calculated by taking the value and dividing it by
        the number of payments.
        The number of payments is determined by the length of the due_dates
        sequence.
        @param payment_group: a L{PaymentGroup} subclass
        @param value: total value of all payments
        @param due_dates: a list of datetime objects
        @returns: a list of L{PaymentAdaptToOutPayment}
        """
        return self.create_payments(IOutPayment, payment_group,
                                    value, due_dates)

    @classmethod
    def get_active_methods(cls, conn):
        """Returns a list of payment method interfaces tied with the
        active payment methods
        """
        return PaymentMethod.selectBy(is_active=True,
                                      connection=conn).orderBy('description')

    @classmethod
    def get_by_name(cls, conn, name):
        """Returns the Payment method associated by the nmae
        @param name: name of a payment method
        @returns: the payment method class
        @rtype: L{PaymentMethod} instance
        """
        return PaymentMethod.selectOneBy(connection=conn,
                                         method_name=name)

    def selectable(self):
        """Finds out if the method is selectable, eg
        if the user can select it when doing a sale.
        @returns: True if selectable, otherwise False
        """
        return self.operation.selectable(self)
