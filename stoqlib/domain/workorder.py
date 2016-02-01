# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013-2015 Async Open Source <http://www.async.com.br>
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

"""Work order implementation and utils"""

# pylint: enable=E1101

import logging

from kiwi.currency import currency
from storm.expr import (Count, Join, LeftJoin, Alias, Select, Sum, Coalesce,
                        In, And, Or, Eq, Not, Cast)
from storm.info import ClassAlias
from storm.references import Reference, ReferenceSet
from zope.interface import implementer

from stoqlib.database.expr import Field, NullIf, Concat
from stoqlib.database.properties import (IntCol, DateTimeCol, UnicodeCol,
                                         PriceCol, DecimalCol, QuantityCol,
                                         IdentifierCol, IdCol, BoolCol, EnumCol)
from stoqlib.database.runtime import get_current_branch, get_current_user
from stoqlib.database.viewable import Viewable
from stoqlib.exceptions import InvalidStatus, NeedReason
from stoqlib.domain.base import Domain
from stoqlib.domain.events import (SaleStatusChangedEvent,
                                   SaleItemBeforeDecreaseStockEvent,
                                   SaleItemBeforeIncreaseStockEvent,
                                   SaleItemAfterSetBatchesEvent)
from stoqlib.domain.interfaces import IDescribable, IContainer
from stoqlib.domain.person import (Branch, Client, Person, SalesPerson,
                                   Company, LoginUser, Employee)
from stoqlib.domain.product import Product, StockTransactionHistory
from stoqlib.domain.sale import Sale
from stoqlib.domain.sellable import Sellable
from stoqlib.lib.dateutils import localnow, localtoday
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

log = logging.getLogger(__name__)


def _validate_package_branch(obj, attr, value):
    other_dict = {
        'destination_branch_id': obj.source_branch_id,
        'source_branch_id': obj.destination_branch_id}

    if other_dict[attr] == value:
        raise ValueError(
            _("The source branch and destination branch can't be equal"))

    return value


class WorkOrderPackageItem(Domain):
    """A |workorderpackage| item

    This is a representation of a |workorder| inside a
    |workorderpackage|. This is used instead of the work
    order directly so we can keep a history of sent and
    received packages.

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/work_order_item.html>`__
    """

    __storm_table__ = 'work_order_package_item'

    package_id = IdCol(allow_none=False)
    #: the |workorderpackage| this item is transported in
    package = Reference(package_id, 'WorkOrderPackage.id')

    order_id = IdCol(allow_none=False)
    #: the |workorder| this item represents
    order = Reference(order_id, 'WorkOrder.id')

    #
    #  Public API
    #

    def send(self):
        """Send the item to the :attr:`WorkOrderPackage.destination_branch`

        This will mark the package as sent. Note that it's only possible
        to call this on the same branch as :attr:`.source_branch`.

        When calling this, the work orders' :attr:`WorkOrder.current_branch`
        will be ``None``, since they are on a package and not on any branch.
        """
        if self.package.destination_branch != self.order.branch:
            old_execution_branch = self.order.execution_branch
            self.order.execution_branch = self.package.destination_branch
            WorkOrderHistory.add_entry(
                self.store, self.order, _(u"Execution branch"),
                old_value=(old_execution_branch and
                           old_execution_branch.get_description()),
                new_value=self.package.destination_branch.get_description())

    def receive(self):
        """Receive this item on the :attr:`WorkOrderPackage.destination_branch`

        This will mark the package as received in the branch
        to receive it there. Note that it's only possible to call this
        on the same branch as :attr:`.destination_branch`.

        When calling this, the work orders' :attr:`WorkOrder.current_branch`
        will be set to :attr:`WorkOrderPackage.destination_branch`, since
        receiving means they got to their destination.
        """
        #FIXME: For unknown reason some of W.O is not setted as None, so we
        #are disabling this check for now
        #assert self.order.current_branch is None
        if self.order.current_branch is not None:  # pragma nocoverage
            log.warning('Work order with wrong current branch %r' % self.order)

        # The order is in destination branch now
        self.order.current_branch = self.package.destination_branch
        WorkOrderHistory.add_entry(
            self.store, self.order, _(u"Current branch"),
            old_value=_(u"Package %s") % self.package.identifier,
            new_value=self.package.destination_branch.get_description())


class WorkOrderPackage(Domain):
    """A package of |workorders|

    This is a package (called 'malote' on Brazil) that will be used to
    send workorder(s) to another branch for the task execution.

    .. graphviz::

       digraph work_order_package_status {
         STATUS_OPENED -> STATUS_SENT;
         STATUS_SENT -> STATUS_RECEIVED;
       }

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/work_order_package.html>`__
    """

    __storm_table__ = 'work_order_package'

    #: package is opened, waiting to be sent
    STATUS_OPENED = u'opened'

    #: package was sent to the :attr:`.destination_branch`
    STATUS_SENT = u'sent'

    #: package was received by the :attr:`.destination_branch`
    STATUS_RECEIVED = u'received'

    statuses = {
        STATUS_OPENED: _(u'Opened'),
        STATUS_SENT: _(u'Sent'),
        STATUS_RECEIVED: _(u'Received')}

    status = EnumCol(allow_none=False, default=STATUS_OPENED)

    # FIXME: Change identifier to another name, to avoid
    # confusions with IdentifierCol used elsewhere
    #: the packages's identifier
    identifier = UnicodeCol()

    #: when the package was sent from the :attr:`.source_branch`
    send_date = DateTimeCol()

    #: when the package was received by the :attr:`.destination_branch`
    receive_date = DateTimeCol()

    send_responsible_id = IdCol(default=None)
    #: the |loginuser| responsible for sending the package
    send_responsible = Reference(send_responsible_id, 'LoginUser.id')

    receive_responsible_id = IdCol(default=None)
    #: the |loginuser| responsible for receiving the package
    receive_responsible = Reference(receive_responsible_id, 'LoginUser.id')

    destination_branch_id = IdCol(validator=_validate_package_branch)
    #: the destination branch, that is, the branch where
    #: the package is going to be sent to
    destination_branch = Reference(destination_branch_id, 'Branch.id')

    source_branch_id = IdCol(allow_none=False,
                             validator=_validate_package_branch)

    #: the source branch, that is, the branch where
    #: the package is leaving
    source_branch = Reference(source_branch_id, 'Branch.id')

    #: the |workorderpackageitems| inside this package
    package_items = ReferenceSet('id', 'WorkOrderPackageItem.package_id')

    @property
    def quantity(self):
        """The quantity of |workorderpackageitems| inside this package"""
        return self.package_items.count()

    #
    #  Public API
    #

    def add_order(self, workorder, notes=None):
        """Add a |workorder| on this package

        Note that this will set the :attr:`WorkOrder.current_branch`
        to ``None`` (since it's now on the package).

        :param notes: some notes that will be used when adding
            an entry on :class:`WorkOrderHistory`
        :returns: the created |workorderpackageitem|
        """
        if not self.package_items.find(order=workorder).is_empty():
            raise ValueError(
                _("The order %s is already on the package %s") % (
                    workorder, self))
        if workorder.current_branch != self.source_branch:
            raise ValueError(
                _("The order %s is not in the source branch") % (
                    workorder, ))

        # The order is going to leave the current_branch
        workorder.current_branch = None
        WorkOrderHistory.add_entry(
            self.store, workorder, _(u"Current branch"),
            old_value=self.source_branch.get_description(),
            new_value=_(u"Package %s") % self.identifier,
            notes=notes)

        return WorkOrderPackageItem(store=self.store,
                                    order=workorder, package=self)

    def can_send(self):
        """If we can send this package to the :attr:`.destination_branch`"""
        return self.status == self.STATUS_OPENED

    def can_receive(self):
        """If we can receive this package in the :attr:`.destination_branch`"""
        return self.status == self.STATUS_SENT

    def send(self):
        """Send the package to the :attr:`.destination_branch`

        This will mark the package as sent. Note that it's only possible
        to call this on the same branch as :attr:`.source_branch`.

        Each :obj:`.package_items` will have it's
        :meth:`WorkOrderPackageItem.send` method called
        """
        assert self.can_send()

        if self.source_branch != get_current_branch(self.store):
            fmt = _("This package's source branch is %s and you are in %s. "
                    "It's not possible to send a package outside the "
                    "source branch")
            raise ValueError(fmt % (self.source_branch,
                                    get_current_branch(self.store)))

        package_items = list(self.package_items)
        if not len(package_items):
            raise ValueError(_("There're no orders to send"))

        for package_item in package_items:
            package_item.send()

        self.send_date = localnow()
        self.status = self.STATUS_SENT

    def receive(self):
        """Receive the package on the :attr:`.destination_branch`

        This will mark the package as received in the branch
        to receive it there. Note that it's only possible to call this
        on the same branch as :attr:`.destination_branch`.

        Each :obj:`.package_items` will have it's
        :meth:`WorkOrderPackageItem.receive` method called
        """
        assert self.can_receive()

        if self.destination_branch != get_current_branch(self.store):
            fmt = _("This package's destination branch is %s and you are in %s. "
                    "It's not possible to receive a package outside the "
                    "destination branch")
            raise ValueError(fmt % (self.destination_branch,
                                    get_current_branch(self.store)))

        for package_item in self.package_items:
            package_item.receive()

        self.receive_date = localnow()
        self.status = self.STATUS_RECEIVED


@implementer(IDescribable)
class WorkOrderCategory(Domain):
    """A |workorder|'s category

    Used to categorize a |workorder|. It can be differentiate
    mainly by the :attr:`.name`, but one can use :obj:`color`
    in a gui to make the differentiation better.

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/work_order_category.html>`__
    """

    __storm_table__ = 'work_order_category'

    #: category's name
    name = UnicodeCol()

    #: category's color (e.g. #ff0000 for red)
    color = UnicodeCol()

    #
    #  IDescribable
    #

    def get_description(self):
        return self.name


class WorkOrderItem(Domain):
    """A |workorder| item

    This is an item in a |workorder|. That is, a |product| or a |service|
    (here referenced by their respective |sellable|) used on the work
    and that will be after used to compose the |saleitem| of the |sale|.

    Note that objects of this type should not be created manually, only by
    calling :meth:`WorkOrder.add_sellable`

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/work_order_item.html>`__
    """

    __storm_table__ = 'work_order_item'

    #: |sellable|'s quantity used on the |workorder|
    quantity = QuantityCol(default=0)

    #: the quantity of |sellable| consumed (i.e. decreased from the stock).
    #: This needs to be equal to :obj:`.quantity` for the work order
    #: to be finished
    quantity_decreased = QuantityCol(default=0)

    #: price of the |sellable|, this is how much the |client| is going
    #: to be charged for the sellable. This includes discounts and markup.
    price = PriceCol()

    sellable_id = IdCol()
    #: the |sellable| of this item, either a |service| or a |product|
    sellable = Reference(sellable_id, 'Sellable.id')

    batch_id = IdCol()
    #: If the sellable is a storable, the |batch| that it was removed from
    batch = Reference(batch_id, 'StorableBatch.id')

    order_id = IdCol()
    #: |workorder| this item belongs
    order = Reference(order_id, 'WorkOrder.id')

    sale_item_id = IdCol()
    #: the corresponding |saleitem| for this item
    sale_item = Reference(sale_item_id, 'SaleItem.id')

    @property
    def total(self):
        """The total value for this item

        Note that this is the same as :obj:`.quantity` * :obj:`.price`
        """
        return currency(self.price * self.quantity)

    #
    #  Public API
    #

    def reserve(self, quantity):
        """Reserve some quantity of this item

        Reserving some quantity of items means decreasing them from
        the stock. All :obj:`.quantity` needs to be reserved for a
        |workorder| to be finished. The already reserved quantity
        will be stored at :obj:`.quantity_decreased`

        :param quantity: the quantity to consume
        :raises: :exc:`ValueError` if the quantity to reserve is
            greater than the unreserved quantity
            (:obj:`.quantity` - :obj:`.quantity_decreased`
        """
        if quantity > self.quantity - self.quantity_decreased:
            raise ValueError(
                "Trying to reserve more than unreserved quantity")

        storable = self.sellable.product_storable
        if storable:
            storable.decrease_stock(
                quantity, self.order.branch,
                StockTransactionHistory.TYPE_WORK_ORDER_USED, self.id,
                batch=self.batch)

        self.quantity_decreased += quantity
        if self.sale_item:
            # Keep the sale_item in sync, so the stock is not increased twice
            self.sale_item.quantity_decreased += quantity

    def return_to_stock(self, quantity):
        """Return some quantity of this item to stock

        Returning some quantity of items to the stock means increasing
        the stock back.

        :param quantity: the quantity to return to the stock
        :raises: :exc:`ValueError` if the quantity to return to the stock
            greater than the :obj:`.quantity_decreased`
        """
        if quantity > self.quantity_decreased:
            raise ValueError(
                "Trying to return more quantity than reserved")

        # TODO: Implement a way to say that this quantity was lost
        # (probably by receiving an extra kwarg here). Then we would still
        # remove the quantity from quantity_decreased, but not reincrease stock
        storable = self.sellable.product_storable
        if storable:
            storable.increase_stock(
                quantity, self.order.branch,
                StockTransactionHistory.TYPE_WORK_ORDER_RETURN_TO_STOCK, self.id,
                batch=self.batch)

        self.quantity_decreased -= quantity
        if self.sale_item:
            # Keep the sale_item in sync, so the stock is not decreased twice
            self.sale_item.quantity_decreased -= quantity

    #
    #  Classmethods
    #

    @classmethod
    def get_from_sale_item(cls, store, sale_item):
        """Get the |workorderitem| given one |saleitem|

        :param store: a store
        :param sale_item: a |saleitem|
        :returns: The |workorderitem| related to the |saleitem|
        :rtype: |workorderitem|
        """
        return store.find(cls, cls.sale_item_id == sale_item.id).one()

    #
    #  Events
    #

    @SaleItemBeforeIncreaseStockEvent.connect
    @classmethod
    def _on_sale_item_before_increase_stock(cls, sale_item):
        self = cls.get_from_sale_item(sale_item.store, sale_item)
        if self is None:
            return

        assert sale_item.quantity == self.quantity
        # When a sale item has an corresponding work order item, they need to
        # be in sync all the time, but the stock management
        # (increasing/decreasing) must be done only once.
        sale_item.quantity_decreased = max(sale_item.quantity_decreased,
                                           self.quantity_decreased)
        # This is why when a sale item is canceled (ie, the stock is returned),
        # we must also inform that the quantity decreased for the work order
        # item was also returned.
        self.quantity_decreased = 0

    @SaleItemBeforeDecreaseStockEvent.connect
    @classmethod
    def _on_sale_item_before_decrease_stock(cls, sale_item):
        self = cls.get_from_sale_item(sale_item.store, sale_item)
        if self is None:
            return

        assert sale_item.quantity == self.quantity
        # When a sale item has an corresponding work order item, they need to
        # be in sync all the time, but the stock management
        # (increasing/decreasing) must be done only once.
        sale_item.quantity_decreased = max(sale_item.quantity_decreased,
                                           self.quantity_decreased)
        # sale_item will decrease everything that was missing, so there's
        # nothing more to decrease here, that's why we are setting
        # quantity_decreased = quantity
        self.quantity_decreased = self.quantity

    @SaleItemAfterSetBatchesEvent.connect
    @classmethod
    def _on_sale_item_after_set_batches(cls, sale_item, new_sale_items):
        self = cls.get_from_sale_item(sale_item.store, sale_item)
        if self is None:
            return

        self.quantity = sale_item.quantity
        self.batch = sale_item.batch

        for sale_item in new_sale_items:
            cls(store=sale_item.store,
                quantity=sale_item.quantity,
                price=sale_item.price,
                batch=sale_item.batch,
                order=self.order,
                sellable=self.sellable,
                sale_item=sale_item)


@implementer(IContainer)
class WorkOrder(Domain):
    """Represents a work order

    Normally, this is a maintenance task, like:
        * The |client| reports a defect on an equipment.
        * The responsible for doing the quote analyzes the equipment
          and detects the real defect.
        * The |client| then approves the quote and the work begins.
        * After it's finished, a |sale| is created for it, the
          |client| pays and gets it's equipment back.

    .. graphviz::

       digraph work_order_status {
         STATUS_OPENED -> STATUS_WORK_WAITING;
         STATUS_OPENED -> STATUS_CANCELLED;
         STATUS_WORK_WAITING -> STATUS_WORK_IN_PROGRESS;
         STATUS_WORK_WAITING -> STATUS_CANCELLED;
         STATUS_WORK_IN_PROGRESS -> STATUS_WORK_FINISHED;
         STATUS_WORK_IN_PROGRESS -> STATUS_WORK_WAITING;
         STATUS_WORK_IN_PROGRESS -> STATUS_CANCELLED;
         STATUS_WORK_FINISHED -> STATUS_DELIVERED;
         STATUS_WORK_FINISHED -> STATUS_WORK_IN_PROGRESS;
       }

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/work_order.html>`__
    """

    __storm_table__ = 'work_order'

    #: a request for an order has been created, the order has not yet
    #: been approved the |client|
    STATUS_OPENED = u'opened'

    #: for some reason it was cancelled
    STATUS_CANCELLED = u'cancelled'

    #: this is the initial status after the order gets approved by the
    #: |client| and also a helper state for :attr:`.STATUS_WORK_IN_PROGRESS`
    #: since when there, the order can come back here to be explicit that
    #: it's waiting (for material, for labor, etc) to continue the work
    STATUS_WORK_WAITING = u'waiting'

    #: work is currently in progress. Note that if at any time we need
    #: to wait for more material to continue the work, the status can
    #: go back to :attr:`.STATUS_WORK_WAITING` and then come back
    #: here when we have it and the work is going to be continued
    STATUS_WORK_IN_PROGRESS = u'in-progress'

    #: work has been finished, but no |sale| has been created yet.
    #: Work orders with this status will be displayed in the till/pos
    #: applications and it's possible to create a |sale| from them.
    STATUS_WORK_FINISHED = u'finished'

    # FIXME: This is not really delivered, it used to be closed, but
    # closed/finished are not ideal. This probably needs to be
    # renamed to something else in the future when we have a better name
    #: a |sale| has been created, delivery and payment handled there
    STATUS_DELIVERED = u'delivered'

    statuses = {
        STATUS_OPENED: _(u'Opened'),
        STATUS_CANCELLED: _(u'Cancelled'),
        STATUS_WORK_WAITING: _(u'Waiting'),
        STATUS_WORK_IN_PROGRESS: _(u'In progress'),
        STATUS_WORK_FINISHED: _(u'Finished'),
        STATUS_DELIVERED: _(u'Delivered')}

    status = EnumCol(default=STATUS_OPENED)

    #: A numeric identifier for this object. This value should be used instead of
    #: :obj:`Domain.id` when displaying a numerical representation of this object to
    #: the user, in dialogs, lists, reports and such.
    identifier = IdentifierCol()

    sellable_id = IdCol()
    #: a corresponding sellable for this equipament. Can be `None` if it is
    #: something that this shop does not sell
    sellable = Reference(sellable_id, 'Sellable.id')

    #: If a sellable is specified, the number of items of this sellable this
    #: workorder is for
    quantity = IntCol()

    #: description of the specific item brought by the client. This can be used
    #: to describe the equipament, if it is not one of the sellables available,
    #: or even to describe the serial number of the object.
    description = UnicodeCol()

    #: defect reported by the |client|
    defect_reported = UnicodeCol(default=u'')

    #: defect detected by the :obj:`.quote_responsible`
    defect_detected = UnicodeCol(default=u'')

    #: estimated hours needed to complete the work
    estimated_hours = DecimalCol(default=None)

    #: estimated cost of the work
    estimated_cost = PriceCol(default=None)

    #: estimated date the work will start
    estimated_start = DateTimeCol(default=None)

    #: estimated date the work will finish
    estimated_finish = DateTimeCol(default=None)

    #: date this work was opened
    open_date = DateTimeCol(default_factory=localnow)

    #: date this work was approved (set by :obj:`.approve`)
    approve_date = DateTimeCol(default=None)

    #: date this work was finished (set by :obj:`.finish`)
    finish_date = DateTimeCol(default=None)

    #: if the order was rejected by the other |branch|, e.g. when one
    #: branch sends the order in a |workorderpackage| to another branch
    #: for execution and it sends it back because of something
    is_rejected = BoolCol(allow_none=False, default=False)

    branch_id = IdCol()
    #: the |branch| where this order was created and responsible for it
    branch = Reference(branch_id, 'Branch.id')

    current_branch_id = IdCol()
    #: the actual branch where the order is. Can differ from
    # :attr:`.branch` if the order was sent in a |workorderpackage|
    #: to another |branch| for execution
    current_branch = Reference(current_branch_id, 'Branch.id')

    execution_branch_id = IdCol()
    #: the branch where the work's execution was made. It's automatically
    #: set by sending the order on a |workorderpackage|
    execution_branch = Reference(execution_branch_id, 'Branch.id')

    quote_responsible_id = IdCol(default=None)
    #: the |employee| responsible for the :obj:`.defect_detected`
    quote_responsible = Reference(quote_responsible_id, 'Employee.id')

    execution_responsible_id = IdCol(default=None)
    #: the |employee| responsible for the execution of the work
    execution_responsible = Reference(execution_responsible_id, 'Employee.id')

    client_id = IdCol(default=None)
    #: the |client|, owner of the equipment
    client = Reference(client_id, 'Client.id')

    category_id = IdCol(default=None)
    #: the |workordercategory| this work belongs
    category = Reference(category_id, 'WorkOrderCategory.id')

    sale_id = IdCol(default=None)
    #: the |sale| created after this work is finished
    sale = Reference(sale_id, 'Sale.id')

    order_items = ReferenceSet('id', 'WorkOrderItem.order_id')

    history_entries = ReferenceSet('id', 'WorkOrderHistory.work_order_id')

    #: Number of supplier order.
    supplier_order = UnicodeCol()

    @property
    def status_str(self):
        return self.statuses[self.status]

    def __init__(self, *args, **kwargs):
        super(WorkOrder, self).__init__(*args, **kwargs)

        if self.current_branch is None:
            self.current_branch = self.branch

    #
    #  IContainer implementation
    #

    def add_item(self, item):
        assert item.order is None
        item.order = self

    def get_items(self):
        return self.order_items

    def remove_item(self, item):
        assert item.order is self
        if item.quantity_decreased > 0:
            item.return_to_stock(item.quantity_decreased)
        item.order = None
        self.store.maybe_remove(item)

    #
    #  Public API
    #

    def get_total_amount(self):
        """Returns the total amount of this work order

        This is the same as::

            sum(item.total for item in :obj:`.order_items`)

        """
        items = self.order_items.find()
        return (items.sum(WorkOrderItem.price * WorkOrderItem.quantity) or
                currency(0))

    def add_sellable(self, sellable, price=None, quantity=1, batch=None):
        """Adds a sellable to this work order

        :param sellable: the |sellable| being added
        :param price: the price the sellable will be sold when
            finishing this work order
        :param quantity: the sellable's quantity
        :param batch: the |batch| this sellable comes from, if the sellable is a
          storable. Should be ``None`` if it is not a storable or if the storable
          does not have batches.
        :returns: the created |workorderitem|
        """
        # We only allow a batch to not be specified if we already have a sale
        # with it (meaning this work order comes from a work order quote)
        if not self.sale:
            self.validate_batch(batch, sellable=sellable)
        if price is None:
            price = sellable.base_price

        item = WorkOrderItem(store=self.store,
                             sellable=sellable,
                             batch=batch,
                             price=price,
                             quantity=quantity,
                             order=self)
        return item

    def is_items_totally_reserved(self):
        """Check if this work order item's are fully reserved

        For a |workorderitem| to be fully synchronized, it's
        :attr:`WorkOrderItem.quantity` should be equal to it's
        :attr:`WorkOrderItem.quantity_decreased`

        :returns: ``True`` if all is synchronized, ``False`` otherwise
        """
        tables = [WorkOrderItem,
                  Join(Sellable, WorkOrderItem.sellable_id == Sellable.id),
                  LeftJoin(Product, Product.id == Sellable.id)]
        # Only products that manage stock should be checked for quantity_decreased
        return self.store.using(*tables).find(
            WorkOrderItem,
            And(WorkOrderItem.order_id == self.id,
                WorkOrderItem.quantity_decreased != WorkOrderItem.quantity,
                Eq(Product.manage_stock, True))).is_empty()

    def is_in_transport(self):
        """Checks if this work order is in transport

        A work order is in transport if it's :attr:`.current_branch`
        is ``None``. The transportation of the work order is done in
        a |workorderpackage|

        :returns: ``True`` if in transport, ``False`` otherwise
        """
        return self.current_branch is None

    def is_approved(self):
        """Checks if this work order is approved

        If the order is paused or in progress, it's
        considered to be approved (obviously, the same applies to
        status after them, like finished and delivered).

        :returns: ``True`` if the order is considered as approved,
            ``False`` otherwise.
        """
        return self.status not in [self.STATUS_OPENED,
                                   self.STATUS_CANCELLED]

    def is_finished(self):
        """Checks if this work order is finished

        A work order is finished when the work that needs to be done
        on it finished, so this will be ``True`` when :obj:`WorkOrder.status` is
        :obj:`.STATUS_WORK_FINISHED` and :obj:`.STATUS_DELIVERED`
        """
        return self.status in [self.STATUS_WORK_FINISHED, self.STATUS_DELIVERED]

    def is_late(self):
        """Checks if this work order is late

        Being late means we set an
        :obj:`estimated finish date <.estimated_finish>` and that
        date has already passed.
        """
        if self.is_finished():
            return False
        if not self.estimated_finish:
            # No estimated_finish means we are not late
            return False

        today = localtoday().date()
        return self.estimated_finish.date() < today

    def can_cancel(self, ignore_sale=False):
        """Checks if this work order can be cancelled

        The order can be cancelled at any point, once it's not
        finished (this is done by checking :meth:`.is_finished`) or its already
        cancelled

        If the work order is related to a sale, the user cannot cancel it, and
        should cancel the sale instead.

        :param ignore_sale: Dont consider the related sale. This should only be
          used when the sale is being canceled
        :returns: ``True`` if can be cancelled, ``False`` otherwise
        """
        if self.status == self.STATUS_CANCELLED:
            return False
        if not ignore_sale and self.sale_id:
            return False
        return not self.is_finished()

    def can_approve(self):
        """Checks if this work order can be approved

        :returns: ``True`` if can be approved, ``False`` otherwise
        """
        return self.status == self.STATUS_OPENED

    def can_pause(self):
        """Checks if we can put the order on "waiting" state

        Only orders with work in progress be put in that state.

        :returns: ``True`` if can work, ``False`` otherwise
        """
        if self.is_rejected or self.is_in_transport():
            return False
        return self.status == self.STATUS_WORK_IN_PROGRESS

    def can_work(self):
        """Checks if this order's task can be worked

        Note that the work needs to be approved before it's task
        can be started to be worked.

        :returns: ``True`` if can work, ``False`` otherwise
        """
        if self.is_rejected or self.is_in_transport():
            return False
        # FIXME: We should not be calling get_current_branch on domain
        if self.current_branch != get_current_branch(self.store):
            return False
        return self.status == self.STATUS_WORK_WAITING

    def can_edit(self):
        """Check if this work order can be edited

        :returns: ``True`` if can edit, ``False`` otherwise
        """
        return not self.is_finished()

    def can_finish(self):
        """Checks if this work order can finish

        Note that the work needs to be started before you can finish.

        :returns: ``True`` if can finish, ``False`` otherwise
        """
        if self.is_rejected or self.is_in_transport():
            return False
        # FIXME: We should not be calling get_current_branch on domain
        if self.current_branch != get_current_branch(self.store):
            return False
        return self.status in [self.STATUS_WORK_IN_PROGRESS,
                               self.STATUS_WORK_WAITING]

    def can_close(self):
        """Checks if this work order can delivery

        Note that the work needs to be finished before you can deliver.

        Also, all of it's items need to be already decreased from
        the stock, that is, :attr:`WorkOrderItem.quantity` needs to
        be equal to :attr:`WorkOrderItem.quantity`.

        :returns: ``True`` if can deliver, ``False`` otherwise
        """
        # Because the way pre-sales are implemented, if we have a sale,
        # we don't need to reserve all quantities here (since the sale will
        # decrease the rest for us).
        if self.sale is None and not self.is_items_totally_reserved():
            return False
        if self.is_rejected or self.is_in_transport():
            return False
        # FIXME: We should not be calling get_current_branch on domain
        if self.current_branch != get_current_branch(self.store):
            return False
        return self.status == self.STATUS_WORK_FINISHED

    def can_reopen(self):
        """Checks if this work order can be re-opened

        A finished or delivered order can be reopened.

        :returns: ``True`` if it can, ``False`` otherwise
        """
        return self.is_finished()

    def can_reject(self):
        """Checks if the :obj:`.is_rejected` flag can be set

        :returns: ``True`` if it can, ``False`` otherwise
        """
        if self.is_rejected or self.is_in_transport():
            return False

        return self.status in [self.STATUS_WORK_WAITING,
                               self.STATUS_WORK_IN_PROGRESS,
                               self.STATUS_WORK_FINISHED]

    def can_undo_rejection(self):
        """Checks if the :obj:`.is_rejected` flag can be unset

        :returns: ``True`` if it can, ``False`` otherwise
        """
        return self.is_rejected and not self.is_in_transport()

    def reject(self, reason):
        """Setter for the :obj:`.is_rejected` flag

        When setting the is_rejected flag to ``True``,
        it should be done here since some additional logic
        (e.g. Registering a :class:`WorkOrderHistory`) will be
        made together.

        :param reason: the explanation to why we are setting this flag
        """
        assert self.can_reject()

        self.is_rejected = True
        WorkOrderHistory.add_entry(
            self.store, self, what=_(u"Rejected"),
            old_value=_(u"No"), new_value=_(u"Yes"), notes=reason)

    def undo_rejection(self, reason):
        """Unsetter for the :obj:`.is_rejected` flag

        When setting the is_rejected flag to ``False``,
        it should be done here since some additional logic
        (e.g. Registering a :class:`WorkOrderHistory`) will be
        made together.

        :param reason: an explanation to what was done to make this
            order not rejected anymore
        """
        assert self.can_undo_rejection()

        self.is_rejected = False
        WorkOrderHistory.add_entry(
            self.store, self, what=_(u"Rejected"),
            old_value=_(u"Yes"), new_value=_(u"No"), notes=reason)

    def cancel(self, reason=None, ignore_sale=False):
        """Cancels this work order

        Cancel the work order, probably because the |client|
        didn't approve it or simply gave up of doing it.

        All reserved items (the ones with
        :attr:`WorkOrderItem.quantity_decreased` > 0) will be
        returned to stock.

        :param reason: an explanation to why this order was cancelled
        """
        assert self.can_cancel(ignore_sale)

        for item in self.order_items:
            if item.quantity_decreased > 0:
                item.return_to_stock(item.quantity_decreased)

        self._change_status(self.STATUS_CANCELLED, notes=reason)

    def approve(self):
        """Approves this work order

        Approving means that the |client| has accepted the
        work's quote and it's cost and it can now start.
        """
        assert self.can_approve()
        self.approve_date = localnow()
        WorkOrderHistory.add_entry(
            self.store, self, what=_(u"Approved"),
            old_value=_(u"No"), new_value=_(u"Yes"))
        self._change_status(self.STATUS_WORK_WAITING)

    def work(self):
        """Set this orders state as "work in progress"

        The :obj:`.execution_responsible` started working on
        this order's task and will finish sometime in the future.

        Note that if the work has to stop for a while for some reason
        (e.g. lack of material, lack of labor, etc), one can call
        :meth:`.pause` to set the state properly and then call this
        again when the work can continue.
        """
        assert self.can_work()
        self._change_status(self.STATUS_WORK_IN_PROGRESS)

    def pause(self, reason):
        """Set this orders state as "waiting"

        This is used to indicate that the work has stopped for a while
        for a reason (e.g. lack of material, lack of labor, etc). When the
        work can continue call :meth:`.work`

        Note: When comming from :attr:`.STATUS_OPENED`, :meth:`.approve` must
        be used instead.

        :param reason: the reason explaining why this order was paused
        """
        assert self.can_pause()
        self._change_status(self.STATUS_WORK_WAITING, notes=reason)

    def finish(self):
        """Finishes this work order's task

        The :obj:`.execution_responsible` has finished working on
        this order's task. It's possible now to give the equipment
        back to the |client| and create a |sale| so we are able
        to :meth:`deliver <.deliver>` this order.
        """
        assert self.can_finish()
        self.finish_date = localnow()
        # Make sure we are not overwriting this value, since we can reopen the
        # order and finish again
        if not self.execution_branch:
            branch = get_current_branch(self.store)
            self.execution_branch = branch
        self._change_status(self.STATUS_WORK_FINISHED)

    def reopen(self, reason):
        """Reopens the work order

        This is useful if the order was finished but needs to be reopened
        for some reason. The state will be back to
        :attr:`.STATUS_WORK_IN_PROGRESS`

        :param reason: the reason explaining why this order was reopened
        """
        assert self.can_reopen()
        self.finish_date = None
        self._change_status(self.STATUS_WORK_IN_PROGRESS, notes=reason)

    def close(self):
        """Delivers this work order

        This order's task is done, the |client| got the equipment
        back and a |sale| was created for the |workorderitems|
        Nothing more needs to be done.
        """
        assert self.can_close()
        self._change_status(self.STATUS_DELIVERED)

    def change_status(self, new_status, reason=None):
        """
        Change the status of this work order

        Using this function you can change the status is several steps.

        :param new_status: the new status
        :param reason: a reason for that status change. Only needed
            by some changes
        :returns: if the status was changed
        :raises: :exc:`stoqlib.exceptions.InvalidStatus` if the status cannot be changed
        :raises: :exc:`stoqlib.exceptions.NeedReason` if the change
            needs a reason to happen
        """
        # This is the logic order of status changes, this is the flow/ordering
        # of the status that should be used
        status_order = [WorkOrder.STATUS_OPENED,
                        WorkOrder.STATUS_WORK_WAITING,
                        WorkOrder.STATUS_WORK_IN_PROGRESS,
                        WorkOrder.STATUS_WORK_FINISHED]

        old_index = status_order.index(self.status)
        new_index = status_order.index(new_status)
        direction = cmp(new_index, old_index)

        next_status = self.status
        while True:
            # Calculate what's the next status we should set in order to reach
            # our goal (new_status). Note that this can go either forward or backward
            # depending on the direction
            next_status = status_order[status_order.index(next_status) + direction]
            if next_status == WorkOrder.STATUS_WORK_IN_PROGRESS:
                if self.can_reopen():
                    if reason is not None:
                        self.reopen(reason=reason)
                    else:
                        raise NeedReason(_("A reason is needed to reopen "
                                           "the work order"))
                elif self.can_work():
                    self.work()
                else:
                    raise InvalidStatus(
                        _("This work order cannot be worked on"))

            if next_status == WorkOrder.STATUS_WORK_FINISHED:
                if not self.can_finish():
                    raise InvalidStatus(
                        _('This work order cannot be finished'))
                self.finish()

            if next_status == WorkOrder.STATUS_WORK_WAITING:
                if self.can_approve():
                    self.approve()
                elif self.can_pause():
                    if reason is not None:
                        self.pause(reason=reason)
                    else:
                        raise NeedReason(_("A reason is needed to pause "
                                           "the work order"))
                else:
                    raise InvalidStatus(
                        _("This work order cannot wait for material"))

            if next_status == WorkOrder.STATUS_OPENED:
                raise InvalidStatus(_("This work order cannot be re-opened"))

            # We've reached our goal, bail out
            if next_status == new_status:
                break

    #
    #  Private
    #

    def _change_status(self, new_status, notes=None):
        old_status = self.status
        self.status = new_status
        WorkOrderHistory.add_entry(self.store, self, what=_(u"Status"),
                                   old_value=self.statuses[old_status],
                                   new_value=self.statuses[new_status],
                                   notes=notes)

    #
    #  Classmethods
    #

    @classmethod
    def find_by_sale(cls, store, sale):
        """Returns all |workorders| associated with the given |sale|.

        :param sale: The |sale| used to filter the existing |workorders|
        :resturn: An iterable with all work orders:
        :rtype: resultset
        """
        return store.find(cls, sale=sale)

    #
    #  Events
    #

    @SaleStatusChangedEvent.connect
    @classmethod
    def _on_sale_status_changed(cls, sale, old_status):
        if sale.status == Sale.STATUS_CANCELLED:
            for self in cls.find_by_sale(sale.store, sale):
                #FIXME: this is sort of hack, currently can not cancel a
                #       finished work order. Maybe we should allow it.
                if self.is_finished():
                    self.reopen(reason=_(u"Reopening work order to "
                                         "cancel the sale"))
                self.cancel(reason=_(u"The sale was cancelled"),
                            ignore_sale=True)


# TODO: Maybe this can be moved to a generic 'DomainHistory' (or something
# like that) so that we can have the same api for logging domain activities
class WorkOrderHistory(Domain):
    """Holds information about changes for |workorders|

    Every time something happens to a |workorder|, it should be logged
    here, e.g. When it is opened, when it is approved, when it sent
    in a |workorderpackage| to another branch, etc.
    """

    __storm_table__ = 'work_order_history'

    #: the date and time that this event happened
    date = DateTimeCol(default_factory=localnow)

    #: the "what has changed". e.g. "Status", "Current branch"
    what = UnicodeCol(allow_none=False)

    #: the old value for the :attr:`.what`
    old_value = UnicodeCol()

    #: the new value for the :attr:`.what`
    new_value = UnicodeCol()

    #: some notes about the change. Usually used for a more detailed
    #: explanation about the :attr:`.what`
    notes = UnicodeCol()

    user_id = IdCol(allow_none=False)
    #: the |loginuser| that made this change
    user = Reference(user_id, 'LoginUser.id')

    work_order_id = IdCol(allow_none=False)
    #: the |workorder| where this change happened
    work_order = Reference(work_order_id, 'WorkOrder.id')

    #
    #  Classmethods
    #

    @classmethod
    def add_entry(cls, store, workorder, what,
                  old_value=None, new_value=None, notes=None):
        """Add an entry to the history

        :param store: a store
        :param workorder: the |workorder| where this change happened
        :param what: the description of what has changed. See
            :attr:`.what` for more information
        :param old_value: the *what's* old value. See
            :attr:`.old_value` for more information
        :param new_value: the *what's* new value. See
            :attr:`.new_value` for more information
        :returns: the newly created :class:`WorkOrderHistory`
        """
        user = get_current_user(store)
        return cls(store=store, work_order=workorder, user=user, what=what,
                   old_value=old_value, new_value=new_value, notes=notes)


_WorkOrderItemsSummary = Alias(Select(
    columns=[
        WorkOrderItem.order_id,
        Alias(Sum(WorkOrderItem.quantity), 'quantity'),
        Alias(Sum(WorkOrderItem.quantity * WorkOrderItem.price), 'total')],
    tables=[WorkOrderItem],
    group_by=[WorkOrderItem.order_id]),
    '_work_order_items')


class WorkOrderView(Viewable):
    """A view for |workorders|

    This is used to get the most information of a |workorder|
    without doing lots of database queries.
    """

    # TODO: Maybe we should have a cache for branches, to avoid all this
    # joins just to get the company name.
    _BranchOriginalBranch = ClassAlias(Branch, "branch_original_branch")
    _BranchCurrentBranch = ClassAlias(Branch, "branch_current_branch")
    _BranchExecutionBranch = ClassAlias(Branch, "branch_execution_branch")
    _PersonOriginalBranch = ClassAlias(Person, "person_original_branch")
    _PersonCurrentBranch = ClassAlias(Person, "person_current_branch")
    _PersonExecutionBranch = ClassAlias(Person, "person_execution_branch")
    _CompanyOriginalBranch = ClassAlias(Company, "company_original_branch")
    _CompanyCurrentBranch = ClassAlias(Company, "company_current_branch")
    _CompanyExecutionBranch = ClassAlias(Company, "company_execution_branch")
    _PersonClient = ClassAlias(Person, "person_client")
    _PersonSalesPerson = ClassAlias(Person, "person_salesperson")
    _PersonEmployee = ClassAlias(Person, "person_employee")

    #: the |workorder| object
    work_order = WorkOrder

    #: the |workordercategory| object
    category = WorkOrderCategory

    #: the |client| object
    client = Client

    #: the |sale| associated with this workorder
    sale = Sale

    # WorkOrder
    id = WorkOrder.id
    identifier = WorkOrder.identifier
    identifier_str = Cast(WorkOrder.identifier, 'text')
    status = WorkOrder.status
    description = WorkOrder.description
    open_date = WorkOrder.open_date
    approve_date = WorkOrder.approve_date
    estimated_start = WorkOrder.estimated_start
    estimated_finish = WorkOrder.estimated_finish
    finish_date = WorkOrder.finish_date
    is_rejected = WorkOrder.is_rejected
    equipment = Coalesce(Concat(Sellable.description, u" - ", WorkOrder.description),
                         WorkOrder.description)
    supplier_order = WorkOrder.supplier_order

    # WorkOrderCategory
    category_id = WorkOrderCategory.id
    category_name = WorkOrderCategory.name
    category_color = WorkOrderCategory.color

    # Client
    client_name = _PersonClient.name

    # SalesPerson
    salesperson_name = _PersonSalesPerson.name

    # Employee
    employee_name = _PersonEmployee.name

    # Branch
    branch_id = WorkOrder.branch_id
    branch_name = Coalesce(NullIf(_CompanyOriginalBranch.fancy_name, u''),
                           _PersonOriginalBranch.name)
    current_branch_name = Coalesce(NullIf(_CompanyCurrentBranch.fancy_name, u''),
                                   _PersonCurrentBranch.name)
    execution_branch_name = Coalesce(NullIf(_CompanyExecutionBranch.fancy_name, u''),
                                     _PersonExecutionBranch.name)

    # Sale
    sale_id = Sale.id
    sale_identifier = Sale.identifier
    sale_identifier_str = Cast(Sale.identifier, 'text')

    # Sellable
    sellable = Sellable.description

    # WorkOrderItem
    quantity = Coalesce(Field('_work_order_items', 'quantity'), 0)
    total = Coalesce(Field('_work_order_items', 'total'), 0)

    tables = [
        WorkOrder,

        LeftJoin(Client, WorkOrder.client_id == Client.id),
        LeftJoin(_PersonClient, Client.person_id == _PersonClient.id),

        LeftJoin(Sale, WorkOrder.sale_id == Sale.id),
        LeftJoin(SalesPerson, Sale.salesperson_id == SalesPerson.id),
        LeftJoin(_PersonSalesPerson,
                 SalesPerson.person_id == _PersonSalesPerson.id),

        LeftJoin(Employee, WorkOrder.quote_responsible_id == Employee.id),
        LeftJoin(_PersonEmployee,
                 Employee.person_id == _PersonEmployee.id),

        LeftJoin(Sellable, WorkOrder.sellable_id == Sellable.id),

        LeftJoin(_BranchOriginalBranch,
                 WorkOrder.branch_id == _BranchOriginalBranch.id),
        LeftJoin(_PersonOriginalBranch,
                 _BranchOriginalBranch.person_id == _PersonOriginalBranch.id),
        LeftJoin(_CompanyOriginalBranch,
                 _CompanyOriginalBranch.person_id == _PersonOriginalBranch.id),

        LeftJoin(_BranchCurrentBranch,
                 WorkOrder.current_branch_id == _BranchCurrentBranch.id),
        LeftJoin(_PersonCurrentBranch,
                 _BranchCurrentBranch.person_id == _PersonCurrentBranch.id),
        LeftJoin(_CompanyCurrentBranch,
                 _CompanyCurrentBranch.person_id == _PersonCurrentBranch.id),

        LeftJoin(_BranchExecutionBranch,
                 WorkOrder.execution_branch_id == _BranchExecutionBranch.id),
        LeftJoin(_PersonExecutionBranch,
                 _BranchExecutionBranch.person_id == _PersonExecutionBranch.id),
        LeftJoin(_CompanyExecutionBranch,
                 _CompanyExecutionBranch.person_id == _PersonExecutionBranch.id),

        LeftJoin(WorkOrderCategory,
                 WorkOrder.category_id == WorkOrderCategory.id),

        LeftJoin(_WorkOrderItemsSummary,
                 Field('_work_order_items', 'order_id') == WorkOrder.id),
    ]

    @property
    def branch(self):
        return self.store.get(Branch, self.branch_id)

    @property
    def status_str(self):
        return self.work_order.status_str

    @classmethod
    def post_search_callback(cls, sresults):
        select = sresults.get_select_expr(Count(1), Sum(cls.total))
        return ('count', 'sum'), select

    @classmethod
    def find_by_current_branch(cls, store, branch):
        return store.find(cls, WorkOrder.current_branch_id == branch.id)

    @classmethod
    def find_by_can_send_to_branch(cls, store, current_branch,
                                   destination_branch):
        if destination_branch.can_execute_foreign_work_orders:
            # When the destination can execute foreign work orders, we can send
            # orders that are originally from it, waiting and any rejected
            query = Or(cls.branch_id == destination_branch.id,
                       cls.status == WorkOrder.STATUS_WORK_WAITING,
                       Eq(cls.is_rejected, True))
        else:
            # When the destination branch can't execute foreign work orders,
            # it just can receive it's own orders back, and those orders needs
            # to be finished or rejected
            query = And(cls.branch_id == destination_branch.id,
                        Or(cls.status == WorkOrder.STATUS_WORK_FINISHED,
                           Eq(cls.is_rejected, True)))

        results = cls.find_by_current_branch(store, current_branch)
        return results.find(query)

    @classmethod
    def find_pending(cls, store, start_date=None, end_date=None):
        """Find results for this view that are pending (not delivered yet)

        :param store: the store that will be used to find the results
        :param start_date: if not ``None``, the results will be filtered
            to show only the ones with :attr:`.estimated_finish` greater
            than it
        :param end_date: if not ``None``, the results will be filtered
            to show only the ones with :attr:`.estimated_finish` lesser
            than it
        :returns: the matching views
        :rtype: a sequence of :class:`WorkOrderWithPackageView`
        """
        query = Not(In(WorkOrder.status,
                       [WorkOrder.STATUS_DELIVERED,
                        WorkOrder.STATUS_CANCELLED]))
        if start_date:
            query = And(query, WorkOrder.estimated_finish >= start_date)
        if end_date:
            query = And(query, WorkOrder.estimated_finish <= end_date)

        return store.find(cls, query)


class WorkOrderWithPackageView(WorkOrderView):
    """A view for |workorders| in a |workorderpackage|

    This is the same as :class:`.WorkOrderView`, but package
    information is joined together
    """

    _BranchSource = ClassAlias(Branch, "branch_source")
    _BranchDestination = ClassAlias(Branch, "branch_destination")
    _PersonSource = ClassAlias(Person, "person_source")
    _PersonDestination = ClassAlias(Person, "person_destination")
    _CompanySource = ClassAlias(Company, "company_source")
    _CompanyDestination = ClassAlias(Company, "company_destination")

    # WorkOrderPackage
    package_id = WorkOrderPackage.id
    package_identifier = WorkOrderPackage.identifier
    package_send_date = WorkOrderPackage.send_date
    package_receive_date = WorkOrderPackage.receive_date

    # WorkOrderPackageItem
    package_item_id = WorkOrderPackageItem.id

    # Branch
    source_branch_name = Coalesce(_CompanySource.fancy_name,
                                  _PersonSource.name)
    destination_branch_name = Coalesce(_CompanyDestination.fancy_name,
                                       _PersonDestination.name)

    tables = WorkOrderView.tables[:]
    tables.extend([
        LeftJoin(WorkOrderPackageItem,
                 WorkOrderPackageItem.order_id == WorkOrder.id),
        LeftJoin(WorkOrderPackage,
                 WorkOrderPackageItem.package_id == WorkOrderPackage.id),

        LeftJoin(_BranchSource,
                 WorkOrderPackage.source_branch_id == _BranchSource.id),
        LeftJoin(_PersonSource,
                 _BranchSource.person_id == _PersonSource.id),
        LeftJoin(_CompanySource,
                 _CompanySource.person_id == _PersonSource.id),

        LeftJoin(_BranchDestination,
                 WorkOrderPackage.destination_branch_id == _BranchDestination.id),
        LeftJoin(_PersonDestination,
                 _BranchDestination.person_id == _PersonDestination.id),
        LeftJoin(_CompanyDestination,
                 _CompanyDestination.person_id == _PersonDestination.id),
    ])

    @classmethod
    def find_by_package(cls, store, package):
        """Find results for this view that are in the *package*

        :param store: the store that will be used to find the
            results
        :param package: the |workorderpackage| used to filter
            the results
        :returns: the matching views
        :rtype: a sequence of :class:`WorkOrderWithPackageView`
        """
        return store.find(cls, package_id=package.id)


class WorkOrderApprovedAndFinishedView(WorkOrderView):
    """A view for approved and finished |workorders|

    This is the same as :class:`.WorkOrderView`, but only
    approved and finished orders are showed here.
    """

    clause = In(WorkOrder.status, [WorkOrder.STATUS_WORK_WAITING,
                                   WorkOrder.STATUS_WORK_FINISHED])


class WorkOrderFinishedView(WorkOrderView):
    """A view for finished |workorders| that still dont have a |sale|

    This viewable should be used only to find what workorders still dont have a
    sale and can be delivered (ie, they can have the sale created).

    This is the same as :class:`.WorkOrderView`, but only finished
    orders are showed here.
    """

    clause = And(WorkOrder.status == WorkOrder.STATUS_WORK_FINISHED,
                 Eq(Sale.id, None))


_WorkOrderPackageItemsSummary = Alias(Select(
    columns=[
        WorkOrderPackageItem.package_id,
        Alias(Count(WorkOrderPackageItem.id), 'quantity')],
    tables=[WorkOrderPackageItem],
    group_by=[WorkOrderPackageItem.package_id]),
    '_package_items')


class WorkOrderPackageView(Viewable):
    """A view for |workorderpackages|

    This is used to get the most information of a |workorderpackage|
    without doing lots of database queries.
    """

    _BranchSource = ClassAlias(Branch, "branch_source")
    _BranchDestination = ClassAlias(Branch, "branch_destination")
    _PersonSource = ClassAlias(Person, "person_source")
    _PersonDestination = ClassAlias(Person, "person_destination")
    _CompanySource = ClassAlias(Company, "company_source")
    _CompanyDestination = ClassAlias(Company, "company_destination")

    #: the |workorderpackage| object
    package = WorkOrderPackage

    # WorkOrderPackage
    id = WorkOrderPackage.id
    identifier = WorkOrderPackage.identifier
    send_date = WorkOrderPackage.send_date
    receive_date = WorkOrderPackage.receive_date

    # Branch
    source_branch_name = Coalesce(NullIf(_CompanySource.fancy_name, u''),
                                  _PersonSource.name)
    destination_branch_name = Coalesce(NullIf(_CompanyDestination.fancy_name, u''),
                                       _PersonDestination.name)

    # WorkOrder
    quantity = Coalesce(Field('_package_items', 'quantity'), 0)

    tables = [
        WorkOrderPackage,

        LeftJoin(_BranchSource,
                 WorkOrderPackage.source_branch_id == _BranchSource.id),
        LeftJoin(_PersonSource,
                 _BranchSource.person_id == _PersonSource.id),
        LeftJoin(_CompanySource,
                 _CompanySource.person_id == _PersonSource.id),

        LeftJoin(_BranchDestination,
                 WorkOrderPackage.destination_branch_id == _BranchDestination.id),
        LeftJoin(_PersonDestination,
                 _BranchDestination.person_id == _PersonDestination.id),
        LeftJoin(_CompanyDestination,
                 _CompanyDestination.person_id == _PersonDestination.id),

        LeftJoin(_WorkOrderPackageItemsSummary,
                 Field('_package_items', 'package_id') == WorkOrderPackage.id),
    ]

    @classmethod
    def find_by_destination_branch(cls, store, branch):
        return store.find(cls,
                          WorkOrderPackage.destination_branch_id == branch.id)


class WorkOrderPackageSentView(WorkOrderPackageView):
    """A view for sent |workorderpackages|

    This is the same as :class:`.WorkOrderPackageView`, but only
    sent orders are showed here.
    """

    clause = WorkOrderPackage.status == WorkOrderPackage.STATUS_SENT


class WorkOrderHistoryView(Viewable):
    """A view for :class:`WorkOrderHistoryView`"""

    #: the :class:`WorkOrderHistory` object
    history = WorkOrderHistory

    # WorkOrderHistory
    id = WorkOrderHistory.id
    date = WorkOrderHistory.date
    what = WorkOrderHistory.what
    old_value = WorkOrderHistory.old_value
    new_value = WorkOrderHistory.new_value
    notes = WorkOrderHistory.notes

    # LoginUser
    user_name = Person.name

    tables = [
        WorkOrderHistory,

        # LoginUser
        Join(LoginUser, WorkOrderHistory.user_id == LoginUser.id),
        Join(Person, LoginUser.person_id == Person.id),
    ]

    #
    #  Classmethods
    #

    @classmethod
    def find_by_work_order(cls, store, workorder):
        """Find results for this view that references *workorder*

        :param store: the store that will be used to find the results
        :param package: the |workorder| used to filter the results
        :returns: the matching views
        :rtype: a sequence of :class:`WorkOrderHistoryView`
        """
        return store.find(cls, WorkOrderHistory.work_order_id == workorder.id)
