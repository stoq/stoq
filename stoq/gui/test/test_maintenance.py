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

import datetime

import mock
import gtk

from stoqlib.api import api
from stoqlib.domain.workorder import WorkOrderItem, WorkOrder

from stoq.gui.maintenance import MaintenanceApp
from stoq.gui.test.baseguitest import BaseGUITest


class TestMaintenance(BaseGUITest):
    def testInitial(self):
        for i in xrange(2):
            wo = self.create_workorder()
            wo.identifier = 666 + i
            wo.open_date = datetime.datetime(2013, 1, 1)

        app = self.create_app(MaintenanceApp, u'maintenance')
        self.assertEqual(len(app.results), 2)

        self.check_app(app, u'maintenance')

    @mock.patch('stoq.gui.maintenance.yesno')
    @mock.patch('stoq.gui.maintenance.api.new_store')
    def test_cancel_workorder_dont_confirm(self, new_store, yesno):
        new_store.return_value = self.store

        self.clean_domain([WorkOrderItem, WorkOrder])
        workorder = self.create_workorder()

        api.sysparam(self.store).update_parameter(u'SMART_LIST_LOADING', u'0')
        app = self.create_app(MaintenanceApp, u'maintenance')

        olist = app.results
        olist.select(olist[0])

        # Initial status for the order is Opened
        self.assertEquals(workorder.status, WorkOrder.STATUS_OPENED)
        self.assertSensitive(app, ['Cancel'])

        with mock.patch.object(self.store, 'close'):
            with mock.patch.object(self.store, 'commit'):
                # Click the cancel order, but dont confirm the change
                yesno.return_value = False
                self.activate(app.Cancel)

                yesno.assert_called_once_with(u"This will cancel the selected "
                                              "order. Are you sure?",
                                              gtk.RESPONSE_NO, u"Cancel order",
                                              u"Don't cancel")

                # Status should not be altered. ie, its still opened
                self.assertEquals(workorder.status, WorkOrder.STATUS_OPENED)

    @mock.patch('stoq.gui.maintenance.yesno')
    @mock.patch('stoq.gui.maintenance.api.new_store')
    def test_cancel_workorder_confirm(self, new_store, yesno):
        new_store.return_value = self.store

        self.clean_domain([WorkOrderItem, WorkOrder])
        workorder = self.create_workorder()

        api.sysparam(self.store).update_parameter(u'SMART_LIST_LOADING', u'0')
        app = self.create_app(MaintenanceApp, u'maintenance')

        olist = app.results
        olist.select(olist[0])

        # Initial status for the order is Opened
        self.assertEquals(workorder.status, WorkOrder.STATUS_OPENED)
        self.assertSensitive(app, ['Cancel'])

        with mock.patch.object(self.store, 'close'):
            with mock.patch.object(self.store, 'commit'):
                # Click the cancel order, and confirm the change
                yesno.return_value = True
                self.activate(app.Cancel)

                yesno.assert_called_once_with(u"This will cancel the selected "
                                              u"order. Are you sure?",
                                              gtk.RESPONSE_NO, u"Cancel order",
                                              u"Don't cancel")

                # Status should be updated to cancelled.
                self.assertEquals(workorder.status, WorkOrder.STATUS_CANCELLED)

    @mock.patch('stoq.gui.maintenance.yesno')
    @mock.patch('stoq.gui.maintenance.api.new_store')
    def test_finish_workorder_dont_confirm(self, new_store, yesno):
        new_store.return_value = self.store

        self.clean_domain([WorkOrderItem, WorkOrder])
        workorder = self.create_workorder()

        # Setted WorkOrder status for Work in Progress
        workorder.status = WorkOrder.STATUS_WORK_IN_PROGRESS

        api.sysparam(self.store).update_parameter(u'SMART_LIST_LOADING', u'0')
        app = self.create_app(MaintenanceApp, u'maintenance')

        olist = app.results
        olist.select(olist[0])

        self.assertNotSensitive(app, ['Finish'])
        workorder.add_sellable(self.create_sellable())
        # Selecting again will update actions sensitivity
        olist.select(olist[0])
        self.assertSensitive(app, ['Finish'])
        # Initial status for the order is Opened
        self.assertEquals(workorder.status, WorkOrder.STATUS_WORK_IN_PROGRESS)
        self.assertTrue(workorder.can_finish())

        with mock.patch.object(self.store, 'close'):
            with mock.patch.object(self.store, 'commit'):
                # Click the finish order, but dont confirm the change
                yesno.return_value = False
                self.activate(app.Finish)

                yesno.assert_called_once_with(u"This will finish the selected "
                                              "order, marking the work as done."
                                              " Are you sure?",
                                              gtk.RESPONSE_NO, u"Finish order",
                                              u"Don't finish")

        # Status should not be altered. ie, its still in Progress
        self.assertEquals(workorder.status, WorkOrder.STATUS_WORK_IN_PROGRESS)

    @mock.patch('stoq.gui.maintenance.yesno')
    @mock.patch('stoq.gui.maintenance.api.new_store')
    def test_finish_workorder_confirm(self, new_store, yesno):
        new_store.return_value = self.store

        self.clean_domain([WorkOrderItem, WorkOrder])
        workorder = self.create_workorder()

        # Setted WorkOrder Status for work in Progress
        workorder.status = WorkOrder.STATUS_WORK_IN_PROGRESS

        api.sysparam(self.store).update_parameter(u'SMART_LIST_LOADING', u'0')
        app = self.create_app(MaintenanceApp, u'maintenance')

        olist = app.results
        olist.select(olist[0])

        self.assertNotSensitive(app, ['Finish'])
        workorder.add_sellable(self.create_sellable())
        # Selecting again will update actions sensitivity
        olist.select(olist[0])
        self.assertSensitive(app, ['Finish'])
        # The status for the order in Progress
        self.assertEquals(workorder.status, WorkOrder.STATUS_WORK_IN_PROGRESS)

        with mock.patch.object(self.store, 'close'):
            with mock.patch.object(self.store, 'commit'):
                # Click the finish order, and confirm the change
                yesno.return_value = True
                self.activate(app.Finish)

                yesno.assert_called_once_with(u"This will finish the selected "
                                              "order, marking the work as done."
                                              " Are you sure?",
                                              gtk.RESPONSE_NO, u"Finish order",
                                              u"Don't finish")

        # status should be updated to Finished
        self.assertEquals(workorder.status, WorkOrder.STATUS_WORK_FINISHED)
