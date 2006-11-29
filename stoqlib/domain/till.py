# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source <http://www.async.com.br>
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
## Author(s):    Henrique Romano        <henrique@async.com.br>
##               Evandro Vale Miquelito <evandro@async.com.br>
##               Johan Dahlin           <jdahlin@async.com.br>
##
""" Implementation of classes related to Payment management. """

import datetime

from sqlobject import (IntCol, DateTimeCol, ForeignKey, BoolCol, UnicodeCol,
                       SQLObject)
from sqlobject.sqlbuilder import AND
from zope.interface import implements
from kiwi.datatypes import currency
from kiwi.log import Logger

from stoqlib.database.columns import PriceCol, AutoIncCol
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.database.runtime import get_current_branch
from stoqlib.exceptions import (TillError, DatabaseInconsistency,
                                StoqlibError)
from stoqlib.domain.base import Domain, BaseSQLView
from stoqlib.domain.sale import Sale
from stoqlib.domain.payment.base import AbstractPaymentGroup, Payment
from stoqlib.domain.interfaces import (IPaymentGroup, ITillOperation,
                                       IOutPayment, IInPayment)
from stoqlib.domain.station import BranchStation

_ = stoqlib_gettext

#
# Domain Classes
#

log = Logger('stoqlib.till')

class Till(Domain):
    """A definition of till operation.

    B{Attributes}:
        - I{STATUS_PENDING}: this till have some sales unconfirmed when
                             closing the till of the last day but it's
                             not opened yet.
        - I{STATUS_OPEN}: this till is opened and we can make sales for it.
        - I{STATUS_CLOSED}: end of the day, the till is closed and no more
                            financial operations can be done in this store.
        - I{balance_sent}: the amount total sent to the warehouse or main
                           store after closing the till.
        - I{initial_cash_amount}: The total amount we have in the moment we
                                  are opening the till. This value is useful
                                  when providing change during sales.
        - I{station}: a till operation is always associated with a branch
                      station which means the computer in a branch company
                      responsible to open the till
    """

    (STATUS_PENDING,
     STATUS_OPEN,
     STATUS_CLOSED) = range(3)

    statuses = {STATUS_PENDING: _(u"Pending"),
                STATUS_OPEN:    _("Opened"),
                STATUS_CLOSED:  _("Closed")}

    status = IntCol(default=STATUS_PENDING)
    balance_sent = PriceCol(default=0)
    final_cash_amount = PriceCol(default=0)
    opening_date = DateTimeCol(default=datetime.datetime.now)
    closing_date = DateTimeCol(default=None)
    station = ForeignKey('BranchStation')


    #
    # Classmethods
    #

    @classmethod
    def get_current(cls, conn):
        """
        Fetches the Till for the current branch.
        @param conn: a database connection
        @returns: a Till instance or None
        """
        branch = get_current_branch(conn)
        assert branch is not None

        result = cls.select(AND(cls.q.status == Till.STATUS_OPEN,
                                cls.q.stationID == BranchStation.q.id,
                                BranchStation.q.branchID == branch.id),
                            connection=conn)
        if result.count() > 1:
            raise TillError(
                "You should have only one Till opened. Got %d instead." %
                result.count())
        elif result.count() == 0:
            return None
        return result[0]

    #
    # Till methods
    #

    def open_till(self):
        if self.status == Till.STATUS_OPEN:
            raise StoqlibError('till_open(): Till was already open')

        conn = self.get_connection()
        last_till = get_last_till_operation_for_current_branch(conn)
        if last_till:
            final_cash = last_till.final_cash_amount
            if final_cash > 0:
                reason = _(u'Cash amount remaining of %s'
                           % last_till.closing_date.strftime('%x'))
                self.create_credit(final_cash, reason)

            sales = last_till.get_unconfirmed_sales()
            for sale in sales:
                sale.till = self

        if IPaymentGroup(self, None) is None:
            # Add a IPaymentGroup facet for the new till and make it easily
            # available to receive new payments
            self.addFacet(IPaymentGroup, connection=conn)

        self.status = Till.STATUS_OPEN

    def close_till(self):
        """ This method close the current till operation with the confirmed
        sales associated. If there is a sale with a differente status than
        SALE_CONFIRMED, a new 'pending' till operation is created and
        these sales are associated with the current one.
        """

        if self.status == Till.STATUS_CLOSED:
            raise StoqlibError("This till is already closed. Open a new till "
                               "before close it.")

        for sale in self.get_unconfirmed_sales():
            group = IPaymentGroup(sale)

            # FIXME: Move this to payment itself
            for payment in group.get_items():
                payment.status = Payment.STATUS_PENDING

        current_balance = self.get_balance()
        if self.balance_sent and self.balance_sent > current_balance:
            raise ValueError("The cash amount that you want to send is "
                             "greater than the current balance.")

        self.closing_date = datetime.datetime.now()
        self.final_cash_amount = current_balance - self.balance_sent
        self.status = self.STATUS_CLOSED

    def create_debit(self, value, reason=u""):
        """
        Add debit to the till
        @param value: amount to add
        @param reason: description of payment
        @returns: payment group representing the added debit
        """
        group = self._get_payment_group()
        return group.create_debit(value, reason, self)

    def create_credit(self, value, reason=u""):
        """
        Add credit to the till
        @param value: amount to add
        @param reason: description of payment
        @returns: payment group representing the added credit
        """
        group = self._get_payment_group()
        return group.create_credit(value, reason, self)

    def get_cash_total(self):
        results = TillEntry.selectBy(
            tillID=self.id, connection=self.get_connection())
        return currency(results.sum('value') or 0)

    def get_unconfirmed_sales(self):
        """
        Fetches a list of all sales which are not confirmed

        @returns: a list of L{stoqlib.domain.sale.Sale} objects
        """
        sales = Sale.get_available_sales(self.get_connection(), self)
        return [sale for sale in sales
                         if sale.status != Sale.STATUS_CONFIRMED]

    #
    # Operations on TillFiscalOperationsView
    #
    # TODO: Should they be moved to the view itself or should the view
    #       only be treated as an implementation details?
    #       or just add a layer of extra indirection?
    #

    def get_balance(self):
        """ Return the total of all "extra" payments (like cash
        advance, till complement, ...) associated to this till
        operation *plus* all the payments, which payment method is
        money, of all the sales associated with this operation
        *plus* the initial cash amount.
        """
        results = TillFiscalOperationsView.selectBy(
            till_id=self.id, connection=self.get_connection())
        return currency(results.sum('value') or 0)

    def get_entries(self):
        return TillFiscalOperationsView.selectBy(
            till_id=self.id, connection=self.get_connection())

    def get_initial_cash_amount(self):
        entry = TillFiscalOperationsView.selectOneBy(
            till_id=self.id,
            is_initial_cash_amount=True,
            connection=self.get_connection())
        if not entry:
            raise DatabaseInconsistency("You should have only one initial "
                                        "cash amount entry at this point")
        return entry.value

    def get_credits_total(self):
        view = TillFiscalOperationsView
        results = view.select(AND(view.q.value > 0,
                                  view.q.till_id == self.id),
                              connection=self.get_connection())
        return currency(results.sum('value') or 0)

    def get_debits_total(self):
        view = TillFiscalOperationsView
        results = view.select(AND(view.q.value < 0,
                                  view.q.till_id == self.id),
                              connection=self.get_connection())
        return currency(results.sum('value') or 0)

    def get_float_remaining(self):
        return currency(self.get_balance() - self.balance_sent)

    #
    # Private
    #

    def _get_payment_group(self):
        group = IPaymentGroup(self, None)

        # TODO: Add a payment group when we create the till, or is
        #       okay/better to do it only when it's needed?
        if group is None:
            group = self.addFacet(IPaymentGroup,
                                  connection=self.get_connection())
        return group

class TillEntry(Domain):
    #
    # It's usefull to use the same sequence of Payment table since we want
    # sometimes do mix payments and till entries in the same database view,
    # so we can search properly by identifier field
    #
    # TODO: Document that a positive "value" attribute represents something
    #       completely different from a negative value.
    #
    identifier = AutoIncCol("stoqlib_payment_identifier_seq")
    date = DateTimeCol(default=datetime.datetime.now)
    description = UnicodeCol()
    value = PriceCol()
    is_initial_cash_amount = BoolCol(default=False)
    till = ForeignKey("Till")
    payment_group = ForeignKey("AbstractPaymentGroup", default=None)


#
# Adapters
#


class TillAdaptToPaymentGroup(AbstractPaymentGroup):
    implements(IPaymentGroup, ITillOperation)

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

    #
    # IPaymentGroup implementation
    #

    def get_thirdparty(self):
        branch = self.get_adapted().branch
        return branch.person

    def get_group_description(self):
        till = self.get_adapted()
        date_format = _(u'%d of %B')
        today_str = till.opening_date.strftime(date_format)
        return _(u'till of %s') % today_str

Till.registerFacet(TillAdaptToPaymentGroup, IPaymentGroup)


#
# Views
#


class TillFiscalOperationsView(SQLObject, BaseSQLView):
    """Stores informations about till fiscal operations, which is a union
    between till_entry and payment tables
    """

    identifier = IntCol()
    date = DateTimeCol()
    closing_date = DateTimeCol()
    description = UnicodeCol()
    value = PriceCol()
    is_initial_cash_amount = IntCol()
    till_id = IntCol()
    station_name = UnicodeCol()
    branch_id = IntCol()
    status = IntCol()


#
# Functions
#


def get_last_till_operation_for_current_branch(conn):
    """  The last till operation is used to get a initial cash amount
    to a new till operation that will be created, this value is based
    on the final_cash_amount attribute of the last till operation
    """

    branch = get_current_branch(conn)
    result = TillFiscalOperationsView.selectBy(status=Till.STATUS_CLOSED,
                                               branch_id=branch.id,
                                               connection=conn)
    if result:
        till_entry = result[-1]
        return Till.get(till_entry.till_id, connection=conn)
