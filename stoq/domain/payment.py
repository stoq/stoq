# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s):    Henrique Romano <henrique@async.com.br>
"""
stoq/domain/payment.py:

   Implementation of classes related to Payment management.
"""

from datetime import datetime
import operator

from sqlobject import (IntCol, DateTimeCol, FloatCol, StringCol, 
                       ForeignKey)
from sqlobject.sqlbuilder import AND
from stoqlib.exceptions import PaymentError, TillError

from stoq.domain.base import (Domain, ModelAdapter,
                              InheritableModelAdapter)
from stoq.domain.interfaces import IInPayment, IOutPayment, IPaymentGroup
from stoq.domain.interfaces import IBranch, IContainer
from stoq.domain.person import Person
from stoq.lib.parameters import sysparam


#
# Domain Classes
# 

class Payment(Domain):
    (STATUS_PREVIEW, STATUS_TO_PAY, STATUS_PAID, STATUS_REVIEWING,
     STATUS_CONFIRMED, STATUS_CANCELLED) = range(6)

    status = IntCol(default=STATUS_PREVIEW)
    due_date = DateTimeCol()
    paid_date = DateTimeCol(default=None)
    paid_value = FloatCol(default=None)
    value = FloatCol()
    description = StringCol(default=None)

    method = ForeignKey('PaymentMethod')
    group = ForeignKey('AbstractPaymentGroup')
    # XXX: It will not be implemented for now.
#    destination = ForeignKey('Account')
    
    def is_to_pay(self):
        return self.status == self.STATUS_TO_PAY

    def pay(self, value=None, paid_date=None):
        if self.group.get_thirdparty() is None:
            raise PaymentError("You must have a thirdparty to quit "
                               "the payment")

        self.paid_value = value and value or self.value
        self.paid_date = paid_date and paid_date or datetime.now()
        self.status = self.STATUS_PAID

    def cancel(self):
        if self.status == self.STATUS_CANCELLED:
            raise PaymentError("This payment is already cancelled")

        self.status = self.STATUS_CANCELLED


class PaymentMethod(Domain):
    description = StringCol()


class Till(Domain):
    STATUS_PENDING, STATUS_OPEN, STATUS_CLOSED = range(3)

    status = IntCol(default=STATUS_PENDING)
    balance_sent = FloatCol(default=None)
    initial_cash_amount = FloatCol(default=0.0)
    final_cash_amount = FloatCol(default=None)
    opening_date = DateTimeCol(default=datetime.now())
    closing_date = DateTimeCol(default=None)

    branch = ForeignKey(Person.getAdapterClass(IBranch).__name__)

    def get_balance(self):
        """ Return the total of all "extra" payments (like cash
        advance, till complement, ...) associated to this till
        movimentation *plus* all the payments, which payment method is
        money, of all the sales associated with this movimentation 
        *plus* the initial cash amount. """

        from stoq.domain.sale import Sale

        conn = self.get_connection()

        query = AND(Sale.q.status == Sale.STATUS_CONFIRMED,
                    Sale.q.tillID == self.id)
        result = Sale.select(query, connection=conn)
        payments = []
        money_payment_method = sysparam(conn).MONEY_PAYMENT_METHOD
        for sale in result:
            sale_pg_facet = IPaymentGroup(sale)
            assert sale_pg_facet, ("The sale associated to this "
                                   "till movimentation don't have "
                                   "a PaymentGroup facet.")
            payments.extend([p for p in sale_pg_facet.get_items() 
                                 if p.method == money_payment_method])
        pg_facet = IPaymentGroup(self, connection=conn)
        if pg_facet:
            payments.extend(pg_facet.get_items())

        total = reduce(operator.add, [p.value for p in payments], 0.0)
        return total + self.initial_cash_amount
    
    def open_till(self, opening_date=datetime.now(), initial_cash_amount=0.0):
        if not initial_cash_amount:
            last_till = get_last_till_movimentation(self.get_connection())
            if last_till:
                self.initial_cash_amount = last_till.final_cash_amount
        self.opening_date = opening_date
        self.status = self.STATUS_OPEN

    def close_till(self, balance_to_send=0.0, closing_date=datetime.now()):
        if self.status != Till.STATUS_OPEN:
            raise ValueError("This till is already closed. Open a new till "
                             "before close it.")

        from stoq.domain.sale import Sale

        conn = self.get_connection()
        sales = Sale.selectBy(till=self, connection=conn)

        money_payment_method = sysparam(conn).MONEY_PAYMENT_METHOD
        for sale in sales:
            for payment in IPaymentGroup(sale).get_items():
                if payment.method is money_payment_method:
                    payment.status = Payment.STATUS_REVIEWING
                else:
                    payment.status = Payment.STATUS_TO_PAY

        current_balance = self.get_balance()
        if balance_to_send and balance_to_send > current_balance:
            raise ValueError("The cash amount that you want to send is "
                             "greater than the current balance.")
        self.status = self.STATUS_CLOSED
        self.closing_date = closing_date
        self.final_cash_amount = current_balance - balance_to_send
        self.balance_sent = balance_to_send


#
# Adapters
#

class PaymentAdaptToInPayment(ModelAdapter):

    __implements__ = IInPayment

    def receive(self):
        payment = self.get_adapted()
        if not payment.is_to_pay():
            raise ValueError("This payment is already received.")
        payment.pay()

Payment.registerFacet(PaymentAdaptToInPayment)


class PaymentAdaptToOutPayment(ModelAdapter):

    __implements__ = IOutPayment

    def pay(self):
        payment = self.get_adapted()
        if not payment.is_to_pay():
            raise ValueError("This payment is already paid.")
        payment.pay()

Payment.registerFacet(PaymentAdaptToOutPayment)


class AbstractPaymentGroup(InheritableModelAdapter):
    STATUS_PREVIEW, STATUS_OPEN, STATUS_CLOSED, STATUS_CANCELLED = range(4)

    __implements__ = IPaymentGroup, IContainer

    status = IntCol(default=STATUS_OPEN)
    open_date = DateTimeCol(default=datetime.now())
    close_date = DateTimeCol(default=None)
    notes = StringCol(default='')
    thirdparty = ForeignKey('Person')


    def set_thirdparty(self, person):
        if not isinstance(person, Person):
            raise TypeError("A Person object is required for set_thirdparty, "
                            "got %s instead." % type(person))
        self.thirdparty = person

    def get_thirdparty(self):
        return self.thirdparty

    def get_balance(self):
        values = [s.value for s in self.get_items()]
        return reduce(operator.add, values, 0.0)

    def add_debit(self, value, reason, category, date=None):
        payment = self.create_payment(value, reason, category, date)

        return payment.addFacet(IOutPayment)

    def add_credit(self, value, reason, category, date=None):
        payment = self.create_payment(value, reason, category, date)
        
        return payment.addFacet(IInPayment)

    #
    # Helper methods
    #

    def create_payment(self, value, reason, category, date=None):
        date = date or datetime.now()
        payment = Payment(due_date=date, value=value, description=reason,
                          category=category, group=self)
        self.add_item(payment)

        return payment

    #
    # IPaymentGroup implementation
    #

    def add_item(self, payment):
        payment.group = self

    def remove_item(self, payment):
        if not isinstance(payment, Payment):
            raise TypeError("A Payment object is required for remove_item, "
                            "got %s instead." % type(payment))

        Payment.delete(payment.id, connection=self.get_connection())

    def get_items(self):
        result = Payment.selectBy(group=self, 
                                   connection=self.get_connection())
        return list(result)


class TillAdaptToPaymentGroup(AbstractPaymentGroup):
    __implements__ = IPaymentGroup

    def add_complement(self, value, reason, category, date=None):
        # TODO: implement this method
        pass

    def get_cash_advance(self, value, reason, category, employee, date=None):
        # TODO: implement this method
        pass

    def get_cancel_payment(self, payment):
        # TODO: implement this method
        pass

Till.registerFacet(TillAdaptToPaymentGroup)

#
# Functions
#

def get_current_till_movimentation(conn):
    result = Till.select(Till.q.status == Till.STATUS_OPEN, connection=conn)
    if result.count() > 1:
        raise TillError("You should have only one Till opened. Got %d "
                        "instead." % result.count())
    elif result.count() == 0:
        return None

    return result[0]


def get_last_till_movimentation(conn):
    """  The last till movimentation is used to get a initial cash amount
    to a new till movimentation that will be created, this value is based
    on the final_cash_amount attribute of the last till movimentation """

    query = AND(Till.q.status == Till.STATUS_CLOSED, 
                Till.q.branchID == sysparam(conn).CURRENT_BRANCH.id)
    result = Till.select(query, connection=conn)
    return result.count() and result[-1] or None
