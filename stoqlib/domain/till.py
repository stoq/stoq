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
from stoqlib.exceptions import TillError, DatabaseInconsistency
from stoqlib.domain.base import Domain, BaseSQLView
from stoqlib.domain.sale import Sale
from stoqlib.domain.payment.payment import AbstractPaymentGroup, Payment
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
        - I{STATUS_PENDING}: this till is created, but not yet opened
        - I{STATUS_OPEN}: this till is opened and we can make sales for it.
        - I{STATUS_CLOSED}: end of the day, the till is closed and no more
                            financial operations can be done in this store.
        - I{initial_cash_amount}: The total amount we have in the moment we
                                  are opening the till.
        - I{final_cash_amount}: The total amount we have in the moment we
                                are closing the till.
        - I{opening_date}: When the till was opened or None if it has not yet
                           been opened.
        - I{closing_date}: When the till was closed or None if it has not yet
                           been closed
        - I{station}: the station associated with the till, eg the computer
                      which opened it.
    """

    (STATUS_PENDING,
     STATUS_OPEN,
     STATUS_CLOSED) = range(3)

    statuses = {STATUS_PENDING: _(u"Pending"),
                STATUS_OPEN:    _(u"Opened"),
                STATUS_CLOSED:  _(u"Closed")}

    status = IntCol(default=STATUS_PENDING)
    initial_cash_amount = PriceCol(default=0, notNull=True)
    final_cash_amount = PriceCol(default=0, notNull=True)
    opening_date = DateTimeCol(default=None)
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

        till = cls.selectOne(AND(cls.q.status == Till.STATUS_OPEN,
                                 cls.q.stationID == BranchStation.q.id,
                                 # Bug 2978: Empty till objects are sometimes created
                                 cls.q.opening_date != None,
                                 BranchStation.q.branchID == branch.id),
                             connection=conn)

        if till and till.needs_closing():
            raise TillError(
                _("You need to close the till opened at %s before "
                  "doing any fiscal operations" % (
                till.opening_date.date(),)))

        return till

    @classmethod
    def get_last_opened(cls, conn):
        """
        Fetches the last Till which was opened.
        If in doubt, use Till.get_current instead. This method is a special case
        which is used to be able to close a till without calling get_current()
        @param conn: a database connection
        """

        result = Till.selectBy(status=Till.STATUS_OPEN,
                               connection=conn).orderBy('opening_date')
        if result:
            return result[0]

    #
    # Till methods
    #

    def open_till(self):
        if self.status == Till.STATUS_OPEN:
            raise TillError(_('Till is already open'))

        conn = self.get_connection()

        # Make sure that the till has not been opened today
        today = datetime.datetime.today().date()
        if Till.select(Till.q.opening_date >= today, connection=conn):
            raise TillError(_("A till has already been opened today"))

        last_till = get_last_till_operation_for_current_branch(conn)
        if last_till:
            if not last_till.closing_date:
                raise TillError(_("Previous till was not closed"))
            elif last_till.opening_date.date() == today:
                raise TillError(_("A till has already been opened today"))

            # FIXME: Move to sale.confirm()
            sales = last_till.get_unconfirmed_sales()
            for sale in sales:
                sale.till = self

            initial_cash_amount = last_till.final_cash_amount
        else:
            initial_cash_amount = 0

        self.initial_cash_amount = initial_cash_amount

        if IPaymentGroup(self, None) is None:
            # Add a IPaymentGroup facet for the new till and make it easily
            # available to receive new payments
            self.addFacet(IPaymentGroup, connection=conn)

        self.opening_date = datetime.datetime.now()
        self.status = Till.STATUS_OPEN

    def close_till(self, removed=0):
        """
        This method close the current till operation with the confirmed
        sales associated. If there is a sale with a differente status than
        SALE_CONFIRMED, a new 'pending' till operation is created and
        these sales are associated with the current one.
        @param removed:
        """

        if self.status == Till.STATUS_CLOSED:
            raise TillError(_("Till is already closed"))

        if removed:
            if removed > self.get_balance():
                raise ValueError("The cash amount that you want to send is "
                                 "greater than the current balance.")

            self.create_debit(removed,
                              _(u'Amount removed from Till on %s' %
                                self.opening_date.strftime('%x')))

        for sale in self.get_unconfirmed_sales():
            group = IPaymentGroup(sale)

            # FIXME: Move this to payment itself
            for payment in group.get_items():
                payment.status = Payment.STATUS_PENDING

        self.closing_date = datetime.datetime.now()
        self.final_cash_amount = self.get_balance()
        self.status = Till.STATUS_CLOSED

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

    def get_unconfirmed_sales(self):
        """
        Fetches a list of all sales which are not confirmed

        @returns: a list of L{stoqlib.domain.sale.Sale} objects
        """
        sales = Sale.get_available_sales(self.get_connection(), self)
        return [sale for sale in sales
                         if sale.status != Sale.STATUS_CONFIRMED]

    def needs_closing(self):
        """
        Checks if there's an open till that needs to be closed before
        we can do any further fiscal operations.
        @returns: True if it needs to be closed, otherwise false
        """
        if self.status != Till.STATUS_CLOSED:
            if not self.opening_date:
                return False

            # Verify that the currently open till was opened today
            open_date = self.opening_date.date()
            if open_date != datetime.datetime.today().date():
                return True

        return False

    #
    # Operations on TillEntryAndPaymentView
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
        results = TillEntryAndPaymentView.selectBy(
            till_id=self.id, connection=self.get_connection())
        return currency(self.initial_cash_amount + (results.sum('value') or 0))

    def get_entries(self):
        return TillEntryAndPaymentView.selectBy(
            till_id=self.id, connection=self.get_connection())

    def get_initial_cash_amount(self):
        """
        Get the total amount we have in the moment we are opening the till.
        This value is useful when providing change during sales.
        @returns: the initial amount
        """
        entry = TillEntryAndPaymentView.selectOneBy(
            till_id=self.id,
            is_initial_cash_amount=True,
            connection=self.get_connection())
        if not entry:
            raise DatabaseInconsistency("You should have only one initial "
                                        "cash amount entry at this point")
        return entry.value

    def get_credits_total(self):
        view = TillEntryAndPaymentView
        results = view.select(AND(view.q.value > 0,
                                  view.q.till_id == self.id),
                              connection=self.get_connection())
        return currency(results.sum('value') or 0)

    def get_debits_total(self):
        view = TillEntryAndPaymentView
        results = view.select(AND(view.q.value < 0,
                                  view.q.till_id == self.id),
                              connection=self.get_connection())
        return currency(results.sum('value') or 0)

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


    @property
    def till(self):
        return self.get_adapted()

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
        return self.till.branch.person

    def get_group_description(self):
        today_str = self.till.opening_date.strftime(_(u'%d of %B'))
        return _(u'till of %s') % today_str

Till.registerFacet(TillAdaptToPaymentGroup, IPaymentGroup)


#
# Views
#


class TillFiscalOperationsView(SQLObject, BaseSQLView):
    """Stores informations about till payment tables
    """

    identifier = IntCol()
    date = DateTimeCol()
    description = UnicodeCol()
    station_name = UnicodeCol()
    value = PriceCol()
    branch_id = IntCol()
    status = IntCol()

class TillEntryAndPaymentView(SQLObject, BaseSQLView):
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
    result = TillEntryAndPaymentView.selectBy(
        status=Till.STATUS_CLOSED,
        branch_id=branch.id,
        connection=conn).orderBy('date')

    if result:
        till_entry = result[-1]
        return Till.get(till_entry.till_id, connection=conn)
