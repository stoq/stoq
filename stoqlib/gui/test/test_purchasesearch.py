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

from stoqlib.api import api
from stoqlib.domain.person import Branch
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.gui.search.purchasesearch import PurchasedItemsSearch
from stoqlib.gui.test.uitestutils import GUITest


class TestPurchasedItemsSearch(GUITest):
    def test_search(self):
        branch = api.get_current_branch(self.store)
        order = self.create_purchase_order(branch=branch)
        item = self.create_purchase_order_item(order=order)
        item.sellable.description = u'Camisa listrada'
        item.quantity = 5
        item.quantity_received = 3
        item.order.open_date = datetime.datetime(2012, 1, 1)
        item.order.status = PurchaseOrder.ORDER_CONFIRMED
        storable = self.create_storable(item.sellable.product)
        self.create_product_stock_item(
            storable=storable, branch=branch, quantity=item.quantity)

        branch = self.store.find(Branch, Branch.id != branch.id).any()
        order = self.create_purchase_order(branch=branch)
        item = self.create_purchase_order_item(order=order)
        item.sellable.description = u'Camisa bordada'
        item.quantity = 4
        item.quantity_received = 2
        item.order.open_date = datetime.datetime(2012, 2, 2)
        item.order.status = PurchaseOrder.ORDER_CONFIRMED
        storable = self.create_storable(item.sellable.product)
        self.create_product_stock_item(
            storable=storable, branch=branch, quantity=item.quantity)

        search = PurchasedItemsSearch(self.store)

        search.search.refresh()
        search.branch_filter.set_state(None)
        self.check_search(search, 'purchased-items-no-filter')

        search.set_searchbar_search_string('bor')
        search.search.refresh()
        self.check_search(search, 'purchased-items-string-filter')

        search.set_searchbar_search_string('')
        search.branch_filter.set_state(api.get_current_branch(self.store).id)
        search.search.refresh()
        self.check_search(search, 'purchased-items-branch-filter')
