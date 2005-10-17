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
## Author(s):    Henrique Romano        <henrique@async.com.br>
##               Evandro Vale Miquelito <evandro@async.com.br>
##
"""
stoq/domain/payment.py:

   Implementation of classes related to Payment management.
"""

from datetime import datetime
import operator

from sqlobject import IntCol, DateTimeCol, FloatCol, ForeignKey
from sqlobject.sqlbuilder import AND
from stoqlib.exceptions import TillError

from stoq.lib.parameters import sysparam
from stoq.domain.base import Domain
from stoq.domain.sale import Sale
from stoq.domain.payment.base import AbstractPaymentGroup, Payment
from stoq.domain.interfaces import (IPaymentGroup, ITillOperation,
                                    IOutPayment, IInPayment)



#
# Domain Classes
# 



class Till(Domain):
    """A definition of till operation.
    
    Notes:

        STATUS_PENDING      =   this till have some sales unconfirmed when
                                closing the till of the last day but it's
                                not opened yet.
        STATUS_OPEN         =   this till is opened and we can make sales for
                                it

        STATUS_CLOSED       =   end of the day, the till is closed and no more
                                financial operations can be done in this store

        balance_sent        =   the amount total sent to the warehouse or main
                                store after closing the till

        initial_cash_amount =   the amount total we have in the moment we
                                are opening the till. This value is very
                                useful when change values are need

        branch              =   a till operation is always associated with a
                                a branch which can means a store or a
                                warehouse
    """

    (STATUS_PENDING, 
     STATUS_OPEN, 
     STATUS_CLOSED) = range(3)

    status = IntCol(default=STATUS_PENDING)
    balance_sent = FloatCol(default=None)
    initial_cash_amount = FloatCol(default=0.0)
    final_cash_amount = FloatCol(default=None)
    opening_date = DateTimeCol(default=datetime.now())
    closing_date = DateTimeCol(default=None)

    branch = ForeignKey('PersonAdaptToBranch')

    def get_balance(self):
        """ Return the total of all "extra" payments (like cash
        advance, till complement, ...) associated to this till
        operation *plus* all the payments, which payment method is
        money, of all the sales associated with this operation 
        *plus* the initial cash amount. """

        conn = self.get_connection()
        query = AND(Sale.q.status == Sale.STATUS_CONFIRMED,
                    Sale.q.tillID == self.id)
        result = Sale.select(query, connection=conn)
        payments = []
        money_payment_method = sysparam(conn).METHOD_MONEY
        for sale in result:
            sale_pg_facet = IPaymentGroup(sale)
            assert sale_pg_facet, ("The sale associated to this "
                                   "till operation don't have a "
                                   "PaymentGroup facet.")
            payments.extend([p for p in sale_pg_facet.get_items() 
                                 if p.method == money_payment_method])
        pg_facet = IPaymentGroup(self, connection=conn)
        if pg_facet:
            payments.extend(pg_facet.get_items())

        total = reduce(operator.add, [p.value for p in payments], 0.0)
        return total + self.initial_cash_amount
    
    def open_till(self, opening_date=datetime.now(), initial_cash_amount=0.0):
        if not initial_cash_amount:
            last_till = get_last_till_operation(self.get_connection())
            if last_till:
                self.initial_cash_amount = last_till.final_cash_amount
        self.opening_date = opening_date
        self.status = self.STATUS_OPEN
        conn = self.get_connection()
        if not IPaymentGroup(self, connection=conn):
            # Add a IPaymentGroup facet for the new till and make it easily
            # available to receive new payments
            self.addFacet(IPaymentGroup, connection=conn)

    def close_till(self, balance_to_send=0.0, closing_date=datetime.now()):
        if self.status != Till.STATUS_OPEN:
            raise ValueError("This till is already closed. Open a new till "
                             "before close it.")
        conn = self.get_connection()
        sales = Sale.selectBy(till=self, connection=conn)

        money_payment_method = sysparam(conn).METHOD_MONEY
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



class TillAdaptToPaymentGroup(AbstractPaymentGroup):
    __implements__ = IPaymentGroup, ITillOperation



    #
    # ITillOperation implementation
    #



    def add_debit(self, value, reason, category, date=None):
        payment = self.add_payment(value, reason, category, date)

        return payment.addFacet(IOutPayment)

    def add_credit(self, value, reason, category, date=None):
        payment = self.add_payment(value, reason, category, date)
        
        return payment.addFacet(IInPayment)

    def add_complement(self, value, reason, category, date=None):
        raise NotImplementedError

    def get_cash_advance(self, value, reason, category, employee, date=None):
        raise NotImplementedError

    def cancel_payment(self, payment, reason, date=None):
        raise NotImplementedError

Till.registerFacet(TillAdaptToPaymentGroup)



#
# Functions
#



def get_current_till_operation(conn):
    query = AND(Till.q.status == Till.STATUS_OPEN, 
                Till.q.branchID == sysparam(conn).CURRENT_BRANCH.id)
    result = Till.select(query, connection=conn)
    if result.count() > 1:
        raise TillError("You should have only one Till opened. Got %d "
                        "instead." % result.count())
    elif result.count() == 0:
        return None

    return result[0]


def get_last_till_operation(conn):
    """  The last till operation is used to get a initial cash amount
    to a new till operation that will be created, this value is based
    on the final_cash_amount attribute of the last till operation """

    query = AND(Till.q.status == Till.STATUS_CLOSED, 
                Till.q.branchID == sysparam(conn).CURRENT_BRANCH.id)
    result = Till.select(query, connection=conn)
    return result.count() and result[-1] or None
