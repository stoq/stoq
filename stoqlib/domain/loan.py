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

from decimal import Decimal

from kiwi.currency import currency
from storm.references import Reference, ReferenceSet
from zope.interface import implements

from stoqlib.database.expr import Round
from stoqlib.database.properties import (UnicodeCol, DateTimeCol, IntCol,
                                         PriceCol, QuantityCol, IdentifierCol)
from stoqlib.domain.base import Domain
from stoqlib.domain.interfaces import IContainer
from stoqlib.domain.product import StockTransactionHistory
from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.lib.dateutils import localnow
from stoqlib.lib.defaults import DECIMAL_PRECISION
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class LoanItem(Domain):
    """An item in a :class:`loan <Loan>`

    Note that when changing :obj:`~.quantity`, :obj:`~.return_quantity`
    or :obj:`~.sale_quantity` you will need to call :meth:`.sync_stock`
    to synchronize the stock (increase or decrease it).

    Also note that objects of this type should never be created manually, only
    by calling :meth:`Loan.add_sellable`

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/loan_item.html>`__
    """
    __storm_table__ = 'loan_item'

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

    sellable_id = IntCol(allow_none=False)

    #: :class:`sellable <stoqlib.domain.sellable.Sellable>` that is loaned
    #: cannot be *None*
    sellable = Reference(sellable_id, 'Sellable.id')

    batch_id = IntCol()

    #: If the sellable is a storable, the |batch| that it was returned in
    batch = Reference(batch_id, 'StorableBatch.id')

    loan_id = IntCol()

    #: :class:`loan <Loan>` this item belongs to
    loan = Reference(loan_id, 'Loan.id')

    def __init__(self, *args, **kwargs):
        # stores the total quantity that was loaned before synching stock
        self._original_quantity = 0
        # stores the loaned quantity that was returned before synching stock
        self._original_return_quantity = self.return_quantity

        super(LoanItem, self).__init__(*args, **kwargs)

    def __storm_loaded__(self):
        super(LoanItem, self).__storm_loaded__()
        self._original_quantity = self.quantity
        self._original_return_quantity = self.return_quantity

    @property
    def branch(self):
        return self.loan.branch

    @property
    def storable(self):
        return self.sellable.product_storable

    def sync_stock(self):
        """Synchronizes the stock, increasing/decreasing it accordingly.
        Using the stored values when this object is created/loaded, compute how
        much we should increase or decrease the stock quantity.

        When setting :obj:`~.quantity`, :obj:`~.return_quantity`
        or :obj:`~.sale_quantity` be sure to call this to properly
        synchronize the stock (increase or decrease it). That counts
        for object creation too.
        """
        loaned = self._original_quantity - self.quantity
        returned = self.return_quantity - self._original_return_quantity
        diff_quantity = loaned + returned

        if diff_quantity > 0:
            self.storable.increase_stock(diff_quantity, self.branch,
                                         StockTransactionHistory.TYPE_RETURNED_LOAN,
                                         self.id)
        elif diff_quantity < 0:
            diff_quantity = - diff_quantity
            self.storable.decrease_stock(diff_quantity, self.branch,
                                         StockTransactionHistory.TYPE_LOANED,
                                         self.id)

        # Reset the values used to calculate the stock quantity, just like
        # when the object as loaded from the database again.
        self._original_quantity = self.quantity
        self._original_return_quantity = self.return_quantity

    def get_remaining_quantity(self):
        """The remaining quantity that wasn't returned/sold yet

        This is the same as
        :obj:`.quantity` - :obj:`.sale_quantity` - :obj:`.return_quantity`
        """
        return self.quantity - self.sale_quantity - self.return_quantity

    def get_quantity_unit_string(self):
        return u"%s %s" % (self.quantity,
                           self.sellable.get_unit_description())

    def get_total(self):
        return currency(self.price * self.quantity)


class Loan(Domain):
    """
    A loan is a collection of |sellable| that is being loaned
    to a |client|, the items are expected to be either be
    returned to stock or sold via a |sale|.

    A loan that can hold a set of :class:`loan items <LoanItem>`

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/loan.html>`__
    `manual <http://doc.stoq.com.br/manual/loan.html>`__
    """

    implements(IContainer)

    __storm_table__ = 'loan'

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

    #: A numeric identifier for this object. This value should be used instead of
    #: :obj:`Domain.id` when displaying a numerical representation of this object to
    #: the user, in dialogs, lists, reports and such.
    identifier = IdentifierCol()

    #: status of the loan
    status = IntCol(default=STATUS_OPEN)

    #: notes related to this loan.
    notes = UnicodeCol(default=u'')

    #: date loan was opened
    open_date = DateTimeCol(default_factory=localnow)

    #: date loan was closed
    close_date = DateTimeCol(default=None)

    #: loan expires on this date, we expect the items to
    #: to be returned by this date
    expire_date = DateTimeCol(default=None)

    removed_by = UnicodeCol(default=u'')

    #: branch where the loan was done
    branch_id = IntCol()
    branch = Reference(branch_id, 'Branch.id')

    #: :class:`user <stoqlib.domain.person.LoginUser>` of the system
    #: that made the loan
    # FIXME: Should probably be a SalesPerson, we can find the
    #        LoginUser via te.user_id
    responsible_id = IntCol()
    responsible = Reference(responsible_id, 'LoginUser.id')

    #: client that loaned the items
    client_id = IntCol(default=None)
    client = Reference(client_id, 'Client.id')

    #: a list of all items loaned in this loan
    loaned_items = ReferenceSet('id', 'LoanItem.loan_id')

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

    def add_item(self, loan_item):
        assert not loan_item.loan
        loan_item.loan = self

    def get_items(self):
        return self.store.find(LoanItem, loan=self)

    def remove_item(self, loan_item):
        LoanItem.delete(loan_item.id, store=self.store)

    #
    # Public API
    #

    def add_sellable(self, sellable, quantity=1, price=None, batch=None):
        """Adds a new sellable item to a loan

        :param sellable: the |sellable|
        :param quantity: quantity to add, defaults to 1
        :param price: optional, the price, it not set the price
          from the sellable will be used
        :param batch: the |batch| this sellable comes from if the sellable is a
          storable. Should be ``None`` if it is not a storable or if the storable
          does not have batches.
        """
        self.validate_batch(batch, sellable=sellable)
        price = price or sellable.price
        return LoanItem(store=self.store,
                        quantity=quantity,
                        loan=self,
                        sellable=sellable,
                        batch=batch,
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
            Round(LoanItem.price * LoanItem.quantity,
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
        self.close_date = localnow()
        self.status = Loan.STATUS_CLOSED
