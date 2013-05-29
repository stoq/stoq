# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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

from kiwi.currency import currency
from storm.expr import Count, LeftJoin, Alias, Select, Sum, Coalesce, In
from storm.info import ClassAlias
from storm.references import Reference, ReferenceSet
from zope.interface import implements

from stoqlib.database.expr import Field, NullIf
from stoqlib.database.properties import (IntCol, DateTimeCol, UnicodeCol,
                                         PriceCol, DecimalCol, QuantityCol,
                                         IdentifierCol, IdCol)
from stoqlib.database.runtime import get_current_branch
from stoqlib.database.viewable import Viewable
from stoqlib.exceptions import InvalidStatus
from stoqlib.domain.base import Domain
from stoqlib.domain.interfaces import IDescribable, IContainer
from stoqlib.domain.person import Branch, Client, Person, SalesPerson, Company
from stoqlib.domain.product import StockTransactionHistory
from stoqlib.domain.sale import Sale
from stoqlib.lib.dateutils import localnow, localtoday
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


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

    #: notes about why the :attr:`.order` is being sent to another branch
    notes = UnicodeCol(default=u'')

    package_id = IdCol(allow_none=False)
    #: the |workorderpackage| this item is transported in
    package = Reference(package_id, 'WorkOrderPackage.id')

    order_id = IdCol(allow_none=False)
    #: the |workorder| this item represents
    order = Reference(order_id, 'WorkOrder.id')


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
    STATUS_OPENED = 0

    #: package was sent to the :attr:`.destination_branch`
    STATUS_SENT = 1

    #: package was received by the :attr:`.destination_branch`
    STATUS_RECEIVED = 2

    statuses = {
        STATUS_OPENED: _(u'Opened'),
        STATUS_SENT: _(u'Sent'),
        STATUS_RECEIVED: _(u'Received')}

    status = IntCol(allow_none=False, default=STATUS_OPENED)

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

    def add_order(self, workorder):
        """Add a |workorder| on this package

        :returns: the created |workorderpackageitem|
        """
        if workorder.current_branch != self.source_branch:
            raise ValueError(
                _("The order %s is not in the source branch") % (
                    workorder, ))
        if not self.package_items.find(order=workorder).is_empty():
            raise ValueError(
                _("The order %s is already on the package %s") % (
                    workorder, self))

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

        When calling this, the work orders' :attr:`WorkOrder.current_branch`
        will be ``None``, since they are on a package and not on any branch.
        """
        assert self.can_send()

        if self.source_branch != get_current_branch(self.store):
            raise ValueError(
                _("This package's source branch is %s and you are in %s. "
                  "It's not possible to send a package outside the "
                  "source branch") % (
                      self.source_branch, get_current_branch(self.store)))

        workorders = [item.order for item in self.package_items]
        if not len(workorders):
            raise ValueError(_("There're no orders to send"))

        for order in workorders:
            assert order.current_branch == self.source_branch
            # The order is going to leave the current_branch
            order.current_branch = None

        self.send_date = localnow()
        self.status = self.STATUS_SENT

    def receive(self):
        """Receive the package on the :attr:`.destination_branch`

        This will mark the package as received in the branch
        to receive it there. Note that it's only possible to call this
        on the same branch as :attr:`.destination_branch`.

        When calling this, the work orders' :attr:`WorkOrder.current_branch`
        will be set to :attr:`.destination_branch`, since receiving means
        they got to their destination.
        """
        assert self.can_receive()

        if self.destination_branch != get_current_branch(self.store):
            raise ValueError(
                _("This package's destination branch is %s and you are in %s. "
                  "It's not possible to receive a package outside the "
                  "destination branch") % (
                      self.destination_branch, get_current_branch(self.store)))

        for order in [item.order for item in self.package_items]:
            assert order.current_branch is None
            # The order is in destination branch now
            order.current_branch = self.destination_branch

        self.receive_date = localnow()
        self.status = self.STATUS_RECEIVED


class WorkOrderCategory(Domain):
    """A |workorder|'s category

    Used to categorize a |workorder|. It can be differentiate
    mainly by the :attr:`.name`, but one can use :obj:`color`
    in a gui to make the differentiation better.

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/work_order_category.html>`__
    """

    __storm_table__ = 'work_order_category'

    implements(IDescribable)

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

    @property
    def total(self):
        """The total value for this item

        Note that this is the same as :obj:`.quantity` * :obj:`.price`
        """
        return currency(self.price * self.quantity)

    def __init__(self, *args, **kwargs):
        self._original_quantity = 0
        super(WorkOrderItem, self).__init__(*args, **kwargs)

    def __storm_loaded__(self):
        super(WorkOrderItem, self).__storm_loaded__()
        self._original_quantity = self.quantity

    #
    #  Public API
    #

    def sync_stock(self):
        """Synchronizes the stock, increasing/decreasing it accordingly.

        When setting :obj:`~.quantity` be sure to call this to properly
        synchronize the stock (increase or decrease it). That counts
        for object creation too.
        """
        storable = self.sellable.product_storable
        if not storable:
            # Not a product
            return

        diff_quantity = self._original_quantity - self.quantity
        if diff_quantity > 0:
            storable.increase_stock(
                diff_quantity, self.order.branch,
                StockTransactionHistory.TYPE_WORK_ORDER_USED, self.id)
        elif diff_quantity < 0:
            diff_quantity = - diff_quantity
            storable.decrease_stock(
                diff_quantity, self.order.branch,
                StockTransactionHistory.TYPE_WORK_ORDER_USED, self.id)

        # Reset the values used to calculate the stock quantity, just like
        # when the object as loaded from the database again.
        self._original_quantity = self.quantity


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
         STATUS_OPENED -> STATUS_APPROVED;
         STATUS_OPENED -> STATUS_CANCELLED;
         STATUS_APPROVED -> STATUS_OPENED;
         STATUS_APPROVED -> STATUS_CANCELLED;
         STATUS_APPROVED -> STATUS_WORK_IN_PROGRESS;
         STATUS_WORK_IN_PROGRESS -> STATUS_WORK_FINISHED;
         STATUS_WORK_FINISHED -> STATUS_CLOSED;
       }

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/work_order.html>`__
    """

    __storm_table__ = 'work_order'

    implements(IContainer)

    #: a request for an order has been created, the order has not yet
    #: been approved the |client|
    STATUS_OPENED = 0

    #: for some reason it was cancelled
    STATUS_CANCELLED = 1

    #: the |client| has approved the order, work has not begun yet
    STATUS_APPROVED = 2

    #: work is currently in progress
    STATUS_WORK_IN_PROGRESS = 3

    #: work has been finished, but no |sale| has been created yet.
    #: Work orders with this status will be displayed in the till/pos
    #: applications and it's possible to create a |sale| from them.
    STATUS_WORK_FINISHED = 4

    #: a |sale| has been created, delivery and payment handled there
    STATUS_CLOSED = 5

    statuses = {
        STATUS_OPENED: _(u'Waiting'),
        STATUS_CANCELLED: _(u'Cancelled'),
        STATUS_APPROVED: _(u'Approved'),
        STATUS_WORK_IN_PROGRESS: _(u'In progress'),
        STATUS_WORK_FINISHED: _(u'Finished'),
        STATUS_CLOSED: _(u'Closed')}

    status = IntCol(default=STATUS_OPENED)

    #: A numeric identifier for this object. This value should be used instead of
    #: :obj:`Domain.id` when displaying a numerical representation of this object to
    #: the user, in dialogs, lists, reports and such.
    identifier = IdentifierCol()

    #: defected equipment
    equipment = UnicodeCol()

    #: defect reported by the |client|
    defect_reported = UnicodeCol()

    #: defect detected by the :obj:`.quote_responsible`
    defect_detected = UnicodeCol()

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

    branch_id = IdCol()
    #: the |branch| where this order was created and responsible for it
    branch = Reference(branch_id, 'Branch.id')

    current_branch_id = IdCol()
    #: the actual branch where the order is. Can differ from
    # :attr:`.branch` if the order was sent in a |workorderpackage|
    #: to another |branch| for execution
    current_branch = Reference(current_branch_id, 'Branch.id')

    quote_responsible_id = IdCol(default=None)
    #: the |loginuser| responsible for the :obj:`.defect_detected`
    quote_responsible = Reference(quote_responsible_id, 'LoginUser.id')

    execution_responsible_id = IdCol(default=None)
    #: the |loginuser| responsible for the execution of the work
    execution_responsible = Reference(execution_responsible_id, 'LoginUser.id')

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

    @property
    def status_str(self):
        if self.is_in_transport():
            return _("In transport")
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
        # Setting the quantity to 0 and calling sync_stock
        # will return all the actual quantity to the stock
        item.quantity = 0
        item.sync_stock()
        self.store.remove(item)

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

    def sync_stock(self):
        """Synchronizes the stock for this work order's items

        Just a shortcut to call :meth:`WorkOrderItem.sync_stock` in all
        items in this work order.
        """
        for item in self.get_items():
            item.sync_stock()

    def is_in_transport(self):
        """Checks if this work order is in transport

        A work order is in transport if it's :attr:`.current_branch`
        is ``None``. The transportation of the work order is done in
        a |workorderpackage|

        :returns: ``True`` if in transport, ``False`` otherwise
        """
        return self.current_branch is None

    def is_finished(self):
        """Checks if this work order is finished

        A work order is finished when the work that needs to be done
        on it finished, so this will be ``True`` when :obj:`WorkOrder.status` is
        :obj:`.STATUS_WORK_FINISHED` and :obj:`.STATUS_CLOSED`
        """
        return self.status in [self.STATUS_WORK_FINISHED, self.STATUS_CLOSED]

    def is_late(self):
        """Checks if this work order is late

        Being late means we set an
        :obj:`estimated finish date <.estimated_finish>` and that
        date has already passed.
        """
        if self.status in [self.STATUS_WORK_FINISHED, self.STATUS_CLOSED]:
            return False
        if not self.estimated_finish:
            # No estimated_finish means we are not late
            return False

        today = localtoday().date()
        return self.estimated_finish.date() < today

    def can_cancel(self):
        """Checks if this work order can be cancelled

        Only opened and approved orders can be cancelled. Once the
        work has started, it should not be possible to do that anymore.

        :returns: ``True`` if can be cancelled, ``False`` otherwise
        """
        return self.status in [self.STATUS_OPENED, self.STATUS_APPROVED]

    def can_approve(self):
        """Checks if this work order can be approved

        :returns: ``True`` if can be approved, ``False`` otherwise
        """
        return self.status == self.STATUS_OPENED

    def can_undo_approval(self):
        """Checks if this work order order can be unapproved

        Only approved orders can be unapproved. Once the work
        has started, it should not be possible to do that anymore

        :returns: ``True`` if can be unapproved, ``False`` otherwise
        """
        return self.status == self.STATUS_APPROVED

    def can_start(self):
        """Checks if this work order can start

        Note that the work needs to be approved before it can be started.

        :returns: ``True`` if can start, ``False`` otherwise
        """
        return self.status == self.STATUS_APPROVED

    def can_finish(self):
        """Checks if this work order can finish

        Note that the work needs to be started before you can finish.

        :returns: ``True`` if can finish, ``False`` otherwise
        """
        if not self.order_items.count():
            return False
        return self.status == self.STATUS_WORK_IN_PROGRESS

    def can_close(self):
        """Checks if this work order can close

        Note that the work needs to be finished before you can close.

        :returns: ``True`` if can close, ``False`` otherwise
        """
        return self.status == self.STATUS_WORK_FINISHED

    def cancel(self):
        """Cancels this work order

        Cancel the work order, probably because the |client|
        didn't approve it or simply gave up of doing it.
        """
        assert self.can_cancel()
        self.status = self.STATUS_CANCELLED

    def approve(self):
        """Approves this work order

        Approving means that the |client| has accepted the
        work's quote and it's cost and it can now start.
        """
        assert self.can_approve()
        self.approve_date = localnow()
        self.status = self.STATUS_APPROVED

    def undo_approval(self):
        """Unapproves this work order

        Unapproving means that the |client| once has approved the
        order's task and it's cost, but now he doesn't anymore.
        Different from :meth:`.cancel`, the |client| still can
        approve this again.
        """
        assert self.can_undo_approval()
        self.approve_date = None
        self.status = self.STATUS_OPENED

    def start(self):
        """Starts this work order's task

        The :obj:`.execution_responsible` started working on
        this order's task and will finish sometime in the future.
        """
        assert self.can_start()
        self.status = self.STATUS_WORK_IN_PROGRESS

    def finish(self):
        """Finishes this work order's task

        The :obj:`.execution_responsible` has finished working on
        this order's task. It's possible now to give the equipment
        back to the |client| and create a |sale| so we are able
        to :meth:`close <.close>` this order.
        """
        assert self.can_finish()
        self.finish_date = localnow()
        self.status = self.STATUS_WORK_FINISHED

    def close(self):
        """Closes this work order

        This order's task is done, the |client| got the equipment
        back and a |sale| was created for the |workorderitems|
        Nothing more needs to be done.
        """
        assert self.can_close()
        self.status = self.STATUS_CLOSED

    def change_status(self, new_status):
        """
        Change the status of this work order

        Using this function you can change the status is several steps.

        :returns: if the status was changed
        :raises: :exc:`stoqlib.exceptions.InvalidStatus` if the status cannot be changed
        """
        if self.status == WorkOrder.STATUS_WORK_FINISHED:
            raise InvalidStatus(
                _("This work order has already been finished, it cannot be modified."))

        # This is the logic order of status changes, this is the flow/ordering
        # of the status that should be used
        status_order = [WorkOrder.STATUS_OPENED,
                        WorkOrder.STATUS_APPROVED,
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
                if not self.can_start():
                    raise InvalidStatus(
                        _("This work order cannot be started"))
                self.start()

            if next_status == WorkOrder.STATUS_WORK_FINISHED:
                if not self.can_finish():
                    raise InvalidStatus(
                        _('This work order cannot be finished'))
                self.finish()

            if next_status == WorkOrder.STATUS_APPROVED:
                if not self.can_approve():
                    raise InvalidStatus(
                        _("This work order cannot be approved, it's already in progress"))
                self.approve()

            if next_status == WorkOrder.STATUS_OPENED:
                if not self.can_undo_approval():
                    raise InvalidStatus(
                        _('This work order cannot be re-opened'))
                self.undo_approval()

            # We've reached our goal, bail out
            if next_status == new_status:
                break

    @classmethod
    def find_by_sale(cls, store, sale):
        """Returns all |workorders| associated with the given |sale|.

        :param sale: The |sale| used to filter the existing |workorders|
        :resturn: An iterable with all work orders:
        :rtype: resultset
        """
        return store.find(cls, sale=sale)

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
    _PersonOriginalBranch = ClassAlias(Person, "person_original_branch")
    _PersonCurrentBranch = ClassAlias(Person, "person_current_branch")
    _CompanyOriginalBranch = ClassAlias(Company, "company_original_branch")
    _CompanyCurrentBranch = ClassAlias(Company, "company_current_branch")
    _PersonClient = ClassAlias(Person, "person_client")
    _PersonSalesPerson = ClassAlias(Person, "person_salesperson")

    #: the |workorder| object
    work_order = WorkOrder

    #: the |workordercategory| object
    category = WorkOrderCategory

    #: the |client| object
    client = Client

    # WorkOrder
    id = WorkOrder.id
    identifier = WorkOrder.identifier
    status = WorkOrder.status
    equipment = WorkOrder.equipment
    open_date = WorkOrder.open_date
    approve_date = WorkOrder.approve_date
    finish_date = WorkOrder.finish_date

    # WorkOrderCategory
    category_name = WorkOrderCategory.name
    category_color = WorkOrderCategory.color

    # Client
    client_name = _PersonClient.name

    # SalesPerson
    salesperson_name = _PersonSalesPerson.name

    # Branch
    branch_name = Coalesce(NullIf(_CompanyOriginalBranch.fancy_name, u''),
                           _PersonOriginalBranch.name)
    current_branch_name = Coalesce(NullIf(_CompanyCurrentBranch.fancy_name, u''),
                                   _PersonCurrentBranch.name)

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

        LeftJoin(WorkOrderCategory,
                 WorkOrder.category_id == WorkOrderCategory.id),

        LeftJoin(_WorkOrderItemsSummary,
                 Field('_work_order_items', 'order_id') == WorkOrder.id),
    ]

    @classmethod
    def post_search_callback(cls, sresults):
        select = sresults.get_select_expr(Count(1), Sum(cls.total))
        return ('count', 'sum'), select

    @classmethod
    def find_by_current_branch(cls, store, branch):
        return store.find(cls, WorkOrder.current_branch_id == branch.id)


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
    package_notes = WorkOrderPackageItem.notes

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

    clause = In(WorkOrder.status, [WorkOrder.STATUS_APPROVED,
                                   WorkOrder.STATUS_WORK_FINISHED])


class WorkOrderFinishedView(WorkOrderView):
    """A view for finished |workorders|

    This is the same as :class:`.WorkOrderView`, but only finished
    orders are showed here.
    """

    clause = WorkOrder.status == WorkOrder.STATUS_WORK_FINISHED


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
