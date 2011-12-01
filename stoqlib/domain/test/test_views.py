# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007-2011 Async Open Source <http://www.async.com.br>
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

from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.purchase import PurchaseOrder, QuoteGroup
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.domain.views import AccountView
from stoqlib.domain.views import ProductComponentView
from stoqlib.domain.views import ProductFullStockView
from stoqlib.domain.views import QuotationView
from stoqlib.domain.views import SellableCategoryView
from stoqlib.domain.views import SellableFullStockView
from stoqlib.domain.views import SoldItemView


class TestSellableFullStockView(DomainTest):
    def testSelectByBranch(self):
        branch = get_current_branch(self.trans)
        results = SellableFullStockView.select_by_branch(
            SellableFullStockView.q.product_id == None,
            None, connection=self.trans)
        self.failUnless(list(results))

        # Bug 3458 We should have services even if send in a branch
        results = SellableFullStockView.select_by_branch(
            SellableFullStockView.q.product_id == None,
            branch, connection=self.trans)
        self.failUnless(list(results))


class TestProductFullStockView(DomainTest):
    def testSelectByBranch(self):
        branch = self.create_branch()
        p1 = self.create_product(branch=branch, stock=1)

        results = ProductFullStockView.select_by_branch(
            None, branch, connection=self.trans)
        self.failUnless(list(results))
        self.assertEquals(results.count(), 1)

        results = ProductFullStockView.select_by_branch(
            ProductFullStockView.q.product_id == p1.id,
            branch, connection=self.trans)
        self.failUnless(list(results))
        self.assertEquals(results.count(), 1)

    def testUnitDescription(self):
        p1 = self.create_product()
        p1.sellable.unit = self.create_sellable_unit()
        p1.sellable.unit.description = "kg"

        p2 = self.create_product()

        results = ProductFullStockView.select_by_branch(
            ProductFullStockView.q.product_id == p1.id,
            None, connection=self.trans)
        self.failUnless(list(results))
        product_view = results[0]
        self.assertEquals(product_view.get_unit_description(), "kg")

        results = ProductFullStockView.select_by_branch(
            ProductFullStockView.q.product_id == p2.id,
            None, connection=self.trans)
        self.failUnless(list(results))
        product_view = results[0]
        self.assertEquals(product_view.get_unit_description(), "un")

    def testGetProductAndCategoryDescription(self):
        p1 = self.create_product()
        p1.sellable.category = self.create_sellable_category()
        p1.sellable.category.description = "category"

        p2 = self.create_product()

        results = ProductFullStockView.select_by_branch(
            ProductFullStockView.q.product_id == p1.id,
            None, connection=self.trans)
        self.failUnless(list(results))
        pv = results[0]
        desc = pv.get_product_and_category_description()
        self.assertEquals(desc, "[category] Description")

        results = ProductFullStockView.select_by_branch(
            ProductFullStockView.q.product_id == p2.id,
            None, connection=self.trans)
        self.failUnless(list(results))
        pv = results[0]
        desc = pv.get_product_and_category_description()
        self.assertEquals(desc, "Description")

    def testStockCost(self):
        branch = self.create_branch()
        p1 = self.create_product(branch=branch, stock=1)

        p2 = self.create_product()

        results = ProductFullStockView.select_by_branch(
            ProductFullStockView.q.product_id == p1.id,
            None, connection=self.trans)
        self.failUnless(list(results))
        pv = results[0]
        self.assertEquals(pv.stock_cost, 10)

        branch = get_current_branch(self.trans)
        results = ProductFullStockView.select_by_branch(
            ProductFullStockView.q.product_id == p2.id,
            None, connection=self.trans)
        self.failUnless(list(results))
        pv = results[0]
        self.assertEquals(pv.stock_cost, 0)

    def testPrice(self):
        p1 = self.create_product()
        results = ProductFullStockView.select_by_branch(
            ProductFullStockView.q.product_id == p1.id,
            None, connection=self.trans)
        self.failUnless(list(results))
        pv = results[0]
        self.assertEquals(pv.price, 10)


class TestProductComponentView(DomainTest):
    def testSellable(self):
        pc1 = self.create_product_component()
        results = ProductComponentView.select(connection=self.trans)
        self.failUnless(list(results))
        pcv = results[0]
        self.assertEquals(pcv.sellable, pc1.product.sellable)


class TestSellableFullStockView(DomainTest):
    def testSelectByBranch(self):
        branch = self.create_branch()
        p1 = self.create_product(branch=branch, stock=1)
        p2 = self.create_product()

        results = SellableFullStockView.select_by_branch(
            SellableFullStockView.q.product_id == p1.id,
            branch, connection=self.trans)
        self.failUnless(list(results))

        results = SellableFullStockView.select_by_branch(
            ProductFullStockView.q.product_id == p2.id,
            branch, connection=self.trans)
        self.failUnless(list(results))
        self.assertEquals(results.count(), 1)

    def testSellable(self):
        branch = self.create_branch()
        p1 = self.create_product(branch=branch, stock=1)

        results = SellableFullStockView.select_by_branch(
            SellableFullStockView.q.product_id == p1.id,
            branch, connection=self.trans)
        self.failUnless(list(results))

        self.assertEquals(results[0].sellable, p1.sellable)

    def testPrice(self):
        branch = self.create_branch()
        p1 = self.create_product(branch=branch, stock=1)
        results = SellableFullStockView.select_by_branch(
            SellableFullStockView.q.product_id == p1.id,
            branch, connection=self.trans)
        self.failUnless(list(results))

        self.assertEquals(results[0].price, 10)


class TestSellableCategoryView(DomainTest):
    def testCategory(self):
        category = self.create_sellable_category()
        results = SellableCategoryView.select(
            SellableCategoryView.q.id == category.id,
            connection=self.trans)
        self.failUnless(list(results))
        self.assertEquals(results[0].category, category)

    def testGetCommission(self):
        category = self.create_sellable_category()
        results = SellableCategoryView.select(
            SellableCategoryView.q.id == category.id,
            connection=self.trans)
        self.failUnless(list(results))
        self.assertEquals(results[0].get_commission(), None)

        base_category = self.create_sellable_category()
        self.create_commission_source(category=base_category)
        category.category = base_category
        results = SellableCategoryView.select(
            SellableCategoryView.q.id == category.id,
            connection=self.trans)
        self.assertEquals(results[0].get_commission(), 10)

        self.create_commission_source(category=category)
        results = SellableCategoryView.select(
            SellableCategoryView.q.id == category.id,
            connection=self.trans)
        self.assertEquals(results[0].get_commission(), 10)

    def testGetInstallmentsCommission(self):
        category = self.create_sellable_category()
        results = SellableCategoryView.select(
            SellableCategoryView.q.id == category.id,
            connection=self.trans)
        self.failUnless(list(results))
        self.assertEquals(results[0].get_installments_commission(), None)

        base_category = self.create_sellable_category()
        category.category = base_category
        self.create_commission_source(category=base_category)
        results = SellableCategoryView.select(
            SellableCategoryView.q.id == category.id,
            connection=self.trans)
        self.assertEquals(results[0].get_installments_commission(), 1)

        self.create_commission_source(category=category)
        results = SellableCategoryView.select(
            SellableCategoryView.q.id == category.id,
            connection=self.trans)
        self.assertEquals(results[0].get_installments_commission(), 1)


class TestQuotationView(DomainTest):
    def testGroupQuotationPurchase(self):
        quote = QuoteGroup(connection=self.trans)
        order = self.create_purchase_order()
        order.status = PurchaseOrder.ORDER_QUOTING
        quote.add_item(order)

        self.assertEqual(order.status, PurchaseOrder.ORDER_QUOTING)
        quotations = quote.get_items()
        self.assertEqual(quotations.count(), 1)

        self.assertFalse(quotations[0].is_closed())
        quotations[0].close()

        results = QuotationView.select(
                QuotationView.q.id == quotations[0].id, connection=self.trans)
        self.failUnless(list(results))
        self.assertEquals(results.count(), 1)
        self.assertEquals(results[0].group, quote)
        self.assertEquals(results[0].quotation, quotations[0])
        self.assertEquals(results[0].purchase, order)


class TestSoldItemView(DomainTest):
    def testSelectByBranchData(self):
        branch = get_current_branch(self.trans)
        sale = self.create_sale()
        sale.branch = branch
        sellable = self.add_product(sale)
        sale.order()
        self.add_payments(sale, method_type='money')
        sale.confirm()

        results = SoldItemView.select_by_branch_date(None, None, None,
                                                     connection=self.trans)
        self.failUnless(results)

        results = SoldItemView.select_by_branch_date(None, branch, None,
                                                     connection=self.trans)
        self.failUnless(results)

        results = SoldItemView.select_by_branch_date(
            SoldItemView.q.id == sellable.id, branch, None,
            connection=self.trans)
        self.assertEquals(results.count(), 1)

        today = datetime.date.today()
        results = SoldItemView.select_by_branch_date(
            SoldItemView.q.id == sellable.id, None, today,
            connection=self.trans)
        self.assertEquals(results.count(), 1)

        yesterday = today - datetime.timedelta(days=1)
        results = SoldItemView.select_by_branch_date(
            SoldItemView.q.id == sellable.id, None, (yesterday, today),
            connection=self.trans)
        self.assertEquals(results.count(), 1)

        yesterday = today - datetime.timedelta(days=1)
        results = SoldItemView.select_by_branch_date(
            None, None, (yesterday, today),
            connection=self.trans)

        self.failUnless(results)

    def testAverageCost(self):
        sale = self.create_sale()
        sellable = self.add_product(sale)
        sale.order()
        self.add_payments(sale, method_type='money')
        sale.confirm()

        results = SoldItemView.select(
            SoldItemView.q.id == sellable.id,
            connection=self.trans)
        self.failUnless(results)
        self.assertEquals(results[0].average_cost, 0)


class TestAccountView(DomainTest):
    def testAccount(self):
        account = self.create_account()
        results = AccountView.select(AccountView.q.id == account.id,
                                     connection=self.trans)
        self.failUnless(list(results))
        self.assertEquals(results[0].account, account)

    def testParentAccount(self):
        account = self.create_account()
        account.parent = self.create_account()
        results = AccountView.select(AccountView.q.id == account.id,
                                     connection=self.trans)
        self.failUnless(list(results))
        self.assertEquals(results[0].parent_account, account.parent)

    def testMatches(self):
        account = self.create_account()
        account.parent = self.create_account()
        results = AccountView.select(AccountView.q.id == account.id,
                                     connection=self.trans)
        self.failUnless(list(results))
        self.failUnless(results[0].matches(account.id))
        self.failUnless(results[0].matches(account.parent.id))

    def testGetCombinedValue(self):
        a1 = self.create_account()
        a2 = self.create_account()
        results = AccountView.select(AccountView.q.id == a1.id,
                                     connection=self.trans)
        self.failUnless(list(results))
        self.assertEquals(results[0].get_combined_value(), 0)

        t1 = self.create_account_transaction(a1)
        t1.source_account = a1
        t1.account = a2
        t1.sync()

        results = AccountView.select(AccountView.q.id == a1.id,
                                     connection=self.trans)
        self.failUnless(list(results))
        self.assertEquals(results.count(), 1)
        self.assertEquals(results[0].get_combined_value(), -1)

        t2 = self.create_account_transaction(a2)
        t2.source_account = a2
        t2.account = a1
        t2.sync()

        results = AccountView.select(AccountView.q.id == a1.id,
                                     connection=self.trans)
        self.failUnless(list(results))
        self.assertEquals(results.count(), 1)
        self.assertEquals(results[0].get_combined_value(), 0)

    def testRepr(self):
        a1 = self.create_account()
        results = AccountView.select(AccountView.q.id == a1.id,
                                     connection=self.trans)
        self.failUnless(list(results))
        self.assertEquals(repr(results[0]), '<AccountView Test Account>')
