# -*- Mode: Python; coding: utf-8 -*-
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
from gi.repository import Gtk
import mock
from stoqlib.lib.objutils import Settable

from stoqlib.database.runtime import StoqlibStore
from stoqlib.database.viewable import Viewable
from stoqlib.domain.person import Person
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.domain.sale import Sale
from stoqlib.domain.workorder import WorkOrderCategory, WorkOrder
from stoq.lib.gui.base.dialogs import run_dialog
from stoq.lib.gui.editors.personeditor import ClientEditor
from stoq.lib.gui.editors.producteditor import ProductEditor
from stoq.lib.gui.editors.workordereditor import WorkOrderEditor
from stoq.lib.gui.events import PrintReportEvent
from stoq.lib.gui.wizards.personwizard import PersonRoleWizard
from stoq.lib.gui.wizards.workorderquotewizard import WorkOrderQuoteWizard
from stoqlib.lib.dateutils import localdate
from stoqlib.lib.parameters import sysparam
from stoqlib.reporting.sale import SaleOrderReport
from stoq.gui.test.baseguitest import BaseGUITest
from stoq.gui.sales import SalesApp
from stoq.gui.services import ServicesApp

from ..medicssearch import OpticalMedicSearch, MedicSalesSearch
from ..opticaldomain import OpticalProduct
from ..opticaleditor import MedicEditor, OpticalWorkOrderEditor, OpticalSupplierEditor
from ..opticalhistory import OpticalPatientDetails
from ..opticalreport import OpticalWorkOrderReceiptReport
from ..opticalui import OpticalUI, OpticalWorkOrderActions
from ..opticalwizard import OpticalSaleQuoteWizard, MedicRoleWizard
from .test_optical_domain import OpticalDomainTest


__tests__ = 'plugins.optical.opticalui.py'


class TestOpticalUI(BaseGUITest, OpticalDomainTest):
    def setUp(self):
        super().setUp()
        self.ui._setup_params()

    @classmethod
    def setUpClass(cls):
        cls.ui = OpticalUI.get_instance()
        BaseGUITest.setUpClass()

    def test_optical_sales(self):
        app = self.create_app(SalesApp, u'sales')
        for sales in app.results:
            sales.open_date = localdate(2012, 1, 1)
            sales.confirm_date = localdate(2012, 2, 3)
            sales.close_date = localdate(2012, 4, 5)
        self.check_app(app, u'sales-optical-plugin')

        app.deactivate()
        self.window.hide_app(empty=True)

    def test_optical_sales_pre_sale(self):
        app = self.create_app(SalesApp, u'sales')
        action = app.OpticalPreSale
        assert action, action
        with mock.patch('plugins.optical.opticalui.run_dialog') as run_dialog_:
            self.activate(action)
            args, kwargs = run_dialog_.call_args
            self.assertEqual(args[0], OpticalSaleQuoteWizard)
            self.assertEqual(args[1], app)
            self.assertTrue(isinstance(args[2], StoqlibStore))

        with mock.patch('plugins.optical.opticalui.warning') as warning_:
            # We need to mock this since it's a cached_function and thus it
            # will return None for some time even if we create an inventory here
            with mock.patch.object(app, 'has_open_inventory') as has_open_inventory:
                has_open_inventory.return_value = True
                self.activate(action)
                warning_.assert_called_once_with(
                    "You cannot create a pre-sale with an open inventory.")
        app.deactivate()

    def test_optical_sales_medic_search(self):
        app = self.create_app(SalesApp, u'sales')
        action = app.OpticalMedicSearch
        assert action, action
        with mock.patch('plugins.optical.opticalui.run_dialog') as run_dialog_:
            self.activate(action)
            args, kwargs = run_dialog_.call_args
            self.assertEqual(args[0], OpticalMedicSearch)
            self.assertEqual(args[1], None)
            self.assertTrue(isinstance(args[2], StoqlibStore))
            self.assertEqual(kwargs['hide_footer'], True)
        app.deactivate()

    def test_optical_sales_medic_sales_search(self):
        app = self.create_app(SalesApp, u'sales')
        action = app.OpticalMedicSaleItems
        assert action, action
        with mock.patch('plugins.optical.opticalui.run_dialog') as run_dialog_:
            self.activate(action)
            args, kwargs = run_dialog_.call_args
            self.assertEqual(args[0], MedicSalesSearch)
            self.assertEqual(args[1], None)
            self.assertTrue(isinstance(args[2], StoqlibStore))
            self.assertEqual(kwargs['hide_footer'], True)
        app.deactivate()

    def test_product_editor(self):
        product = self.create_product(stock=10)
        editor = ProductEditor(store=self.store, model=product)
        self.check_editor(editor, u'editor-product-optical-plugin')

    def test_work_order_editor(self):
        sysparam.set_bool(self.store,
                          'ALLOW_OUTDATED_OPERATIONS',
                          True)

        sale = self.create_sale()
        workorder = self.create_workorder()
        workorder.identifier = 1234
        workorder.open_date = localdate(2012, 1, 1)
        workorder.sale = sale

        editor = WorkOrderEditor(store=self.store, model=workorder)
        self.check_editor(editor, u'editor-work-order-optical-plugin')

        # FIXME: baseditor should probably add an api for getting a list
        #        of buttons
        print_button = editor.main_dialog.action_area.get_children()[0]
        assert print_button.get_label() == Gtk.STOCK_PRINT
        with mock.patch('plugins.optical.opticalui.print_report') as print_report_:
            self.click(print_button)
            print_report_.assert_called_once_with(
                OpticalWorkOrderReceiptReport, [editor.model])

    def test_run_optical_sale_quote_wizard(self):
        sale = self.create_sale()
        sale.status = Sale.STATUS_QUOTE
        sale.add_sellable(self.create_sellable())

        wo_category = WorkOrderCategory(name=u'category', store=self.store)
        workorder = self.create_workorder()
        workorder.category = wo_category
        workorder.sale = sale

        name = 'stoq.lib.gui.base.dialogs.run_dialog_internal'
        with mock.patch(name) as run_dialog_internal:
            # Without a Sale that has workorders -> optical wizard
            run_dialog(WorkOrderQuoteWizard, None, self.store, sale)
            args, kwargs = run_dialog_internal.call_args
            self.assertTrue(isinstance(args[0], OpticalSaleQuoteWizard))

            # Without a Sale, normal wizard
            run_dialog_internal.reset_mock()
            run_dialog(WorkOrderQuoteWizard, None, self.store, None)
            args, kwargs = run_dialog_internal.call_args
            self.assertTrue(isinstance(args[0], WorkOrderQuoteWizard))

    def test_run_medic_role_wizard(self):
        name = 'stoq.lib.gui.base.dialogs.run_dialog_internal'
        with mock.patch(name) as run_dialog_internal:
            run_dialog(PersonRoleWizard, None, self.store, MedicEditor)
            args, kwargs = run_dialog_internal.call_args
            self.assertTrue(isinstance(args[0], MedicRoleWizard))

    def test_person_editor(self):
        sysparam.__init__()
        client = self.create_client()
        editor = ClientEditor(self.store, client, role_type=Person.ROLE_INDIVIDUAL)
        self.check_editor(editor, 'editor-client-optical-plugin')

        with mock.patch('plugins.optical.opticalui.run_dialog') as run_dialog_:
            self.click(editor.patient_history_button)
            run_dialog_.assert_called_once_with(OpticalPatientDetails, editor, self.store, client)

    def test_product_search(self):
        from stoq.lib.gui.search.productsearch import ProductSearch
        from stoq.lib.gui.search.costcentersearch import CostCenterSearch
        # ProductSearch should have new columns
        search = ProductSearch(self.store)
        search.search.refresh()
        self.check_search(search, 'search-optical-product-search')

        # Cost center search does not use a viewable, so it should not have columns
        assert not issubclass(CostCenterSearch.search_spec, Viewable)
        search = CostCenterSearch(self.store)
        search.search.refresh()
        self.check_search(search, 'search-optical-cost-center-search')

    def test_services_app(self):
        product = self.create_product()
        product.manufacturer = self.create_product_manufacturer(u'Empresa Tal')
        workorder = self.create_workorder()
        workorder.identifier = 99412
        workorder.open_date = localdate(2013, 12, 7)
        workorder.sellable = product.sellable

        app = self.create_app(ServicesApp, u'services')
        app.search.refresh()
        self.check_app(app, u'services-optical-plugin')
        app.deactivate()

    @mock.patch('plugins.optical.opticalui.api.new_store')
    @mock.patch('plugins.optical.opticalui.run_dialog')
    def test_edit_optical_details(self, run_dialog, new_store):
        new_store.return_value = self.store

        product = self.create_product()
        work_order = self.create_workorder()
        work_order.identifier = 666
        work_order.open_date = localdate(2014, 1, 31)
        work_order.sellable = product.sellable
        self.create_optical_work_order(work_order)

        app = self.create_app(ServicesApp, u'services')
        app.search.refresh()

        for wo_view in app.search.results:
            if wo_view.work_order == work_order:
                break

        self.assertIsNotNone(wo_view)
        app.search.results.select(wo_view)

        action = OpticalWorkOrderActions.get_instance().get_action('OpticalDetails')
        with contextlib.nested(
                mock.patch.object(self.store, 'commit'),
                mock.patch.object(self.store, 'close')):
            self.activate(action)

        run_dialog.assert_called_once_with(OpticalWorkOrderEditor, None,
                                           self.store, work_order)
        app.deactivate()

    @mock.patch('plugins.optical.opticalui.api.new_store')
    @mock.patch('plugins.optical.opticalui.run_dialog')
    def test_new_purchase_cancel(self, run_dialog, new_store):
        new_store.return_value = self.store

        sale = self.create_sale()
        product = self.create_product()
        work_order = self.create_workorder()
        work_order.status = WorkOrder.STATUS_WORK_IN_PROGRESS
        work_order.sale = sale
        work_order.add_sellable(product.sellable)
        self.create_optical_work_order(work_order)
        app = self.create_app(ServicesApp, u'services')
        app.search.refresh()

        for wo_view in app.search.results:
            if wo_view.work_order == work_order:
                break

        self.assertIsNotNone(wo_view)
        app.search.results.select(wo_view)

        action = OpticalWorkOrderActions.get_instance().get_action('OpticalNewPurchase')
        run_dialog.return_value = False
        with contextlib.nested(
                mock.patch.object(self.store, 'commit'),
                mock.patch.object(self.store, 'close')):
            self.activate(action)

        run_dialog.assert_called_once_with(OpticalSupplierEditor, None,
                                           self.store, work_order)
        app.deactivate()

    @mock.patch('plugins.optical.opticalui.api.new_store')
    @mock.patch('plugins.optical.opticalui.run_dialog')
    def test_new_purchase_confirm(self, run_dialog, new_store):
        new_store.return_value = self.store

        supplier = self.create_supplier()
        sale = self.create_sale()
        product = self.create_product()
        work_order = self.create_workorder()
        work_order.status = WorkOrder.STATUS_WORK_IN_PROGRESS
        work_order.sale = sale
        work_item = work_order.add_sellable(product.sellable)
        self.create_optical_work_order(work_order)
        app = self.create_app(ServicesApp, u'services')
        app.search.refresh()

        for wo_view in app.search.results:
            if wo_view.work_order == work_order:
                break

        self.assertIsNotNone(wo_view)
        app.search.results.select(wo_view)

        # Before the action, there are no purchase orders for this work order
        results = PurchaseOrder.find_by_work_order(self.store, work_order)
        self.assertEquals(results.count(), 0)

        action = OpticalWorkOrderActions.get_instance().get_action('OpticalNewPurchase')
        run_dialog.return_value = Settable(supplier=supplier,
                                           supplier_order='1111',
                                           item=work_item,
                                           is_freebie=True)
        with contextlib.nested(
                mock.patch.object(self.store, 'commit'),
                mock.patch.object(self.store, 'close')):
            self.activate(action)

        run_dialog.assert_called_once_with(OpticalSupplierEditor, None,
                                           self.store, work_order)

        # Now there should be one purchase order
        results = PurchaseOrder.find_by_work_order(self.store, work_order)
        self.assertEquals(results.count(), 1)
        app.deactivate()

    @mock.patch('plugins.optical.opticalui.print_report')
    def test_print_report_event(self, print_report):

        # Emitting with something different from SaleOrderReport
        rv = PrintReportEvent.emit(object)
        self.assertFalse(rv)
        self.assertEqual(print_report.call_count, 0)

        # Emitting with SaleOrderReport, but without workorders
        sale = self.create_sale()
        rv = PrintReportEvent.emit(SaleOrderReport, sale)
        self.assertFalse(rv)
        self.assertEqual(print_report.call_count, 0)

        # Emitting with SaleOrderReport and with workorders
        optical_wo = self.create_optical_work_order()
        optical_wo.work_order.sale = sale
        rv = PrintReportEvent.emit(SaleOrderReport, sale)
        self.assertTrue(rv)
        print_report.assert_called_once_with(OpticalWorkOrderReceiptReport,
                                             [optical_wo.work_order])

    def test_work_order_change_status(self):
        supplier = self.create_supplier()
        product = self.create_product()
        opt_type = OpticalProduct.TYPE_GLASS_LENSES
        optical_product = self.create_optical_product(optical_type=opt_type)
        optical_product.product = product
        sale = self.create_sale()
        sale_item = sale.add_sellable(sellable=product.sellable)
        wo = self.create_workorder()
        work_item = wo.add_sellable(product.sellable)
        work_item.sale_item = sale_item
        wo.sale = sale
        optical_wo = self.create_optical_work_order()
        optical_wo.work_order = wo

        app = self.create_app(ServicesApp, u'services')
        app.search.refresh()

        for wo_view in app.search.results:
            if wo_view.work_order == wo:
                break

        self.assertIsNotNone(wo_view)
        app.search.results.select(wo_view)
        with mock.patch('plugins.optical.opticalui.run_dialog') as run_dialog:
            wo.approve(self.current_user)
            run_dialog.return_value = Settable(supplier=supplier,
                                               supplier_order='1111',
                                               item=work_item,
                                               is_freebie=False)
            wo.work(self.current_branch, self.current_user)
            results = PurchaseOrder.find_by_work_order(wo.store, wo)
            self.assertEquals(len(list(results)), 1)

        wo.finish(self.current_branch, self.current_user)
        app.deactivate()

    def test_work_order_cancel_change_status(self):
        product = self.create_product()
        opt_type = OpticalProduct.TYPE_GLASS_LENSES
        optical_product = self.create_optical_product(optical_type=opt_type)
        optical_product.product = product
        sale = self.create_sale()
        sale_item = sale.add_sellable(sellable=product.sellable)
        wo = self.create_workorder()
        work_item = wo.add_sellable(product.sellable)
        work_item.sale_item = sale_item
        wo.sale = sale
        wo.approve(self.current_user)

        app = self.create_app(ServicesApp, u'services')
        app.search.refresh()

        for wo_view in app.search.results:
            if wo_view.work_order == wo:
                break

        self.assertIsNotNone(wo_view)
        app.search.results.select(wo_view)

        with mock.patch('plugins.optical.opticalui.run_dialog') as run_dialog:
            # No optical work order related to this WO, the dialog doesn't even run
            wo.work(self.current_branch, self.current_user)
            self.assertNotCalled(run_dialog)

        wo.pause(self.current_user, 'Reason')
        optical_wo = self.create_optical_work_order()
        optical_wo.work_order = wo

        with mock.patch('plugins.optical.opticalui.run_dialog') as run_dialog:
            run_dialog.return_value = None
            wo.work(self.current_branch, self.current_user)
            # At this point we didnt create a purchase
            results = PurchaseOrder.find_by_work_order(wo.store, wo)
            self.assertEquals(len(list(results)), 0)
        app.deactivate()
