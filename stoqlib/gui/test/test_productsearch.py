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

from stoqlib.api import api
from stoqlib.database.runtime import get_current_branch, get_current_user
from stoqlib.domain.person import Branch
from stoqlib.domain.product import (ProductHistory, Storable, Product,
                                    ProductStockItem, ProductSupplierInfo,
                                    StockTransactionHistory)
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.domain.sale import SaleItem
from stoqlib.domain.sellable import Sellable
from stoqlib.gui.search.productsearch import (ProductSearch,
                                              ProductSearchQuantity,
                                              ProductsSoldSearch,
                                              ProductStockSearch,
                                              ProductClosedStockSearch,
                                              ProductBrandSearch)
from stoqlib.gui.search.searchfilters import DateSearchFilter
from stoqlib.gui.search.searchoptions import Any
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.lib.dateutils import localtoday
from stoqlib.lib.permissions import PermissionManager
from stoqlib.lib.translation import stoqlib_gettext as _
from stoqlib.reporting.product import (ProductReport, ProductPriceReport,
                                       ProductQuantityReport,
                                       ProductsSoldReport,
                                       ProductStockReport,
                                       ProductClosedStockReport, ProductBrandReport)


class TestProductSearch(GUITest):
    def tearDown(self):
        GUITest.tearDown(self)

        # Reset the permitions so they wont influence other tests
        pm = PermissionManager.get_permission_manager()
        pm.set('Product', PermissionManager.PERM_ALL)

    def _show_search(self):
        search = ProductSearch(self.store)
        search.search.refresh()
        search.results.select(search.results[0])
        return search

    def test_show(self):
        search = self._show_search()
        self.check_search(search, 'product-show')

    @mock.patch('stoqlib.gui.search.searcheditor.run_dialog')
    def test_show_with_permission(self, run_dialog):
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

    @mock.patch('stoqlib.gui.search.searcheditor.run_dialog')
    def test_show_without_permission(self, run_dialog):
        # Our only permission now is to see details
        pm = PermissionManager.get_permission_manager()
        default_persmission = pm.get('Product')
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

        # Retore the default permission so it doens't effect other tests
        pm.set('Product', default_persmission)

    @mock.patch('stoqlib.gui.search.searchdialog.print_report')
    def test_print_button(self, print_report):
        search = self._show_search()

        self.assertSensitive(search._details_slave, ['print_button'])

        self.click(search._details_slave.print_button)
        args, kwargs = print_report.call_args
        print_report.assert_called_once_with(
            ProductReport, search.results, list(search.results),
            filters=search.search.get_search_filters())

    @mock.patch('stoqlib.gui.search.productsearch.print_report')
    def test_print_price_button(self, print_report):
        search = self._show_search()

        self.assertSensitive(search._print_slave, ['print_price_button'])

        self.click(search._print_slave.print_price_button)
        args, kwargs = print_report.call_args
        print_report.assert_called_once_with(
            ProductPriceReport, list(search.results),
            filters=search.search.get_search_filters(),
            branch_name=search.branch_filter.combo.get_active_text())

    def test_search(self):
        self.clean_domain([StockTransactionHistory, ProductSupplierInfo,
                           ProductStockItem, Storable, Product])

        branches = list(self.store.find(Branch))

        product = self.create_product()
        storable = self.create_storable(product=product)
        self.create_product_stock_item(
            storable=storable, branch=branches[0], quantity=1)
        self.create_product_stock_item(
            storable=storable, branch=branches[1], quantity=2)
        product.sellable.code = u'1'
        product.sellable.description = u'Luvas'

        product = self.create_product()
        storable = self.create_storable(product=product)
        self.create_product_stock_item(
            storable=storable, branch=branches[0], quantity=3)
        self.create_product_stock_item(
            storable=storable, branch=branches[1], quantity=4)
        product.sellable.code = u'2'
        product.sellable.description = u'Botas'
        product.sellable.status = Sellable.STATUS_CLOSED

        search = ProductSearch(self.store)

        search.search.refresh()
        self.check_search(search, 'product-no-filter')

        search.set_searchbar_search_string('bot')
        search.search.refresh()
        self.check_search(search, 'product-string-filter')

        search.set_searchbar_search_string('')
        search.status_filter.set_state(Sellable.STATUS_AVAILABLE)
        search.search.refresh()
        self.check_search(search, 'product-status-filter')

        search.status_filter.set_state(None)
        search.branch_filter.set_state(branches[0].id)
        search.search.refresh()
        self.check_search(search, 'product-branch-filter')

    def test_search_without_price_column(self):
        search = ProductSearch(self.store, hide_price_column=True)
        self.check_search(search, 'product-search-without-price')


class TestProductSearchQuantity(GUITest):
    def _show_search(self):
        search = ProductSearchQuantity(self.store)
        search.search.refresh()
        search.results.select(search.results[0])
        return search

    def _create_domain(self):
        self.clean_domain([ProductHistory])

        branch = get_current_branch(self.store)
        user = get_current_user(self.store)
        self.today = localtoday()

        product = self.create_product()
        Storable(store=self.store, product=product)
        product.sellable.code = u'1'
        product.sellable.description = u'Luvas'
        product2 = self.create_product()
        Storable(store=self.store, product=product2)
        product2.sellable.code = u'2'
        product2.sellable.description = u'Botas'

        # Purchase
        order = self.create_purchase_order(branch=branch)
        order.identifier = 111
        order.open_date = self.today
        order.status = PurchaseOrder.ORDER_PENDING
        p_item = order.add_item(product.sellable, 10)
        p2_item = order.add_item(product2.sellable, 15)
        order.confirm()

        # Receiving
        receiving = self.create_receiving_order(order, branch, user)
        receiving.identifier = 222
        receiving.receival_date = self.today
        self.create_receiving_order_item(receiving, product.sellable, p_item, 8)
        self.create_receiving_order_item(receiving, product2.sellable, p2_item,
                                         12)
        receiving.confirm()

        # Sale
        sale = self.create_sale(branch=branch)
        sale.identifier = 123
        sale.open_date = self.today
        sale.add_sellable(product.sellable, 3)
        sale.add_sellable(product2.sellable, 5)
        sale.order()
        self.add_payments(sale, date=self.today)
        sale.confirm()

    def test_search(self):
        self._create_domain()
        search = self._show_search()

        search.date_filter.select(Any)
        self.check_search(search, 'product-quantity-branch-filter')

        search.set_searchbar_search_string('bot')
        search.search.refresh()
        self.check_search(search, 'product-quantity-string-filter')

        search.set_searchbar_search_string('')
        search.date_filter.select(DateSearchFilter.Type.USER_DAY)
        search.date_filter.start_date.update(datetime.date.today())
        search.search.refresh()
        self.check_search(search, 'product-quantity-date-today-filter')

        search.date_filter.start_date.update(datetime.date(2012, 1, 1))
        search.search.refresh()
        self.check_search(search, 'product-quantity-date-day-filter')

    @mock.patch('stoqlib.gui.search.searchdialog.print_report')
    def test_print_button(self, print_report):
        self._create_domain()
        search = self._show_search()

        self.assertSensitive(search._details_slave, ['print_button'])

        self.click(search._details_slave.print_button)
        args, kwargs = print_report.call_args
        print_report.assert_called_once_with(
            ProductQuantityReport, search.results, list(search.results),
            filters=search.search.get_search_filters())


class TestProductsSoldSearch(GUITest):
    def _show_search(self):
        search = ProductsSoldSearch(self.store)
        search.search.refresh()
        search.results.select(search.results[0])
        return search

    def _create_domain(self):
        self.clean_domain([SaleItem])

        branch = get_current_branch(self.store)
        self.today = localtoday()

        product = self.create_product()
        storable = Storable(store=self.store, product=product)
        self.create_product_stock_item(
            storable=storable, branch=branch, quantity=5)
        product.sellable.code = u'1'
        product.sellable.description = u'Luvas'

        product2 = self.create_product()
        storable2 = Storable(store=self.store, product=product2)
        self.create_product_stock_item(
            storable=storable2, branch=branch, quantity=5)
        product2.sellable.code = u'2'
        product2.sellable.description = u'Botas'

        # Sale
        sale = self.create_sale(branch=branch)
        sale.identifier = 123
        sale.open_date = self.today
        sale.add_sellable(product.sellable, 3)
        sale.add_sellable(product2.sellable, 5)
        sale.order()
        self.add_payments(sale, date=self.today)
        sale.confirm()

    def test_search(self):
        self._create_domain()
        search = self._show_search()

        search.date_filter.select(Any)
        self.check_search(search, 'product-sold-no-filter')

        search.set_searchbar_search_string('bot')
        search.search.refresh()
        self.check_search(search, 'product-sold-string-filter')

        search.set_searchbar_search_string('')
        search.branch_filter.set_state(api.get_current_branch(self.store).id)
        search.search.refresh()
        self.check_search(search, 'product-sold-branch-filter')

        search.branch_filter.set_state(None)
        search.date_filter.select(DateSearchFilter.Type.USER_DAY)
        search.date_filter.start_date.update(datetime.date.today())
        search.search.refresh()
        self.check_search(search, 'product-sold-date-today-filter')

        search.date_filter.select(DateSearchFilter.Type.USER_INTERVAL)
        search.date_filter.start_date.update(datetime.date(2012, 1, 1))
        search.date_filter.end_date.update(datetime.date(2012, 2, 2))
        search.search.refresh()
        self.check_search(search, 'product-sold-date-day-filter')

    @mock.patch('stoqlib.gui.search.searchdialog.print_report')
    def test_print_button(self, print_report):
        self._create_domain()
        search = self._show_search()

        self.assertSensitive(search._details_slave, ['print_button'])

        self.click(search._details_slave.print_button)
        args, kwargs = print_report.call_args
        print_report.assert_called_once_with(ProductsSoldReport,
                                             search.results,
                                             list(search.results),
                                             filters=search.search.get_search_filters())


class TestProductStockSearch(GUITest):
    def _show_search(self):
        search = ProductStockSearch(self.store)
        search.search.refresh()
        search.results.select(search.results[0])
        return search

    def _create_domain(self):
        self.clean_domain([StockTransactionHistory, ProductSupplierInfo,
                           ProductStockItem, Storable, Product])

        branch = get_current_branch(self.store)
        user = get_current_user(self.store)
        self.today = localtoday()

        product = self.create_product()
        Storable(store=self.store, product=product, minimum_quantity=3,
                 maximum_quantity=20)
        product.sellable.code = u'1'
        product.sellable.description = u'Luvas'

        product2 = self.create_product()
        Storable(store=self.store, product=product2, minimum_quantity=4,
                 maximum_quantity=20)
        product2.sellable.code = u'2'
        product2.sellable.description = u'Botas'

        # Purchase
        order = self.create_purchase_order(branch=branch)
        order.identifier = 111
        order.open_date = self.today
        order.status = PurchaseOrder.ORDER_PENDING
        p_item = order.add_item(product.sellable, 10)
        p2_item = order.add_item(product2.sellable, 15)
        order.confirm()

        # Receiving
        receiving = self.create_receiving_order(order, branch, user)
        receiving.identifier = 222
        receiving.receival_date = self.today
        self.create_receiving_order_item(receiving, product.sellable, p_item, 8)
        self.create_receiving_order_item(receiving, product2.sellable, p2_item,
                                         12)
        receiving.confirm()

    def test_search(self):
        self._create_domain()
        search = self._show_search()

        search.branch_filter.set_state(None)
        self.check_search(search, 'product-stock-no-filter')

        search.set_searchbar_search_string('bot')
        search.search.refresh()
        self.check_search(search, 'product-stock-string-filter')

        search.set_searchbar_search_string('')
        search.branch_filter.set_state(api.get_current_branch(self.store).id)
        search.search.refresh()
        self.check_search(search, 'product-stock-branch-filter')

    @mock.patch('stoqlib.gui.search.searchdialog.print_report')
    def test_print_button(self, print_report):
        self._create_domain()
        search = self._show_search()

        self.assertSensitive(search._details_slave, ['print_button'])

        self.click(search._details_slave.print_button)
        args, kwargs = print_report.call_args
        print_report.assert_called_once_with(ProductStockReport,
                                             search.results,
                                             list(search.results),
                                             filters=search.search.get_search_filters())


class TestProductBrandSearch(GUITest):
    def _show_search(self):
        search = ProductBrandSearch(self.store)
        search.search.refresh()
        search.results.select(search.results[0])
        return search

    def _create_domain(self):
        branch = get_current_branch(self.store)

        product = self.create_product()
        storable = Storable(store=self.store, product=product)
        self.create_product_stock_item(
            storable=storable, branch=branch, quantity=2)
        product.brand = u''
        product.sellable.code = u'1'
        product.sellable.description = u'Luvas'

        product2 = self.create_product()
        storable2 = Storable(store=self.store, product=product2)
        self.create_product_stock_item(
            storable=storable2, branch=branch, quantity=4)
        product2.brand = u'brand'
        product.sellable.code = u'2'
        product.sellable.description = u'Botas'

    def test_search(self):
        self._create_domain()
        search = self._show_search()

        search.branch_filter.set_state(None)
        self.check_search(search, 'brand-no-filter')

        search.set_searchbar_search_string('bran')
        search.search.refresh()
        self.check_search(search, 'brand-string-filter')

        search.set_searchbar_search_string('')
        search.branch_filter.set_state(api.get_current_branch(self.store).id)
        search.search.refresh()
        self.check_search(search, 'brand-branch-filter')

    @mock.patch('stoqlib.gui.search.searchdialog.print_report')
    def test_print_button(self, print_report):
        self._create_domain()
        search = self._show_search()

        self.assertSensitive(search._details_slave, ['print_button'])

        self.click(search._details_slave.print_button)
        args, kwargs = print_report.call_args
        print_report.assert_called_once_with(ProductBrandReport,
                                             search.results,
                                             list(search.results),
                                             filters=search.search.get_search_filters())


class TestProductClosedStockSearch(GUITest):
    def _show_search(self):
        search = ProductClosedStockSearch(self.store)
        search.search.refresh()
        search.results.select(search.results[0])
        return search

    def _create_domain(self):
        self.today = datetime.date.today()

        branch = get_current_branch(self.store)

        product = self.create_product()
        storable = Storable(store=self.store, product=product)
        self.create_product_stock_item(
            storable=storable, branch=branch, quantity=2)
        product.sellable.code = u'1'
        product.sellable.description = u'Luvas'
        product.sellable.status = Sellable.STATUS_CLOSED

        product = self.create_product()
        storable = Storable(store=self.store, product=product)
        self.create_product_stock_item(
            storable=storable, branch=branch, quantity=4)
        product.sellable.code = u'2'
        product.sellable.description = u'Botas'
        product.sellable.status = Sellable.STATUS_CLOSED

    def test_search(self):
        self._create_domain()
        search = self._show_search()

        search.branch_filter.set_state(None)
        self.check_search(search, 'product-closed-stock-no-filter')

        search.set_searchbar_search_string('bot')
        search.search.refresh()
        self.check_search(search, 'product-closed-stock-string-filter')

        search.set_searchbar_search_string('')
        search.branch_filter.set_state(api.get_current_branch(self.store).id)
        search.search.refresh()
        self.check_search(search, 'product-closed-stock-branch-filter')

    @mock.patch('stoqlib.gui.search.searchdialog.print_report')
    def test_print_button(self, print_report):
        self._create_domain()
        search = self._show_search()

        self.assertSensitive(search._details_slave, ['print_button'])

        self.click(search._details_slave.print_button)
        args, kwargs = print_report.call_args
        print_report.assert_called_once_with(
            ProductClosedStockReport,
            search.results, list(search.results),
            filters=search.search.get_search_filters())
