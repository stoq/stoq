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

from storm.expr import Join, LeftJoin, Sum
from storm.info import ClassAlias
from storm.references import Reference
from zope.interface import implements

from stoqlib.database.properties import (QuantityCol, IntCol, DateTimeCol,
                                         IdentifierCol)
from stoqlib.database.viewable import Viewable
from stoqlib.domain.base import Domain
from stoqlib.domain.product import ProductHistory, StockTransactionHistory
from stoqlib.domain.person import Person, Branch
from stoqlib.domain.interfaces import IContainer
from stoqlib.lib.dateutils import localnow, localtoday
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class TransferOrderItem(Domain):
    """Transfer order item

    """

    __storm_table__ = 'transfer_order_item'

    sellable_id = IntCol()

    #: The |sellable| to transfer
    sellable = Reference(sellable_id, 'Sellable.id')

    transfer_order_id = IntCol()

    #: The |transfer| this item belongs to
    transfer_order = Reference(transfer_order_id, 'TransferOrder.id')

    #: The quantity to transfer
    quantity = QuantityCol()

    #
    # Public API
    #

    def get_total(self):
        """Returns the total cost of a transfer item eg quantity * cost"""
        return self.quantity * self.sellable.cost


class TransferOrder(Domain):
    """ Transfer Order class
    """
    implements(IContainer)

    __storm_table__ = 'transfer_order'

    (STATUS_PENDING,
     STATUS_CLOSED) = range(2)

    statuses = {STATUS_PENDING: _(u'Pending'),
                STATUS_CLOSED: _(u'Closed')}

    status = IntCol(default=STATUS_PENDING)

    #: A numeric identifier for this object. This value should be used instead of
    #: :obj:`Domain.id` when displaying a numerical representation of this object to
    #: the user, in dialogs, lists, reports and such.
    identifier = IdentifierCol()

    #: The date the order was created
    open_date = DateTimeCol(default_factory=localnow)

    #: The date the order was received
    receival_date = DateTimeCol(default_factory=localnow)

    source_branch_id = IntCol()

    #: The |branch| sending the stock
    source_branch = Reference(source_branch_id, 'Branch.id')

    destination_branch_id = IntCol()

    #: The |branch| receiving the stock
    destination_branch = Reference(destination_branch_id, 'Branch.id')

    source_responsible_id = IntCol()

    #: The |employee| responsible for the |transfer| at source |branch|
    source_responsible = Reference(source_responsible_id, 'Employee.id')

    destination_responsible_id = IntCol()

    #: The |employee| responsible for the |transfer| at destination |branch|
    destination_responsible = Reference(destination_responsible_id, 'Employee.id')

    #
    # IContainer implementation
    #

    def get_items(self):
        return self.store.find(TransferOrderItem, transfer_order=self)

    def add_item(self, item):
        item.transfer_order = self

    def remove_item(self, item):
        if item.transfer_order is not self:
            raise ValueError(_('The item does not belong to this '
                               'transfer order'))
        self.store.remove(item)

    #
    # Public API
    #

    def can_close(self):
        if self.status == TransferOrder.STATUS_PENDING:
            return self.get_items().count() > 0
        return False

    def send_item(self, transfer_item):
        """Sends a |product| of this order to it's destination |branch|"""
        assert self.can_close()

        storable = transfer_item.sellable.product_storable
        storable.decrease_stock(transfer_item.quantity, self.source_branch,
                                StockTransactionHistory.TYPE_TRANSFER_TO,
                                transfer_item.id)
        store = self.store
        ProductHistory.add_transfered_item(store, self.source_branch,
                                           transfer_item)

    def receive(self, receival_date=None):
        """Confirms the receiving of the transfer order"""
        assert self.can_close()

        if not receival_date:
            receival_date = localtoday().date()
        self.receival_date = receival_date

        for item in self.get_items():
            storable = item.sellable.product_storable
            from_stock = storable.get_stock_item(self.source_branch)
            storable.increase_stock(item.quantity,
                                    self.destination_branch,
                                    StockTransactionHistory.TYPE_TRANSFER_FROM,
                                    item.id, unit_cost=from_stock.stock_cost)
        self.status = TransferOrder.STATUS_CLOSED

    def get_source_branch_name(self):
        """Returns the source |branch| name"""
        return self.source_branch.person.name

    def get_destination_branch_name(self):
        """Returns the destination |branch| name"""
        return self.destination_branch.person.name

    def get_source_responsible_name(self):
        """Returns the name of the |employee| responsible for the transfer
           at source |branch|
        """
        return self.source_responsible.person.name

    def get_destination_responsible_name(self):
        """Returns the name of the |employee| responsible for the transfer
           at destination |branch|
        """
        return self.destination_responsible.person.name

    def get_total_items_transfer(self):
        """Retuns the |transferitems| quantity
        """
        return sum([item.quantity for item in self.get_items()], 0)


class TransferOrderView(Viewable):
    BranchDest = ClassAlias(Branch, 'branch_dest')
    PersonDest = ClassAlias(Person, 'person_dest')

    transfer_order = TransferOrder

    id = TransferOrder.id
    identifier = TransferOrder.identifier
    open_date = TransferOrder.open_date
    receival_date = TransferOrder.receival_date
    source_branch_id = TransferOrder.source_branch_id
    destination_branch_id = TransferOrder.destination_branch_id
    source_branch_name = Person.name
    destination_branch_name = PersonDest.name

    # Aggregates
    total_itens = Sum(TransferOrderItem.quantity)

    group_by = [TransferOrder, source_branch_name, destination_branch_name]

    tables = [
        TransferOrder,
        Join(TransferOrderItem,
             TransferOrder.id == TransferOrderItem.transfer_order_id),
        # Source
        LeftJoin(Branch, TransferOrder.source_branch_id == Branch.id),
        LeftJoin(Person, Branch.person_id == Person.id),
        # Destination
        LeftJoin(BranchDest, TransferOrder.destination_branch_id == BranchDest.id),
        LeftJoin(PersonDest, BranchDest.person_id == PersonDest.id),
    ]
