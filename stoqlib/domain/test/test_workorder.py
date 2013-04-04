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
import datetime

import mock

from stoqlib.domain.workorder import (WorkOrder, WorkOrderItem,
                                      WorkOrderCategory, WorkOrderView,
                                      WorkOrderFinishedView)
from stoqlib.domain.test.domaintest import DomainTest


class TestWorkOrderCategory(DomainTest):
    def testGetDescription(self):
        category = WorkOrderCategory(self.store, name=u'xxx')
        self.assertEqual(category.get_description(), u'xxx')


class TestWorkOrderItem(DomainTest):
    def testTotal(self):
        sellable = self.create_sellable()
        workorder = self.create_workorder()
        workorderitem = WorkOrderItem(self.store, price=10, quantity=15,
                                      order=workorder, sellable=sellable)
        self.assertEqual(workorderitem.total, 150)


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

    @mock.patch('stoqlib.domain.workorder.datetime', DomainTest.fake.datetime)
    def testIsLate(self):
        workorder = self.create_workorder()
        self.assertEqual(workorder.estimated_finish, None)
        for status in WorkOrder.statuses.keys():
            workorder.status = status
            # If we have no estimated_finish, we are not late
            self.assertFalse(workorder.is_late())

        # datetime.today will expand to 2012, so this is in the future
        workorder.estimated_finish = datetime.datetime(2013, 1, 1)
        for status in WorkOrder.statuses.keys():
            workorder.status = status
            self.assertFalse(workorder.is_late())

        # datetime.today will expand to 2012, so this is in the past
        workorder.estimated_finish = datetime.datetime(2011, 1, 1)
        for status in WorkOrder.statuses.keys():
            workorder.status = status
            if status in [WorkOrder.STATUS_WORK_FINISHED,
                          WorkOrder.STATUS_CLOSED]:
                self.assertFalse(workorder.is_late())
            else:
                self.assertTrue(workorder.is_late())

    def testCanCancel(self):
        workorder = self.create_workorder()
        for status in WorkOrder.statuses.keys():
            workorder.status = status
            if status in [WorkOrder.STATUS_OPENED, WorkOrder.STATUS_APPROVED]:
                self.assertTrue(workorder.can_cancel())
            else:
                self.assertFalse(workorder.can_cancel())

    def testCanApprove(self):
        workorder = self.create_workorder()
        for status in WorkOrder.statuses.keys():
            workorder.status = status
            if status == WorkOrder.STATUS_OPENED:
                self.assertTrue(workorder.can_approve())
            else:
                self.assertFalse(workorder.can_approve())

    def testCanUndoApproval(self):
        workorder = self.create_workorder()
        for status in WorkOrder.statuses.keys():
            workorder.status = status
            if status == WorkOrder.STATUS_APPROVED:
                self.assertTrue(workorder.can_undo_approval())
            else:
                self.assertFalse(workorder.can_undo_approval())

    def testCanStart(self):
        workorder = self.create_workorder()
        for status in WorkOrder.statuses.keys():
            workorder.status = status
            if status == WorkOrder.STATUS_APPROVED:
                self.assertTrue(workorder.can_start())
            else:
                self.assertFalse(workorder.can_start())

    def testCanFinish(self):
        sellable = self.create_sellable()
        for status in WorkOrder.statuses.keys():
            workorder = self.create_workorder()
            workorder.status = status

            # This should be False even on STATUS_WORK_IN_PROGRESS, since
            # there're no items on the order
            self.assertFalse(workorder.can_finish())
            workorder.add_sellable(sellable)
            # After adding, only STATUS_WORK_IN_PROGRESS should be True
            if status == WorkOrder.STATUS_WORK_IN_PROGRESS:
                self.assertTrue(workorder.can_finish())
            else:
                self.assertFalse(workorder.can_finish())

    def testCanClose(self):
        workorder = self.create_workorder()
        for status in WorkOrder.statuses.keys():
            workorder.status = status
            if status == WorkOrder.STATUS_WORK_FINISHED:
                self.assertTrue(workorder.can_close())
            else:
                self.assertFalse(workorder.can_close())

    def testCancel(self):
        workorder = self.create_workorder()
        self.assertNotEqual(workorder.status, WorkOrder.STATUS_CANCELLED)

        workorder.cancel()
        self.assertEqual(workorder.status, WorkOrder.STATUS_CANCELLED)

    @mock.patch('stoqlib.domain.workorder.datetime', DomainTest.fake.datetime)
    def testApprove(self):
        workorder = self.create_workorder()
        self.assertNotEqual(workorder.status, WorkOrder.STATUS_APPROVED)
        self.assertEqual(workorder.approve_date, None)

        workorder.approve()
        self.assertEqual(workorder.status, WorkOrder.STATUS_APPROVED)
        self.assertEqual(workorder.approve_date,
                         self.fake.datetime.datetime.now())

    def testUndoApproval(self):
        workorder = self.create_workorder()
        workorder.approve()
        self.assertNotEqual(workorder.status, WorkOrder.STATUS_OPENED)
        self.assertNotEqual(workorder.approve_date, None)

        workorder.undo_approval()
        self.assertEqual(workorder.status, WorkOrder.STATUS_OPENED)
        self.assertEqual(workorder.approve_date, None)

    def testStart(self):
        workorder = self.create_workorder()
        workorder.approve()
        self.assertNotEqual(workorder.status, WorkOrder.STATUS_WORK_IN_PROGRESS)

        workorder.start()
        self.assertEqual(workorder.status, WorkOrder.STATUS_WORK_IN_PROGRESS)

    @mock.patch('stoqlib.domain.workorder.datetime', DomainTest.fake.datetime)
    def testFinish(self):
        workorder = self.create_workorder()
        workorder.approve()
        workorder.start()
        self.assertNotEqual(workorder.status, WorkOrder.STATUS_WORK_FINISHED)
        self.assertEqual(workorder.finish_date, None)

        self.assertRaises(AssertionError, workorder.finish)
        workorder.add_sellable(self.create_sellable())
        workorder.finish()
        self.assertEqual(workorder.status, WorkOrder.STATUS_WORK_FINISHED)
        self.assertEqual(workorder.finish_date,
                         self.fake.datetime.datetime.now())

    def testClose(self):
        workorder = self.create_workorder()
        workorder.approve()
        workorder.start()
        self.assertRaises(AssertionError, workorder.finish)
        workorder.add_sellable(self.create_sellable())
        workorder.finish()
        self.assertNotEqual(workorder.status, WorkOrder.STATUS_CLOSED)

        workorder.close()
        self.assertEqual(workorder.status, WorkOrder.STATUS_CLOSED)


class TestWorkOrderView(DomainTest):
    def testFind(self):
        workorders_ids = set()
        for i in range(10):
            wo = self.create_workorder()
            workorders_ids.add(wo.id)

        self.assertEqual(
            workorders_ids,
            set([wo.id for wo in self.store.find(WorkOrderView)]))

    def testValues(self):
        workorder1 = self.create_workorder()
        workorder2 = self.create_workorder()

        sellable = self.create_sellable()
        workorder1.add_sellable(sellable, quantity=10, price=100)
        workorder1.add_sellable(sellable, quantity=5, price=50)

        workorderview1 = self.store.find(WorkOrderView,
                                         id=workorder1.id).one()
        workorderview2 = self.store.find(WorkOrderView,
                                         id=workorder2.id).one()

        # This is the sum of quantities and total from the 2 sellables added
        self.assertEqual(workorderview1.quantity, 15)
        self.assertEqual(workorderview1.total, 1250)
        # This should be 0 since no sellables were added
        self.assertEqual(workorderview2.quantity, 0)
        self.assertEqual(workorderview2.total, 0)


class TestWorkOrderFinishedView(DomainTest):
    def testFind(self):
        finished_workorders_ids = set()
        for i in range(10):
            wo = self.create_workorder()
            # Mark half of the created work orders as finished
            if i % 2 == 0:
                wo.status = WorkOrder.STATUS_WORK_FINISHED
                finished_workorders_ids.add(wo.id)

        self.assertEqual(
            finished_workorders_ids,
            set([wo.id for wo in self.store.find(WorkOrderFinishedView)]))

    def testPostSearchCallback(self):
        sellable = self.create_sellable()
        for i in range(10):
            wo = self.create_workorder()
            wo.add_sellable(sellable, quantity=i, price=10)

        sresults = self.store.find(WorkOrderView)
        postresults = WorkOrderView.post_search_callback(sresults)
        self.assertEqual(postresults[0], ('count', 'sum'))
        self.assertEqual(
            self.store.execute(postresults[1]).get_one(), (10, 450))
