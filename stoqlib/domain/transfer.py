# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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
##  Author(s):      George Kussumoto    <george@async.com.br>
##
"""  Product transfer management """

import datetime
from kiwi.argcheck import argcheck
from zope.interface import implements

from sqlobject import ForeignKey
from sqlobject.col import DateTimeCol

from stoqlib.database.columns import DecimalCol
from stoqlib.domain.base import Domain
from stoqlib.domain.interfaces import IContainer
from stoqlib.lib.translation import stoqlib_gettext


_ = stoqlib_gettext


class TransferOrderItem(Domain):
    """Transfer order item

    @ivar sellable: The sellable to transfer
    @ivar transfer_order: The order this item belongs to
    @ivar quantity: The quantity to transfer
    """
    sellable = ForeignKey('ASellable')
    transfer_order = ForeignKey('TransferOrder')
    quantity = DecimalCol()


class TransferOrder(Domain):
    """ Transfer Order class

    @ivar open_date: The date the order was created
    @ivar receival_date: The date the order was received
    @ivar source_branch: The branch sending the stock
    @ivar destination_branch: The branch receiving the stock
    @ivar source_responsible: Employee responsible for the transfer at
        source branch
     @ivar destination_responsible: Employee responsible for the transfer at
        destination branch
    """
    implements(IContainer)

    open_date = DateTimeCol(default=datetime.datetime.now)
    receival_date = DateTimeCol(default=datetime.datetime.now)
    source_branch = ForeignKey('PersonAdaptToBranch')
    destination_branch = ForeignKey('PersonAdaptToBranch')
    source_responsible = ForeignKey('PersonAdaptToEmployee')
    destination_responsible = ForeignKey('PersonAdaptToEmployee')

    #
    # IContainer implementation
    #

    def get_items(self):
        return TransferOrderItem.selectBy(transfer_order=self,
                                          connection=self.get_connection())

    def add_item(self, item):
        pass

    @argcheck(TransferOrderItem)
    def remove_item(self, item):
        if item.transfer_order is not self:
            raise ValueError('The item does not belong to this '
                             'transfer order')
        TransferOrderItem.delete(item.id,
                                 connection=self.get_connection())

    #
    # Public API
    #

    def get_destination_branch_name(self):
        """Returns the destination branch name"""
        return self.destination_branch.person.name

    def get_source_responsible_name(self):
        """Returns the name of the employee responsible for the transfer
           at source branch
        """
        return self.source_responsible.person.name
