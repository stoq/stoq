# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2010 Async Open Source <http://www.async.com.br>
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

"""

This module contains classes for working with loans.

The main class is :class:`Loan` which can hold a
set of :class:`LoanItem`.
"""

import datetime
from decimal import Decimal

from kiwi.argcheck import argcheck
from kiwi.currency import currency
from zope.interface import implements

from stoqlib.database.orm import ForeignKey, UnicodeCol, DateTimeCol, IntCol
from stoqlib.database.orm import PriceCol, const, QuantityCol
from stoqlib.domain.base import Domain
from stoqlib.domain.interfaces import IContainer
from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.lib.defaults import DECIMAL_PRECISION
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class LoanItem(Domain):
    """An item in a :class:`loan <Loan>`

    Note that when changing :obj:`~.quantity`, :obj:`~.return_quantity`
    or :obj:`~.sale_quantity` you will need to call :meth:`.sync_stock`
    to synchronize the stock (increase or decrease it).

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/loan_item.html>`__

    """
    # FIXME: Implement lazy updates in here to avoid all the _set_* bellow

    #: The total quantity that was loaned. The product stock for this
    #: will be decreased when the loan stock is synchonized
    quantity = QuantityCol()

    #: The loadned quantity that was sold. Will increase stock so
    #: it's decreased correctly when the
    #: :class:`sale <stoqlib.domain.sale.Sale>` is confirmed
    sale_quantity = QuantityCol(default=Decimal(0))

    #: The loaned quantity that was returned. Will increase stock
    return_quantity = QuantityCol(default=Decimal(0))

    #: price to use for this :obj:`~.sellable` when creating
    #: a :class:`sale <stoqlib.domain.sale.Sale>`
    price = PriceCol()

    #: :class:`sellable <stoqlib.domain.sellable.Sellable>` that is loaned
    #: cannot be *None*
    sellable = ForeignKey('Sellable', notNull=True)

    #: :class:`loan <Loan>` this item belongs to
    loan = ForeignKey('Loan')

    def __init__(self, *args, **kwargs):
        self._diff_quantity = 0
        super(LoanItem, self).__init__(*args, **kwargs)

    @property
    def branch(self):
        return self.loan.branch

    @property
    def storable(self):
        return self.sellable.product_storable

    #
    # ORMObject
    #

    def _set_quantity(self, quantity):
        diff_quantity = getattr(self, 'quantity', 0) - quantity

        self._diff_quantity += diff_quantity
        self._SO_set_quantity(quantity)

    def _set_return_quantity(self, quantity):
        diff_quantity = quantity - getattr(self, 'return_quantity', 0)

        self._diff_quantity += diff_quantity
        self._SO_set_return_quantity(quantity)

    def _set_sale_quantity(self, quantity):
        diff_quantity = quantity - getattr(self, 'sale_quantity', 0)

        self._diff_quantity += diff_quantity
        self._SO_set_sale_quantity(quantity)

    #
    # Public API
    #

    def sync_stock(self):
        """Synchronizes the stock, increasing/decreasing it accordingly

        When setting :obj:`~.quantity`, :obj:`~.return_quantity`
        or :obj:`~.sale_quantity` be sure to call this to properly
        synchronize the stock (increase or decrease it). That counts
        for object creation too.
        """
        diff_quantity = self._diff_quantity

        if diff_quantity > 0:
            self.storable.increase_stock(diff_quantity, self.branch)
        elif diff_quantity < 0:
            diff_quantity = - diff_quantity
            self.storable.decrease_stock(diff_quantity, self.branch)

        self._diff_quantity = 0

    def get_quantity_unit_string(self):
        return "%s %s" % (self.quantity,
                          self.sellable.get_unit_description())

    def get_total(self):
        return currency(self.price * self.quantity)


class Loan(Domain):
    """
    A loan is a collection of sellable items that is being loaned
    to a client, the items are expected to be returned at some
    point in the future.

    A loan that can hold a set of :class:`loan items <LoanItem>`

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/loan.html>`__
    `manual <http://doc.stoq.com.br/manual/loan.html>`__
    """

    implements(IContainer)

    #: The request for a loan has been added to the system,
    #: we know which of the items the client wishes to loan,
    #: it's not defined if the client has actually picked up
    #: the items.
    STATUS_OPEN = 0

    #: All the products or other sellable items have been
    #: returned and are available in stock.
    STATUS_CLOSED = 1

    # FIXME: This is missing a few states,
    #        STATUS_LOANED: stock is completely synchronized
    statuses = {STATUS_OPEN: _(u'Opened'),
                STATUS_CLOSED: _(u'Closed')}

    #: status of the loan
    status = IntCol(default=STATUS_OPEN)

    #: notes related to this loan.
    notes = UnicodeCol(default='')

    #: date loan was opened
    open_date = DateTimeCol(default=datetime.datetime.now)

    #: date loan was closed
    close_date = DateTimeCol(default=None)

    #: loan expires on this date, we expect the items to
    #: to be returned by this date
    expire_date = DateTimeCol(default=None)

    removed_by = UnicodeCol(default='')

    #: branch where the loan was done
    branch = ForeignKey('Branch', default=None)

    #: :class:`user <stoqlib.domain.person.LoginUser>` of the system
    #: that made the loan
    # FIXME: Should probably be a SalesPerson, we can find the
    #        LoginUser via te_created.user
    responsible = ForeignKey('LoginUser')

    #: client that loaned the items
    client = ForeignKey('Client', default=None)

    #
    # Classmethods
    #

    @classmethod
    def get_status_name(cls, status):
        if not status in cls.statuses:
            raise DatabaseInconsistency(_("Invalid status %d") % status)
        return cls.statuses[status]

    #
    # IContainer implementation
    #

    @argcheck(LoanItem)
    def add_item(self, loan_item):
        assert not loan_item.loan
        loan_item.loan = self

    def get_items(self):
        return LoanItem.selectBy(loan=self, connection=self.get_connection())

    @argcheck(LoanItem)
    def remove_item(self, loan_item):
        LoanItem.delete(loan_item.id, connection=self.get_connection())

    #
    # Public API
    #

    def add_sellable(self, sellable, quantity=1, price=None):
        """Adds a new sellable item to a loan

        :param sellable: the sellable
        :param quantity: quantity to add, defaults to 1
        :param price: optional, the price, it not set the price
          from the sellable will be used
        """
        price = price or sellable.price
        return LoanItem(connection=self.get_connection(),
                        quantity=quantity,
                        loan=self,
                        sellable=sellable,
                        price=price)

    #
    # Accessors
    #

    def get_total_amount(self):
        """
        Fetches the total value of the loan, that is to be paid by
        the client.

        It can be calculated as::

            Sale total = Sum(product and service prices) + surcharge +
                             interest - discount

        :returns: the total value
        """
        return currency(self.get_items().sum(
            const.ROUND(LoanItem.q.price * LoanItem.q.quantity,
                        DECIMAL_PRECISION)) or 0)

    def get_client_name(self):
        if self.client:
            return self.client.person.name
        return u''

    def get_branch_name(self):
        if self.branch:
            return self.branch.person.name
        return u''

    def get_responsible_name(self):
        return self.responsible.person.name

    def get_order_number_str(self):
        return u'%05d' % self.id

    #
    # Public API
    #

    def sync_stock(self):
        """Synchronizes the stock of *self*'s :class:`loan items <LoanItem>`

        Just a shortcut to call :meth:`LoanItem.sync_stock` of all of
        *self*'s :class:`loan items <LoanItem>` instead of having
        to do that one by one.
        """
        for loan_item in self.get_items():
            loan_item.sync_stock()

    def can_close(self):
        """Checks if the loan can be closed. A loan can be closed if it is
        opened and all the items have been returned or sold.
        :returns: True if the loan can be closed, False otherwise.
        """
        if self.status != Loan.STATUS_OPEN:
            return False
        for item in self.get_items():
            if item.sale_quantity + item.return_quantity != item.quantity:
                return False
        return True

    def close(self):
        """Closes the loan. At this point, all the loan items have been
        returned to stock or sold."""
        assert self.can_close()
        self.close_date = datetime.datetime.now()
        self.status = Loan.STATUS_CLOSED
