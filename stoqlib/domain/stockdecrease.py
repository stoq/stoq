# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2009 Async Open Source <http://www.async.com.br>
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
""" Stock Decrease object and related objects implementation """

import datetime

from kiwi.argcheck import argcheck
from zope.interface import implements

from stoqlib.database.orm import ForeignKey, UnicodeCol, DateTimeCol, IntCol
from stoqlib.database.orm import QuantityCol
from stoqlib.domain.base import Domain
from stoqlib.domain.interfaces import IContainer, IStorable
from stoqlib.domain.product import ProductHistory
from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.lib.translation import stoqlib_gettext


_ = stoqlib_gettext

#
# Base Domain Classes
#


class StockDecreaseItem(Domain):
    """An item in a stock decrease object.

    @param sellable: the kind of item
    @param stock_decrease: the same
    @param quantity: the quantity decreased for this item
    """
    stock_decrease = ForeignKey('StockDecrease', default=None)
    sellable = ForeignKey('Sellable')
    quantity = QuantityCol()

    def _create(self, id, **kw):
        if not 'kw' in kw:
            if not 'sellable' in kw:
                raise TypeError('You must provide a sellable argument')
        Domain._create(self, id, **kw)

    def decrease(self, branch):
        assert branch

        storable = IStorable(self.sellable.product, None)
        if storable:
            storable.decrease_stock(self.quantity, branch)

    #
    # Accessors
    #

    def get_quantity_unit_string(self):
        return "%s %s" % (self.quantity, self.sellable.get_unit_description())

    def get_description(self):
        return self.sellable.get_description()


class StockDecrease(Domain):
    """Stock Decrease object implementation.

    Stock Decrease is when the user need to manually decrease the stock
    quantity, for some reason that is not a sale, transfer or other cases
    already covered in stoqlib.

    @cvar STATUS_INITIAL: Stock Decrease is still being edited
    @cvar STATUS_CONFIRMED: Stock Decrease is confirmed and stock items have
                            been decreased.
    @ivar status: status of the sale
    @ivar responsible: who should be blamed for this
    @ivar branch: branch where the sale was done
    @ivar confirm_date: the date sale was created
    @ivar notes: Some optional additional information related to this sale.
    """

    implements(IContainer)

    (STATUS_INITIAL,
     STATUS_CONFIRMED) = range(2)

    statuses = {STATUS_INITIAL: _(u'Opened'),
                STATUS_CONFIRMED: _(u'Confirmed')}

    status = IntCol(default=STATUS_INITIAL)
    reason = UnicodeCol(default='')
    notes = UnicodeCol(default='')
    confirm_date = DateTimeCol(default=datetime.datetime.now)
    responsible = ForeignKey('PersonAdaptToUser')
    removed_by = ForeignKey('PersonAdaptToEmployee')
    branch = ForeignKey('PersonAdaptToBranch', default=None)
    cfop = ForeignKey('CfopData')

    #
    # Classmethods
    #

    @classmethod
    def get_status_name(cls, status):
        if not status in cls.statuses:
            raise DatabaseInconsistency(_("Invalid status %d") % status)
        return cls.statuses[status]

    @argcheck(StockDecreaseItem)
    def add_item(self, item):
        assert not item.stock_decrease
        item.stock_decrease = self

    def get_items(self):
        return StockDecreaseItem.selectBy(stock_decrease=self,
                                          connection=self.get_connection())

    @argcheck(StockDecreaseItem)
    def remove_item(self, item):
        StockDecreaseItem.delete(item.id, connection=self.get_connection())

    # Status

    def can_confirm(self):
        """Only ordered sales can be confirmed
        @returns: True if the sale can be confirmed, otherwise False
        """
        return self.status == StockDecrease.STATUS_INITIAL

    def confirm(self):
        """Confirms the sale

        """
        assert self.can_confirm()
        assert self.branch

        conn = self.get_connection()
        branch = self.branch
        for item in self.get_items():
            if item.sellable.product:
                ProductHistory.add_decreased_item(conn, branch, item)
            item.decrease(branch)

        self.status = StockDecrease.STATUS_CONFIRMED

    #
    # Accessors
    #

    def get_order_number_str(self):
        return u'%05d' % self.id

    def get_branch_name(self):
        return self.branch.get_description()

    def get_responsible_name(self):
        return self.responsible.get_description()

    def get_removed_by_name(self):
        if not self.removed_by:
            return u''

        return self.removed_by.get_description()

    def get_total_items_removed(self):
        return sum([item.quantity for item in self.get_items()], 0)

    def get_cfop_description(self):
        return self.cfop.get_description()

    # Other methods

    def add_sellable(self, sellable, quantity=1):
        """Adds a new sellable item to a stock decrease

        @param sellable: the sellable
        @param quantity: quantity to add, defaults to 1
        """
        return StockDecreaseItem(connection=self.get_connection(),
                                 quantity=quantity,
                                 stock_decrease=self,
                                 sellable=sellable,
                                 )

    @property
    def order_number(self):
        return self.id
