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
""" Loan object and related objects implementation """

import datetime
from decimal import Decimal

from kiwi.argcheck import argcheck
from kiwi.datatypes import currency
from zope.interface import implements

from stoqlib.database.orm import ForeignKey, UnicodeCol, DateTimeCol, IntCol
from stoqlib.database.orm import PriceCol, const, QuantityCol
from stoqlib.domain.base import Domain
from stoqlib.domain.interfaces import IContainer, IStorable
from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.lib.defaults import DECIMAL_PRECISION
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class LoanItem(Domain):
    """An item in a loan.

    @param sellable: the kind of item
    @param loan: the same
    @param quantity: the quantity of the of sold item in this loan
    @param price: the price of each individual item
    """
    quantity = QuantityCol()
    sale_quantity = QuantityCol(default=Decimal(0))
    return_quantity = QuantityCol(default=Decimal(0))
    price = PriceCol()
    sellable = ForeignKey('Sellable')
    loan = ForeignKey('Loan')

    def _create(self, id, **kw):
        if not 'kw' in kw:
            if not 'sellable' in kw:
                raise TypeError('You must provide a sellable argument')
        Domain._create(self, id, **kw)

    def do_loan(self, branch):
        """Performs the loan of the product. The quantity requested of the
        product will be out of stock of the given branch.
        """
        storable = IStorable(self.sellable.product, None)
        if storable is not None:
            storable.decrease_stock(self.quantity, branch)

    def return_product(self, quantity):
        """Returns a certain quantity of the loan product to stock. The
        quantity returned should be lesser or equal than the total quantity.
        """
        assert quantity <= self.quantity
        storable = IStorable(self.sellable.product, None)
        if storable is not None:
            branch = self.loan.branch
            storable.increase_stock(quantity, branch)

    #
    # Accessors
    #

    def get_quantity_unit_string(self):
        return "%s %s" % (self.quantity,
                          self.sellable.get_unit_description())

    def get_total(self):
        return currency(self.price * self.quantity)


class Loan(Domain):
    """Loan object implementation.

    @cvar STATUS_OPEN: The loan is opened, products or other sellable items
      might have been added and might not be in stock.
    @cvar STATUS_CLOSED: All the products or other sellable items have been
    returned and are available in stock.
    @ivar status: status of the loan
    @ivar client: who we loan
    @ivar responsinble: who is responsible for this loan
    @ivar branch: branch where the loan was done
    @ivar open_date: the date loan was created
    @ivar close_date: the date loan was closed
    @ivar expire_return_date: the expected date loan will return
    @ivar notes: Some optional additional information related to this loan.
    """

    implements(IContainer)

    (STATUS_OPEN,
     STATUS_CLOSED) = range(2)

    statuses = {STATUS_OPEN: _(u'Opened'),
                STATUS_CLOSED: _(u'Closed')}

    status = IntCol(default=STATUS_OPEN)
    notes = UnicodeCol(default='')
    open_date = DateTimeCol(default=datetime.datetime.now)
    close_date = DateTimeCol(default=None)
    expire_date = DateTimeCol(default=None)
    removed_by = UnicodeCol(default='')
    branch = ForeignKey('PersonAdaptToBranch', default=None)
    responsible = ForeignKey('PersonAdaptToUser')
    client = ForeignKey('PersonAdaptToClient', default=None)

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

    def add_sellable(self, sellable, quantity=1, price=None):
        """Adds a new sellable item to a loan
        @param sellable: the sellable
        @param quantity: quantity to add, defaults to 1
        @param price: optional, the price, it not set the price
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
        Fetches the total value  paid by the client.
        It can be calculated as::

            Sale total = Sum(product and service prices) + surcharge +
                             interest - discount

        @returns: the total value
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

    def can_close(self):
        """Checks if the loan can be closed. A loan can be closed if it is
        opened and all the items have been returned or sold.
        @returns: True if the loan can be closed, False otherwise.
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
        self.close_date = datetime.date.today()
        self.status = Loan.STATUS_CLOSED
