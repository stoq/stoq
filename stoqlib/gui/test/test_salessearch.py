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

from kiwi.ui.search import DateSearchFilter

from stoqlib.domain.commission import Commission
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.person import Branch
from stoqlib.domain.sale import Sale, SaleItem
from stoqlib.gui.search.salesearch import (SaleSearch,
                                           SaleWithToolbarSearch,
                                           SalesByPaymentMethodSearch,
                                           SoldItemsByBranchSearch)
from stoqlib.gui.uitestutils import GUITest


class TestSaleSearch(GUITest):
    def testShow(self):
        search = SaleSearch(self.trans)
        search.search.refresh()
        self.check_search(search, 'sale-show')


class TestSaleWithToolbarSearch(GUITest):
    def testShow(self):
        search = SaleWithToolbarSearch(self.trans)
        search.search.refresh()
        self.check_search(search, 'sale-with-toolbar-show')


class TestSalesByPaymentMethodSearch(GUITest):
    def testShow(self):
        search = SalesByPaymentMethodSearch(self.trans)
        search.search.refresh()
        self.check_search(search, 'sale-payment-method-show')


class TestSoldItemsByBranchSearch(GUITest):
    def _create_domain(self):
        self.clean_domain([Commission, SaleItem, Sale])

        branches = Branch.select(connection=self.trans)

        sale = self.create_sale(branch=branches[0])
        sale_item = self.create_sale_item(sale=sale)
        storable = self.create_storable(product=sale_item.sellable.product)
        storable.increase_stock(10, branches[0])
        self.create_payment(payment_type=Payment.TYPE_IN, group=sale.group)
        sale.order()
        sale.confirm()
        sale_item.sellable.code = '1'
        sale_item.sellable.description = 'Luvas'
        sale.open_date = datetime.date(2012, 1, 1)
        sale.confirm_date = datetime.date(2012, 1, 1)

        sale = self.create_sale(branch=branches[1])
        sale_item = self.create_sale_item(sale=sale)
        storable = self.create_storable(product=sale_item.sellable.product)
        storable.increase_stock(10, branches[0])
        self.create_payment(payment_type=Payment.TYPE_IN, group=sale.group)
        sale.order()
        sale.confirm()
        sale_item.sellable.code = '2'
        sale_item.sellable.description = 'Botas'
        sale.open_date = datetime.date(2012, 2, 2)
        sale.confirm_date = datetime.date(2012, 2, 2)

    def _show_search(self):
        search = SoldItemsByBranchSearch(self.trans)
        search.search.refresh()
        search.results.select(search.results[0])
        return search

    def testShow(self):
        self._create_domain()
        search = self._show_search()

        self.check_search(search, 'sold-items-no-filter')

        search.set_searchbar_search_string('bot')
        search.search.refresh()
        self.check_search(search, 'sold-items-string-filter')

        search.set_searchbar_search_string('')
        search.branch_filter.set_state(1)
        search.search.refresh()
        self.check_search(search, 'sold-items-branch-filter')

        search.branch_filter.set_state(None)
        search.date_filter.select(DateSearchFilter.Type.USER_DAY)
        search.date_filter.start_date.update(datetime.date(2012, 2, 2))
        search.search.refresh()
        self.check_search(search, 'product-sold-date-filter')
