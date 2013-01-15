# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2012 Async Open Source <http://www.async.com.br>
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
import operator

from kiwi import ValueUnset
from kiwi.argcheck import argcheck
from storm.expr import And
from storm.references import Reference
from zope.interface import implements

from stoqlib.database.expr import TransactionTimestamp
from stoqlib.database.orm import IntCol, BoolCol, StringCol
from stoqlib.database.orm import PercentCol
from stoqlib.domain.base import Domain
from stoqlib.domain.interfaces import IActive, IDescribable
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.person import Branch
from stoqlib.domain.till import Till
from stoqlib.exceptions import DatabaseInconsistency, PaymentMethodError
from stoqlib.lib.defaults import quantize
from stoqlib.lib.translation import locale_sorted, stoqlib_gettext

_ = stoqlib_gettext

#
# Domain Classes
#


class CheckData(Domain):
    """Stores check informations and also a history of possible
    devolutions.
    """

    __storm_table__ = 'check_data'

    payment_id = IntCol()

    #: the :class:`payment <stoqlib.domain.payment.Payment>`
    payment = Reference(payment_id, 'Payment.id')

    bank_account_id = IntCol()

    #: the :class:`bank account <stoqlib.domain.account.BankAccount>`
    bank_account = Reference(bank_account_id, 'BankAccount.id')


class PaymentMethod(Domain):
    """A PaymentMethod controls how a payments is paid. Example of payment
    methods are::

    * money
    * bill
    * check
    * credit card

    This class consists of the persistent part of a payment method.
    The logic itself for the various different methods are in the
    PaymentMethodOperation classes. Each :class:`PaymentMethod` has a
    PaymentMethodOperation associated.
    """

    implements(IActive, IDescribable)

    __storm_table__ = 'payment_method'

    method_name = StringCol()
    is_active = BoolCol(default=True)
    daily_interest = PercentCol(default=0)

    #: a value for the penalty. It must always be in the format::
    #:
    #:  0 <= penalty <= 100
    #:
    penalty = PercentCol(default=0)

    #: which day in the month is the credit provider going to pay the store?
    #: Usually they pay in the same day every month.
    payment_day = IntCol(default=None)

    #: which day the credit provider stoq counting sales to pay in the
    #: payment_day? Sales after this day will be paid only in the next month.
    closing_day = IntCol(default=None)
    max_installments = IntCol(default=1)
    destination_account_id = IntCol(default=None)
    destination_account = Reference(destination_account_id, 'Account.id')

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
    def description(self):
        return self.operation.description

    @property
    def operation(self):
        """Get the operation for this method.
        The operation contains method specific logic when
        creating/deleting a payment.

        :return: the operation associated with the method
        :rtype: object implementing IPaymentOperation
        """
        from stoqlib.domain.payment.operation import get_payment_operation
        return get_payment_operation(self.method_name)

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

    def _check_penalty_value(self, penalty):
        penalty = penalty or Decimal(0)
        if not isinstance(penalty, (int, Decimal)):
            raise TypeError('penalty argument must be integer '
                            'or Decimal, got %s instead'
                            % type(penalty))
        if not (0 <= penalty <= 100):
            raise ValueError(_("Argument penalty must be "
                               "between 0 and 100, got %s")
                             % penalty)

    def _calculate_payment_value(self, total_value, installments_number,
                                 payment_type, penalty=None):
        if not installments_number:
            raise ValueError(_('The payment_qty argument must be greater '
                               'than zero'))
        if payment_type == Payment.TYPE_IN:
            self._check_installments_number(installments_number)

        self._check_penalty_value(penalty)

        if not penalty:
            return total_value / installments_number

        penalty_rate = penalty / 100 + 1
        return (total_value / installments_number) * penalty_rate

    #
    # Public API
    #

    # FIXME All create_* methods should be moved to a separate class,
    #       they don't really belong to the method itself.
    #       They should either go into the group or to a separate payment
    #       factory singleton.
    @argcheck(int, PaymentGroup, Branch, Decimal, datetime.datetime,
              basestring, basestring, object, basestring)
    def create_payment(self, payment_type, payment_group, branch, value,
                       due_date=None, description=None, base_value=None,
                       till=ValueUnset, payment_number=None):
        """Creates a new payment according to a payment method interface

        :param payment_type: the kind of payment, in or out
        :param payment_group: a :class:`PaymentGroup` subclass
        :param branch: the :class:`branch <stoqlib.domain.person.Branch>'
          associated with the payment, for incoming payments this is the
          branch receiving the payment and for outgoing payments this is the
          branch sending the payment.
        :param value: value of payment
        :param due_date: optional, due date of payment
        :param details: optional
        :param description: optional, description of the payment
        :param base_value: optional
        :param till: optional
        :param payment_number: optional
        :returns: a :class:`payment <stoqlib.domain.payment.Payment>`
        """
        store = self.store

        if due_date is None:
            due_date = TransactionTimestamp()

        if payment_type == Payment.TYPE_IN:
            query = And(Payment.group_id == payment_group.id,
                        Payment.method_id == self.id,
                        Payment.payment_type == Payment.TYPE_IN,
                        Payment.status != Payment.STATUS_CANCELLED)
            payment_count = store.find(Payment, query).count()
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
        if till is ValueUnset:
            # We only need a till for inpayments
            if payment_type == Payment.TYPE_IN:
                till = Till.get_current(store)
            elif payment_type == Payment.TYPE_OUT:
                till = None
            else:
                raise AssertionError(payment_type)

        payment = Payment(store=store,
                          branch=branch,
                          payment_type=payment_type,
                          due_date=due_date,
                          value=value,
                          base_value=base_value,
                          group=payment_group,
                          method=self,
                          category=None,
                          till=till,
                          description=description,
                          payment_number=payment_number)
        self.operation.payment_create(payment)
        return payment

    @argcheck(int, PaymentGroup, Branch, Decimal, object)
    def create_payments(self, payment_type, group, branch, value, due_dates):
        """Creates new payments
        The values of the individual payments are calculated by taking
        the value and dividing it by the number of payments.
        The number of payments is determined by the length of the due_dates
        sequence.

        :param payment_type: the kind of payment, in or out
        :param payment_group: a :class:`PaymentGroup` subclass
        :param branch: the :class:`branch <stoqlib.domain.person.Branch>'
          associated with the payments, for incoming payments this is the
          branch receiving the payment and for outgoing payments this is the
          branch sending the payment.
        :param value: value of payment
        :param due_dates: a list of datetime objects
        :returns: a list of :class:`payments <stoqlib.domain.payment.Payment>`
        """
        installments = len(due_dates)
        penalty = Decimal(0)

        normalized_value = self._calculate_payment_value(
            value, installments, payment_type, penalty)

        normalized_value = quantize(normalized_value)
        if penalty:
            penalty_total = normalized_value * installments - value
        else:
            penalty_total = Decimal(0)

        payments = []
        payments_total = Decimal(0)
        for i, due_date in enumerate(due_dates):
            payment = self.create_payment(payment_type,
                group, branch, normalized_value, due_date,
                description=self.describe_payment(group, i + 1, installments))
            payments.append(payment)
            payments_total += normalized_value

        # Adjust the last payment so it the total will sum up nicely.
        difference = -(payments_total - penalty_total - value)
        if difference:
            payment.value += difference
        return payments

    def describe_payment(self, payment_group, installment=1, installments=1):
        """ Returns a string describing payment, in the following
        format: current_installment/total_of_installments payment_description
        for payment_group_description

        :param payment_group: a :class:`PaymentGroup`
        :param installment: current installment
        :param installments: total installments
        :returns: a payment description
        """
        assert installment > 0
        assert installments > 0
        assert installments >= installment

        # TRANSLATORS: This will generate something like: 1/1 Money for sale 00001
        return _(u'{installment} {method_name} for {order_description}').format(
                 installment='%s/%s' % (installment, installments),
                 method_name=self.get_description(),
                 order_description=payment_group.get_description())

    @argcheck(PaymentGroup, Branch, Decimal, datetime.datetime,
              basestring, Decimal, object)
    def create_inpayment(self, payment_group, branch, value, due_date=None,
                         description=None, base_value=None, till=ValueUnset):
        """Creates a new inpayment

        :param payment_group: a :class:`PaymentGroup` subclass
        :param branch: the :class:`branch <stoqlib.domain.person.Branch>'
          that will receive the payment created.
        :param value: value of payment
        :param due_date: optional, due date of payment
        :param description: optional, description of the payment
        :param base_value: optional
        :param till: optional
        :returns: a :class:`payment <stoqlib.domain.payment.Payment>`
        """
        return self.create_payment(Payment.TYPE_IN, payment_group,
                                   branch, value, due_date,
                                   description, base_value, till)

    @argcheck(PaymentGroup, Branch, Decimal, datetime.datetime,
              basestring, Decimal, object)
    def create_outpayment(self, payment_group, branch, value, due_date=None,
                          description=None, base_value=None, till=ValueUnset):
        """Creates a new outpayment

        :param payment_group: a :class:`PaymentGroup` subclass
        :param branch: the :class:`branch <stoqlib.domain.person.Branch>'
          that will pay the payment created.
        :param value: value of payment
        :param due_date: optional, due date of payment
        :param description: optional, description of the payment
        :param base_value: optional
        :param till: optional
        :returns: a :class:`payment <stoqlib.domain.payment.Payment>`
        """
        return self.create_payment(Payment.TYPE_OUT, payment_group,
                                   branch, value, due_date,
                                   description, base_value, till)

    @argcheck(PaymentGroup, Branch, Decimal, object)
    def create_inpayments(self, payment_group, branch, value, due_dates):
        """Creates a list of new inpayments, the values of the individual
        payments are calculated by taking the value and dividing it by
        the number of payments.
        The number of payments is determined by the length of the due_dates
        sequence.

        :param payment_group: a :class:`PaymentGroup` subclass
        :param branch: the :class:`branch <stoqlib.domain.person.Branch>'
          that will receive the payments created.
        :param value: total value of all payments
        :param due_dates: a list of datetime objects
        :returns: a list of :class:`payments <stoqlib.domain.payment.Payment>`
        """
        return self.create_payments(Payment.TYPE_IN, payment_group,
                                    branch, value, due_dates)

    @argcheck(PaymentGroup, Branch, Decimal, object)
    def create_outpayments(self, payment_group, branch, value, due_dates):
        """Creates a list of new outpayments, the values of the individual
        payments are calculated by taking the value and dividing it by
        the number of payments.
        The number of payments is determined by the length of the due_dates
        sequence.

        :param payment_group: a :class:`PaymentGroup` subclass
        :param branch: the :class:`branch <stoqlib.domain.person.Branch>'
          that will pay the payments created.
        :param value: total value of all payments
        :param due_dates: a list of datetime objects
        :returns: a list of :class:`payments <stoqlib.domain.payment.Payment>`
        """
        return self.create_payments(Payment.TYPE_OUT, payment_group,
                                    branch, value, due_dates)

    @classmethod
    def get_active_methods(cls, store):
        """Returns a list of active payment methods
        """
        methods = store.find(PaymentMethod, is_active=True)
        return locale_sorted(methods,
                             key=operator.attrgetter('description'))

    @classmethod
    def get_by_name(cls, store, name):
        """Returns the Payment method associated by the nmae

        :param name: name of a payment method
        :returns: a :class:`payment methods <PaymentMethod>`
        """
        return store.find(PaymentMethod, method_name=name).one()

    @classmethod
    def get_by_account(cls, store, account):
        """Returns the Payment method associated with an account

        :param account: |account| for which the payment methods are
           associated with
        :returns: a sequence :class:`payment methods <PaymentMethod>`
        """
        return store.find(PaymentMethod, destination_account=account)

    @classmethod
    def get_creatable_methods(cls, store, payment_type, separate):
        """Gets a list of methods that are creatable.
        Eg, you can use them to create new payments.

        :returns: a list of :class:`payment methods <PaymentMethod>`
        """
        methods = []
        for method in cls.get_active_methods(store):
            if not method.operation.creatable(method, payment_type,
                                              separate):
                continue
            methods.append(method)
        return methods

    @classmethod
    def get_editable_methods(cls, store):
        """Gets a list of methods that are editable
        Eg, you can change the details such as maximum installments etc.

        :returns: a list of :class:`payment methods <PaymentMethod>`
        """
        # FIXME: Dont let users see online payments for now, to avoid
        #        confusions with active state. online is an exception to that
        #        logic. 'trade' for the same reason
        clause = And(cls.method_name != 'online',
                     cls.method_name != 'trade')
        methods = store.find(cls, clause)
        return locale_sorted(methods,
                             key=operator.attrgetter('description'))

    def selectable(self):
        """Finds out if the method is selectable, eg
        if the user can select it when doing a sale.

        :returns: ``True`` if selectable
        """
        return self.operation.selectable(self)
