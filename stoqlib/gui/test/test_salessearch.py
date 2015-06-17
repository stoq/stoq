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

import mock

from stoqlib.api import api
from stoqlib.domain.commission import Commission
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.person import Branch
from stoqlib.domain.sale import Sale, SaleItem, SaleView
from stoqlib.database.runtime import get_current_branch
from stoqlib.gui.dialogs.saledetails import SaleDetailsDialog
from stoqlib.gui.search.searchfilters import DateSearchFilter
from stoqlib.gui.search.salesearch import (SaleSearch,
                                           SaleWithToolbarSearch,
                                           SalesByPaymentMethodSearch,
                                           SoldItemsByBranchSearch,
                                           UnconfirmedSaleItemsSearch,
                                           SaleTokenSearch)
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.lib.dateutils import localdate


class TestSaleSearch(GUITest):
    def test_show(self):
        search = SaleSearch(self.store)
        search.search.refresh()
        self.check_search(search, 'sale-show')


class TestSaleWithToolbarSearch(GUITest):
    def test_show(self):
        search = SaleWithToolbarSearch(self.store)
        search.search.refresh()
        self.check_search(search, 'sale-with-toolbar-show')


class TestSalesByPaymentMethodSearch(GUITest):
    def test_show(self):
        search = SalesByPaymentMethodSearch(self.store)
        search.search.refresh()
        self.check_search(search, 'sale-payment-method-show')


class TestSoldItemsByBranchSearch(GUITest):
    def _create_domain(self):
        self.clean_domain([Commission, SaleItem, Sale])

        branches = self.store.find(Branch)

        sale = self.create_sale(branch=branches[0])
        sale_item = self.create_sale_item(sale=sale)
        self.create_storable(sale_item.sellable.product, branches[0], 10)
        self.create_payment(payment_type=Payment.TYPE_IN, group=sale.group)
        sale.order()
        sale.confirm()
        sale_item.sellable.code = u'1'
        sale_item.sellable.description = u'Luvas'
        sale.open_date = localdate(2012, 1, 1).date()
        sale.confirm_date = localdate(2012, 1, 1).date()

        sale = self.create_sale(branch=branches[1])
        sale_item = self.create_sale_item(sale=sale)
        self.create_storable(sale_item.sellable.product, branches[0], 10)
        self.create_payment(payment_type=Payment.TYPE_IN, group=sale.group)
        sale.order()
        sale.confirm()
        sale_item.sellable.code = u'2'
        sale_item.sellable.description = u'Botas'
        sale.open_date = localdate(2012, 2, 2).date()
        sale.confirm_date = localdate(2012, 2, 2).date()

    def _show_search(self):
        search = SoldItemsByBranchSearch(self.store)
        search.search.refresh()
        search.results.select(search.results[0])
        return search

    def test_show(self):
        self._create_domain()
        search = self._show_search()

        self.check_search(search, 'sold-items-no-filter')

        search.set_searchbar_search_string('bot')
        search.search.refresh()
        self.check_search(search, 'sold-items-string-filter')

        search.set_searchbar_search_string('')
        search.branch_filter.set_state(api.get_current_branch(self.store).id)
        search.search.refresh()
        self.check_search(search, 'sold-items-branch-filter')

        search.branch_filter.set_state(None)
        search.date_filter.select(DateSearchFilter.Type.USER_DAY)
        search.date_filter.start_date.update(localdate(2012, 2, 2).date())
        search.search.refresh()
        self.check_search(search, 'product-sold-date-filter')


class TestUnconfirmedSaleItemsSearch(GUITest):
    def _create_domain(self):
        branch = get_current_branch(self.store)
        sale = self.create_sale(branch=branch)
        sale_item = self.create_sale_item(sale=sale)
        sale_item.quantity = 66
        sale_item.quantity_decreased = 23
        sale_item.sellable.description = u'Schrubbery'
        sale_item.sale.identifier = 42
        sale.status = sale.STATUS_ORDERED
        sale.open_date = localdate(2013, 12, 11)

        sale2 = self.create_sale(branch=branch)
        sale_item2 = self.create_sale_item(sale=sale2)
        sale_item2.quantity = 29
        sale_item2.quantity_decreased = 29
        sale_item2.sellable.description = u'Holy Grail'
        sale_item2.sale.identifier = 73
        sale2.open_date = localdate(2013, 12, 11)
        sale2.status = sale2.STATUS_QUOTE

        self.branch2 = self.create_branch(u'The Meaning of Life')
        sale3 = self.create_sale(branch=self.branch2)
        sale_item3 = self.create_sale_item(sale=sale3)
        sale_item3.quantity = 41
        sale_item3.quantity_decreased = 1
        sale_item3.sellable.description = u'The Funniest Joke in this Code'
        sale_item3.sale.identifier = 99
        sale3.open_date = localdate(2013, 12, 11)
        sale3.status = sale3.STATUS_QUOTE

        # With work order
        sale4 = self.create_sale(branch=branch)
        sale4.identifier = 43
        sale_item4 = self.create_sale_item(sale=sale4)
        sale_item4.quantity = 33
        sale_item4.quantity_decreased = 33
        sale_item4.description = u'Knights who say Ni'
        sale4.open_date = localdate(2014, 6, 12)
        sale4.status = sale4.STATUS_QUOTE

        work_order = self.create_workorder(branch=branch)
        work_order.identifier = 44
        work_order_item = self.create_work_order_item()
        work_order_item.sale_item = sale_item4
        work_order_item.sellable = sale_item4.sellable
        work_order_item.order = work_order
        work_order.sale = sale4

    def _show_search(self):
        search = UnconfirmedSaleItemsSearch(self.store)
        search.search.refresh()
        search.results.select(search.results[0])
        return search

    def test_show(self):
        self._create_domain()
        search = self._show_search()

        self.check_search(search, 'search-reserved-product-no-filter')

        search.branch_filter.set_state(self.branch2.id)
        search.search.refresh()
        self.check_search(search, 'search-reserved-product-branch-filter')

    def test_actions(self):
        self._create_domain()
        search = self._show_search()
        search.search.refresh()

        self.assertNotSensitive(search, ['sale_details_button'])
        search.results.select(search.results[0])
        self.assertSensitive(search, ['sale_details_button'])

        with mock.patch('stoqlib.gui.search.salesearch.run_dialog') as run_dialog:
            self.click(search.sale_details_button)
            sale_view = self.store.find(SaleView, id=search.results[0].sale_id).one()
            run_dialog.assert_called_once_with(SaleDetailsDialog, search,
                                               self.store, sale_view)


class TestSaleTokenSearch(GUITest):
    def test_show(self):
        self.create_sale_token(code=u'sale token 1')
        self.create_sale_token(code=u'sale token 2')
        search = SaleTokenSearch(self.store, hide_footer=True)
        self.check_search(search, 'sale-token-show')

        search.search.refresh()
        self.check_search(search, 'sale-token-after-search-show')
