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

from gi.repository import Gtk
import mock
from nose.exc import SkipTest

from stoqlib.api import api
from stoqlib.domain.workorder import WorkOrderItem, WorkOrder
from stoq.lib.gui.dialogs.workordercategorydialog import WorkOrderCategoryDialog
from stoq.lib.gui.editors.noteeditor import NoteEditor, Note
from stoqlib.reporting.workorder import (WorkOrderReceiptReport,
                                         WorkOrderQuoteReport)
from stoq.lib.gui.search.personsearch import ClientSearch
from stoq.lib.gui.search.productsearch import ProductSearch
from stoq.lib.gui.search.servicesearch import ServiceSearch

from stoq.gui.services import ServicesApp
from stoq.gui.test.baseguitest import BaseGUITest


class TestServices(BaseGUITest):
    def test_initial(self):
        api.sysparam.set_bool(self.store, 'SMART_LIST_LOADING', True)
        for i in range(2):
            wo = self.create_workorder()
            wo.identifier = 666 + i
            wo.open_date = datetime.datetime(2013, 1, 1)

        app = self.create_app(ServicesApp, u'services')
        self.assertEqual(len(app.search.results), 2)

        self.check_app(app, u'services')
        app.deactivate()

    @mock.patch('stoq.lib.gui.actions.base.run_dialog')
    @mock.patch('stoq.lib.gui.actions.workorder.api.new_store')
    def test_cancel_workorder_dont_confirm(self, new_store, run_dialog):
        new_store.return_value = self.store

        self.clean_domain([WorkOrderItem, WorkOrder])
        workorder = self.create_workorder()

        api.sysparam.set_bool(self.store, 'SMART_LIST_LOADING', False)
        app = self.create_app(ServicesApp, u'services')

        olist = app.search.results
        olist.select(olist[0])

        # Initial status for the order is Opened
        self.assertEqual(workorder.status, WorkOrder.STATUS_OPENED)
        self.assertSensitive(app.actions, ['Cancel'])

        with mock.patch.object(self.store, 'close'):
            with mock.patch.object(self.store, 'commit'):
                # Click the cancel order, but dont confirm the change
                run_dialog.return_value = False
                self.activate(app.actions.get_action('Cancel'))

                run_dialog.assert_called_once_with(
                    NoteEditor, None, None,
                    message_text=(u"This will cancel the selected order. "
                                  u"Any reserved items will return to stock. "
                                  u"Are you sure?"),
                    model=Note(), mandatory=True, label_text=u'Reason')

                # Status should not be altered. ie, its still opened
                self.assertEqual(workorder.status, WorkOrder.STATUS_OPENED)
        app.deactivate()

    @mock.patch('stoq.lib.gui.actions.base.run_dialog')
    @mock.patch('stoq.lib.gui.actions.workorder.api.new_store')
    def test_cancel_workorder_confirm(self, new_store, run_dialog):
        new_store.return_value = self.store

        self.clean_domain([WorkOrderItem, WorkOrder])
        workorder = self.create_workorder()

        api.sysparam.set_bool(self.store, 'SMART_LIST_LOADING', False)
        app = self.create_app(ServicesApp, u'services')

        olist = app.search.results
        olist.select(olist[0])

        # Initial status for the order is Opened
        self.assertEqual(workorder.status, WorkOrder.STATUS_OPENED)
        self.assertSensitive(app.actions, ['Cancel'])

        with mock.patch.object(self.store, 'close'):
            with mock.patch.object(self.store, 'commit'):
                # Click the cancel order, and confirm the change
                run_dialog.return_value = Note(notes=u'xxx')
                self.activate(app.actions.get_action('Cancel'))

                run_dialog.assert_called_once_with(
                    NoteEditor, None, None,
                    message_text=(u"This will cancel the selected order. "
                                  u"Any reserved items will return to stock. "
                                  u"Are you sure?"),
                    model=Note(), mandatory=True, label_text=u'Reason')

                # Status should be updated to cancelled.
                self.assertEqual(workorder.status, WorkOrder.STATUS_CANCELLED)
        app.deactivate()

    @mock.patch('stoq.lib.gui.actions.workorder.yesno')
    @mock.patch('stoq.lib.gui.actions.workorder.api.new_store')
    def test_finish_workorder_dont_confirm(self, new_store, yesno):
        new_store.return_value = self.store

        self.clean_domain([WorkOrderItem, WorkOrder])
        workorder = self.create_workorder()

        # Setted WorkOrder status for Work in Progress
        workorder.status = WorkOrder.STATUS_WORK_IN_PROGRESS

        api.sysparam.set_bool(self.store, 'SMART_LIST_LOADING', False)
        app = self.create_app(ServicesApp, u'services')

        olist = app.search.results
        olist.select(olist[0])

        workorder.add_sellable(self.create_sellable())
        for item in workorder.order_items:
            item.reserve(self.current_user, item.quantity)
        # Selecting again will update actions sensitivity
        olist.select(olist[0])
        self.assertSensitive(app.actions, ['Finish'])
        # Initial status for the order is Opened
        self.assertEqual(workorder.status, WorkOrder.STATUS_WORK_IN_PROGRESS)
        self.assertTrue(workorder.can_finish(self.current_branch))

        with mock.patch.object(self.store, 'close'):
            with mock.patch.object(self.store, 'commit'):
                # Click the finish order, but dont confirm the change
                yesno.return_value = False
                self.activate(app.actions.get_action('Finish'))

                yesno.assert_called_once_with(u"This will finish the selected "
                                              "order, marking the work as done."
                                              " Are you sure?",
                                              Gtk.ResponseType.NO, u"Finish order",
                                              u"Don't finish")

        # Status should not be altered. ie, its still in Progress
        self.assertEqual(workorder.status, WorkOrder.STATUS_WORK_IN_PROGRESS)
        app.deactivate()

    @mock.patch('stoq.lib.gui.actions.workorder.yesno')
    @mock.patch('stoq.lib.gui.actions.workorder.api.new_store')
    def test_finish_workorder_confirm(self, new_store, yesno):
        new_store.return_value = self.store

        self.clean_domain([WorkOrderItem, WorkOrder])
        workorder = self.create_workorder()

        # Setted WorkOrder Status for work in Progress
        workorder.status = WorkOrder.STATUS_WORK_IN_PROGRESS

        api.sysparam.set_bool(self.store, 'SMART_LIST_LOADING', False)
        app = self.create_app(ServicesApp, u'services')

        olist = app.search.results
        olist.select(olist[0])

        workorder.add_sellable(self.create_sellable())
        for item in workorder.order_items:
            item.reserve(self.current_user, item.quantity)
        # Selecting again will update actions sensitivity
        olist.select(olist[0])
        self.assertSensitive(app.actions, ['Finish'])
        # The status for the order in Progress
        self.assertEqual(workorder.status, WorkOrder.STATUS_WORK_IN_PROGRESS)

        with mock.patch.object(self.store, 'close'):
            with mock.patch.object(self.store, 'commit'):
                # Click the finish order, and confirm the change
                yesno.return_value = True
                self.activate(app.actions.get_action('Finish'))

                yesno.assert_called_once_with(u"This will finish the selected "
                                              "order, marking the work as done."
                                              " Are you sure?",
                                              Gtk.ResponseType.NO, u"Finish order",
                                              u"Don't finish")

        # status should be updated to Finished
        self.assertEqual(workorder.status, WorkOrder.STATUS_WORK_FINISHED)
        app.deactivate()

    def test_client_search(self):
        app = self.create_app(ServicesApp, u'services')

        with mock.patch.object(app, 'run_dialog') as rd:
            self.activate(app.Clients)
            rd.assert_called_once_with(ClientSearch, app.store,
                                       hide_footer=True)
        app.deactivate()

    def test_on_ViewKanban__toggled(self):
        if True:
            raise SkipTest('Changing to kan ban view is not working in tests')
        app = self.create_app(ServicesApp, u'services')
        self.activate(app.ViewKanban)
        app.deactivate()

    @mock.patch('stoq.gui.services.api.new_store')
    def test_on_Categories__activate(self, new_store):
        new_store.return_value = self.store
        app = self.create_app(ServicesApp, u'services')

        with mock.patch.object(self.store, 'close'):
            with mock.patch.object(app, 'run_dialog') as rd:
                self.activate(app.Categories)
                rd.assert_called_once_with(WorkOrderCategoryDialog, self.store)
        app.deactivate()

    def test_on_Services__activate(self):
        app = self.create_app(ServicesApp, u'services')

        with mock.patch.object(app, 'run_dialog') as rd:
            self.activate(app.Services)
            rd.assert_called_once_with(ServiceSearch, self.store)
        app.deactivate()

    def test_on_Products__activate(self):
        app = self.create_app(ServicesApp, u'services')

        with mock.patch.object(app, 'run_dialog') as rd:
            self.activate(app.Products)
            rd.assert_called_once_with(ProductSearch, self.store,
                                       hide_footer=True, hide_toolbar=True)
        app.deactivate()

    @mock.patch('stoq.gui.services.print_report')
    def _test_on_PrintReceipt(self, print_report):
        workorder = self.create_workorder(description=u'teste')
        workorder.status = WorkOrder.STATUS_WORK_FINISHED

        app = self.create_app(ServicesApp, u'services')
        results = app.search.results
        results.select(results[0])
        self.activate(app.actions.get_action('PrintReceipt'))
        print_report.assert_called_once_with(WorkOrderReceiptReport,
                                             results[0].work_order)
        app.deactivate()

    @mock.patch('stoq.gui.services.print_report')
    def _test_on_PrintQuote(self, print_report):
        workorder = self.create_workorder(description=u'teste')
        workorder.defect_detected = u'quote'
        workorder.status = WorkOrder.STATUS_WORK_FINISHED

        app = self.create_app(ServicesApp, u'services')
        results = app.search.results
        results.select(results[0])
        self.activate(app.actions.get_action('PrintQuote'))
        print_report.assert_called_once_with(WorkOrderQuoteReport,
                                             results[0].work_order)
        app.deactivate()
