# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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

from kiwi.ui.search import DateSearchFilter

from stoqlib.database.runtime import get_current_branch, get_current_user
from stoqlib.domain.person import Branch
from stoqlib.domain.product import (ProductHistory, Storable, Product,
                                    ProductStockItem, ProductSupplierInfo)
from stoqlib.domain.sellable import Sellable
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.gui.uitestutils import GUITest
from stoqlib.gui.search.productsearch import (ProductSearch,
                                              ProductSearchQuantity)
from stoqlib.lib.permissions import PermissionManager
from stoqlib.lib.translation import stoqlib_gettext as _
from stoqlib.reporting.product import ProductReport, ProductPriceReport


class TestProductSearch(GUITest):

    def _show_search(self):
        search = ProductSearch(self.trans)
        search.search.refresh()
        search.results.select(search.results[0])
        return search

    def testShow(self):
        search = self._show_search()
        self.check_search(search, 'product-show')

    @mock.patch('stoqlib.gui.base.search.run_dialog')
    def testShowWithPermission(self, run_dialog):
        search = self._show_search()

        self.assertVisible(search._toolbar, ['new_button'])
        self.assertSensitive(search._toolbar, ['edit_button'])
        self.assertEquals(search._toolbar.edit_button_label.get_label(),
                          _('_Edit...'))
        self.click(search._toolbar.edit_button)

        # We have permission to edit Product, so visual_mode should be false
        args, kwargs = run_dialog.call_args
        self.assertTrue('visual_mode' in kwargs)
        self.assertEquals(kwargs['visual_mode'], False)

    @mock.patch('stoqlib.gui.base.search.run_dialog')
    def testShowWithoutPermission(self, run_dialog):
        # Our only permission now is to see details
        pm = PermissionManager.get_permission_manager()
        pm.set('Product', pm.PERM_ONLY_DETAILS)
        search = self._show_search()

        # New button shoud not be visible and edit button should actually be
        # 'Details'
        self.assertNotVisible(search._toolbar, ['new_button'])
        self.assertSensitive(search._toolbar, ['edit_button'])
        self.assertEquals(search._toolbar.edit_button_label.get_label(),
                          _('Details'))

        # Editor should be called with visual mode set.
        self.click(search._toolbar.edit_button)
        args, kwargs = run_dialog.call_args
        self.assertTrue('visual_mode' in kwargs)
        self.assertEquals(kwargs['visual_mode'], True)

    @mock.patch('stoqlib.gui.search.productsearch.print_report')
    def testPrintButton(self, print_report):
        search = self._show_search()

        self.assertSensitive(search._details_slave, ['print_button'])

        self.click(search._details_slave.print_button)
        args, kwargs = print_report.call_args
        print_report.assert_called_once_with(ProductReport, search.results,
                      list(search.results),
                      filters=search.search.get_search_filters(),
                      branch_name=search.branch_filter.combo.get_active_text())

    @mock.patch('stoqlib.gui.search.productsearch.print_report')
    def testPrintPriceButton(self, print_report):
        search = self._show_search()

        self.assertSensitive(search._print_slave, ['print_price_button'])

        self.click(search._print_slave.print_price_button)
        args, kwargs = print_report.call_args
        print_report.assert_called_once_with(ProductPriceReport,
                      list(search.results),
                      filters=search.search.get_search_filters(),
                      branch_name=search.branch_filter.combo.get_active_text())

    @mock.patch('stoqlib.gui.search.productsearch.SpreadSheetExporter.export')
    def testPrintExportCSVButton(self, export):
        search = self._show_search()

        self.assertSensitive(search, ['csv_button'])

        self.click(search.csv_button)
        args, kwargs = export.call_args
        export.assert_called_once_with(object_list=search.results,
                                       name=_('Product'),
                                       filename_prefix=_('product'))

    def testSearch(self):
        self.clean_domain([ProductSupplierInfo, ProductStockItem, Storable,
                           Product])

        branches = Branch.select(connection=self.trans)

        product = self.create_product()
        storable = self.create_storable(product=product)
        ProductStockItem(quantity=1, branch=branches[0], storable=storable,
                         connection=self.trans)
        ProductStockItem(quantity=2, branch=branches[1], storable=storable,
                         connection=self.trans)
        product.sellable.code = '1'
        product.sellable.description = 'Luvas'
        product.sellable.status = Sellable.STATUS_AVAILABLE

        product = self.create_product()
        storable = self.create_storable(product=product)
        ProductStockItem(quantity=3, branch=branches[0], storable=storable,
                         connection=self.trans)
        ProductStockItem(quantity=4, branch=branches[1], storable=storable,
                         connection=self.trans)
        product.sellable.code = '2'
        product.sellable.description = 'Botas'
        product.sellable.status = Sellable.STATUS_UNAVAILABLE

        search = ProductSearch(self.trans)

        search.search.refresh()
        self.check_search(search, 'product-no-filter')

        search.search.search._primary_filter.entry.set_text('bot')
        search.search.refresh()
        self.check_search(search, 'product-string-filter')

        search.search.search._primary_filter.entry.set_text('')
        search.status_filter.set_state(Sellable.STATUS_AVAILABLE)
        search.search.refresh()
        self.check_search(search, 'product-status-filter')

        search.status_filter.set_state(None)
        search.branch_filter.set_state(branches[0].id)
        search.search.refresh()
        self.check_search(search, 'product-branch-filter')


class TestProductSearchQuantity(GUITest):

    def _show_search(self):
        search = ProductSearchQuantity(self.trans)
        return search

    def _create_domain(self):
        self.clean_domain([ProductHistory])

        self.date = datetime.date(2012, 1, 1)
        self.today = datetime.date.today()
        branch = get_current_branch(self.trans)
        user = get_current_user(self.trans)
        product = self.create_product()
        Storable(connection=self.trans, product=product)

        # Purchase
        order = self.create_purchase_order(branch=branch)
        order.identifier = 111
        order.open_date = self.today
        order.status = PurchaseOrder.ORDER_PENDING
        p_item = order.add_item(product.sellable, 10)
        order.confirm()

        # Receiving
        receiving = self.create_receiving_order(order, branch, user)
        receiving.identifier = 222
        receiving.receival_date = self.date
        r_item = self.create_receiving_order_item(receiving, product.sellable, p_item)
        r_item.quantity_received = 8
        receiving.confirm()

        # Sale
        sale = self.create_sale(123, branch=branch)
        sale.open_date = self.today
        sale.add_sellable(product.sellable, 3)
        sale.order()
        self.add_payments(sale, date=self.today)
        sale.confirm()

    def testShow(self):
        self._create_domain()
        search = self._show_search()
        search.date_filter.select(DateSearchFilter.Type.USER_DAY)

        search.date_filter.start_date.update(self.date)
        search.search.refresh()
        self.check_search(search, 'product-quantity-filter-date')

        search.date_filter.start_date.update(self.today)
        search.search.refresh()
        self.check_search(search, 'product-quantity-filter-today')
