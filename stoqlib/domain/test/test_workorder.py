# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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

import contextlib

import mock

from stoqlib.exceptions import InvalidStatus, NeedReason
from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.workorder import (WorkOrder, WorkOrderItem,
                                      WorkOrderPackage, WorkOrderPackageItem,
                                      WorkOrderCategory, WorkOrderView,
                                      WorkOrderWithPackageView,
                                      WorkOrderApprovedAndFinishedView,
                                      WorkOrderFinishedView,
                                      WorkOrderPackageView,
                                      WorkOrderPackageSentView)
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib.dateutils import localdate


def _combine(iter1, iter2):
    for j in iter2:
        for i in iter1:
            yield (i, j)


class TestWorkOrderPackage(DomainTest):
    def testBranchValidation(self):
        package = self.create_workorder_package()
        with self.assertRaisesRegexp(
                ValueError,
                "The source branch and destination branch can't be equal"):
            package.destination_branch = package.source_branch

    def testQuantity(self):
        package = self.create_workorder_package()
        self.assertEqual(package.quantity, 0)

        item = package.add_order(self.create_workorder())
        self.assertEqual(package.quantity, 1)

        self.store.remove(item)
        self.assertEqual(package.quantity, 0)

    def testAddOrder(self):
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

    def testCanSend(self):
        package = self.create_workorder_package()
        for status in WorkOrderPackage.statuses.keys():
            package.status = status
            if status == WorkOrderPackage.STATUS_OPENED:
                self.assertTrue(package.can_send())
            else:
                self.assertFalse(package.can_send())

    def testCanReceived(self):
        package = self.create_workorder_package()
        for status in WorkOrderPackage.statuses.keys():
            package.status = status
            if status == WorkOrderPackage.STATUS_SENT:
                self.assertTrue(package.can_receive())
            else:
                self.assertFalse(package.can_receive())

    @mock.patch('stoqlib.domain.workorder.localnow')
    def testSend(self, localnow):
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
    def testReceive(self, localnow):
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
    def testGetDescription(self):
        category = WorkOrderCategory(self.store, name=u'xxx')
        self.assertEqual(category.get_description(), u'xxx')


class TestWorkOrderItem(DomainTest):
    def testGetRemainingQuantity(self):
        branch = self.create_branch()
        sellable = self.create_sellable()
        self.create_storable(product=sellable.product, branch=branch, stock=30)
        workorder = self.create_workorder(branch=branch)

        item = workorder.add_sellable(sellable, quantity=10)
        self.assertEqual(item.get_remaining_quantity(), 20)
        item.sync_stock()
        self.assertEqual(item.get_remaining_quantity(), 20)

        item.quantity = 20
        self.assertEqual(item.get_remaining_quantity(), 10)
        item.sync_stock()
        self.assertEqual(item.get_remaining_quantity(), 10)

    def testTotal(self):
        sellable = self.create_sellable()
        workorder = self.create_workorder()
        workorderitem = WorkOrderItem(self.store, price=10, quantity=15,
                                      order=workorder, sellable=sellable)
        self.assertEqual(workorderitem.total, 150)

    def testGetFromSaleItem(self):
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


class TestWorkOrder(DomainTest):
    def testGetTotalAmount(self):
        workorder = self.create_workorder()
        self.assertEqual(workorder.get_total_amount(), 0)
        workorder.add_sellable(self.create_sellable(), quantity=1, price=10)
        self.assertEqual(workorder.get_total_amount(), 10)
        workorder.add_sellable(self.create_sellable(), quantity=5, price=20)
        self.assertEqual(workorder.get_total_amount(), 110)

    def testStatusStr(self):
        workorder = self.create_workorder()
        for status, status_str in WorkOrder.statuses.items():
            workorder.status = status
            self.assertEqual(workorder.status_str, status_str)

    def testAddItem(self):
        sellable = self.create_sellable()
        item = WorkOrderItem(self.store, sellable=sellable)
        workorder = self.create_workorder()
        workorder.add_item(item)
        self.assertEqual(item.order, workorder)

        self.assertRaises(AssertionError, workorder.add_item, item)

    def testGetItems(self):
        sellable = self.create_sellable()
        item1 = WorkOrderItem(self.store, sellable=sellable)
        item2 = WorkOrderItem(self.store, sellable=sellable)
        workorder = self.create_workorder()
        workorder.add_item(item1)
        workorder.add_item(item2)

        self.assertEqual(set(workorder.get_items()), set([item1, item2]))

    def testRemove(self):
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

        # Only item1 will sync stock. The other one is to test it being
        # removed without ever decreasing the stock
        item1.sync_stock()
        self.assertEqual(
            product1.storable.get_balance_for_branch(workorder.branch), 5)
        self.assertEqual(
            product2.storable.get_balance_for_branch(workorder.branch), 10)

        for item in [item1, item2]:
            with mock.patch.object(self.store, 'remove') as remove:
                workorder.remove_item(item)
                remove.assert_called_once_with(item)
                storable = item.sellable.product.storable
                # Everything should be back to the stock, like
                # the item never existed
                self.assertEqual(
                    storable.get_balance_for_branch(workorder.branch), 10)

    def testAddSellable(self):
        sellable = self.create_sellable(price=50)
        workorder = self.create_workorder()

        item1 = workorder.add_sellable(sellable)
        item2 = workorder.add_sellable(sellable, price=60)
        item3 = workorder.add_sellable(sellable, quantity=2)

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

    def testSyncStock(self):
        product1 = self.create_product(stock=100)
        storable1 = product1.storable
        product2 = self.create_product(stock=100)
        storable2 = product2.storable

        workorder = self.create_workorder()
        item1 = workorder.add_sellable(product1.sellable, quantity=5)
        item2 = workorder.add_sellable(product2.sellable, quantity=10)

        with contextlib.nested(
                mock.patch.object(item1, 'sync_stock'),
                mock.patch.object(item2, 'sync_stock')) as (sync_stock1,
                                                            sync_stock2):
            original_sync_stock = WorkOrderItem.sync_stock
            # We are mocking to test if they were called just once.
            # Put original on side effect so it will be called too
            sync_stock1.side_effect = lambda: original_sync_stock(item1)
            sync_stock2.side_effect = lambda: original_sync_stock(item2)

            workorder.sync_stock()
            sync_stock1.assert_called_once()
            sync_stock2.assert_called_once()

            # item1 should have removed 5 from stock, leaving it with 95
            self.assertEqual(
                storable1.get_balance_for_branch(workorder.branch), 95)
            # item2 should have removed 10 from stock, leaving it with 90
            self.assertEqual(
                storable2.get_balance_for_branch(workorder.branch), 90)

            item1.quantity = 10
            item2.quantity = 5
            sync_stock1.reset_mock()
            sync_stock2.reset_mock()
            workorder.sync_stock()
            sync_stock1.assert_called_once()
            sync_stock2.assert_called_once()

            # item1 should have removed 10 from stock, leaving it with 90
            self.assertEqual(
                storable1.get_balance_for_branch(workorder.branch), 90)
            # item2 should have removed 5 from stock, leaving it with 95
            self.assertEqual(
                storable2.get_balance_for_branch(workorder.branch), 95)

    def testIsInTransport(self):
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

    def testIsApproved(self):
        workorder = self.create_workorder()
        for status in WorkOrder.statuses.keys():
            workorder.status = status
            if status in [WorkOrder.STATUS_WORK_WAITING,
                          WorkOrder.STATUS_WORK_IN_PROGRESS,
                          WorkOrder.STATUS_WORK_FINISHED,
                          WorkOrder.STATUS_CLOSED]:
                self.assertTrue(workorder.is_approved())
            else:
                self.assertFalse(workorder.is_approved())

    def testIsFinished(self):
        workorder = self.create_workorder()
        self.assertEqual(workorder.estimated_finish, None)
        for status in WorkOrder.statuses.keys():
            workorder.status = status
            if status in [WorkOrder.STATUS_WORK_FINISHED,
                          WorkOrder.STATUS_CLOSED]:
                self.assertTrue(workorder.is_finished())
            else:
                self.assertFalse(workorder.is_finished())

    @mock.patch('stoqlib.domain.workorder.localtoday')
    def testIsLate(self, localtoday):
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
                          WorkOrder.STATUS_CLOSED]:
                self.assertFalse(workorder.is_late())
            else:
                self.assertTrue(workorder.is_late())

    def testCanCancel(self):
        sellable = self.create_sellable()
        for status in WorkOrder.statuses.keys():
            workorder = self.create_workorder()
            workorder.status = status

            item = workorder.add_sellable(sellable)
            # This should be False even at any state since there're items
            self.assertFalse(workorder.can_cancel())
            workorder.remove_item(item)

            # After adding, only STATUS_WORK_IN_PROGRESS should be True
            if status in [WorkOrder.STATUS_WORK_FINISHED,
                          WorkOrder.STATUS_CLOSED]:
                self.assertFalse(workorder.can_cancel())
            else:
                self.assertTrue(workorder.can_cancel())

    def testCanApprove(self):
        workorder = self.create_workorder()
        for status in WorkOrder.statuses.keys():
            workorder.status = status
            if status == WorkOrder.STATUS_OPENED:
                self.assertTrue(workorder.can_approve())
            else:
                self.assertFalse(workorder.can_approve())

    def testCanPause(self):
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

    def testCanWork(self):
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

            if status == WorkOrder.STATUS_WORK_WAITING:
                self.assertTrue(workorder.can_work())
            else:
                self.assertFalse(workorder.can_work())

    def testCanFinish(self):
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

            if status in [WorkOrder.STATUS_WORK_IN_PROGRESS,
                          WorkOrder.STATUS_WORK_WAITING]:
                self.assertTrue(workorder.can_finish())
            else:
                self.assertFalse(workorder.can_finish())

    def testCanClose(self):
        workorder = self.create_workorder()
        for status in WorkOrder.statuses.keys():
            workorder.status = status

            # Rejected cannot close
            workorder.is_rejected = True
            self.assertFalse(workorder.can_close())
            workorder.is_rejected = False
            # In transport cannot close
            with mock.patch.object(workorder, 'is_in_transport', new=lambda: True):
                self.assertFalse(workorder.can_close())

            if status == WorkOrder.STATUS_WORK_FINISHED:
                self.assertTrue(workorder.can_close())
            else:
                self.assertFalse(workorder.can_close())

    def testCanReopen(self):
        workorder = self.create_workorder()
        for status in WorkOrder.statuses.keys():
            workorder.status = status

            if status == WorkOrder.STATUS_WORK_FINISHED:
                self.assertTrue(workorder.can_reopen())
            else:
                self.assertFalse(workorder.can_reopen())

    def testCanReject(self):
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

    def testCanUndoRejection(self):
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

    def testReject(self):
        workorder = self.create_workorder()
        workorder.approve()
        self.assertFalse(workorder.is_rejected)
        workorder.reject(reason=u'Reject reason')
        self.assertTrue(workorder.is_rejected)

    def testUndoRejection(self):
        workorder = self.create_workorder()
        workorder.approve()
        workorder.reject(reason=u'Reject reason')
        self.assertTrue(workorder.is_rejected)
        workorder.undo_rejection(u'Undo reject reason')
        self.assertFalse(workorder.is_rejected)

    def testCancel(self):
        workorder = self.create_workorder()
        self.assertNotEqual(workorder.status, WorkOrder.STATUS_CANCELLED)

        workorder.cancel()
        self.assertEqual(workorder.status, WorkOrder.STATUS_CANCELLED)

    @mock.patch('stoqlib.domain.workorder.localnow')
    def testApprove(self, localnow):
        localnow.return_value = localdate(2012, 1, 1)
        workorder = self.create_workorder()
        self.assertNotEqual(workorder.status, WorkOrder.STATUS_WORK_WAITING)
        self.assertEqual(workorder.approve_date, None)

        workorder.approve()
        self.assertEqual(workorder.status, WorkOrder.STATUS_WORK_WAITING)
        self.assertEqual(workorder.approve_date,
                         self.fake.datetime.datetime.now())

    def testPause(self):
        workorder = self.create_workorder()
        workorder.approve()
        workorder.work()
        self.assertEqual(workorder.status, WorkOrder.STATUS_WORK_IN_PROGRESS)

        workorder.pause(reason=u'Pause reason')
        self.assertEqual(workorder.status, WorkOrder.STATUS_WORK_WAITING)

    def testWork(self):
        workorder = self.create_workorder()
        workorder.approve()
        self.assertNotEqual(workorder.status, WorkOrder.STATUS_WORK_IN_PROGRESS)

        workorder.work()
        self.assertEqual(workorder.status, WorkOrder.STATUS_WORK_IN_PROGRESS)

    @mock.patch('stoqlib.domain.workorder.localnow')
    def testFinish(self, localnow):
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

    def testReopen(self):
        workorder = self.create_workorder()
        workorder.approve()
        workorder.work()
        workorder.add_sellable(self.create_sellable())
        workorder.finish()
        self.assertEqual(workorder.status, WorkOrder.STATUS_WORK_FINISHED)

        workorder.reopen(reason=u"Reopen reason")
        self.assertEqual(workorder.status, WorkOrder.STATUS_WORK_IN_PROGRESS)

    def testClose(self):
        workorder = self.create_workorder()
        workorder.approve()
        workorder.work()
        workorder.add_sellable(self.create_sellable())
        workorder.finish()
        self.assertNotEqual(workorder.status, WorkOrder.STATUS_CLOSED)

        workorder.close()
        self.assertEqual(workorder.status, WorkOrder.STATUS_CLOSED)

    def testChangeStatus(self):
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

    def testChangeStatusReverse(self):
        # FIXME: Improve this test by adding more status change cases
        workorder = self.create_workorder()
        workorder.change_status(WorkOrder.STATUS_WORK_IN_PROGRESS)

        with self.assertRaises(NeedReason) as se:
            workorder.change_status(WorkOrder.STATUS_WORK_WAITING)
        self.assertEquals(str(se.exception),
                          'A reason is needed to pause the work order')

    def testFindBySale(self):
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


class _TestWorkOrderView(DomainTest):
    # The view being tested
    view = None

    # The status that will be used to do some base tests on views, since
    # some of them define a clause based on status
    default_status = []

    # Status that should not appear on the view. If empty, all status are
    # assumed to be able to appear
    excluded_status = []

    # Just a facility for all default/excluded status
    all_status = default_status + excluded_status

    def testFind(self):
        workorders_ids = set()
        for status in self.all_status:
            wo = self.create_workorder()
            wo.status = status

            # Only those items will apear on the view
            if status in self.default_status:
                workorders_ids.add(wo.id)

        self.assertEqual(
            workorders_ids,
            set([wo.id for wo in self.store.find(self.view)]))

    def testFindByCurrentBranch(self):
        branch = self.create_branch()
        workorders_ids = set()

        for status, set_branch in _combine(self.all_status, [True, False]):
            wo = self.create_workorder()
            wo.status = status
            # Half of default/excluded will set current branch
            if set_branch:
                wo.current_branch = branch
            # But only those in default status should appear
            if set_branch and status in self.default_status:
                workorders_ids.add(wo.id)

        workorders = self.view.find_by_current_branch(self.store, branch)
        self.assertEqual(workorders_ids, set([wo.id for wo in workorders]))

    def testValues(self):
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

    def testPostSearchCallback(self):
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
    default_status = [WorkOrder.STATUS_OPENED]


class TestWorkWithPackageView(TestWorkOrderView):
    view = WorkOrderWithPackageView

    def testFindByPackage(self):
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
        self.assertEqual(workorders_ids, set([wo.id for wo in workorders]))

        workorders = self.view.find_by_package(self.store, package2)
        self.assertEqual(workorders.count(), 0)


class TestWorkOrderApprovedAndFinishedView(_TestWorkOrderView):
    view = WorkOrderApprovedAndFinishedView
    default_status = [WorkOrder.STATUS_WORK_WAITING,
                      WorkOrder.STATUS_WORK_FINISHED]
    excluded_status = [k for k in WorkOrder.statuses.keys() if
                       k not in default_status]


class TestWorkOrderFinishedView(_TestWorkOrderView):
    view = WorkOrderFinishedView
    default_status = [WorkOrder.STATUS_WORK_FINISHED]
    excluded_status = [k for k in WorkOrder.statuses.keys() if
                       k not in default_status]


class _TestWorkOrderPackageView(DomainTest):
    # The view being tested
    view = None

    # The status that will be used to do some base tests on views, since
    # some of them define a clause based on status
    default_status = []

    # Status that should not appear on the view. If empty, all status are
    # assumed to be able to appear
    excluded_status = []

    # Just a facility for all default/excluded status
    all_status = default_status + excluded_status

    def testFind(self):
        packages_ids = set()

        for status in self.all_status:
            package = self.create_workorder_package()
            package.status = status

            # Only those items will apear on the view
            if status in self.default_status:
                packages_ids.add(package.id)

        self.assertEqual(
            packages_ids,
            set([package.id for package in self.store.find(self.view)]))

    def testFindByDestinationBranch(self):
        branch = self.create_branch()
        packages_ids = set()

        for status, set_branch in _combine(self.all_status, [True, False]):
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
                         set([package.id for package in packages]))

    def testValues(self):
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
    excluded_status = [k for k in WorkOrderPackage.statuses.keys() if
                       k not in default_status]
