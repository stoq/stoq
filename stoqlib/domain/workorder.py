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

import datetime

from kiwi.currency import currency
from storm.expr import Count, LeftJoin, Alias, Select, Sum, Coalesce
from storm.references import Reference, ReferenceSet
from storm.store import AutoReload
from zope.interface import implements

from stoqlib.database.expr import Field
from stoqlib.database.properties import (IntCol, DateTimeCol, UnicodeCol,
                                         PriceCol, DecimalCol, QuantityCol)
from stoqlib.database.viewable import Viewable
from stoqlib.domain.base import Domain
from stoqlib.domain.interfaces import IDescribable, IContainer
from stoqlib.domain.person import Client, Person
from stoqlib.domain.product import StockTransactionHistory
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


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
    """A |workorder|'s item

    This is an item in a |workorder|. That is, a |product| or a |service|
    (here referenced by their respective |sellable|s) used on the work
    and that will be after used to compose the |saleitem|s of the |sale|.

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/work_order_item.html>`__
    """

    __storm_table__ = 'work_order_item'

    #: |sellable|'s quantity used on the |workorder|
    quantity = QuantityCol(default=0)

    #: price of the |sellable|, this is how much the |client| is going
    #: to be charged for the sellable. This includes discounts and markup.
    price = PriceCol()

    sellable_id = IntCol()
    #: the |sellable| of this item, either a |service| or a |product|
    sellable = Reference(sellable_id, 'Sellable.id')

    order_id = IntCol()
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
    #: :obj:`.id` when displaying a numerical representation of this object to
    #: the user, in dialogs, lists, reports and such.
    identifier = IntCol(default=AutoReload)

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
    open_date = DateTimeCol(default_factory=datetime.datetime.now)

    #: date this work was approved (set by :obj:`.approve`)
    approve_date = DateTimeCol(default=None)

    #: date this work was finished (set by :obj:`.finish`)
    finish_date = DateTimeCol(default=None)

    branch_id = IntCol()
    #: the |branch| holding the equipment and responsible for the work
    branch = Reference(branch_id, 'Branch.id')

    quote_responsible_id = IntCol(default=None)
    #: the |user| responsible for the :obj:`.defect_detected`
    quote_responsible = Reference(quote_responsible_id, 'LoginUser.id')

    execution_responsible_id = IntCol(default=None)
    #: the |user| responsible for the execution of the work
    execution_responsible = Reference(execution_responsible_id, 'LoginUser.id')

    client_id = IntCol(default=None)
    #: the |client|, owner of the equipment
    client = Reference(client_id, 'Client.id')

    category_id = IntCol(default=None)
    #: the |workordercategory| this work belongs
    category = Reference(category_id, 'WorkOrderCategory.id')

    sale_id = IntCol(default=None)
    #: the |sale| created after this work is finished
    sale = Reference(sale_id, 'Sale.id')

    order_items = ReferenceSet('id', 'WorkOrderItem.order_id')

    @property
    def status_str(self):
        return self.statuses[self.status]

    @property
    def order_number_str(self):
        # FIXME: Add branch acronym name in front
        return u'%05d' % self.identifier

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

    def add_sellable(self, sellable, price=None, quantity=1):
        """Adds a sellable to this work order

        :param sellable: the |sellable| being added
        :param price: the price the sellable will be sold when
            finishing this work order
        :param quantity: the sellable's quantity
        :returns: the created |workorderitem|
        """
        if price is None:
            price = sellable.base_price

        item = WorkOrderItem(store=self.store,
                             sellable=sellable,
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

    def is_finished(self):
        """Checks if this work order is finished

        A work order is finished when the work that needs to be done
        on it finished, so this will be ``True`` when :obj:`.status` is
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

        today = datetime.date.today()
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
        self.approve_date = datetime.datetime.now()
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
        self.finish_date = datetime.datetime.now()
        self.status = self.STATUS_WORK_FINISHED

    def close(self):
        """Closes this work order

        This order's task is done, the |client| got the equipment
        back and a |sale| was created for the |workorderitems|s.
        Nothing more needs to be done.
        """
        assert self.can_close()
        self.status = self.STATUS_CLOSED


_WorkOrderItemsSummary = Alias(Select(
    columns=[
        WorkOrderItem.order_id,
        Alias(Sum(WorkOrderItem.quantity), 'quantity'),
        Alias(Sum(WorkOrderItem.quantity * WorkOrderItem.price), 'total')],
    tables=[WorkOrderItem],
    group_by=[WorkOrderItem.order_id]),
    '_work_order_items')


class WorkOrderView(Viewable):
    """A view for |workorder|s

    This is used to get the most information of a |workorder|
    without doing lots of database queries.
    """

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
    client_name = Person.name

    # WorkOrderItem
    quantity = Coalesce(Field('_work_order_items', 'quantity'), 0)
    total = Coalesce(Field('_work_order_items', 'total'), 0)

    tables = [
        WorkOrder,
        LeftJoin(Client, WorkOrder.client_id == Client.id),
        LeftJoin(Person, Client.person_id == Person.id),
        LeftJoin(WorkOrderCategory,
                 WorkOrder.category_id == WorkOrderCategory.id),
        LeftJoin(_WorkOrderItemsSummary,
                 Field('_work_order_items', 'order_id') == WorkOrder.id),
        ]

    @classmethod
    def post_search_callback(cls, sresults):
        select = sresults.get_select_expr(Count(1), Sum(cls.total))
        return ('count', 'sum'), select


class WorkOrderFinishedView(WorkOrderView):
    """A view for finished |workorder|s

    This is the same as :class:`.WorkOrderView`, but only finished
    orders are showed here.
    """

    clause = WorkOrder.status == WorkOrder.STATUS_WORK_FINISHED
