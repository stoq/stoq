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
import gtk
import mock

from stoqlib.database.runtime import StoqlibStore
from stoqlib.database.viewable import Viewable
from stoqlib.domain.person import Person
from stoqlib.domain.sale import Sale
from stoqlib.domain.workorder import WorkOrderCategory
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.personeditor import ClientEditor
from stoqlib.gui.editors.producteditor import ProductEditor
from stoqlib.gui.editors.workordereditor import WorkOrderEditor
from stoqlib.gui.events import PrintReportEvent
from stoqlib.gui.wizards.personwizard import PersonRoleWizard
from stoqlib.gui.wizards.workorderquotewizard import WorkOrderQuoteWizard
from stoqlib.lib.dateutils import localdate
from stoqlib.lib.parameters import sysparam
from stoqlib.reporting.sale import SaleOrderReport
from stoq.gui.test.baseguitest import BaseGUITest
from stoq.gui.sales import SalesApp
from stoq.gui.services import ServicesApp

from ..medicssearch import OpticalMedicSearch, MedicSalesSearch
from ..opticaleditor import MedicEditor, OpticalWorkOrderEditor
from ..opticalhistory import OpticalPatientDetails
from ..opticalreport import OpticalWorkOrderReceiptReport
from ..opticalui import OpticalUI
from ..opticalwizard import OpticalSaleQuoteWizard, MedicRoleWizard
from .test_optical_domain import OpticalDomainTest


__tests__ = 'plugins.optical.opticalui.py'


class TestOpticalUI(BaseGUITest, OpticalDomainTest):
    @classmethod
    def setUpClass(cls):
        cls.ui = OpticalUI()
        BaseGUITest.setUpClass()

    def test_optical_sales(self):
        app = self.create_app(SalesApp, u'sales')
        for sales in app.results:
            sales.open_date = localdate(2012, 1, 1)
            sales.confirm_date = localdate(2012, 2, 3)
            sales.close_date = localdate(2012, 4, 5)
        self.check_app(app, u'sales-optical-plugin')

        self.window.hide_app(empty=True)

    def test_optical_sales_pre_sale(self):
        app = self.create_app(SalesApp, u'sales')
        action = app.uimanager.get_action(
            '/ui/menubar/ExtraMenubarPH/OpticalMenu/OpticalPreSale')
        assert action, action
        with mock.patch('plugins.optical.opticalui.run_dialog') as run_dialog_:
            self.activate(action)
            args, kwargs = run_dialog_.call_args
            self.assertEquals(args[0], OpticalSaleQuoteWizard)
            self.assertEquals(args[1], app)
            self.assertTrue(isinstance(args[2], StoqlibStore))

        with mock.patch('plugins.optical.opticalui.warning') as warning_:
            # We need to mock this since it's a cached_function and thus it
            # will return None for some time even if we create an inventory here
            with mock.patch.object(app, 'has_open_inventory') as has_open_inventory:
                has_open_inventory.return_value = True
                self.activate(action)
                warning_.assert_called_once_with(
                    "You cannot create a pre-sale with an open inventory.")

    def test_optical_sales_medic_search(self):
        app = self.create_app(SalesApp, u'sales')
        action = app.uimanager.get_action(
            '/ui/menubar/ExtraMenubarPH/OpticalMenu/OpticalMedicSearch')
        assert action, action
        with mock.patch('plugins.optical.opticalui.run_dialog') as run_dialog_:
            self.activate(action)
            args, kwargs = run_dialog_.call_args
            self.assertEquals(args[0], OpticalMedicSearch)
            self.assertEquals(args[1], None)
            self.assertTrue(isinstance(args[2], StoqlibStore))
            self.assertEquals(kwargs['hide_footer'], True)

    def test_optical_sales_medic_sales_search(self):
        app = self.create_app(SalesApp, u'sales')
        action = app.uimanager.get_action(
            '/ui/menubar/ExtraMenubarPH/OpticalMenu/OpticalMedicSaleItems')
        assert action, action
        with mock.patch('plugins.optical.opticalui.run_dialog') as run_dialog_:
            self.activate(action)
            args, kwargs = run_dialog_.call_args
            self.assertEquals(args[0], MedicSalesSearch)
            self.assertEquals(args[1], None)
            self.assertTrue(isinstance(args[2], StoqlibStore))
            self.assertEquals(kwargs['hide_footer'], True)

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
        assert print_button.get_label() == gtk.STOCK_PRINT
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

        name = 'stoqlib.gui.base.dialogs.run_dialog_internal'
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
        name = 'stoqlib.gui.base.dialogs.run_dialog_internal'
        with mock.patch(name) as run_dialog_internal:
            run_dialog(PersonRoleWizard, None, self.store, MedicEditor)
            args, kwargs = run_dialog_internal.call_args
            self.assertTrue(isinstance(args[0], MedicRoleWizard))

    def test_person_editor(self):
        client = self.create_client()
        editor = ClientEditor(self.store, client, role_type=Person.ROLE_INDIVIDUAL)
        self.check_editor(editor, 'editor-client-optical-plugin')

        with mock.patch('plugins.optical.opticalui.run_dialog') as run_dialog_:
            self.click(editor.patient_history_button)
            run_dialog_.assert_called_once_with(OpticalPatientDetails, editor, self.store, client)

    def test_product_search(self):
        from stoqlib.gui.search.productsearch import ProductSearch
        from stoqlib.gui.search.costcentersearch import CostCenterSearch
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

    @mock.patch('plugins.optical.opticalui.api.new_store')
    @mock.patch('plugins.optical.opticalui.run_dialog')
    def test_edit_optical_details(self, run_dialog, new_store):
        new_store.return_value = self.store

        product = self.create_product()
        work_order = self.create_workorder()
        work_order.identifier = 666
        work_order.open_date = localdate(2014, 01, 31)
        work_order.sellable = product.sellable

        app = self.create_app(ServicesApp, u'services')
        app.search.refresh()

        for wo_view in app.search.results:
            if wo_view.work_order == work_order:
                break

        self.assertIsNotNone(wo_view)
        app.search.results.select(wo_view)

        action = app.uimanager.get_action(
            '/menubar/AppMenubarPH/OrderMenu/OpticalDetails')
        with contextlib.nested(
                mock.patch.object(self.store, 'commit'),
                mock.patch.object(self.store, 'close')):
            self.activate(action)

        run_dialog.assert_called_once_with(OpticalWorkOrderEditor, None,
                                           self.store, work_order)

    @mock.patch('plugins.optical.opticalui.print_report')
    def test_print_report_event(self, print_report):

        # Emitting with something different from SaleOrderReport
        rv = PrintReportEvent.emit(object)
        self.assertFalse(rv)
        self.assertEquals(print_report.call_count, 0)

        # Emitting with SaleOrderReport, but without workorders
        sale = self.create_sale()
        rv = PrintReportEvent.emit(SaleOrderReport, sale)
        self.assertFalse(rv)
        self.assertEquals(print_report.call_count, 0)

        # Emitting with SaleOrderReport and with workorders
        optical_wo = self.create_optical_work_order()
        optical_wo.work_order.sale = sale
        rv = PrintReportEvent.emit(SaleOrderReport, sale)
        self.assertTrue(rv)
        print_report.assert_called_once_with(OpticalWorkOrderReceiptReport,
                                             [optical_wo.work_order])
