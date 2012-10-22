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

from stoqlib.gui.search.productionsearch import ProductionProductSearch
from stoqlib.domain.person import Branch
from stoqlib.domain.product import ProductStockItem
from stoqlib.domain.sellable import Sellable
from stoqlib.gui.uitestutils import GUITest


class TestProductionSearch(GUITest):
    def testProductionProductSearch(self):
        branches = Branch.select(connection=self.trans)

        product = self.create_product()
        storable = self.create_storable(product=product)
        ProductStockItem(quantity=1, branch=branches[0], storable=storable,
                         connection=self.trans)
        ProductStockItem(quantity=2, branch=branches[1], storable=storable,
                         connection=self.trans)
        product.sellable.code = '65432'
        product.sellable.description = 'Camiseta'
        product.sellable.status = Sellable.STATUS_AVAILABLE
        self.create_product_component(product=product)

        product = self.create_product()
        storable = self.create_storable(product=product)
        ProductStockItem(quantity=3, branch=branches[0], storable=storable,
                         connection=self.trans)
        ProductStockItem(quantity=4, branch=branches[1], storable=storable,
                         connection=self.trans)
        product.sellable.code = '54321'
        product.sellable.description = 'Luva'
        product.sellable.status = Sellable.STATUS_UNAVAILABLE
        self.create_product_component(product=product)

        search = ProductionProductSearch(self.trans)

        search.search.refresh()
        self.check_search(search, 'production-product-no-filter')

        search.search.search._primary_filter.entry.set_text('luv')
        search.search.refresh()
        self.check_search(search, 'production-product-string-filter')

        search.search.search._primary_filter.entry.set_text('')
        search.branch_filter.set_state(2)
        search.search.refresh()
        self.check_search(search, 'production-product-branch-filter')

        search.branch_filter.set_state(None)
        search.status_filter.set_state(Sellable.STATUS_AVAILABLE)
        search.search.refresh()
        self.check_search(search, 'production-product-status-filter')
