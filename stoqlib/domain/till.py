# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2014 Async Open Source <http://www.async.com.br>
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

# pylint: enable=E1101

import logging

from kiwi.currency import currency
from storm.expr import And, Eq, Join, LeftJoin, Or
from storm.info import ClassAlias
from storm.references import Reference

from stoqlib.database.runtime import get_current_user
from stoqlib.database.expr import Date, TransactionTimestamp
from stoqlib.database.properties import (PriceCol, DateTimeCol, UnicodeCol,
                                         IdentifierCol, IdCol, EnumCol)
from stoqlib.database.runtime import get_current_station
from stoqlib.database.viewable import Viewable
from stoqlib.domain.base import Domain
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.person import Person, LoginUser
from stoqlib.domain.station import BranchStation
from stoqlib.exceptions import TillError
from stoqlib.lib.dateutils import localnow, localtoday
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

log = logging.getLogger(__name__)

#
# Domain Classes
#


class Till(Domain):
    """The Till describes the financial operations of a specific day.

    The operations that are recorded in a Till:

      * Sales
      * Adding cash
      * Removing cash
      * Giving out an early salary

    Each operation is associated with a |tillentry|.

    You can only open a Till once per day, and you cannot open a new
    till before you closed the previously opened one.
    """

    __storm_table__ = 'till'

    #: this till is created, but not yet opened
    STATUS_PENDING = u'pending'

    #: this till is opened and we can make sales for it.
    STATUS_OPEN = u'open'

    #: end of the day, the till is closed and no more
    #: financial operations can be done in this store.
    STATUS_CLOSED = u'closed'

    statuses = {STATUS_PENDING: _(u'Pending'),
                STATUS_OPEN: _(u'Opened'),
                STATUS_CLOSED: _(u'Closed')}

    status = EnumCol(default=STATUS_PENDING)

    #: The total amount we had the moment the till was opened.
    initial_cash_amount = PriceCol(default=0, allow_none=False)

    #: The total amount we have the moment the till is closed.
    final_cash_amount = PriceCol(default=0, allow_none=False)

    #: When the till was opened or None if it has not yet been opened.
    opening_date = DateTimeCol(default=None)

    #: When the till was closed or None if it has not yet been closed
    closing_date = DateTimeCol(default=None)

    station_id = IdCol()

    #: the |branchstation| associated with the till, eg the computer
    #: which opened it.
    station = Reference(station_id, 'BranchStation.id')

    observations = UnicodeCol(default=u"")

    responsible_open_id = IdCol()

    #: The responsible for opening the till
    responsible_open = Reference(responsible_open_id, "LoginUser.id")

    responsible_close_id = IdCol()

    #: The responsible for closing the till
    responsible_close = Reference(responsible_close_id, "LoginUser.id")

    #
    # Classmethods
    #

    @classmethod
    def get_current(cls, store):
        """Fetches the Till for the current station.

        :param store: a store
        :returns: a Till instance or None
        """
        station = get_current_station(store)
        assert station is not None

        till = store.find(cls, status=Till.STATUS_OPEN, station=station).one()
        if till and till.needs_closing():
            fmt = _("You need to close the till opened at %s before "
                    "doing any fiscal operations")
            raise TillError(fmt % (till.opening_date.date(), ))

        return till

    @classmethod
    def get_last_opened(cls, store):
        """Fetches the last Till which was opened.
        If in doubt, use Till.get_current instead. This method is a special case
        which is used to be able to close a till without calling get_current()

        :param store: a store
        """

        result = store.find(Till,
                            status=Till.STATUS_OPEN,
                            station=get_current_station(store))
        result = result.order_by(Till.opening_date)
        if not result.is_empty():
            return result[0]

    @classmethod
    def get_last(cls, store):
        station = get_current_station(store)
        result = store.find(Till, station=station).order_by(Till.opening_date)
        return result.last()

    @classmethod
    def get_last_closed(cls, store):
        station = get_current_station(store)
        result = store.find(Till, station=station,
                            status=Till.STATUS_CLOSED).order_by(Till.opening_date)
        return result.last()

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
        today = localtoday().date()
        if not self.store.find(Till,
                               And(Date(Till.opening_date) >= today,
                                   Till.station_id == self.station.id)).is_empty():
            raise TillError(_("A till has already been opened today"))

        last_till = self._get_last_closed_till()
        if last_till:
            if not last_till.closing_date:
                raise TillError(_("Previous till was not closed"))

            initial_cash_amount = last_till.final_cash_amount
        else:
            initial_cash_amount = 0

        self.initial_cash_amount = initial_cash_amount

        self.opening_date = TransactionTimestamp()
        self.status = Till.STATUS_OPEN
        self.responsible_open = get_current_user(self.store)

    def close_till(self, observations=u""):
        """This method close the current till operation with the confirmed
        sales associated. If there is a sale with a differente status than
        SALE_CONFIRMED, a new 'pending' till operation is created and
        these sales are associated with the current one.
        """

        if self.status == Till.STATUS_CLOSED:
            raise TillError(_("Till is already closed"))

        if self.get_balance() < 0:
            raise ValueError(_("Till balance is negative, but this should not "
                               "happen. Contact Stoq Team if you need "
                               "assistance"))

        self.final_cash_amount = self.get_balance()
        self.closing_date = TransactionTimestamp()
        self.status = Till.STATUS_CLOSED
        self.observations = observations
        self.responsible_close = get_current_user(self.store)

    def add_entry(self, payment):
        """
        Adds an entry to the till.

        :param payment: a |payment|
        :returns: |tillentry| representing the added debit
        """
        if payment.is_inpayment():
            value = payment.value
        elif payment.is_outpayment():
            value = -payment.value
        else:  # pragma nocoverage
            raise AssertionError(payment)

        return self._add_till_entry(value, payment.description, payment)

    def add_debit_entry(self, value, reason=u""):
        """Add debit to the till

        :param value: amount to add
        :param reason: description of payment
        :returns: |tillentry| representing the added debit
        """
        assert value >= 0

        return self._add_till_entry(-value, reason)

    def add_credit_entry(self, value, reason=u""):
        """Add credit to the till

        :param value: amount to add
        :param reason: description of entry
        :returns: |tillentry| representing the added credit
        """
        assert value >= 0

        return self._add_till_entry(value, reason)

    def needs_closing(self):
        """Checks if there's an open till that needs to be closed before
        we can do any further fiscal operations.
        :returns: True if it needs to be closed, otherwise false
        """
        if self.status != Till.STATUS_OPEN:
            return False

        # Verify that the till wasn't opened today
        if self.opening_date.date() == localtoday().date():
            return False

        return True

    def get_balance(self):
        """Returns the balance of all till operations plus the initial amount
        cash amount.
        :returns: the balance
        :rtype: currency
        """
        total = self.get_entries().sum(TillEntry.value) or 0
        return currency(self.initial_cash_amount + total)

    def get_cash_amount(self):
        """Returns the total cash amount on the till. That includes "extra"
        payments (like cash advance, till complement and so on), the money
        payments and the initial cash amount.
        :returns: the cash amount on the till
        :rtype: currency
        """
        from stoqlib.domain.payment.method import PaymentMethod
        store = self.store
        money = PaymentMethod.get_by_name(store, u'money')

        clause = And(Or(Eq(TillEntry.payment_id, None),
                        Payment.method_id == money.id),
                     TillEntry.till_id == self.id)

        join = LeftJoin(Payment, Payment.id == TillEntry.payment_id)
        results = store.using(TillEntry, join).find(TillEntry, clause)

        return currency(self.initial_cash_amount +
                        (results.sum(TillEntry.value) or 0))

    def get_entries(self):
        """Fetches all the entries related to this till
        :returns: all entries
        :rtype: sequence of |tillentry|
        """
        return self.store.find(TillEntry, till=self)

    def get_credits_total(self):
        """Calculates the total credit for all entries in this till
        :returns: total credit
        :rtype: currency
        """
        results = self.store.find(
            TillEntry, And(TillEntry.value > 0,
                           TillEntry.till_id == self.id))
        return currency(results.sum(TillEntry.value) or 0)

    def get_debits_total(self):
        """Calculates the total debit for all entries in this till
        :returns: total debit
        :rtype: currency
        """
        results = self.store.find(
            TillEntry, And(TillEntry.value < 0,
                           TillEntry.till_id == self.id))
        return currency(results.sum(TillEntry.value) or 0)

    #
    # Private
    #

    def _get_last_closed_till(self):
        results = self.store.find(Till, status=Till.STATUS_CLOSED,
                                  station=self.station).order_by(Till.opening_date)
        return results.last()

    def _add_till_entry(self, value, description, payment=None):
        assert value != 0
        return TillEntry(value=value,
                         description=description,
                         payment=payment,
                         till=self,
                         branch=self.station.branch,
                         store=self.store)


class TillEntry(Domain):
    """A TillEntry is a representing cash added or removed in a |till|.
     * A positive value represents addition.
     * A negative value represents removal.
    """
    __storm_table__ = 'till_entry'

    #: A numeric identifier for this object. This value should be used instead of
    #: :obj:`Domain.id` when displaying a numerical representation of this object to
    #: the user, in dialogs, lists, reports and such.
    identifier = IdentifierCol()

    #: the date the entry was created
    date = DateTimeCol(default_factory=localnow)

    #: A small string describing what was done
    description = UnicodeCol()

    #: value of transaction
    value = PriceCol()

    till_id = IdCol(allow_none=False)

    #: the |till| the entry takes part of
    till = Reference(till_id, 'Till.id')

    payment_id = IdCol(default=None)

    #: |payment| of this entry, if any
    payment = Reference(payment_id, 'Payment.id')

    branch_id = IdCol()

    #: |branch| that received or gave money
    branch = Reference(branch_id, 'Branch.id')

    @property
    def time(self):
        """The time of the entry

        Note that this is the same as :obj:`.date.time()`, but with
        microseconds replaced to *0*.
        """
        time = self.date.time()
        return time.replace(microsecond=0)

    @property
    def branch_name(self):
        return self.branch.get_description()


class TillClosedView(Viewable):

    id = Till.id
    observations = Till.observations
    opening_date = Date(Till.opening_date)
    closing_date = Date(Till.closing_date)
    initial_cash_amount = Till.initial_cash_amount
    final_cash_amount = Till.final_cash_amount

    branch_id = BranchStation.branch_id

    _ResponsibleOpen = ClassAlias(Person, "responsible_open")
    _ResponsibleClose = ClassAlias(Person, "responsible_close")
    _LoginUserOpen = ClassAlias(LoginUser, "login_responsible_open")
    _LoginUserClose = ClassAlias(LoginUser, "login_responsible_close")

    responsible_open_name = _ResponsibleOpen.name
    responsible_close_name = _ResponsibleClose.name

    tables = [
        Till,
        Join(BranchStation, BranchStation.id == Till.station_id),
        # These two need to be left joins, since historical till dont have a
        # responsible
        LeftJoin(_LoginUserOpen, Till.responsible_open_id == _LoginUserOpen.id),
        LeftJoin(_LoginUserClose, Till.responsible_close_id == _LoginUserClose.id),
        LeftJoin(_ResponsibleOpen, _LoginUserOpen.person_id == _ResponsibleOpen.id),
        LeftJoin(_ResponsibleClose, _LoginUserClose.person_id == _ResponsibleClose.id),
    ]

    clause = Till.status == Till.STATUS_CLOSED
