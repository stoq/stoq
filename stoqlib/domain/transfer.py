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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
"""  Product transfer management """

import datetime
from kiwi.argcheck import argcheck
from zope.interface import implements

from stoqlib.database.orm import QuantityCol, const, INNERJOINOn, LEFTJOINOn
from stoqlib.database.orm import ForeignKey, IntCol, Viewable, Alias
from stoqlib.database.orm import DateTimeCol
from stoqlib.domain.base import Domain
from stoqlib.domain.product import ProductHistory
from stoqlib.domain.person import Person, Branch
from stoqlib.domain.interfaces import IContainer
from stoqlib.lib.translation import stoqlib_gettext


_ = stoqlib_gettext


class TransferOrderItem(Domain):
    """Transfer order item

    :attribute sellable: The sellable to transfer
    :attribute transfer_order: The order this item belongs to
    :attribute quantity: The quantity to transfer
    """
    sellable = ForeignKey('Sellable')
    transfer_order = ForeignKey('TransferOrder')
    quantity = QuantityCol()

    #
    # Public API
    #

    def get_total(self):
        """Returns the total cost of a transfer item eg quantity * cost"""
        return self.quantity * self.sellable.cost


class TransferOrder(Domain):
    """ Transfer Order class

    :attribute open_date: The date the order was created
    :attribute receival_date: The date the order was received
    :attribute source_branch: The branch sending the stock
    :attribute destination_branch: The branch receiving the stock
    :attribute source_responsible: Employee responsible for the transfer at
        source branch
     :attribute destination_responsible: Employee responsible for the transfer at
        destination branch
    """
    implements(IContainer)

    (STATUS_PENDING,
     STATUS_CLOSED) = range(2)

    statuses = {STATUS_PENDING: _(u'Pending'),
                STATUS_CLOSED: _(u'Closed')}

    status = IntCol(default=STATUS_PENDING)
    open_date = DateTimeCol(default=datetime.datetime.now)
    receival_date = DateTimeCol(default=datetime.datetime.now)
    source_branch = ForeignKey('Branch')
    destination_branch = ForeignKey('Branch')
    source_responsible = ForeignKey('Employee')
    destination_responsible = ForeignKey('Employee')

    #
    # IContainer implementation
    #

    def get_items(self):
        return TransferOrderItem.selectBy(transfer_order=self,
                                          connection=self.get_connection())

    def add_item(self, item):
        item.transfer_order = self

    @argcheck(TransferOrderItem)
    def remove_item(self, item):
        if item.transfer_order is not self:
            raise ValueError(_('The item does not belong to this '
                               'transfer order'))
        TransferOrderItem.delete(item.id,
                                 connection=self.get_connection())

    #
    # Public API
    #

    def can_close(self):
        if self.status == TransferOrder.STATUS_PENDING:
            return self.get_items().count() > 0
        return False

    @argcheck(TransferOrderItem)
    def send_item(self, transfer_item):
        """Sends a product of this order to it's destination branch"""
        assert self.can_close()

        storable = transfer_item.sellable.product_storable
        storable.decrease_stock(transfer_item.quantity, self.source_branch)
        conn = self.get_connection()
        ProductHistory.add_transfered_item(conn, self.source_branch,
                                           transfer_item)

    def receive(self, receival_date=None):
        """Confirms the receiving of the transfer order"""
        assert self.can_close()

        if not receival_date:
            receival_date = datetime.date.today()
        self.receival_date = receival_date

        for item in self.get_items():
            storable = item.sellable.product_storable
            from_stock = storable.get_stock_item(self.source_branch)
            storable.increase_stock(item.quantity,
                                    self.destination_branch,
                                    from_stock.stock_cost)
        self.status = TransferOrder.STATUS_CLOSED

    def get_source_branch_name(self):
        """Returns the source branch name"""
        return self.source_branch.person.name

    def get_destination_branch_name(self):
        """Returns the destination branch name"""
        return self.destination_branch.person.name

    def get_source_responsible_name(self):
        """Returns the name of the employee responsible for the transfer
           at source branch
        """
        return self.source_responsible.person.name

    def get_destination_responsible_name(self):
        """Returns the name of the employee responsible for the transfer
           at destination branch
        """
        return self.destination_responsible.person.name

    def get_total_items_transfer(self):
        """Retuns the transfer items quantity or zero if there is no
           item in transfer
        """
        return sum([item.quantity for item in self.get_items()], 0)


class TransferOrderView(Viewable):
    BranchDest = Alias(Branch, 'branch_dest')
    PersonDest = Alias(Person, 'person_dest')

    columns = dict(
        id=TransferOrder.q.id,
        open_date=TransferOrder.q.open_date,
        receival_date=TransferOrder.q.receival_date,
        source_branch_id=TransferOrder.q.source_branchID,
        destination_branch_id=TransferOrder.q.destination_branchID,
        source_branch_name=Person.q.name,
        destination_branch_name=PersonDest.q.name,
        total_itens=const.SUM(TransferOrderItem.q.quantity),
    )

    joins = [
        INNERJOINOn(None, TransferOrderItem,
                    TransferOrder.q.id == TransferOrderItem.q.transfer_orderID),
        # Source
        LEFTJOINOn(None, Branch,
                   TransferOrder.q.source_branchID == Branch.q.id),
        LEFTJOINOn(None, Person,
                   Branch.q.personID == Person.q.id),
        # Destination
        LEFTJOINOn(None, BranchDest,
                   TransferOrder.q.destination_branchID == BranchDest.q.id),
        LEFTJOINOn(None, PersonDest,
                   BranchDest.q.personID == PersonDest.q.id),
    ]

    @property
    def transfer_order(self):
        return TransferOrder.get(self.id)
