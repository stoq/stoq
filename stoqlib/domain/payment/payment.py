# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2007 Async Open Source <http://www.async.com.br>
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

from kiwi.datatypes import currency
from sqlobject.col import IntCol, DateTimeCol, UnicodeCol, ForeignKey
from sqlobject.sqlbuilder import const
from zope.interface import implements

from stoqlib.database.columns import PriceCol
from stoqlib.domain.base import Domain, ModelAdapter
from stoqlib.domain.payment.operation import PaymentOperation
from stoqlib.domain.interfaces import (IInPayment, IOutPayment,
                                       IPaymentDevolution,
                                       IPaymentDeposit)
from stoqlib.exceptions import DatabaseInconsistency, StoqlibError
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class Payment(Domain):
    """ The payment representation in Stoq.

    B{Importante attributes}:
        - I{interest}: the absolute value for the interest associated with
                       this payment.
        - I{discount}: the absolute value for the discount associated with
                       this payment.
    """

    # Status description
    # Sale: (PENDING, PAID, CANCELLED)
    # A payment is created in STATUS_PREVIEW
    # When you confirm a sale or a purchase, the status is modified to PENDING
    # If you pay with money, status is set to STATUS_PAID
    # Otherwise it's left as pending until the money is received.
    # Finally if you cancel the payment (or use a gift certificate),
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
    description = UnicodeCol(default=None)
    payment_number = UnicodeCol(default=None)
    method = ForeignKey('APaymentMethod')
    # FIXME: Move to methods itself?
    method_details = ForeignKey('PaymentMethodDetails', default=None)
    group = ForeignKey('AbstractPaymentGroup')
    till = ForeignKey('Till')
    destination = ForeignKey('PaymentDestination')
    category = ForeignKey('PaymentCategory')

    def _check_status(self, status, operation_name):
        assert self.status == status, ('Invalid status for %s '
                                       'operation: %s' % (operation_name,
                                       self.statuses[self.status]))

    #
    # SQLObject hooks
    #

    def _create(self, id, **kw):
        if not 'value' in kw:
            raise TypeError('You must provide a value argument')
        if not 'base_value' in kw or not kw['base_value']:
            kw['base_value'] = kw['value']
        Domain._create(self, id, **kw)

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

    def set_not_paid(self, change_entry):
        """Set a STATUS_PAID payment as STATUS_PENDING. This requires clearing
        paid_date and paid_value

        @param change_entry: an PaymentChangeHistory object, that will hold the changes
        information
        """
        self._check_status(self.STATUS_PAID, 'set_not_paid')

        change_entry.last_status = self.STATUS_PAID
        change_entry.new_status = self.STATUS_PENDING

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
        if self.group:
            self.group.pay(self)

    def submit(self, submit_date=None):
        """The first stage of payment acquittance is submiting and mark a
        payment with STATUS_REVIEWING
        """
        self._check_status(self.STATUS_PAID, 'submit')
        conn = self.get_connection()
        operation = PaymentOperation(connection=conn,
                                     operation_date=submit_date)
        operation.addFacet(IPaymentDeposit, connection=conn)
        self.status = self.STATUS_REVIEWING

    def reject(self, reason, reject_date=None):
        """If there is some problems in the  first stage of payment
        acquittance we must call reject for it.
        """
        self._check_status(self.STATUS_REVIEWING, 'reject')
        conn = self.get_connection()
        operation = PaymentOperation(connection=conn,
                                     operation_date=reject_date)
        operation.addFacet(IPaymentDevolution, connection=conn, reason=reason)
        self.status = self.STATUS_PAID

    def cancel(self):
        # TODO Check for till entries here and call cancel_till_entry if
        # it's possible. Bug 2598
        if self.status not in [Payment.STATUS_PREVIEW, Payment.STATUS_PENDING,
                               Payment.STATUS_PAID]:
            raise StoqlibError("Invalid status for cancel operation, "
                                "got %s" % self.get_status_str())
        self.status = self.STATUS_CANCELLED
        self.cancel_date = const.NOW()

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

    def get_thirdparty(self):
        if self.method_details:
            return self.method_details.get_thirdparty()
        return self.method.get_thirdparty(self.group)

    def get_thirdparty_name(self):
        thirdparty = self.get_thirdparty()
        if thirdparty:
            return thirdparty.name
        return _(u'Anonymous')

    def is_paid(self):
        """Check if the payment is paid.
        @returns: True if the payment is paid, otherwise False
        """
        return self.status == Payment.STATUS_PAID

    def is_preview(self):
        """Check if the payment is in preview state
        @returns: True if the payment is paid, otherwise False
        """
        return self.status == Payment.STATUS_PREVIEW

    @property
    def bank(self):
        """Get a BankAccount instance
        @returns: a BankAccount instance, if the payment method does not
        provide a bank account.
        """
        if self.method.name == 'check':
            data = self.method.get_check_data_by_payment(self)
            return data.bank_data

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


#
# Payment adapters
#


class PaymentAdaptToInPayment(ModelAdapter):

    implements(IInPayment)

    # TODO: Unused
    def receive(self):
        payment = self.get_adapted()
        if not payment.status == Payment.STATUS_PENDING:
            raise ValueError("This payment is already received.")
        payment.pay()
        payment.group.update_thirdparty_status()

Payment.registerFacet(PaymentAdaptToInPayment, IInPayment)


class PaymentAdaptToOutPayment(ModelAdapter):

    implements(IOutPayment)

    def pay(self):
        payment = self.get_adapted()
        if not payment.status == Payment.STATUS_PENDING:
            raise ValueError("This payment is already paid.")
        payment.pay()

Payment.registerFacet(PaymentAdaptToOutPayment, IOutPayment)

