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
## Author(s):   Evandro Vale Miquelito     <evandro@async.com.br>
##              Henrique Romano            <henrique@async.com.br>
##              Johan Dahlin               <jdahlin@async.com.br>
##
""" Payment management implementations."""

import datetime
from decimal import Decimal

from kiwi.datatypes import currency
from kiwi.log import Logger
from zope.interface import implements

from stoqlib.database.orm import (IntCol, DateTimeCol, UnicodeCol, ForeignKey,
                                  PriceCol, DecimalCol)
from stoqlib.database.orm import const, DESC, AND, OR
from stoqlib.domain.base import Domain, ModelAdapter
from stoqlib.domain.interfaces import IInPayment, IOutPayment
from stoqlib.exceptions import DatabaseInconsistency, StoqlibError
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext
log = Logger('stoqlib.domain.payment.payment')


class Payment(Domain):
    """ The payment representation in Stoq.

    B{Importante attributes}:
        - I{interest}: the absolute value for the interest associated with
                       this payment.
        - I{discount}: the absolute value for the discount associated with
                       this payment.
        - I{penalty}: the absolute value for the penalty associated with
                       this payment.
    """

    # Status description
    # Sale: (PENDING, PAID, CANCELLED)
    # A payment is created in STATUS_PREVIEW
    # When you confirm a sale or a purchase, the status is modified to PENDING
    # If you pay with money, status is set to STATUS_PAID
    # Otherwise it's left as pending until the money is received.
    # Finally if you cancel the payment
    # the status is set to STATUS_CANCELLED

    # Purchase: (PENDING, PAID, REVIEWING, CONFIRMED, CANCELLED)
    # TODO
    (STATUS_PREVIEW,
     STATUS_PENDING,
     STATUS_PAID,
     STATUS_REVIEWING,
     STATUS_CONFIRMED,
     STATUS_CANCELLED) = range(6)

    statuses = {STATUS_PREVIEW: _(u'Preview'),
                STATUS_PENDING: _(u'To Pay'),
                STATUS_PAID: _(u'Paid'),
                STATUS_REVIEWING: _(u'Reviewing'),
                STATUS_CONFIRMED: _(u'Confirmed'),
                STATUS_CANCELLED: _(u'Cancelled')}

    status = IntCol(default=STATUS_PREVIEW)
    open_date = DateTimeCol(default=datetime.datetime.now)
    due_date = DateTimeCol()
    paid_date = DateTimeCol(default=None)
    cancel_date = DateTimeCol(default=None)
    paid_value = PriceCol(default=None)
    base_value = PriceCol(default=None)
    value = PriceCol()
    interest = PriceCol(default=0)
    discount = PriceCol(default=0)
    penalty = PriceCol(default=0)
    description = UnicodeCol(default=None)
    payment_number = UnicodeCol(default=None)
    method = ForeignKey('PaymentMethod')
    group = ForeignKey('PaymentGroup')
    till = ForeignKey('Till')
    destination = ForeignKey('PaymentDestination')
    category = ForeignKey('PaymentCategory')

    def _check_status(self, status, operation_name):
        assert self.status == status, ('Invalid status for %s '
                                       'operation: %s' % (operation_name,
                                       self.statuses[self.status]))

    #
    # ORMObject hooks
    #

    def _create(self, id, **kw):
        if not 'value' in kw:
            raise TypeError('You must provide a value argument')
        if not 'base_value' in kw or not kw['base_value']:
            kw['base_value'] = kw['value']
        Domain._create(self, id, **kw)

    @classmethod
    def delete(cls, obj_id, connection):
        # First call hooks, do this first so the hook
        # have access to everything it needs
        payment = cls.get(obj_id, connection)
        payment.method.operation.payment_delete(payment)

        # Remove from the In/Out tables, ideally this would
        # be stored so we don't have to do trial and error
        out_payment = IOutPayment(payment, None)
        in_payment = IInPayment(payment, None)
        if out_payment is not None:
            PaymentAdaptToOutPayment.delete(
                out_payment.id, connection)
        elif in_payment is not None:
            PaymentAdaptToInPayment.delete(
                in_payment.id, connection)

        super(cls, Payment).delete(obj_id, connection)

    #
    # Properties
    #
    
    @property
    def bank(self):
        """Get a BankAccount instance
        @returns: a BankAccount instance, if the payment method does not
        provide a bank account.
        """
        # This is mainly used by receipt.rml, and is a convenience
        # property, ideally we should move it to payment operation
        # somehow
        if self.method.method_name == 'check':
            data = self.method.operation.get_check_data_by_payment(self)
            return data.bank_data


    #
    # Public API
    #

    def get_status_str(self):
        if not self.statuses.has_key(self.status):
            raise DatabaseInconsistency('Invalid status for Payment '
                                        'instance, got %d' % self.status)
        return self.statuses[self.status]

    def get_days_late(self):
        if self.status == Payment.STATUS_PAID:
            return 0

        days_late = datetime.date.today() - self.due_date.date()
        if days_late.days < 0:
            return 0

        return days_late.days

    def set_pending(self):
        """Set a STATUS_PREVIEW payment as STATUS_PENDING. This also means
        that this is valid payment and its owner actually can charge it
        """
        self._check_status(self.STATUS_PREVIEW, 'set_pending')
        self.status = self.STATUS_PENDING

        PaymentFlowHistory.add_payment(self.get_connection(), self)

    def set_not_paid(self, change_entry):
        """Set a STATUS_PAID payment as STATUS_PENDING. This requires clearing
        paid_date and paid_value

        @param change_entry: an PaymentChangeHistory object, that will hold the changes
        information
        """
        self._check_status(self.STATUS_PAID, 'set_not_paid')

        change_entry.last_status = self.STATUS_PAID
        change_entry.new_status = self.STATUS_PENDING

        PaymentFlowHistory.remove_paid_payment(self.get_connection(), self,
                                               self.paid_date)

        self.status = self.STATUS_PENDING
        self.paid_date = None
        self.paid_value = None

    def pay(self, paid_date=None, paid_value=None):
        """Pay the current payment set its status as STATUS_PAID"""
        self._check_status(self.STATUS_PENDING, 'pay')

        paid_value = paid_value or (self.value - self.discount +
                                    self.interest)
        self.paid_value = paid_value
        self.paid_date = paid_date or const.NOW()
        self.status = self.STATUS_PAID

        PaymentFlowHistory.add_paid_payment(self.get_connection(), self)

    def cancel(self, change_entry=None):
        # TODO Check for till entries here and call cancel_till_entry if
        # it's possible. Bug 2598
        if self.status not in [Payment.STATUS_PREVIEW, Payment.STATUS_PENDING,
                               Payment.STATUS_PAID]:
            raise StoqlibError("Invalid status for cancel operation, "
                                "got %s" % self.get_status_str())

        if self.status == Payment.STATUS_PAID:
             PaymentFlowHistory.remove_paid_payment(self.get_connection(),
                                                    self)
        else:
            PaymentFlowHistory.remove_payment(self.get_connection(), self)

        old_status = self.status
        self.status = self.STATUS_CANCELLED
        self.cancel_date = const.NOW()

        if change_entry is not None:
            change_entry.last_status = old_status
            change_entry.new_status = self.status

    def get_payable_value(self):
        """ Returns the calculated payment value with the daily penalty.
            Note that the payment group daily_penalty must be
            between 0 and 100.
        """
        if self.status in [self.STATUS_PREVIEW, self.STATUS_CANCELLED]:
            return self.value
        if self.status in [self.STATUS_PAID, self.STATUS_REVIEWING,
                           self.STATUS_CONFIRMED]:
            return self.paid_value

        return self.value + self.get_penalty()

    def get_penalty(self, date=None):
        """Calculate the penalty in an absolute value
        @param date: date of payment
        @returns: penalty
        @rtype: currency
        """
        if not date:
            date = datetime.date.today()
        elif date < self.open_date.date():
            raise ValueError("Date can not be less then open date")
        elif date > datetime.date.today():
            raise ValueError("Date can not be greather then future date")

        if not self.method.daily_penalty:
            return currency(0)

        days = (date - self.due_date.date()).days
        if days <= 0:
            return currency(0)

        return currency(days * self.method.daily_penalty / 100 * self.value)

    def get_interest(self, date=None):
        """Calculate the interest in an absolute value
        @param date: date of payment
        @returns: interest
        @rtype: currency
        """
        if not date:
            date = datetime.date.today()
        elif date < self.open_date.date():
            raise ValueError("Date can not be less then open date")
        elif date > datetime.date.today():
            raise ValueError("Date can not be greather then future date")
        if not self.method.interest:
            return currency(0)

        # Don't add interest if we pay in time!
        if self.due_date.date() >= date:
            return currency(0)

        return currency(self.method.interest / 100 * self.value)

    def is_paid(self):
        """Check if the payment is paid.
        @returns: True if the payment is paid, otherwise False
        """
        return self.status == Payment.STATUS_PAID

    def is_pending(self):
        """Check if the payment is pending.
        @returns: True if the payment is pending, otherwise False
        """
        return self.status == Payment.STATUS_PENDING

    def is_preview(self):
        """Check if the payment is in preview state
        @returns: True if the payment is paid, otherwise False
        """
        return self.status == Payment.STATUS_PREVIEW

    def is_cancelled(self):
        """Check if the payment was cancelled.
        @returns: True if the payment was cancelled, otherwise False.
        """
        return self.status == Payment.STATUS_CANCELLED

    def get_paid_date_string(self):
        """Get a paid date string
        @returns: the paid date string or PAID DATE if the payment isn't
        paid
        """
        if self.paid_date:
            return self.paid_date.date().strftime('%x')
        return _('NOT PAID')

    def get_open_date_string(self):
        """Get a open date string
        @returns: the open date string or empty string
        """
        if self.open_date:
            return self.open_date.date().strftime('%x')
        return ""

class PaymentChangeHistory(Domain):
    """ A class to hold information about changes to a payment.

    Only one tuple (last_due_date, new_due_date) or (last_status, new_status)
    should be non-null at a time.

    @param payment: the payment changed
    @param change_reason: the reason of the due date change
    @param last_due_date: the due date that was set before the changed
    @param new_due_date: the due date that was set after changed
    @param last_status: status before the change
    @param new_status: status after change
    """
    payment = ForeignKey('Payment')
    change_reason = UnicodeCol(default=None)
    change_date = DateTimeCol(default=datetime.datetime.now)
    last_due_date = DateTimeCol(default=None)
    new_due_date = DateTimeCol(default=None)
    last_status = IntCol(default=None)
    new_status = IntCol(default=None)


class PaymentFlowHistory(Domain):
    """A class to hold information about the financial flow.

    @param history_date: the date when payments were registered.
    @param to_receive: the amount scheduled to be received in the
                       history_date.
    @param received: the amount received in the history_date.
    @param to_pay: the amount scheduled to be paid in the history_date.
    @param paid: the amount paid in the history_date.
    @param balance_expected: the balance of the last day plus the amount to be
                             received minus the amount to be paid.
    @param balance_real: the balance of the last day plus the amount received
                         minus the amount paid.
    """

    history_date = DateTimeCol(default=datetime.datetime.now)
    to_receive = DecimalCol(default=Decimal(0))
    received = DecimalCol(default=Decimal(0))
    to_pay = DecimalCol(default=Decimal(0))
    paid = DecimalCol(default=Decimal(0))
    balance_expected = DecimalCol(default=Decimal(0))
    balance_real = DecimalCol(default=Decimal(0))

    #
    # Public API
    #

    def get_last_day_real_balance(self):
        """Returns the real balance value of the previous day or zero if
        there's no previous day.
        """
        last_day = PaymentFlowHistory.get_last_day(self.get_connection(),
                                                   self.history_date)
        if last_day:
            return last_day.balance_real
        return Decimal(0)

    def get_divergent_payments(self):
        """Returns a L{Payment} sequence that meet to following requirements:
            - The payment due date, paid date or cancel date is the current
              PaymentFlowHistory date.
            - The payment was paid/received with different values (eg with
              discount or surcharges).
            - The payment was scheduled to be paid/received in the current,
              but it was not.
            - The payment was not expected to be paid/received the current date.
        """
        date = self.history_date
        query = AND(OR(Payment.q.due_date == date,
                       Payment.q.paid_date == date,
                       Payment.q.cancel_date == date),
                    OR(Payment.q.paid_value == None,
                       Payment.q.value != Payment.q.paid_value,
                       Payment.q.paid_date == None,
                       Payment.q.due_date != Payment.q.paid_date))
        return Payment.select(query, connection=self.get_connection())

    #
    # Private API
    #

    def _update_balance(self):
        """Updates the balance_expected and balance_real values following this
        rule:
            - balance_expected: last_day_balance + to_receive - to_pay
            - balance_real: last_day_balance + received - paid
        """
        last_day = self.get_last_day_real_balance()
        self.balance_expected =  last_day + self.to_receive - self.to_pay
        self.balance_real = last_day + self.received - self.paid

    def _update_registers(self, payment, value, accomplished=True):
        """Updates the L{PaymentFlowHistory} attributes according to the
        payment facet, value and if the payment was accomplished or not.

        @param payment: the payment that will be registered.
        @param value: the value that will be used to update history
                      attributes.
        @param accomplished: indicates if we should update the attributes that
                             holds information about the accomplished payments
                             or attributes related to payments that will be
                             accomplished later.
        """
        if not payment.getFacets():
            log.info('Payment %r will not be registered in %r: missing '
                     'payment facets.' % (payment, self))

        if IOutPayment(payment, None) is not None:
            if accomplished:
                self.paid += value
            else:
                self.to_pay += value
        elif IInPayment(payment, None) is not None:
            if accomplished:
                self.received += value
            else:
                self.to_receive += value
        self._update_balance()

    #
    # Classmethods
    #

    @classmethod
    def get_last_day(cls, conn, reference_date=None):
        """Returns the L{PaymentFlowHistory} instance of the last day
        registered or None if there is no registry. If reference_date was not
        specified, the referente date will be the current date.

        @param reference_date: the reference date to use when querying the
                               last day.
        @param conn: a database connection.
        """
        if reference_date is None:
            reference_date = datetime.date.today()
        results = PaymentFlowHistory.select(
                            PaymentFlowHistory.q.history_date < reference_date,
                            orderBy=DESC(PaymentFlowHistory.q.history_date),
                            connection=conn).limit(1)
        if results:
            return results[0]

    @classmethod
    def get_or_create_flow_history(cls, conn, date):
        """Returns a L{PaymentFlowHistory} instance.

        @param conn: a database connection.
        @param date: the date of the L{PaymentFlowHistory} we want to
                     retrieve or create.
        """
        day_history = PaymentFlowHistory.selectOneBy(history_date=date,
                                                     connection=conn)
        if day_history is not None:
            return day_history
        return cls(history_date=date, connection=conn)

    @classmethod
    def add_payment(cls, conn, payment, reference_date=None):
        """Adds a payment in the L{PaymentFlowHistory} registry according to
        the payment due date.

        @param conn: a database connection.
        @param payment: the payment to be added in the registry.
        @param reference_date: the reference date to use when add the payment,
                               if not specified, the reference will be the
                               payment due date.
        """
        if reference_date is None:
            reference_date = payment.due_date.date()
        day_history = cls.get_or_create_flow_history(conn, reference_date)
        day_history._update_registers(payment, payment.value,
                                      accomplished=False)

    @classmethod
    def add_paid_payment(cls, conn, payment, reference_date=None):
        """Adds a paid payment in the L{PaymentFlowHistory} registry. The paid
        payment will be added in the current day registry.

        @param conn: a database connection.
        @param payment: the paid payment to be added in the registry.
        @param reference_date: the reference date to use when add the paid
                               payment, if not specified, the reference will
                               be the current date.
        """
        if reference_date is None:
            reference_date = datetime.date.today()
        day_history = cls.get_or_create_flow_history(conn, reference_date)
        day_history._update_registers(payment, payment.value,
                                      accomplished=True)

    @classmethod
    def remove_payment(cls, conn, payment, reference_date=None):
        """Removes a payment in the L{PaymentFlowHistory} registry. The
        payment will be deducted from registry according to its due date.

        @param conn: a database connection.
        @param payment: the payment to be removed in the registry.
        @param reference_date: the reference date to use when remove the
                               payment, if not specified, the reference will
                               be the payment due date.
        """
        if reference_date is None:
            reference_date = payment.due_date.date()
        day_history = cls.get_or_create_flow_history(conn, reference_date)
        day_history._update_registers(payment, -payment.value,
                                      accomplished=False)

    @classmethod
    def remove_paid_payment(cls, conn, payment, reference_date=None):
        """Removes a paid payment in the L{PaymentFlowHistory} registry. The paid
        payment will be removed in the current day registry.

        @param conn: a database connection.
        @param payment: the paid payment to be removed in the registry.
        @param reference_date: the reference date to use when remove the paid
                               payment, if not specified, the reference will
                               be the current date.
        """
        if reference_date is None:
            reference_date = datetime.date.today()
        day_history = cls.get_or_create_flow_history(conn, reference_date)
        day_history._update_registers(payment, -payment.paid_value,
                                      accomplished=True)


#
# Payment adapters
#


class PaymentAdaptToInPayment(ModelAdapter):

    implements(IInPayment)

Payment.registerFacet(PaymentAdaptToInPayment, IInPayment)


class PaymentAdaptToOutPayment(ModelAdapter):

    implements(IOutPayment)

    def pay(self):
        payment = self.get_adapted()
        if not payment.status == Payment.STATUS_PENDING:
            raise ValueError("This payment is already paid.")
        payment.pay()

Payment.registerFacet(PaymentAdaptToOutPayment, IOutPayment)

