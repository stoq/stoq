# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013-2015 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

__tests__ = 'stoqlib/domain/workorder.py'

import contextlib
import mock

from stoqlib.exceptions import InvalidStatus, NeedReason
from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.product import StockTransactionHistory
from stoqlib.domain.workorder import (WorkOrder, WorkOrderItem,
                                      WorkOrderPackage, WorkOrderPackageItem,
                                      WorkOrderCategory, WorkOrderView,
                                      WorkOrderWithPackageView,
                                      WorkOrderApprovedAndFinishedView,
                                      WorkOrderFinishedView,
                                      WorkOrderPackageView,
                                      WorkOrderPackageSentView,
                                      WorkOrderHistory,
                                      WorkOrderHistoryView)
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib.dateutils import localdate


def _combine(iter1, iter2):
    for j in iter2:
        for i in iter1:
            yield (i, j)


class TestWorkOrderPackage(DomainTest):
    def test_branch_validation(self):
        package = self.create_workorder_package()
        with self.assertRaisesRegexp(
                ValueError,
                "The source branch and destination branch can't be equal"):
            package.destination_branch = package.source_branch

    def test_quantity(self):
        package = self.create_workorder_package()
        self.assertEqual(package.quantity, 0)

        item = package.add_order(self.create_workorder())
        self.assertEqual(package.quantity, 1)

        self.store.remove(item)
        self.assertEqual(package.quantity, 0)

    def test_add_order(self):
        package = self.create_workorder_package()
        workorder = self.create_workorder()
        workorder.current_branch = self.create_branch()
        with self.assertRaisesRegexp(
                ValueError,
                "The order <WorkOrder u'[0-9a-f-]+'> is not in the source branch"):
            package.add_order(workorder)

        workorder.current_branch = package.source_branch
        item = package.add_order(workorder)
        self.assertTrue(isinstance(item, WorkOrderPackageItem))
        self.assertEqual(item.order, workorder)
        self.assertEqual(item.package, package)

        with self.assertRaisesRegexp(
                ValueError,
                ("The order <WorkOrder u'[0-9a-f-]+'> is already on "
                 "the package <WorkOrderPackage u'[0-9a-f-]+'>")):
            package.add_order(workorder)

    def test_can_send(self):
        package = self.create_workorder_package()
        for status in WorkOrderPackage.statuses.keys():
            package.status = status
            if status == WorkOrderPackage.STATUS_OPENED:
                self.assertTrue(package.can_send())
            else:
                self.assertFalse(package.can_send())

    def test_can_received(self):
        package = self.create_workorder_package()
        for status in WorkOrderPackage.statuses.keys():
            package.status = status
            if status == WorkOrderPackage.STATUS_SENT:
                self.assertTrue(package.can_receive())
            else:
                self.assertFalse(package.can_receive())

    @mock.patch('stoqlib.domain.workorder.localnow')
    def test_send(self, localnow):
        localnow.return_value = localdate(2013, 1, 1)

        package = self.create_workorder_package()
        package.destination_branch = self.create_branch()
        workorder1 = self.create_workorder()
        workorder2 = self.create_workorder()

        with mock.patch('stoqlib.domain.workorder.get_current_branch') as gcb:
            gcb.return_value = self.create_branch()
            with self.assertRaisesRegexp(
                    ValueError,
                    ("This package's source branch is <Branch u'[0-9a-f-]+'> "
                     "and you are in <Branch u'[0-9a-f-]+'>. It's not possible "
                     "to send a package outside the source branch")):
                package.send()

        with self.assertRaisesRegexp(
                ValueError, "There're no orders to send"):
            package.send()

        for order in [workorder1, workorder2]:
            self.assertNotEqual(order.branch, None)
            self.assertEqual(order.branch, order.current_branch)
            package.add_order(order)

        self.assertEqual(package.status, WorkOrderPackage.STATUS_OPENED)
        self.assertEqual(package.send_date, None)
        package.send()
        self.assertEqual(package.status, WorkOrderPackage.STATUS_SENT)
        self.assertEqual(package.send_date, localdate(2013, 1, 1))

        for order in [workorder1, workorder2]:
            self.assertEqual(order.current_branch, None)

    @mock.patch('stoqlib.domain.workorder.localnow')
    def test_receive(self, localnow):
        localnow.return_value = localdate(2013, 1, 1)

        package = self.create_workorder_package(
            source_branch=self.create_branch())
        package.destination_branch = get_current_branch(self.store)
        workorder1 = self.create_workorder(current_branch=package.source_branch)
        workorder2 = self.create_workorder(current_branch=package.source_branch)

        # Mimic WorkOrderPackage.send
        for order in [workorder1, workorder2]:
            package.add_order(order)
            order.current_branch = None
        package.status = WorkOrderPackage.STATUS_SENT

        with mock.patch('stoqlib.domain.workorder.get_current_branch') as gcb:
            gcb.return_value = self.create_branch()
            with self.assertRaisesRegexp(
                    ValueError,
                    ("This package's destination branch is <Branch u'[0-9a-f-]+'> "
                     "and you are in <Branch u'[0-9a-f-]+'>. It's not possible "
                     "to receive a package outside the destination branch")):
                package.receive()

        self.assertEqual(package.receive_date, None)
        package.receive()
        self.assertEqual(package.status, WorkOrderPackage.STATUS_RECEIVED)
        self.assertEqual(package.receive_date, localdate(2013, 1, 1))

        for order in [workorder1, workorder2]:
            self.assertEqual(order.current_branch, package.destination_branch)


class TestWorkOrderCategory(DomainTest):
    def test_get_description(self):
        category = WorkOrderCategory(self.store, name=u'xxx')
        self.assertEqual(category.get_description(), u'xxx')


class TestWorkOrderItem(DomainTest):
    def test_total(self):
        sellable = self.create_sellable()
        workorder = self.create_workorder()
        workorderitem = WorkOrderItem(self.store, price=10, quantity=15,
                                      order=workorder, sellable=sellable)
        self.assertEqual(workorderitem.total, 150)

    def test_get_from_sale_item(self):
        sale_item = self.create_sale_item()

        # There is no work order item yet.
        wo_item = WorkOrderItem.get_from_sale_item(self.store, sale_item)
        self.assertEquals(wo_item, None)

        # Create one work order
        item = WorkOrderItem(store=self.store, sellable=sale_item.sellable)

        # They are still not related.
        wo_item = WorkOrderItem.get_from_sale_item(self.store, sale_item)
        self.assertEquals(wo_item, None)

        # After relating them, it should be found.
        item.sale_item = sale_item
        wo_item = WorkOrderItem.get_from_sale_item(self.store, sale_item)
        self.assertEquals(wo_item, item)

    def test_reserve(self):
        item = self.create_work_order_item()
        item_without_storable = self.create_work_order_item()
        item.quantity = 20
        item_without_storable.quantity = 20
        storable = self.create_storable(product=item.sellable.product,
                                        branch=item.order.branch)

        storable.increase_stock(10, item.order.branch,
                                StockTransactionHistory.TYPE_INITIAL, None)
        self.assertEqual(item.quantity_decreased, 0)
        item.reserve(6)
        self.assertEqual(item.quantity_decreased, 6)
        self.assertEqual(storable.get_balance_for_branch(item.order.branch), 4)

        with self.assertRaisesRegexp(
                ValueError, "Trying to reserve more than unreserved quantity"):
            item.reserve(50)

        self.assertEqual(item_without_storable.quantity_decreased, 0)
        item_without_storable.reserve(4)
        self.assertEqual(item_without_storable.quantity_decreased, 4)

    def test_reserve_with_sale(self):
        sale = self.create_sale()
        work_order = self.create_workorder(branch=sale.branch)

        storable = self.create_storable(branch=sale.branch, stock=20)
        sale_item = sale.add_sellable(storable.product.sellable, quantity=5)
        wo_item = work_order.add_sellable(storable.product.sellable, quantity=5)
        wo_item.sale_item = sale_item

        self.assertEqual(sale_item.quantity_decreased, 0)

        # When some stock is reserved for a work order item, the quantity
        # reserved for the sale item should be the same
        wo_item.reserve(4)
        self.assertEqual(sale_item.quantity_decreased, 4)

    def test_return_to_stock(self):
        item = self.create_work_order_item()
        item_without_storable = self.create_work_order_item()
        item.quantity = 20
        item.quantity_decreased = 20
        item_without_storable.quantity = 20
        item_without_storable.quantity_decreased = 20
        storable = self.create_storable(product=item.sellable.product,
                                        branch=item.order.branch)

        item.return_to_stock(6)
        self.assertEqual(item.quantity_decreased, 14)
        self.assertEqual(storable.get_balance_for_branch(item.order.branch), 6)

        with self.assertRaisesRegexp(
                ValueError, "Trying to return more quantity than reserved"):
            item.return_to_stock(50)

        item_without_storable.return_to_stock(4)
        self.assertEqual(item_without_storable.quantity_decreased, 16)

        # Work order with sale
        sale = self.create_sale()
        work_order = self.create_workorder()
        product = self.create_product(stock=10)

        branch = sale.branch
        storable = product.storable
        self.assertEquals(storable.get_balance_for_branch(branch), 10)

        sale_item = sale.add_sellable(product.sellable, quantity=3)
        wo_item = work_order.add_sellable(product.sellable, quantity=3)
        wo_item.sale_item = sale_item
        wo_item.reserve(3)
        self.assertEquals(wo_item.quantity_decreased, 3)
        self.assertEquals(storable.get_balance_for_branch(branch), 7)

        wo_item.return_to_stock(2)
        self.assertEquals(wo_item.quantity_decreased, 1)
        self.assertEquals(storable.get_balance_for_branch(branch), 9)


class TestWorkOrder(DomainTest):
    def test_get_total_amount(self):
        workorder = self.create_workorder()
        self.assertEqual(workorder.get_total_amount(), 0)
        workorder.add_sellable(self.create_sellable(), quantity=1, price=10)
        self.assertEqual(workorder.get_total_amount(), 10)
        workorder.add_sellable(self.create_sellable(), quantity=5, price=20)
        self.assertEqual(workorder.get_total_amount(), 110)

    def test_status_str(self):
        workorder = self.create_workorder()
        for status, status_str in WorkOrder.statuses.items():
            workorder.status = status
            self.assertEqual(workorder.status_str, status_str)

    def test_add_item(self):
        sellable = self.create_sellable()
        item = WorkOrderItem(self.store, sellable=sellable)
        workorder = self.create_workorder()
        workorder.add_item(item)
        self.assertEqual(item.order, workorder)

        self.assertRaises(AssertionError, workorder.add_item, item)

    def test_get_items(self):
        sellable = self.create_sellable()
        item1 = WorkOrderItem(self.store, sellable=sellable)
        item2 = WorkOrderItem(self.store, sellable=sellable)
        workorder = self.create_workorder()
        workorder.add_item(item1)
        workorder.add_item(item2)

        self.assertEqual(set(workorder.get_items()), set([item1, item2]))

    def test_remove(self):
        workorder = self.create_workorder()
        product1 = self.create_product(stock=10, branch=workorder.branch)
        product2 = self.create_product(stock=10, branch=workorder.branch)
        item1 = WorkOrderItem(self.store, sellable=product1.sellable,
                              quantity=5)
        item2 = WorkOrderItem(self.store, sellable=product1.sellable,
                              quantity=5)

        for item in [item1, item2]:
            self.assertRaises(AssertionError, workorder.remove_item, item)
        workorder.add_item(item1)
        workorder.add_item(item2)

        # Only item1 will reserve stock. The other one is to test it being
        # removed without ever decreasing the stock
        item1.reserve(item1.quantity)
        self.assertEqual(
            product1.storable.get_balance_for_branch(workorder.branch), 5)
        self.assertEqual(
            product2.storable.get_balance_for_branch(workorder.branch), 10)

        for item in [item1, item2]:
            workorder.remove_item(item)
            storable = item.sellable.product.storable
            # Everything should be back to the stock, like
            # the item never existed
            self.assertEqual(
                storable.get_balance_for_branch(workorder.branch), 10)

        with self.sysparam(SYNCHRONIZED_MODE=True):
            item = self.create_work_order_item()
            order = item.order

            before_remove = self.store.find(WorkOrderItem).count()
            order.remove_item(item)
            after_remove = self.store.find(WorkOrderItem).count()

            # The item should still be on the database
            self.assertEqual(before_remove, after_remove)

            # But not related to the loan
            self.assertEquals(self.store.find(WorkOrderItem, order=order).count(), 0)

    def test_add_sellable(self):
        sellable = self.create_sellable(price=50)
        workorder = self.create_workorder()

        with mock.patch.object(workorder, 'validate_batch') as validate_batch:
            item1 = workorder.add_sellable(sellable)
            validate_batch.assert_called_once_with(None, sellable=sellable)
            validate_batch.reset_mock()

            item2 = workorder.add_sellable(sellable, price=60)
            validate_batch.assert_called_once_with(None, sellable=sellable)
            validate_batch.reset_mock()

            item3 = workorder.add_sellable(sellable, quantity=2)
            validate_batch.assert_called_once_with(None, sellable=sellable)
            validate_batch.reset_mock()

        for item in [item1, item2, item3]:
            self.assertEqual(item.order, workorder)
            self.assertEqual(item.sellable, sellable)

        self.assertEqual(item1.price, 50)
        self.assertEqual(item2.price, 60)
        self.assertEqual(item3.price, 50)

        self.assertEqual(item1.quantity, 1)
        self.assertEqual(item2.quantity, 1)
        self.assertEqual(item3.quantity, 2)

        # make sure we have those (and only those) items on workorder
        self.assertEqual(set(workorder.order_items),
                         set([item1, item2, item3]))

        # If there's a sale, validate_batch should not be called
        with mock.patch.object(workorder, 'validate_batch') as validate_batch:
            workorder.sale = self.create_sale()
            workorder.add_sellable(sellable)
            self.assertEqual(validate_batch.call_count, 0)

    def test_is_in_transport(self):
        workorder = self.create_workorder()
        branch = self.create_branch()
        for status in WorkOrder.statuses.keys():
            workorder.status = status
            # For any status, if the order's current_branch is not None,
            # it's not in transport
            workorder.current_branch = branch
            self.assertFalse(workorder.is_in_transport())
            # But if the order's current_branch is None, it it
            workorder.current_branch = None
            self.assertTrue(workorder.is_in_transport())

    def test_is_approved(self):
        workorder = self.create_workorder()
        for status in WorkOrder.statuses.keys():
            workorder.status = status
            if status in [WorkOrder.STATUS_WORK_WAITING,
                          WorkOrder.STATUS_WORK_IN_PROGRESS,
                          WorkOrder.STATUS_WORK_FINISHED,
                          WorkOrder.STATUS_DELIVERED]:
                self.assertTrue(workorder.is_approved())
            else:
                self.assertFalse(workorder.is_approved())

    def test_is_finished(self):
        workorder = self.create_workorder()
        self.assertEqual(workorder.estimated_finish, None)
        for status in WorkOrder.statuses.keys():
            workorder.status = status
            if status in [WorkOrder.STATUS_WORK_FINISHED,
                          WorkOrder.STATUS_DELIVERED]:
                self.assertTrue(workorder.is_finished())
            else:
                self.assertFalse(workorder.is_finished())

    @mock.patch('stoqlib.domain.workorder.localtoday')
    def test_is_late(self, localtoday):
        localtoday.return_value = localdate(2012, 1, 1)
        workorder = self.create_workorder()
        self.assertEqual(workorder.estimated_finish, None)
        for status in WorkOrder.statuses.keys():
            workorder.status = status
            # If we have no estimated_finish, we are not late
            self.assertFalse(workorder.is_late())

        # datetime.today will expand to 2012, so this is in the future
        workorder.estimated_finish = localdate(2013, 1, 1)
        for status in WorkOrder.statuses.keys():
            workorder.status = status
            self.assertFalse(workorder.is_late())

        # datetime.today will expand to 2012, so this is in the past
        workorder.estimated_finish = localdate(2011, 1, 1)
        for status in WorkOrder.statuses.keys():
            workorder.status = status
            if status in [WorkOrder.STATUS_WORK_FINISHED,
                          WorkOrder.STATUS_DELIVERED]:
                self.assertFalse(workorder.is_late())
            else:
                self.assertTrue(workorder.is_late())

    def test_can_cancel(self):
        workorder = self.create_workorder()
        for status in WorkOrder.statuses.keys():
            workorder.status = status

            # After adding, only STATUS_WORK_IN_PROGRESS should be True
            if status in [WorkOrder.STATUS_WORK_FINISHED,
                          WorkOrder.STATUS_DELIVERED,
                          WorkOrder.STATUS_CANCELLED]:
                self.assertFalse(workorder.can_cancel())
            else:
                self.assertTrue(workorder.can_cancel())

        workorder = self.create_workorder()
        self.assertTrue(workorder.can_cancel())

        workorder.sale = self.create_sale()
        self.assertFalse(workorder.can_cancel())

    def test_can_approve(self):
        workorder = self.create_workorder()
        for status in WorkOrder.statuses.keys():
            workorder.status = status
            if status == WorkOrder.STATUS_OPENED:
                self.assertTrue(workorder.can_approve())
            else:
                self.assertFalse(workorder.can_approve())

    def test_can_pause(self):
        workorder = self.create_workorder()
        for status in WorkOrder.statuses.keys():
            workorder.status = status

            # Rejected cannot pause
            workorder.is_rejected = True
            self.assertFalse(workorder.can_pause())
            workorder.is_rejected = False
            # In transport cannot pause
            with mock.patch.object(workorder, 'is_in_transport', new=lambda: True):
                self.assertFalse(workorder.can_pause())

            if status == WorkOrder.STATUS_WORK_IN_PROGRESS:
                self.assertTrue(workorder.can_pause())
            else:
                self.assertFalse(workorder.can_pause())

    def test_can_work(self):
        workorder = self.create_workorder()
        for status in WorkOrder.statuses.keys():
            workorder.status = status

            # Rejected cannot work
            workorder.is_rejected = True
            self.assertFalse(workorder.can_work())
            workorder.is_rejected = False
            # In transport cannot work
            with mock.patch.object(workorder, 'is_in_transport', new=lambda: True):
                self.assertFalse(workorder.can_work())
            # Cannot work on other branch than the current one
            with mock.patch('stoqlib.domain.workorder.get_current_branch',
                            new=lambda store: self.create_branch()):
                self.assertFalse(workorder.can_work())

            if status == WorkOrder.STATUS_WORK_WAITING:
                self.assertTrue(workorder.can_work())
            else:
                self.assertFalse(workorder.can_work())

    def test_can_finish(self):
        workorder = self.create_workorder()
        for status in WorkOrder.statuses.keys():
            workorder.status = status

            # Rejected cannot finish
            workorder.is_rejected = True
            self.assertFalse(workorder.can_finish())
            workorder.is_rejected = False
            # In transport cannot finish
            with mock.patch.object(workorder, 'is_in_transport', new=lambda: True):
                self.assertFalse(workorder.can_finish())

            old_branch = workorder.current_branch
            workorder.current_branch = self.create_branch()
            self.assertFalse(workorder.can_finish())
            workorder.current_branch = old_branch

            if status in [WorkOrder.STATUS_WORK_IN_PROGRESS,
                          WorkOrder.STATUS_WORK_WAITING]:
                self.assertTrue(workorder.can_finish())
            else:
                self.assertFalse(workorder.can_finish())

    def test_can_close(self):
        workorder = self.create_workorder()
        wo_item = workorder.add_sellable(self.create_sellable(), quantity=1)
        for status in WorkOrder.statuses.keys():
            workorder.status = status

            # Rejected cannot close
            workorder.is_rejected = True
            self.assertFalse(workorder.can_close())
            workorder.is_rejected = False
            # In transport cannot close
            with mock.patch.object(workorder, 'is_in_transport', new=lambda: True):
                self.assertFalse(workorder.can_close())

            old_branch = workorder.current_branch
            workorder.current_branch = self.create_branch()
            self.assertFalse(workorder.can_close())
            workorder.current_branch = old_branch

            # Cannot close on other branch than the current one
            with mock.patch('stoqlib.domain.workorder.get_current_branch',
                            new=lambda store: self.create_branch()):
                self.assertFalse(workorder.can_close())
            # Cannot close if not all items have been decreased
            wo_item.quantity_decreased = 0
            self.assertFalse(workorder.can_close())
            wo_item.quantity_decreased = wo_item.quantity

            if status == WorkOrder.STATUS_WORK_FINISHED:
                self.assertTrue(workorder.can_close())
            else:
                self.assertFalse(workorder.can_close())

    def test_can_reopen(self):
        workorder = self.create_workorder()
        for status in WorkOrder.statuses.keys():
            workorder.status = status

            if status in [WorkOrder.STATUS_WORK_FINISHED,
                          WorkOrder.STATUS_DELIVERED]:
                self.assertTrue(workorder.can_reopen())
            else:
                self.assertFalse(workorder.can_reopen())

    def test_can_reject(self):
        workorder = self.create_workorder()
        for status in WorkOrder.statuses.keys():
            workorder.status = status

            # If already rejected, it can't be rejected again
            workorder.is_rejected = True
            self.assertFalse(workorder.can_close())
            workorder.is_rejected = False
            # In transport cannot reject
            with mock.patch.object(workorder, 'is_in_transport', new=lambda: True):
                self.assertFalse(workorder.can_reject())

            if status in [WorkOrder.STATUS_WORK_WAITING,
                          WorkOrder.STATUS_WORK_IN_PROGRESS,
                          WorkOrder.STATUS_WORK_FINISHED]:
                self.assertTrue(workorder.can_reject())
            else:
                self.assertFalse(workorder.can_reject())

    def test_can_undo_rejection(self):
        workorder = self.create_workorder()
        for status in WorkOrder.statuses.keys():
            workorder.status = status

            # In transport cannot undo rejection
            with mock.patch.object(workorder, 'is_in_transport', new=lambda: True):
                self.assertFalse(workorder.can_undo_rejection())

            workorder.is_rejected = True
            self.assertTrue(workorder.can_undo_rejection())
            workorder.is_rejected = False
            self.assertFalse(workorder.can_undo_rejection())

    def test_reject(self):
        workorder = self.create_workorder()
        workorder.approve()
        self.assertFalse(workorder.is_rejected)
        workorder.reject(reason=u'Reject reason')
        self.assertTrue(workorder.is_rejected)

    def test_undo_rejection(self):
        workorder = self.create_workorder()
        workorder.approve()
        workorder.reject(reason=u'Reject reason')
        self.assertTrue(workorder.is_rejected)
        workorder.undo_rejection(u'Undo reject reason')
        self.assertFalse(workorder.is_rejected)

    def test_cancel(self):
        workorder = self.create_workorder()
        sellable = self.create_sellable()
        storable = self.create_storable(sellable.product, stock=10,
                                        branch=workorder.branch)
        item1 = workorder.add_sellable(sellable, quantity=2)
        item2 = workorder.add_sellable(sellable, quantity=4)
        item3 = workorder.add_sellable(sellable, quantity=7)
        item1.reserve(2)
        item2.reserve(3)
        self.assertEqual(storable.get_balance_for_branch(workorder.branch), 5)
        self.assertNotEqual(workorder.status, WorkOrder.STATUS_CANCELLED)

        workorder.cancel()
        self.assertEqual(workorder.status, WorkOrder.STATUS_CANCELLED)
        self.assertEqual(storable.get_balance_for_branch(workorder.branch), 10)
        for item in [item1, item2, item3]:
            self.assertEqual(item.quantity_decreased, 0)

    @mock.patch('stoqlib.domain.workorder.localnow')
    def test_approve(self, localnow):
        localnow.return_value = localdate(2012, 1, 1)
        workorder = self.create_workorder()
        self.assertNotEqual(workorder.status, WorkOrder.STATUS_WORK_WAITING)
        self.assertEqual(workorder.approve_date, None)

        workorder.approve()
        self.assertEqual(workorder.status, WorkOrder.STATUS_WORK_WAITING)
        self.assertEqual(workorder.approve_date,
                         self.fake.datetime.datetime.now())

    def test_pause(self):
        workorder = self.create_workorder()
        workorder.approve()
        workorder.work()
        self.assertEqual(workorder.status, WorkOrder.STATUS_WORK_IN_PROGRESS)

        workorder.pause(reason=u'Pause reason')
        self.assertEqual(workorder.status, WorkOrder.STATUS_WORK_WAITING)

    def test_work(self):
        workorder = self.create_workorder()
        workorder.approve()
        self.assertNotEqual(workorder.status, WorkOrder.STATUS_WORK_IN_PROGRESS)

        workorder.work()
        self.assertEqual(workorder.status, WorkOrder.STATUS_WORK_IN_PROGRESS)

    @mock.patch('stoqlib.domain.workorder.localnow')
    def test_finish(self, localnow):
        branch = get_current_branch(self.store)
        localnow.return_value = localdate(2012, 1, 1)
        workorder = self.create_workorder()
        workorder.approve()
        workorder.work()
        self.assertNotEqual(workorder.status, WorkOrder.STATUS_WORK_FINISHED)
        self.assertEqual(workorder.finish_date, None)

        workorder.add_sellable(self.create_sellable())
        workorder.finish()
        self.assertEqual(workorder.status, WorkOrder.STATUS_WORK_FINISHED)
        self.assertEqual(workorder.finish_date,
                         self.fake.datetime.datetime.now())
        self.assertEquals(workorder.execution_branch, branch)

        path = 'stoqlib.database.runtime.get_current_branch'
        with mock.patch(path) as current_branch:
            new_branch = self.create_branch()
            current_branch.return_value = new_branch
            workorder.reopen(reason=u'reopen test')
            workorder.finish()
            # Checking that we are not overwriting the value
            self.assertEquals(workorder.execution_branch, branch)

    def test_reopen(self):
        workorder = self.create_workorder()
        workorder.approve()
        workorder.work()
        workorder.add_sellable(self.create_sellable())
        workorder.finish()
        self.assertEqual(workorder.status, WorkOrder.STATUS_WORK_FINISHED)

        workorder.reopen(reason=u"Reopen reason")
        self.assertEqual(workorder.status, WorkOrder.STATUS_WORK_IN_PROGRESS)

    def test_close(self):
        workorder = self.create_workorder()
        workorder.approve()
        workorder.work()
        workorder.add_sellable(self.create_sellable())
        for item in workorder.order_items:
            item.reserve(item.quantity)
        workorder.finish()
        self.assertNotEqual(workorder.status, WorkOrder.STATUS_DELIVERED)

        workorder.close()
        self.assertEqual(workorder.status, WorkOrder.STATUS_DELIVERED)

    def test_change_status(self):
        workorder = self.create_workorder()

        # Open
        self.assertEquals(workorder.status, WorkOrder.STATUS_OPENED)
        with self.assertRaises(InvalidStatus) as se:
            workorder.change_status(WorkOrder.STATUS_OPENED)
        self.assertEquals(str(se.exception), 'This work order cannot be re-opened')

        # Waiting material
        workorder.change_status(WorkOrder.STATUS_WORK_WAITING)
        with self.assertRaises(InvalidStatus) as se:
            workorder.change_status(WorkOrder.STATUS_WORK_WAITING)
        self.assertEquals(str(se.exception),
                          "This work order cannot wait for material")

        # In progress
        workorder.change_status(WorkOrder.STATUS_WORK_IN_PROGRESS)
        with self.assertRaises(InvalidStatus) as se:
            workorder.change_status(WorkOrder.STATUS_WORK_IN_PROGRESS)
        self.assertEquals(str(se.exception),
                          "This work order cannot be worked on")

        # Finished
        prod = self.create_product(stock=100)
        workorder.add_sellable(prod.sellable, quantity=5)

        workorder.change_status(WorkOrder.STATUS_WORK_FINISHED)
        with self.assertRaises(InvalidStatus) as se:
            workorder.change_status(WorkOrder.STATUS_WORK_FINISHED)
        self.assertEquals(str(se.exception),
                          'This work order cannot be finished')

        # Reopen
        with self.assertRaises(NeedReason) as exc:
            workorder.change_status(WorkOrder.STATUS_WORK_IN_PROGRESS)
            self.assertEquals(str(exc),
                              "A reason is needed to reopen the work order")

        workorder.change_status(WorkOrder.STATUS_WORK_IN_PROGRESS,
                                reason=u'reason')

    def test_change_status_reverse(self):
        # FIXME: Improve this test by adding more status change cases
        workorder = self.create_workorder()
        workorder.change_status(WorkOrder.STATUS_WORK_IN_PROGRESS)

        with self.assertRaises(NeedReason) as se:
            workorder.change_status(WorkOrder.STATUS_WORK_WAITING)
        self.assertEquals(str(se.exception),
                          'A reason is needed to pause the work order')

        workorder.change_status(WorkOrder.STATUS_WORK_WAITING,
                                reason=u"Pause")

    def test_find_by_sale(self):
        workorder1 = self.create_workorder()
        workorder2 = self.create_workorder()
        workorder3 = self.create_workorder()

        sale = self.create_sale()
        workorder1.sale = sale
        workorder2.sale = sale

        workorders = list(WorkOrder.find_by_sale(self.store, sale))
        self.assertEquals(len(workorders), 2)
        self.assertIn(workorder1, workorders)
        self.assertIn(workorder2, workorders)
        self.assertNotIn(workorder3, workorders)

    def test_sale_status_changed(self):
        sale = self.create_sale()
        self.add_product(sale)
        sale.order()
        work_order = self.create_workorder()
        work_order.sale = sale

        with self.sysparam(ALLOW_CANCEL_CONFIRMED_SALES=True):
            with contextlib.nested(
                    mock.patch.object(work_order, 'reopen'),
                    mock.patch.object(work_order, 'cancel')) as (reopen, cancel):
                work_order.approve()
                work_order.finish()
                sale.cancel()
                reopen.assert_called_once_with(
                    reason="Reopening work order to cancel the sale")
                cancel.assert_called_with(reason="The sale was cancelled",
                                          ignore_sale=True)


class _TestWorkOrderView(DomainTest):
    # The view being tested
    view = None

    # The status that will be used to do some base tests on views, since
    # some of them define a clause based on status
    default_status = []

    @property
    def excluded_status(self):
        return [k for k in WorkOrder.statuses.keys() if
                k not in self.default_status]

    def test_find(self):
        workorders_ids = set()
        for status in WorkOrder.statuses.keys():
            wo = self.create_workorder()
            wo.status = status

            # Only those items will apear on the view
            if status in self.default_status:
                workorders_ids.add(wo.id)

        self.assertEqual(
            workorders_ids,
            set([wo_.id for wo_ in self.store.find(self.view)]))

    def test_find_by_current_branch(self):
        branch = self.create_branch()
        workorders_ids = set()

        for status, set_branch in _combine(WorkOrder.statuses.keys(),
                                           [True, False]):
            wo = self.create_workorder()
            wo.status = status
            # Half of default/excluded will set current branch
            if set_branch:
                wo.current_branch = branch
            # But only those in default status should appear
            if set_branch and status in self.default_status:
                workorders_ids.add(wo.id)

        workorders = self.view.find_by_current_branch(self.store, branch)
        self.assertEqual(workorders_ids, set([wo_.id for wo_ in workorders]))

    def test_find_by_can_send_to_branch(self):
        current_branch = self.create_branch()
        destination_branch = self.create_branch()

        workorders = set()
        visibles = set()

        for status, is_rejected in _combine(WorkOrder.statuses.keys(),
                                            [True, False]):
            wo = self.create_workorder()
            wo.status = status
            wo.is_rejected = is_rejected

            workorders.add(wo)
            # This is the minimum filter for workorders to appear in the results
            if status in self.default_status:
                visibles.add(wo)

        # The view should be empty here because we didn't set current_branch
        # for any of the work orders
        for can_execute in [True, False]:
            destination_branch.can_execute_foreign_work_orders = can_execute
            results = self.view.find_by_can_send_to_branch(
                self.store, current_branch=current_branch,
                destination_branch=destination_branch)
            self.assertEqual(results.count(), 0)

        for wo in workorders:
            wo.current_branch = current_branch

        # When the destination_branch can execute foreign work orders

        destination_branch.can_execute_foreign_work_orders = True
        results = self.view.find_by_can_send_to_branch(
            self.store, current_branch=current_branch,
            destination_branch=destination_branch)
        self.assertEqual(
            set(wo.id for wo in results),
            set(wo.id for wo in visibles if
                wo.status == WorkOrder.STATUS_WORK_WAITING or wo.is_rejected))

        # When the destination_branch can't execute foreign work orders

        destination_branch.can_execute_foreign_work_orders = False
        results = self.view.find_by_can_send_to_branch(
            self.store, current_branch=current_branch,
            destination_branch=destination_branch)
        # In here no orders should appear since the destination_branch and
        # their creation branches doesn't match
        self.assertEqual(results.count(), 0)

        for wo in workorders:
            wo.branch = destination_branch

        results = self.view.find_by_can_send_to_branch(
            self.store, current_branch=current_branch,
            destination_branch=destination_branch)
        self.assertEqual(
            set(wo.id for wo in results),
            set(wo.id for wo in visibles if
                wo.status == WorkOrder.STATUS_WORK_FINISHED or wo.is_rejected))

    def test_find_pending(self):
        wo1 = self.create_workorder()
        wo1.status = WorkOrder.STATUS_OPENED
        wo2 = self.create_workorder()
        wo2.status = WorkOrder.STATUS_WORK_WAITING
        wo3 = self.create_workorder()
        wo3.status = WorkOrder.STATUS_WORK_IN_PROGRESS
        wo4 = self.create_workorder()
        wo4.status = WorkOrder.STATUS_WORK_FINISHED
        # Those 2 should not appear on the results
        wo5 = self.create_workorder()
        wo5.status = WorkOrder.STATUS_DELIVERED
        wo6 = self.create_workorder()
        wo6.status = WorkOrder.STATUS_CANCELLED

        work_orders = set(wov.work_order for wov in
                          WorkOrderView.find_pending(self.store))
        self.assertEqual(work_orders, set([wo1, wo2, wo3, wo4]))

        wo1.estimated_finish = localdate(2013, 1, 1)
        wo2.estimated_finish = localdate(2013, 2, 1)
        wo3.estimated_finish = localdate(2013, 3, 1)
        wo4.estimated_finish = localdate(2013, 4, 1)
        wo5.estimated_finish = localdate(2013, 1, 1)
        wo6.estimated_finish = localdate(2013, 2, 1)

        # Filtering by start date only
        work_orders = set(wov.work_order for wov in
                          WorkOrderView.find_pending(
                              self.store,
                              start_date=localdate(2013, 1, 1)))
        self.assertEqual(work_orders, set([wo1, wo2, wo3, wo4]))
        work_orders = set(wov.work_order for wov in
                          WorkOrderView.find_pending(
                              self.store,
                              start_date=localdate(2013, 1, 2)))
        self.assertEqual(work_orders, set([wo2, wo3, wo4]))

        # Filtering by end date only
        work_orders = set(wov.work_order for wov in
                          WorkOrderView.find_pending(
                              self.store,
                              end_date=localdate(2013, 1, 2)))
        self.assertEqual(work_orders, set([wo1]))
        work_orders = set(wov.work_order for wov in
                          WorkOrderView.find_pending(
                              self.store,
                              end_date=localdate(2013, 4, 2)))
        self.assertEqual(work_orders, set([wo1, wo2, wo3, wo4]))

        # Filtering by both start and end dates
        work_orders = set(wov.work_order for wov in
                          WorkOrderView.find_pending(
                              self.store,
                              start_date=localdate(2013, 1, 1),
                              end_date=localdate(2013, 4, 2)))
        self.assertEqual(work_orders, set([wo1, wo2, wo3, wo4]))
        work_orders = set(wov.work_order for wov in
                          WorkOrderView.find_pending(
                              self.store,
                              start_date=localdate(2013, 3, 1),
                              end_date=localdate(2013, 4, 2)))
        self.assertEqual(work_orders, set([wo3, wo4]))

    def test_values(self):
        workorder1 = self.create_workorder()
        workorder1.status = self.default_status[0]
        workorder2 = self.create_workorder()
        workorder2.status = self.default_status[0]

        sellable = self.create_sellable()
        workorder1.add_sellable(sellable, quantity=10, price=100)
        workorder1.add_sellable(sellable, quantity=5, price=50)

        workorderview1 = self.store.find(self.view,
                                         id=workorder1.id).one()
        workorderview2 = self.store.find(self.view,
                                         id=workorder2.id).one()

        # This is the sum of quantities and total from the 2 sellables added
        self.assertEqual(workorderview1.quantity, 15)
        self.assertEqual(workorderview1.total, 1250)
        # This should be 0 since no sellables were added
        self.assertEqual(workorderview2.quantity, 0)
        self.assertEqual(workorderview2.total, 0)

    def test_post_search_callback(self):
        sellable = self.create_sellable()

        # Only those 10 will appear on the result
        default_status = (self.default_status * 10)[:10]
        for i, status in enumerate(default_status + self.excluded_status):
            wo = self.create_workorder()
            wo.status = status
            wo.add_sellable(sellable, quantity=i, price=10)

        sresults = self.store.find(self.view)
        postresults = self.view.post_search_callback(sresults)
        self.assertEqual(postresults[0], ('count', 'sum'))
        self.assertEqual(
            self.store.execute(postresults[1]).get_one(), (10, 450))


class TestWorkOrderView(_TestWorkOrderView):
    view = WorkOrderView
    default_status = WorkOrder.statuses.keys()

    def test_equipment(self):
        wo = self.create_workorder(description=u'Foo')

        # Without a sellable, the equipemnt should be only the description
        wo.sellable = None
        wo_view = self.store.find(self.view, self.view.id == wo.id).one()
        self.assertEquals(wo_view.equipment, 'Foo')

        # With a sellable, the equipemnt should be the sellable description +
        # the work order description
        wo.sellable = self.create_sellable(description=u'Bar')
        wo_view = self.store.find(self.view, self.view.id == wo.id).one()
        self.assertEquals(wo_view.equipment, 'Bar - Foo')


class TestWorkWithPackageView(TestWorkOrderView):
    view = WorkOrderWithPackageView

    def test_find_by_package(self):
        package1 = self.create_workorder_package()
        package2 = self.create_workorder_package()

        workorders_ids = set()
        for status, set_package in _combine(self.default_status, [True, False]):
            wo = self.create_workorder()
            wo.status = status
            # Only this half will appear on find_by_package
            if set_package:
                package1.add_order(wo)
                workorders_ids.add(wo.id)

        workorders = self.view.find_by_package(self.store, package1)
        self.assertEqual(workorders_ids, set([wo_.id for wo_ in workorders]))

        workorders = self.view.find_by_package(self.store, package2)
        self.assertEqual(workorders.count(), 0)


class TestWorkOrderApprovedAndFinishedView(_TestWorkOrderView):
    view = WorkOrderApprovedAndFinishedView
    default_status = [WorkOrder.STATUS_WORK_WAITING,
                      WorkOrder.STATUS_WORK_FINISHED]


class TestWorkOrderFinishedView(_TestWorkOrderView):
    view = WorkOrderFinishedView
    default_status = [WorkOrder.STATUS_WORK_FINISHED]


class _TestWorkOrderPackageView(DomainTest):
    # The view being tested
    view = None

    # The status that will be used to do some base tests on views, since
    # some of them define a clause based on status
    default_status = []

    def test_find(self):
        packages_ids = set()

        for status in self.default_status:
            package = self.create_workorder_package()
            package.status = status

            # Only those items will apear on the view
            if status in self.default_status:
                packages_ids.add(package.id)

        self.assertEqual(
            packages_ids,
            set([p.id for p in self.store.find(self.view)]))

    def test_find_by_destination_branch(self):
        branch = self.create_branch()
        packages_ids = set()

        for status, set_branch in _combine(self.default_status, [True, False]):
            package = self.create_workorder_package()
            package.status = status
            # Half of default/excluded will set destination branch
            if set_branch:
                package.destination_branch = branch
            # But only those in default status should appear
            if set_branch and status in self.default_status:
                packages_ids.add(package.id)

        packages = self.view.find_by_destination_branch(self.store, branch)
        self.assertEqual(packages_ids,
                         set([p.id for p in packages]))

    def test_values(self):
        package1 = self.create_workorder_package()
        package1.status = self.default_status[0]
        package2 = self.create_workorder_package()
        package2.status = self.default_status[0]

        for i in xrange(5):
            package2.add_order(self.create_workorder())

        packageview1 = self.store.find(self.view, id=package1.id).one()
        self.assertEqual(packageview1.quantity, 0)

        packageview2 = self.store.find(self.view, id=package2.id).one()
        self.assertEqual(packageview2.quantity, 5)


class TestWorkOrderPackageView(_TestWorkOrderPackageView):
    view = WorkOrderPackageView
    default_status = [WorkOrderPackage.STATUS_OPENED]


class TestWorkOrderPackageSentView(_TestWorkOrderPackageView):
    view = WorkOrderPackageSentView
    default_status = [WorkOrderPackage.STATUS_SENT]


class TestWorkOrderHistoryView(DomainTest):
    def test_find_by_work_order(self):
        work_order = self.create_workorder()
        user = self.create_user()
        WorkOrderHistory(store=self.store,
                         work_order=work_order,
                         user=user,
                         what=u"what!")
        view = WorkOrderHistoryView.find_by_work_order(self.store, work_order).one()
        self.assertEquals(view.user_name, u'individual')
