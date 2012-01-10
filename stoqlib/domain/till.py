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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
"""Implementation of classes related to Fiscal operations.
"""

import datetime

from kiwi.datatypes import currency
from kiwi.log import Logger

from stoqlib.database.orm import PriceCol
from stoqlib.database.orm import IntCol, DateTimeCol, ForeignKey, UnicodeCol
from stoqlib.database.orm import AND, const, OR, LEFTJOINOn
from stoqlib.database.runtime import get_current_station
from stoqlib.domain.base import Domain
from stoqlib.domain.payment.payment import Payment
from stoqlib.exceptions import TillError
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

log = Logger('stoqlib.till')

#
# Domain Classes
#


class Till(Domain):
    """The Till describes the financial operations of a specific day.

    The operations that are recorded in a Till:
      - Sales
      - Adding cash
      - Removing cash
      - Giving out an early salary

    Each operation is associated with a L{TillEntry}.

    You can only open a Till once per day, and you cannot open a new
    till before you closed the previously opened one.

    @cvar STATUS_PENDING: this till is created, but not yet opened
    @cvar STATUS_OPEN: this till is opened and we can make sales for it.
    @cvar STATUS_CLOSED: end of the day, the till is closed and no more
      financial operations can be done in this store.
    @ivar initial_cash_amount: The total amount we have in the moment we
      are opening the till.
    @ivar final_cash_amount: The total amount we have in the moment we
      are closing the till.
    @ivar opening_date: When the till was opened or None if it has not yet
      been opened.
    @ivar closing_date: When the till was closed or None if it has not yet
      been closed
    @ivar station: the station associated with the till, eg the computer
      which opened it.
    """

    (STATUS_PENDING,
     STATUS_OPEN,
     STATUS_CLOSED) = range(3)

    statuses = {STATUS_PENDING: _(u'Pending'),
                STATUS_OPEN: _(u'Opened'),
                STATUS_CLOSED: _(u'Closed')}

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
        """Fetches the Till for the current station.
        @param conn: a database connection
        @returns: a Till instance or None
        """
        station = get_current_station(conn)
        assert station is not None

        till = cls.selectOneBy(status=Till.STATUS_OPEN,
                               station=station,
                               connection=conn)
        if till and till.needs_closing():
            raise TillError(
                _("You need to close the till opened at %s before "
                  "doing any fiscal operations") % (
                till.opening_date.date(), ))

        return till

    @classmethod
    def get_last_opened(cls, conn):
        """Fetches the last Till which was opened.
        If in doubt, use Till.get_current instead. This method is a special case
        which is used to be able to close a till without calling get_current()
        @param conn: a database connection
        """

        result = Till.selectBy(status=Till.STATUS_OPEN,
                               station=get_current_station(conn),
                               connection=conn).orderBy('opening_date')
        if result:
            return result[0]

    @classmethod
    def get_last(cls, conn):
        result = Till.selectBy(station=get_current_station(conn),
                               connection=conn).orderBy('opening_date')
        if result:
            return result[-1]

    @classmethod
    def get_last_closed(cls, conn):
        results = Till.selectBy(status=Till.STATUS_CLOSED,
                                station=get_current_station(conn),
                                connection=conn).orderBy('opening_date')
        if results:
            return results[-1]

    #
    # Till methods
    #

    def open_till(self):
        """Open the till.

        It can only be done once per day.
        The final cash amount of the previous till will be used
        as the initial value in this one after opening it.
        """
        if self.status == Till.STATUS_OPEN:
            raise TillError(_('Till is already open'))

        # Make sure that the till has not been opened today
        today = datetime.date.today()
        if Till.select(AND(const.date(Till.q.opening_date) >= today,
                           Till.q.stationID == self.station.id),
                       connection=self.get_connection()):
            raise TillError(_("A till has already been opened today"))

        last_till = self._get_last_closed_till()
        if last_till:
            if not last_till.closing_date:
                raise TillError(_("Previous till was not closed"))

            initial_cash_amount = last_till.final_cash_amount
        else:
            initial_cash_amount = 0

        self.initial_cash_amount = initial_cash_amount

        self.opening_date = const.NOW()
        self.status = Till.STATUS_OPEN

    def close_till(self):
        """This method close the current till operation with the confirmed
        sales associated. If there is a sale with a differente status than
        SALE_CONFIRMED, a new 'pending' till operation is created and
        these sales are associated with the current one.
        @param removed:
        """

        if self.status == Till.STATUS_CLOSED:
            raise TillError(_("Till is already closed"))

        if self.get_balance() < 0:
            raise ValueError(_("Till balance is negative, but this should not "
                               "happen. Contact Stoq Team if you need "
                               "assistance"))

        self.final_cash_amount = self.get_balance()
        self.closing_date = const.NOW()
        self.status = Till.STATUS_CLOSED

    def add_entry(self, payment):
        """
        Adds an entry to the till.
        @param payment:
        @returns: till entry representing the added debit
        @rtype: L{TillEntry}
        """
        if payment.is_inpayment():
            value = payment.value
        elif payment.is_outpayment():
            value = -payment.value
        else:
            raise AssertionError(payment)

        return self._add_till_entry(value, payment.description, payment)

    def add_debit_entry(self, value, reason=u""):
        """Add debit to the till
        @param value: amount to add
        @param reason: description of payment
        @returns: till entry representing the added debit
        @rtype: L{TillEntry}
        """
        assert value >= 0

        return self._add_till_entry(-value, reason)

    def add_credit_entry(self, value, reason=u""):
        """Add credit to the till
        @param value: amount to add
        @param reason: description of payment
        @returns: till entry representing the added credit
        @rtype: L{TillEntry}
        """
        assert value >= 0

        return self._add_till_entry(value, reason)

    def needs_closing(self):
        """Checks if there's an open till that needs to be closed before
        we can do any further fiscal operations.
        @returns: True if it needs to be closed, otherwise false
        """
        if self.status != Till.STATUS_OPEN:
            return False

        # Verify that the till wasn't opened today
        if self.opening_date.date() == datetime.date.today():
            return False

        return True

    def get_balance(self):
        """Returns the balance of all till operations plus the initial amount
        cash amount.
        @returns: the balance
        @rtype: currency
        """
        total = self.get_entries().sum('value') or 0
        return currency(self.initial_cash_amount + total)

    def get_cash_amount(self):
        """Returns the total cash amount on the till. That includes "extra"
        payments (like cash advance, till complement and so on), the money
        payments and the initial cash amount.
        @returns: the cash amount on the till
        @rtype: currency
        """
        from stoqlib.domain.payment.method import PaymentMethod
        conn = self.get_connection()
        money = PaymentMethod.get_by_name(conn, 'money')

        results = TillEntry.select(
            join=LEFTJOINOn(None, Payment, Payment.q.id == TillEntry.q.paymentID),
            clause=AND(OR(TillEntry.q.paymentID == None,
                          Payment.q.methodID == money.id),
                       TillEntry.q.tillID == self.id),
            connection=conn)

        return currency(self.initial_cash_amount +
                        (results.sum('till_entry.value') or 0))

    def get_entries(self):
        """Fetches all the entries related to this till
        @returns: all entries
        @rtype: sequence of L{TillEntry}
        """
        return TillEntry.selectBy(
            till=self, connection=self.get_connection())

    def get_credits_total(self):
        """Calculates the total credit for all entries in this till
        @returns: total credit
        @rtype: currency
        """
        results = TillEntry.select(AND(TillEntry.q.value > 0,
                                       TillEntry.q.tillID == self.id),
                                   connection=self.get_connection())
        return currency(results.sum('value') or 0)

    def get_debits_total(self):
        """Calculates the total debit for all entries in this till
        @returns: total debit
        @rtype: currency
        """
        results = TillEntry.select(AND(TillEntry.q.value < 0,
                                       TillEntry.q.tillID == self.id),
                                   connection=self.get_connection())
        return currency(results.sum('value') or 0)

    #
    # Private
    #

    def _get_last_closed_till(self):
        results = Till.selectBy(
            status=Till.STATUS_CLOSED,
            station=self.station,
            connection=self.get_connection()).orderBy('opening_date')

        if results:
            return results[-1]

    def _add_till_entry(self, value, description, payment=None):
        assert value != 0
        return TillEntry(value=value,
                         description=description,
                         payment=payment,
                         till=self,
                         connection=self.get_connection())


class TillEntry(Domain):
    """A TillEntry is a representing cash added or removed in a L{Till}.
    A positive value represents addition
    A negative value represents removal

    @cvar date: the date the entry was created
    @cvar description:
    @cvar value: value of transaction
    @cvar till: the till the entry takes part of
    @cvar payment: optional, if a payment referrers the TillEntry
    """

    date = DateTimeCol(default=datetime.datetime.now)
    description = UnicodeCol()
    value = PriceCol()
    till = ForeignKey("Till", notNull=True)
    payment = ForeignKey("Payment", default=None)
