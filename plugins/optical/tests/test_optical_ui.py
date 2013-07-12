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

import gtk
import mock

from stoqlib.database.runtime import StoqlibStore
from stoqlib.domain.sale import Sale
from stoqlib.domain.workorder import WorkOrderCategory
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.producteditor import ProductEditor
from stoqlib.gui.editors.workordereditor import WorkOrderEditor
from stoqlib.gui.wizards.salequotewizard import SaleQuoteWizard
from stoqlib.lib.dateutils import localdate
from stoqlib.lib.parameters import sysparam
from stoq.gui.test.baseguitest import BaseGUITest
from stoq.gui.sales import SalesApp

from ..medicssearch import OpticalMedicSearch
from ..opticalreport import OpticalWorkOrderReceiptReport
from ..opticalui import OpticalUI
from ..opticalwizard import OpticalSaleQuoteWizard


class TestOpticalUI(BaseGUITest):
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

    def test_product_editor(self):
        product = self.create_product()
        editor = ProductEditor(store=self.store, model=product)
        self.check_editor(editor, u'editor-product-optical-plugin')

    def test_work_order_editor(self):
        sysparam(self.store).update_parameter(
            u'ALLOW_OUTDATED_OPERATIONS',
            u'True')

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
            run_dialog(SaleQuoteWizard, None, self.store, sale)
            args, kwargs = run_dialog_internal.call_args
            self.assertTrue(isinstance(args[0], OpticalSaleQuoteWizard))

            # Without a Sale, normal wizard
            run_dialog_internal.reset_mock()
            run_dialog(SaleQuoteWizard, None, self.store, None)
            args, kwargs = run_dialog_internal.call_args
            self.assertTrue(isinstance(args[0], SaleQuoteWizard))
