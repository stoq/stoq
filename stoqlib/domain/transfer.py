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
                                         IdentifierCol, IdCol)
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

    sellable_id = IdCol()

    # FIXME: This should be a product, since it does not make sense to transfer
    # serviçes
    #: The |sellable| to transfer
    sellable = Reference(sellable_id, 'Sellable.id')

    batch_id = IdCol()

    #: If the sellable is a storable, the |batch| that was transfered
    batch = Reference(batch_id, 'StorableBatch.id')

    transfer_order_id = IdCol()

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

    def send(self):
        """Sends this item to it's destination |branch|"""
        assert self.transfer_order.can_close()

        storable = self.sellable.product_storable
        storable.decrease_stock(self.quantity, self.transfer_order.source_branch,
                                StockTransactionHistory.TYPE_TRANSFER_TO,
                                self.id, batch=self.batch)
        ProductHistory.add_transfered_item(self.store, self.transfer_order.source_branch, self)

    def receive(self):
        """Receives this item, increasing the quantity in the stock
        """
        storable = self.sellable.product_storable
        from_stock = storable.get_stock_item(self.transfer_order.source_branch,
                                             self.batch)
        storable.increase_stock(self.quantity,
                                self.transfer_order.destination_branch,
                                StockTransactionHistory.TYPE_TRANSFER_FROM,
                                self.id, unit_cost=from_stock.stock_cost,
                                batch=self.batch)


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

    source_branch_id = IdCol()

    #: The |branch| sending the stock
    source_branch = Reference(source_branch_id, 'Branch.id')

    destination_branch_id = IdCol()

    #: The |branch| receiving the stock
    destination_branch = Reference(destination_branch_id, 'Branch.id')

    source_responsible_id = IdCol()

    #: The |employee| responsible for the |transfer| at source |branch|
    source_responsible = Reference(source_responsible_id, 'Employee.id')

    destination_responsible_id = IdCol()

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

    def add_sellable(self, sellable, batch, quantity=1):
        """Add the given |sellable| to this |transfer|.

        :param sellable: The |sellable| we are transfering
        :param batch: What |batch| of the storable (represented by sellable) we
          are transfering.
        :param quantity: The quantity of this product that is being transfered.
        """
        self.validate_batch(batch, sellable=sellable)
        return TransferOrderItem(store=self.store,
                                 transfer_order=self,
                                 sellable=sellable,
                                 batch=batch,
                                 quantity=quantity)

    def can_close(self):
        if self.status == TransferOrder.STATUS_PENDING:
            return self.get_items().count() > 0
        return False

    def receive(self, receival_date=None):
        """Confirms the receiving of the transfer order"""
        assert self.can_close()
        for item in self.get_items():
            item.receive()

        self.receival_date = receival_date or localtoday().date()
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
