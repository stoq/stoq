# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005,2006 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s):   Evandro Vale Miquelito     <evandro@async.com.br>
##              Henrique Romano            <henrique@async.com.br>
##
""" Payment management implementations."""

import datetime

from kiwi.argcheck import argcheck
from sqlobject.sqlbuilder import AND
from sqlobject import IntCol, DateTimeCol, UnicodeCol, ForeignKey
from zope.interface import implements

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.exceptions import PaymentError, DatabaseInconsistency
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.defaults import (get_method_names, get_all_methods_dict,
                                  METHOD_MULTIPLE, METHOD_MONEY)
from stoqlib.domain.columns import PriceCol
from stoqlib.domain.base import Domain, ModelAdapter, InheritableModelAdapter
from stoqlib.domain.payment.operation import PaymentOperation
from stoqlib.domain.interfaces import (IInPayment, IOutPayment, IPaymentGroup,
                                       ICheckPM, IBillPM, IContainer,
                                       IPaymentDevolution, IPaymentDeposit)

_ = stoqlib_gettext


#
# Domain Classes
#


class Payment(Domain):
    """Base class for payments.

    B{Importante attributes}:
        - I{interest}: the absolute value for the interest associated with
                       this payment.
        - I{discount}: the absolute value for the discount associated with
                       this payment.
    """

    (STATUS_PREVIEW,
     STATUS_TO_PAY,
     STATUS_PAID,
     STATUS_REVIEWING,
     STATUS_CONFIRMED,
     STATUS_CANCELLED) = range(6)

    statuses = {STATUS_PREVIEW: _(u'Preview'),
                STATUS_TO_PAY: _(u'To Pay'),
                STATUS_PAID: _(u'Paid'),
                STATUS_REVIEWING: _(u'Reviewing'),
                STATUS_CONFIRMED: _(u'Confirmed'),
                STATUS_CANCELLED: _(u'Cancelled')}

    # XXX The payment_id attribute will be an alternateID after
    # fixing bug 2214
    payment_id = IntCol(default=None)
    status = IntCol(default=STATUS_PREVIEW)
    due_date = DateTimeCol()
    paid_date = DateTimeCol(default=None)
    paid_value = PriceCol(default=0)
    base_value = PriceCol()
    value = PriceCol()
    interest = PriceCol(default=0)
    discount = PriceCol(default=0)
    description = UnicodeCol(default=None)
    payment_number = UnicodeCol(default=None)

    method = ForeignKey('AbstractPaymentMethodAdapter')
    method_details = ForeignKey('PaymentMethodDetails', default=None)
    group = ForeignKey('AbstractPaymentGroup')
    destination = ForeignKey('PaymentDestination')


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
    # General methods
    #

    def get_status_str(self):
        if not self.statuses.has_key(self.status):
            raise DatabaseInconsistency('Invalid status for Payment '
                                        'instance, got %d' % self.status)
        return self.statuses[self.status]

    def is_to_pay(self):
        return self.status == self.STATUS_TO_PAY

    def set_to_pay(self):
        """Set a STATUS_PREVIEW payment as STATUS_TO_PAY. This also means
        that this is valid payment and its owner actually can charge it
        """
        self._check_status(self.STATUS_PREVIEW, 'set_to_pay')
        self.status = self.STATUS_TO_PAY

    def pay(self, paid_date=None):
        """Pay the current payment set its status as STATUS_PAID"""
        self._check_status(self.STATUS_TO_PAY, 'pay')
        if self.group.get_thirdparty() is None:
            raise PaymentError("You must have a thirdparty to quit "
                               "the payment")

        self.paid_value = self.value - self.discount + self.interest
        self.paid_date = paid_date or datetime.datetime.now()
        self.status = self.STATUS_PAID

    def _check_status(self, status, operation_name):
        assert self.status == status, ('Invalid status for %s '
                                       'operation: %s' % (operation_name,
                                       self.statuses[self.status]))

    def _register_payment_operation(self,
                                    operation_date=datetime.datetime.now()):
        conn = self.get_connection()
        operation = PaymentOperation(connection=conn,
                                     operation_date=operation_date)
        return operation

    def submit(self, submit_date=None):
        """The first stage of payment acquitance is submiting and mark a
        payment with STATUS_REVIEWING
        """
        self._check_status(self.STATUS_PAID, 'submit')
        operation = self._register_payment_operation(submit_date)
        conn = self.get_connection()
        operation.addFacet(IPaymentDeposit, connection=conn)
        self.status = self.STATUS_REVIEWING

    def reject(self, reason, reject_date=None):
        """If there is some problems in the  first stage of payment
        acquitance we must call reject for it.
        """
        self._check_status(self.STATUS_REVIEWING, 'reject')
        operation = self._register_payment_operation(reject_date)
        conn = self.get_connection()
        operation.addFacet(IPaymentDevolution, connection=conn,
                           reason=reason)
        self.status = self.STATUS_PAID

    def cancel_payment(self):
        if self.status != Payment.STATUS_CANCELLED:
            self._check_status(self.STATUS_TO_PAY, 'reverse selection')
            self.status = self.STATUS_CANCELLED
            payment = self.clone()
            # payment_id should be incremented automatically.
            # Waiting for bug 2214.
            description = _('Cancellation of payment number %s') % self.payment_id
            payment.description = description
            payment.value *= -1
            payment.due_date = datetime.datetime.now()

    def get_payable_value(self, paid_date=None):
        """ Returns the calculated payment value with the daily penalty.
            Note that the payment group daily_penalty must be
            between 0 and 100.
        """
        if self.status in [self.STATUS_PREVIEW, self.STATUS_CANCELLED]:
            return self.value
        if self.status in [self.STATUS_PAID, self.STATUS_REVIEWING,
                           self.STATUS_CONFIRMED]:
            return self.paid_value
        if paid_date and not isinstance(paid_date, datetime.datetime.date):
            raise TypeError('Argument paid_date must be of type '
                            'datetime.date, got %s instead' %
                            type(paid_date))
        if self.method.get_implemented_iface() in (ICheckPM, IBillPM):
            paid_date = paid_date or datetime.datetime.now()
            days = (paid_date - self.due_date).days
            if days <= 0:
                return self.value
            daily_penalty = self.method.daily_penalty / 100
            return self.value + days * (daily_penalty * self.value)
        else:
            return self.value

    def get_thirdparty(self):
        if self.method_details:
            return self.method_details.get_thirdparty()
        return self.method.get_thirdparty(self.group)

    def get_thirdparty_name(self):
        thirdparty = self.get_thirdparty()
        if thirdparty:
            return thirdparty.name
        return _(u'Anonymous')


class AbstractPaymentGroup(InheritableModelAdapter):
    """A base class for payment group adapters. """

    (STATUS_PREVIEW,
     STATUS_OPEN,
     STATUS_CLOSED,
     STATUS_CANCELLED) = range(4)

    implements(IPaymentGroup, IContainer)

    status = IntCol(default=STATUS_OPEN)
    open_date = DateTimeCol(default=datetime.datetime.now)
    close_date = DateTimeCol(default=None)
    default_method = IntCol(default=METHOD_MONEY)
    installments_number = IntCol(default=1)
    interval_type = IntCol(default=None)
    intervals = IntCol(default=None)
    renegotiation_data = ForeignKey('RenegotiationData', default=None)

    #
    # IPaymentGroup implementation
    #

    def get_thirdparty(self):
        raise NotImplementedError

    def get_group_description(self):
        """Returns a small description for the payment group which will be
        used in payment descriptions
        """
        raise NotImplementedError

    def update_thirdparty_status(self):
        raise NotImplementedError

    def get_balance(self):
        return sum([s.value for s in self.get_items()])

    def add_payment(self, value, description, method, destination,
                    due_date=datetime.datetime.now()):
        """Add a new payment sending correct arguments to Payment
        class
        """
        conn = self.get_connection()
        payment = Payment(due_date=due_date, value=value,
                          description=description, group=self,
                          method=method, destination=method.destination,
                          connection=conn)
        self.add_item(payment)
        return payment

    def get_method_id_by_iface(self, iface):
        methods = get_all_methods_dict()
        if not iface in methods.values():
            raise ValueError('Invalid interface, got %s' % iface)
        method_data = [method_id for method_id, m_iface in methods.items()
                            if m_iface is iface]
        qty = len(method_data)
        if not qty == 1:
            raise ValueError('It should have only one item on method_data '
                             'list, got %d instead' % qty)
        return method_data[0]

    def set_method(self, method_iface):
        items = get_all_methods_dict().items()
        method = [method_id for method_id, iface in items
                        if method_iface is iface]
        if len(method) != 1:
            raise TypeError('Invalid method_class argument, got type %s'
                            % method_iface)
        self.default_method = method[0]

    def get_default_payment_method(self):
        """This hook must be redefined in a subclass when it's necessary"""
        return self.default_method

    def get_default_payment_method_name(self):
        """This hook must be redefined in a subclass when it's necessary"""
        method_names = get_method_names()
        if not self.default_method in method_names.keys():
            raise DatabaseInconsistency('Invalid payment method, got %d'
                                        % self.default_method)
        return method_names[self.default_method]

    def setup_inpayments(self):
        methods = get_all_methods_dict()
        payment_method = self.get_default_payment_method()
        if payment_method != METHOD_MULTIPLE:
            self.clear_preview_payments(methods[payment_method])
        payments = self.get_items()
        if not payments.count():
            raise ValueError('You must have at least one payment for each '
                             'payment group')
        self.installments_number = payments.count()
        self.set_payments_to_pay()

    def set_payments_to_pay(self):
        """Checks if all the payments have STATUS_PREVIEW and set them as
        STATUS_TO_PAY
        """
        for payment in self.get_items():
            payment.set_to_pay()

    #
    # IContainer implementation
    #

    @argcheck(Payment)
    def add_item(self, payment):
        payment.group = self

    @argcheck(Payment)
    def remove_item(self, payment):
        Payment.delete(payment.id, connection=self.get_connection())

    def get_items(self):
        return Payment.selectBy(group=self,
                                connection=self.get_connection())

    #
    # Auxiliar method
    #

    def clear_preview_payments(self, ignore_method_iface=None):
        """Delete payments of preview status associated to the current
        payment_group. It can happen if user open and cancel this wizard.
        Notes:
            ignore_method_iface = a payment method interface which is
                                  ignored in the search for payments
        """
        conn = self.get_connection()
        q1 = Payment.q.status == Payment.STATUS_PREVIEW
        q2 = Payment.q.groupID == self.id
        if ignore_method_iface:
            base_method = sysparam(conn).BASE_PAYMENT_METHOD
            method = ignore_method_iface(base_method, connection=conn)
            q3 = Payment.q.methodID != method.id
            query = AND(q1, q2, q3)
        else:
            query = AND(q1, q2)
        payments = Payment.select(query, connection=conn)
        conn = self.get_connection()
        for payment in payments:
            inpayment = IInPayment(payment, connection=conn)
            if not inpayment:
                continue
            payment.method.delete_inpayment(inpayment)


#
# Adapters for Payment class
#


class PaymentAdaptToInPayment(ModelAdapter):

    implements(IInPayment)

    def receive(self):
        payment = self.get_adapted()
        if not payment.is_to_pay():
            raise ValueError("This payment is already received.")
        payment.pay()
        payment.group.update_thirdparty_status()

Payment.registerFacet(PaymentAdaptToInPayment, IInPayment)


class PaymentAdaptToOutPayment(ModelAdapter):

    implements(IOutPayment)

    def pay(self):
        payment = self.get_adapted()
        if not payment.is_to_pay():
            raise ValueError("This payment is already paid.")
        payment.pay()

Payment.registerFacet(PaymentAdaptToOutPayment, IOutPayment)

class CashAdvanceInfo(Domain):
    employee = ForeignKey("PersonAdaptToEmployee")
    payment = ForeignKey("Payment")
    open_date = DateTimeCol(default=datetime.datetime.now)

