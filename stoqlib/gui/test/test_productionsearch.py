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
from stoqlib.gui.search.productionsearch import (ProductionProductSearch,
                                                 ProductionItemsSearch,
                                                 ProductionHistorySearch)
from stoqlib.domain.person import Branch
from stoqlib.domain.product import ProductHistory
from stoqlib.domain.production import ProductionOrder
from stoqlib.domain.sellable import Sellable
from stoqlib.gui.search.searchfilters import DateSearchFilter
from stoqlib.gui.search.searchoptions import Any
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.reporting.production import ProductionItemReport


class TestProductionProductSearch(GUITest):
    def test_search(self):
        branches = self.store.find(Branch)

        product = self.create_product()
        storable = self.create_storable(product=product)
        self.create_product_stock_item(
            storable=storable, branch=branches[0], quantity=1)
        self.create_product_stock_item(
            storable=storable, branch=branches[1], quantity=2)
        product.sellable.code = u'65432'
        product.sellable.description = u'Camiseta'
        product.is_composed = True
        self.create_product_component(product=product)

        product = self.create_product()
        storable = self.create_storable(product=product)
        self.create_product_stock_item(
            storable=storable, branch=branches[0], quantity=3)
        self.create_product_stock_item(
            storable=storable, branch=branches[1], quantity=4)
        product.sellable.code = u'54321'
        product.sellable.description = u'Luva'
        product.sellable.status = Sellable.STATUS_CLOSED
        self.create_product_component(product=product)

        search = ProductionProductSearch(self.store)

        search.search.refresh()
        self.check_search(search, 'production-product-no-filter')

        search.set_searchbar_search_string('luv')
        search.search.refresh()
        self.check_search(search, 'production-product-string-filter')

        search.set_searchbar_search_string('')
        search.branch_filter.set_state(api.get_current_branch(self.store).id)
        search.search.refresh()
        self.check_search(search, 'production-product-branch-filter')

        search.branch_filter.set_state(None)
        search.status_filter.set_state(Sellable.STATUS_AVAILABLE)
        search.search.refresh()
        self.check_search(search, 'production-product-status-filter')


class TestProductionItemsSearch(GUITest):
    def _show_search(self):
        search = ProductionItemsSearch(self.store)
        search.status_filter.set_state(None)
        search.search.refresh()
        search.results.select(search.results[0])
        return search

    def _create_domain(self):
        item = self.create_production_item(5)
        item.order.identifier = 78425
        item.product.sellable.description = u'Luvas'
        item.order.start_production()
        item.produced = 2

        item = self.create_production_item(3)
        item.order.identifier = 45978
        item.product.sellable.description = u'Botas'

    def test_search(self):
        self._create_domain()
        search = self._show_search()

        self.check_search(search, 'production-items-no-filter')

        search.set_searchbar_search_string('bot')
        search.search.refresh()
        self.check_search(search, 'production-items-string-filter')

        search.set_searchbar_search_string('')
        search.status_filter.set_state(ProductionOrder.ORDER_PRODUCING)
        search.search.refresh()
        self.check_search(search, 'production-items-status-filter')

    @mock.patch('stoqlib.gui.search.searchdialog.print_report')
    def test_print_button(self, print_report):
        self._create_domain()
        search = self._show_search()

        self.assertSensitive(search._details_slave, ['print_button'])

        self.click(search._details_slave.print_button)
        args, kwargs = print_report.call_args
        print_report.assert_called_once_with(
            ProductionItemReport, search.results, list(search.results),
            filters=search.search.get_search_filters())


class TestProductionHistorySearch(GUITest):
    def _show_search(self):
        search = ProductionHistorySearch(self.store)
        search.branch_filter.set_state(api.get_current_branch(self.store).id)
        search.date_filter.select(Any)
        search.search.refresh()
        search.results.select(search.results[0])
        return search

    def _create_domain(self):
        self.clean_domain([ProductHistory])

        branches = self.store.find(Branch)

        luvas = self.create_sellable(description=u'Luvas')
        luvas.code = u'1'
        botas = self.create_sellable(description=u'Botas')
        botas.code = u'2'

        ProductHistory(branch=branches[0], sellable=luvas,
                       quantity_produced=1,
                       production_date=datetime.date.today(),
                       store=self.store)
        ProductHistory(branch=branches[0], sellable=luvas,
                       quantity_lost=2,
                       production_date=datetime.date(2012, 1, 1),
                       store=self.store)
        ProductHistory(branch=branches[0], sellable=botas,
                       quantity_lost=3,
                       production_date=datetime.date(2012, 2, 2),
                       store=self.store)

        ProductHistory(branch=branches[1], sellable=luvas,
                       quantity_produced=3,
                       production_date=datetime.date(2012, 3, 3),
                       store=self.store)
        ProductHistory(branch=branches[1], sellable=botas,
                       quantity_lost=4,
                       production_date=datetime.date(2012, 4, 4),
                       store=self.store)

    def test_search(self):
        self._create_domain()
        search = self._show_search()

        self.check_search(search, 'production-history-branch-filter')

        search.set_searchbar_search_string('bot')
        search.search.refresh()
        self.check_search(search, 'production-history-string-filter')

        search.set_searchbar_search_string('')
        search.date_filter.select(DateSearchFilter.Type.USER_DAY)
        search.date_filter.start_date.update(datetime.date.today())
        search.search.refresh()
        self.check_search(search, 'production-history-date-today-filter')

        search.date_filter.select(DateSearchFilter.Type.USER_INTERVAL)
        search.date_filter.start_date.update(datetime.date(2012, 1, 1))
        search.date_filter.end_date.update(datetime.date(2012, 2, 2))
        search.search.refresh()
        self.check_search(search, 'production-history-date-day-filter')

    @mock.patch('stoqlib.gui.search.searchdialog.print_report')
    def test_print_button(self, print_report):
        self._create_domain()
        search = self._show_search()

        details_slave = search.get_slave('details_holder')
        self.assertSensitive(details_slave, ['print_button'])

        self.click(details_slave.print_button)
        print_report.assert_called_once_with(ProductionItemReport,
                                             search.results,
                                             list(search.results),
                                             filters=search.search.get_search_filters())
