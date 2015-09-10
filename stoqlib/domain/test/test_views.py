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


__tests__ = 'stoqlib/domain/views.py'

import datetime
from decimal import Decimal

from kiwi.datatypes import converter

from stoqlib.database.expr import Date
from stoqlib.database.runtime import get_current_branch
from stoqlib.database.viewable import Viewable
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment, PaymentChangeHistory
from stoqlib.domain.payment.views import (BasePaymentView, InPaymentView,
                                          OutPaymentView, CardPaymentView,
                                          InCheckPaymentView,
                                          PaymentChangeHistoryView)
from stoqlib.domain.product import (ProductSupplierInfo, ProductStockItem,
                                    Storable, Product, StockTransactionHistory)
from stoqlib.domain.purchase import PurchaseOrder, QuoteGroup
from stoqlib.domain.sellable import Sellable
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.domain.views import AccountView
from stoqlib.domain.views import ClientWithSalesView
from stoqlib.domain.views import ProductBrandByBranchView
from stoqlib.domain.views import ProductComponentView
from stoqlib.domain.views import ProductFullStockView
from stoqlib.domain.views import ProductFullStockItemView
from stoqlib.domain.views import ProductFullStockItemSupplierView
from stoqlib.domain.views import QuotationView
from stoqlib.domain.views import SellableCategoryView
from stoqlib.domain.views import SellableFullStockView
from stoqlib.domain.views import SoldItemView
from stoqlib.lib.dateutils import localtoday
from stoqlib.lib.introspection import get_all_classes


def _get_all_views():
    for klass in get_all_classes('stoqlib/domain'):
        try:
            # Exclude Viewable, since we just want to test it's subclasses
            if not issubclass(klass, Viewable) or klass is Viewable:
                continue
            # This is a base viewable for other classes that should not be
            # tested.
            if klass.__name__ == 'BaseTransferView':
                continue
        except TypeError:
            continue

        yield klass


class TestViewsGeneric(DomainTest):
    """Generic tests for views"""

    def _test_view(self, view):
        from stoqlib.domain.person import Branch
        if view.__name__ == 'ProductWithStockBranchView':
            # This viewable must be queried with a branch
            branch = self.store.find(Branch).any()
            results_list = self.store.find(view, branch_id=branch.id)
        elif view.__name__ in ['SellableFullStockView',
                               'ProductBrandByBranchView']:
            # This viewable must be queried with a branch
            branch = self.store.find(Branch).any()
            results_list = view.find_by_branch(self.store, branch)
        elif view.__name__ == 'ProductBranchStockView':
            # This viewable must be queried with a storable
            storable = self.store.find(Storable).any()
            results_list = self.store.find(view, storable_id=storable.id)
        else:
            # This viewable must show everything
            results_list = self.store.find(view)

        # See if there are no duplicates
        ids_set = set()
        for result in results_list:
            self.assertNotIn(result.id, ids_set)
            ids_set.add(result.id)


for view_ in _get_all_views():
    name = 'test' + view_.__name__
    func = lambda s, v=view_: TestViewsGeneric._test_view(s, v)
    func.__name__ = name
    setattr(TestViewsGeneric, name, func)
    del func


class TestBasePaymentView(DomainTest):
    def test_post_search_callback(self):
        self.create_payment()
        sresults = BasePaymentView.find_pending(self.store)
        results = BasePaymentView.post_search_callback(sresults=sresults)
        self.assertEquals(results[0], ('count', 'sum'))
        self.assertIsNotNone(results[1])

    def test_can_cancel_payment(self):
        payment = self.create_payment(payment_type=Payment.TYPE_IN)
        payment.status = Payment.STATUS_PENDING
        payment_view = self.store.find(InPaymentView, id=payment.id).one()
        self.assertTrue(payment_view.can_cancel_payment())

        payment.status = Payment.STATUS_PREVIEW
        payment_view = self.store.find(InPaymentView, id=payment.id).one()
        self.assertFalse(payment_view.can_cancel_payment())

        sale = self.create_sale()
        payment = self.add_payments(sale)[0]
        view = self.store.find(InPaymentView, id=payment.id).one()
        self.assertFalse(view.can_cancel_payment())

        purchase = self.create_purchase_order()
        payment = self.add_payments(purchase)[0]
        view = self.store.find(OutPaymentView, id=payment.id).one()
        self.assertFalse(view.can_cancel_payment())

    def test_is_late(self):
        payment = self.create_payment(payment_type=Payment.TYPE_IN)
        payment.due_date = localtoday() + datetime.timedelta(-4)
        payment.status = Payment.STATUS_PREVIEW
        view = self.store.find(InPaymentView, id=payment.id).one()
        self.assertTrue(view.is_late())
        payment.status = Payment.STATUS_PAID
        view = self.store.find(InPaymentView, id=payment.id).one()
        self.assertFalse(view.is_late())

    def test_get_days_late(self):
        payment = self.create_payment(payment_type=Payment.TYPE_IN)
        view = self.store.find(InPaymentView, id=payment.id).one()
        self.assertFalse(view.get_days_late())

        payment.due_date = localtoday() + datetime.timedelta(-4)
        view = self.store.find(InPaymentView, id=payment.id).one()
        self.assertEquals(view.get_days_late(), 4)

        payment.due_date = localtoday() + datetime.timedelta(+4)
        view = self.store.find(InPaymentView, id=payment.id).one()
        self.assertFalse(view.get_days_late())

    def test_is_paid(self):
        payment = self.create_payment(payment_type=Payment.TYPE_IN)
        payment.status = Payment.STATUS_PENDING
        view = self.store.find(InPaymentView, id=payment.id).one()
        self.assertFalse(view.is_paid())

        payment.status = Payment.STATUS_PAID
        view = self.store.find(InPaymentView, id=payment.id).one()
        self.assertTrue(view.is_paid())

    def test_find_pending(self):
        due_date = localtoday() + datetime.timedelta(-4), localtoday()
        for i in range(5):
            if i % 2 == 0:
                payment = self.create_payment(payment_type=Payment.TYPE_IN)
                payment.status = Payment.STATUS_PENDING
                payment.due_date = localtoday() + datetime.timedelta(-2)
            else:
                payment = self.create_payment(payment_type=Payment.TYPE_IN)
                payment.status = Payment.STATUS_PENDING
                payment.due_date = Date(localtoday())

        result = InPaymentView.find_pending(store=self.store, due_date=due_date)
        self.assertEquals(result.count(), 5)

        result = InPaymentView.find_pending(store=self.store,
                                            due_date=Date(localtoday()))
        self.assertEquals(result.count(), 2)
        result = InPaymentView.find_pending(store=self.store,
                                            due_date=None)
        self.assertEquals(result.count(), 7)


class TestInPaymentView(DomainTest):
    def test_renegotiation(self):
        payment = self.create_payment(payment_type=Payment.TYPE_IN)
        self.create_payment_renegotiation(group=payment.group)
        result = self.store.find(InPaymentView, id=payment.id).one()
        self.assertEquals(result.renegotiation.client.person.name, u'Client')

    def test_renegotiated(self):
        payment = self.create_payment(payment_type=Payment.TYPE_IN)
        payment.set_pending()
        payment.group.renegotiation = self.create_payment_renegotiation(
            group=payment.group)
        payment.group.renegotiation.set_renegotiated()
        result = self.store.find(InPaymentView, id=payment.id).one()
        self.assertEquals(result.renegotiated.client.person.name, u'Client')

    def test_get_parent(self):
        sale = self.create_sale()
        payment = self.add_payments(sale)
        result = self.store.find(InPaymentView, id=payment[0].id).one()
        self.assertIs(result.get_parent(), sale)


class TestCardPaymentView(DomainTest):
    def test_status_str(self):
        payment = self.create_card_payment(payment_type=Payment.TYPE_IN)
        result = self.store.find(CardPaymentView, id=payment.id).one()
        self.assertEquals(result.status_str, u'Preview')

    def test_renegotiation(self):
        payment = self.create_card_payment(payment_type=Payment.TYPE_IN)
        self.create_payment_renegotiation(group=payment.group)
        result = self.store.find(CardPaymentView, id=payment.id).one()
        self.assertEquals(result.renegotiation.client.person.name, u'Client')


class Test_BillandCheckPaymentView(DomainTest):
    def test_status_str(self):
        method = self.store.find(PaymentMethod, method_name=u'check').one()
        p = self.create_payment(payment_type=Payment.TYPE_IN,
                                method=method)
        view = self.store.find(InCheckPaymentView, id=p.id).one()
        self.assertEquals(view.status_str, u'Preview')

    def test_method_description(self):
        method = self.store.find(PaymentMethod, method_name=u'check').one()
        p = self.create_payment(payment_type=Payment.TYPE_IN,
                                method=method)
        view = self.store.find(InCheckPaymentView, id=p.id).one()
        self.assertEquals(view.method_description, u'Check')


class TestPaymentChangeHistoryView(DomainTest):
    def test_changed_field(self):
        payment = self.create_payment()
        history = PaymentChangeHistory(payment=payment,
                                       change_reason=u'Teste test test')
        view = self.store.find(PaymentChangeHistoryView, id=history.id).one()
        self.assertIsNotNone(view.changed_field)

        history.last_due_date = Date(localtoday())
        history.last_status = Payment.STATUS_PENDING
        view = self.store.find(PaymentChangeHistoryView, id=history.id).one()
        self.assertEquals(view.changed_field, u'Due Date')

        history.last_due_date = None
        view = self.store.find(PaymentChangeHistoryView, id=history.id).one()
        self.assertEquals(view.changed_field, u'Status')

    def test_from_value(self):
        payment = self.create_payment()
        history = PaymentChangeHistory(payment=payment,
                                       change_reason=u'Teste test test')
        view = self.store.find(PaymentChangeHistoryView, id=history.id).one()
        self.assertIsNotNone(view.from_value)

        history.last_due_date = Date(localtoday())
        due_date = converter.as_string(datetime.date, history.last_due_date)
        history.last_status = Payment.STATUS_PENDING
        view = self.store.find(PaymentChangeHistoryView, id=history.id).one()
        self.assertEquals(view.from_value, due_date)

        history.last_due_date = None
        status = Payment.statuses[history.last_status]
        view = self.store.find(PaymentChangeHistoryView, id=history.id).one()
        self.assertEquals(view.from_value, status)

    def test_to_value(self):
        payment = self.create_payment()
        history = PaymentChangeHistory(payment=payment,
                                       change_reason=u'Teste test test')
        view = self.store.find(PaymentChangeHistoryView, id=history.id).one()
        self.assertIsNotNone(view.to_value)

        history.new_due_date = Date(localtoday())
        due_date = converter.as_string(datetime.date, history.new_due_date)
        history.new_status = Payment.STATUS_CONFIRMED
        view = self.store.find(PaymentChangeHistoryView, id=history.id).one()
        self.assertEquals(view.to_value, due_date)

        history.new_due_date = None
        status = Payment.statuses[history.new_status]
        view = self.store.find(PaymentChangeHistoryView, id=history.id).one()
        self.assertEquals(view.to_value, status)


class TestProductFullStockView(DomainTest):
    def test_select_by_branch(self):
        branch = self.create_branch()
        p1 = self.create_product(branch=branch, stock=1)

        results = ProductFullStockView.find_by_branch(self.store, branch)
        self.failUnless(list(results))
        # FIXME: Storm does not support count() with group_by
        # self.assertEquals(results.count(), 1)
        # The results should have 11 items. 10 for the products that already
        # exists, and 1 more for the one we created
        self.assertEquals(len(list(results)), 11)

        results = ProductFullStockView.find_by_branch(self.store, branch)
        results = results.find(ProductFullStockView.product_id == p1.id)
        self.failUnless(list(results))
        self.assertEquals(len(list(results)), 1)

    def test_post_search_callback(self):
        self.clean_domain([StockTransactionHistory, ProductSupplierInfo, ProductStockItem,
                           Storable, Product])

        branch = self.create_branch()
        for i in range(20):
            self.create_product(branch=branch, stock=5)
        for i in range(10):
            self.create_product(branch=branch, stock=10)

        # Get just the products we created here
        sresults = self.store.find(ProductFullStockView)

        postresults = ProductFullStockView.post_search_callback(sresults)
        self.assertEqual(postresults[0], ('count', 'sum'))
        self.assertEqual(
            # Total stock = (10 * 10) + (20 * 5) = 200
            self.store.execute(postresults[1]).get_one(), (30, 200))

        sresults = sresults.find(ProductFullStockView.stock > 5)
        postresults = ProductFullStockView.post_search_callback(sresults)
        self.assertEqual(postresults[0], ('count', 'sum'))
        self.assertEqual(
            # Total stock = (10 * 10) = 100
            self.store.execute(postresults[1]).get_one(), (10, 100))

    def test_unit_description(self):
        p1 = self.create_product()
        p1.sellable.unit = self.create_sellable_unit()
        p1.sellable.unit.description = u"kg"

        p2 = self.create_product()

        results = ProductFullStockView.find_by_branch(self.store, None)
        results = results.find(ProductFullStockView.product_id == p1.id)
        self.failUnless(list(results))
        product_view = results[0]
        self.assertEquals(product_view.unit_description, u"kg")

        results = ProductFullStockView.find_by_branch(self.store, None).find(
            ProductFullStockView.product_id == p2.id)
        self.failUnless(list(results))
        product_view = results[0]
        self.assertEquals(product_view.unit_description, u"un")

    def test_get_product_and_category_description(self):
        p1 = self.create_product()
        p1.sellable.category = self.create_sellable_category()
        p1.sellable.category.description = u"category"

        p2 = self.create_product()

        results = ProductFullStockView.find_by_branch(self.store, None).find(
            ProductFullStockView.product_id == p1.id)
        self.failUnless(list(results))
        pv = results[0]
        desc = pv.get_product_and_category_description()
        self.assertEquals(desc, u"[category] Description")

        results = ProductFullStockView.find_by_branch(self.store, None).find(
            ProductFullStockView.product_id == p2.id)
        self.failUnless(list(results))
        pv = results[0]
        desc = pv.get_product_and_category_description()
        self.assertEquals(desc, u"Description")

    def test_stock_cost(self):
        branch = self.create_branch()
        p1 = self.create_product(branch=branch, stock=1)

        p2 = self.create_product()

        results = ProductFullStockView.find_by_branch(self.store, None).find(
            ProductFullStockView.product_id == p1.id)
        self.failUnless(list(results))
        pv = results[0]
        self.assertEquals(pv.stock_cost, 10)

        branch = get_current_branch(self.store)
        results = ProductFullStockView.find_by_branch(self.store, None).find(
            ProductFullStockView.product_id == p2.id)
        self.failUnless(list(results))
        pv = results[0]
        self.assertEquals(pv.stock_cost, 0)

    def test_price(self):
        p1 = self.create_product()
        results = ProductFullStockView.find_by_branch(self.store, None).find(
            ProductFullStockView.product_id == p1.id)
        self.failUnless(list(results))
        pv = results[0]
        self.assertEquals(pv.price, 10)

        # Set a sale price
        sellable = p1.sellable
        sellable.on_sale_price = Decimal('5.55')

        # And a interval that includes today
        yesterday = localtoday() - datetime.timedelta(days=1)
        tomorrow = localtoday() + datetime.timedelta(days=1)
        sellable.on_sale_start_date = yesterday
        sellable.on_sale_end_date = tomorrow

        results = ProductFullStockView.find_by_branch(self.store, None).find(
            ProductFullStockView.product_id == p1.id)
        self.assertEquals(results[0].price, Decimal('5.55'))

        # Testing with a sale price set, but in the past
        date1 = localtoday() - datetime.timedelta(days=10)
        date2 = localtoday() - datetime.timedelta(days=5)
        sellable.on_sale_start_date = date1
        sellable.on_sale_end_date = date2

        results = ProductFullStockView.find_by_branch(self.store, None).find(
            ProductFullStockView.product_id == p1.id)
        self.assertEquals(results[0].price, 10)

    def test_with_unblocked_sellables_query(self):
        # This is used in the purchase wizard and breaks storm
        from stoqlib.domain.sellable import Sellable

        p1 = self.create_product()
        supplier = self.create_supplier()

        # Product should appear when querying without a supplier
        query = Sellable.get_unblocked_sellables_query(self.store)
        results = self.store.find(ProductFullStockView, query)
        self.assertTrue(p1.id in [p.product_id for p in results])

        # But should not appear when querying with a supplier
        # When querying using the supplier, we should use the
        # ProductFullStockSupplierView instead.
        query = Sellable.get_unblocked_sellables_query(self.store,
                                                       supplier=supplier)
        results = self.store.find(ProductFullStockItemSupplierView, query)
        self.assertFalse(p1.id in [p.id for p in results])

        # Now relate the two
        ProductSupplierInfo(store=self.store,
                            supplier=supplier,
                            product=p1,
                            is_main_supplier=True)

        # And it should appear now
        query = Sellable.get_unblocked_sellables_query(self.store,
                                                       supplier=supplier)
        results = self.store.find(ProductFullStockItemSupplierView, query)
        self.assertTrue(p1.id in [s.product_id for s in results])

        # But should not appear for a different supplier
        other_supplier = self.create_supplier()
        query = Sellable.get_unblocked_sellables_query(self.store,
                                                       supplier=other_supplier)
        results = self.store.find(ProductFullStockItemSupplierView, query)
        self.assertFalse(p1.id in [s.product_id for s in results])

    def test_highjacked_equality(self):
        self.clean_domain([StockTransactionHistory, ProductStockItem, Storable,
                           ProductSupplierInfo, Product])

        branch = self.create_branch()
        self.create_product(branch=branch, stock=1)

        res = self.store.find(ProductFullStockView)
        res_by_branch = ProductFullStockView.find_by_branch(self.store, branch)

        self.assertEqual(res[0], res_by_branch[0])
        self.assertEqual(res_by_branch[0], res[0])

        product = self.create_product()
        other_viewable = self.store.find(
            ProductFullStockView, Sellable.id == product.sellable.id).one()
        self.assertNotEqual(res[0], other_viewable)
        self.assertNotEqual(res[0], object())

    def test_get_parent(self):
        parent = self.create_product()
        product = self.create_product(parent=parent)

        viewable = self.store.find(ProductFullStockView,
                                   Sellable.id == product.sellable.id).one()
        parent_viewable = self.store.find(
            ProductFullStockView, Sellable.id == parent.sellable.id).one()

        self.assertIsNone(parent_viewable.get_parent())
        self.assertEqual(viewable.get_parent(), parent_viewable)


class TestProductComponentView(DomainTest):
    def test_sellable(self):
        pc1 = self.create_product_component()
        pc1.product.is_composed = True
        results = self.store.find(ProductComponentView)
        self.failUnless(list(results))
        pcv = results[0]
        self.assertEquals(pcv.sellable, pc1.product.sellable)


class TestSellableFullStockView(DomainTest):
    def test_select_by_branch(self):
        branch = self.create_branch()
        p1 = self.create_product(branch=branch, stock=1)
        p2 = self.create_product()

        results = SellableFullStockView.find_by_branch(self.store, branch).find(
            SellableFullStockView.product_id == p1.id)
        self.failUnless(list(results))

        results = SellableFullStockView.find_by_branch(self.store, branch).find(
            SellableFullStockView.product_id == p2.id,)
        self.failUnless(list(results))
        # FIXME: Storm does not support count() with group_by
        # self.assertEquals(results.count(), 1)
        self.assertEquals(len(list(results)), 1)

    def test_sellable(self):
        branch = self.create_branch()
        p1 = self.create_product(branch=branch, stock=1)

        results = SellableFullStockView.find_by_branch(self.store, branch).find(
            SellableFullStockView.product_id == p1.id)
        self.failUnless(list(results))

        self.assertEquals(results[0].sellable, p1.sellable)

    def test_price(self):
        branch = self.create_branch()
        p1 = self.create_product(branch=branch, stock=1, price=Decimal('10.15'))
        results = SellableFullStockView.find_by_branch(self.store, branch).find(
            SellableFullStockView.product_id == p1.id)
        self.failUnless(list(results))

        self.assertEquals(results[0].price, Decimal('10.15'))

        # Set a sale price
        sellable = p1.sellable
        sellable.on_sale_price = Decimal('5.55')

        # And a interval that includes today
        yesterday = localtoday() - datetime.timedelta(days=1)
        tomorrow = localtoday() + datetime.timedelta(days=1)
        sellable.on_sale_start_date = yesterday
        sellable.on_sale_end_date = tomorrow

        results = SellableFullStockView.find_by_branch(self.store, branch).find(
            SellableFullStockView.product_id == p1.id)
        self.assertEquals(results[0].price, Decimal('5.55'))

        # Testing with a sale price set, but in the past
        date1 = localtoday() - datetime.timedelta(days=10)
        date2 = localtoday() - datetime.timedelta(days=5)
        sellable.on_sale_start_date = date1
        sellable.on_sale_end_date = date2

        results = SellableFullStockView.find_by_branch(self.store, branch).find(
            SellableFullStockView.product_id == p1.id)
        self.assertEquals(results[0].price, Decimal('10.15'))


class TestSellableCategoryView(DomainTest):
    def test_category(self):
        category = self.create_sellable_category()
        results = self.store.find(SellableCategoryView, id=category.id)
        self.failUnless(list(results))
        self.assertEquals(results[0].category, category)

    def test_get_commission(self):
        category = self.create_sellable_category()
        results = self.store.find(SellableCategoryView, id=category.id)
        self.failUnless(list(results))
        self.assertEquals(results[0].get_commission(), None)

        base_category = self.create_sellable_category()
        self.create_commission_source(category=base_category)
        category.category = base_category
        results = self.store.find(SellableCategoryView, id=category.id)
        self.assertEquals(results[0].get_commission(), 10)

        self.create_commission_source(category=category)
        results = self.store.find(SellableCategoryView, id=category.id)
        self.assertEquals(results[0].get_commission(), 10)

    def test_get_installments_commission(self):
        category = self.create_sellable_category()
        results = self.store.find(SellableCategoryView, id=category.id)
        self.failUnless(list(results))
        self.assertEquals(results[0].get_installments_commission(), None)

        base_category = self.create_sellable_category()
        category.category = base_category
        self.create_commission_source(category=base_category)
        results = self.store.find(SellableCategoryView, id=category.id)
        self.assertEquals(results[0].get_installments_commission(), 1)

        self.create_commission_source(category=category)
        results = self.store.find(SellableCategoryView, id=category.id)
        self.assertEquals(results[0].get_installments_commission(), 1)

    def test_get_suggested_markup(self):

        parent_category = self.create_sellable_category()
        parent_category.suggested_markup = 100

        category = self.create_sellable_category()
        category.suggested_markup = 200

        view = self.store.find(SellableCategoryView, id=category.id).one()
        self.assertEquals(view.get_suggested_markup(), 200)

        category.category = parent_category
        category.suggested_markup = None
        view = self.store.find(SellableCategoryView, id=category.id).one()
        self.assertEquals(view.get_suggested_markup(), 100)


class TestQuotationView(DomainTest):
    def test_group_quotation_purchase(self):
        order = self.create_purchase_order()
        quote = QuoteGroup(store=self.store, branch=order.branch)
        order.status = PurchaseOrder.ORDER_QUOTING
        quote.add_item(order)

        self.assertEqual(order.status, PurchaseOrder.ORDER_QUOTING)
        quotations = quote.get_items()
        self.assertEqual(quotations.count(), 1)

        self.assertFalse(quotations[0].is_closed())
        quotations[0].close()

        results = self.store.find(QuotationView, id=quotations[0].id)
        self.failUnless(list(results))
        self.assertEquals(results.count(), 1)
        self.assertEquals(results[0].group, quote)
        self.assertEquals(results[0].quotation, quotations[0])
        self.assertEquals(results[0].purchase, order)


class TestSoldItemView(DomainTest):

    def test_average_cost(self):
        sale = self.create_sale()
        sellable = self.add_product(sale)
        sale.order()
        self.add_payments(sale, method_type=u'money')
        sale.confirm()

        view = self.store.find(SoldItemView, id=sellable.id).one()
        self.assertEquals(view.average_cost, 0)


class TestAccountView(DomainTest):
    def test_account(self):
        account = self.create_account()
        results = self.store.find(AccountView, id=account.id)
        self.failUnless(list(results))
        self.assertEquals(results[0].account, account)

    def test_parent_account(self):
        account = self.create_account()
        account.parent = self.create_account()
        results = self.store.find(AccountView, id=account.id)
        self.failUnless(list(results))
        self.assertEquals(results[0].parent_account, account.parent)

    def test_matches(self):
        account = self.create_account()
        account.parent = self.create_account()
        results = self.store.find(AccountView, id=account.id)
        self.failUnless(list(results))
        self.failUnless(results[0].matches(account.id))
        self.failUnless(results[0].matches(account.parent.id))

    def test_get_combined_value(self):
        a1 = self.create_account()
        a2 = self.create_account()
        results = self.store.find(AccountView, id=a1.id)
        self.failUnless(list(results))
        self.assertEquals(results[0].get_combined_value(), 0)

        t1 = self.create_account_transaction(a1, 1)
        t1.source_account = a1
        t1.account = a2
        self.store.flush()
        t2 = self.create_account_transaction(a1, 9)
        t2.source_account = a1
        t2.account = a2
        self.store.flush()

        results = self.store.find(AccountView, id=a1.id)
        self.failUnless(list(results))
        self.assertEquals(results.count(), 1)
        # The negative sum of t1 and t2
        self.assertEquals(results[0].get_combined_value(), -10)

        t3 = self.create_account_transaction(a2, 10)
        t3.source_account = a2
        t3.account = a1
        self.store.flush()
        t4 = self.create_account_transaction(a2, 90)
        t4.source_account = a2
        t4.account = a1
        self.store.flush()

        results = self.store.find(AccountView, id=a1.id)
        self.failUnless(list(results))
        self.assertEquals(results.count(), 1)
        # The negative sum of t1 and t2 plus the sum of t3 and t4
        self.assertEquals(results[0].get_combined_value(), 90)

    def test_repr(self):
        a1 = self.create_account()
        results = self.store.find(AccountView, id=a1.id)
        self.failUnless(list(results))
        self.assertEquals(repr(results[0]), u'<AccountView Test Account>')


class TestProductFullStockItemView(DomainTest):

    def test_select(self):
        product = self.store.find(Product)[0]

        order = self.create_purchase_order()
        order.add_item(product.sellable, 1)
        order.status = PurchaseOrder.ORDER_CONFIRMED

        order2 = self.create_purchase_order()
        order2.add_item(product.sellable, 4)
        order2.status = PurchaseOrder.ORDER_CONFIRMED

        # This viewable should return only one item for each existing product,
        # event if there is more than one purchase order for the product.
        results = self.store.find(ProductFullStockItemView)
        ids = [r.id for r in results]
        self.assertEquals(ids.count(product.sellable.id), 1)


class TestProductBrandByBranchView(DomainTest):
    def test_find_by_category(self):
        # Creating product 1
        branch = self.create_branch(name=u"branch1")
        p1 = self.create_product(branch=branch, stock=5)
        p1.sellable.category = self.create_sellable_category(description=u"Category")
        p1.brand = u"Black Mesa"
        # Creating product 2
        branch2 = self.create_branch(name=u"branch2")
        p2 = self.create_product(branch=branch2, stock=1)
        p2.sellable.category = p1.sellable.category
        category = p1.sellable.category
        p2.brand = u"Black Mesa"

        # Search with a specific category
        results = ProductBrandByBranchView.find_by_category(self.store,
                                                            category).find()
        results.order_by(ProductBrandByBranchView.id)

        # Checking the quantity for each product
        self.assertEqual(results[0].quantity, 5)
        self.assertEqual(results[1].quantity, 1)

        # Checking total products
        total_products = 0
        for i in results:
            total_products += i.quantity
        self.assertEqual(total_products, 6)

        # Without category, total item shouldnt be 0
        results2 = ProductBrandByBranchView.find_by_category(self.store,
                                                             None).find()
        total_products = 0
        for i in results2:
            total_products += i.quantity
        self.assertNotEqual(total_products, 0)


class TestClientWithSalesView(DomainTest):
    def test_find_by_birth_date(self):
        client = self.create_client()
        client_view_obj = self.store.find(
            ClientWithSalesView, id=client.id).one()
        individual = client.person.individual

        # Clients without birthdate should be excluded by default
        self.assertNotIn(
            client_view_obj,
            list(ClientWithSalesView.find_by_birth_date(
                self.store, datetime.datetime(2015, 4, 20))))

        individual.birth_date = datetime.datetime(1988, 4, 21)

        # The client should not appear here since his birthday is different
        # from the one we are querying
        self.assertNotIn(
            client_view_obj,
            list(ClientWithSalesView.find_by_birth_date(
                self.store, datetime.datetime(2015, 4, 20))))
        self.assertNotIn(
            client_view_obj,
            list(ClientWithSalesView.find_by_birth_date(
                self.store, (datetime.datetime(2015, 2, 10),
                             datetime.datetime(2015, 4, 20)))))

        self.assertIn(
            client_view_obj,
            list(ClientWithSalesView.find_by_birth_date(
                self.store, datetime.datetime(2015, 4, 21))))
        self.assertIn(
            client_view_obj,
            list(ClientWithSalesView.find_by_birth_date(
                self.store, (datetime.datetime(2015, 4, 10),
                             datetime.datetime(2015, 4, 28)))))

        branch = self.create_branch()

        # Adding the branch to the query should exclude the client again
        # as there isn't any sale referencing it on that branch yet
        self.assertNotIn(
            client_view_obj,
            list(ClientWithSalesView.find_by_birth_date(
                self.store, datetime.datetime(2015, 4, 21), branch=branch)))
        self.assertNotIn(
            client_view_obj,
            list(ClientWithSalesView.find_by_birth_date(
                self.store, (datetime.datetime(2015, 4, 10),
                             datetime.datetime(2015, 4, 28)), branch=branch)))

        sale = self.create_sale()
        sale.branch = branch
        sale.client = client

        self.assertIn(
            client_view_obj,
            list(ClientWithSalesView.find_by_birth_date(
                self.store, datetime.datetime(2015, 4, 21), branch=branch)))
        self.assertIn(
            client_view_obj,
            list(ClientWithSalesView.find_by_birth_date(
                self.store, (datetime.datetime(2015, 4, 10),
                             datetime.datetime(2015, 4, 28)), branch=branch)))

        other_sale = self.create_sale()
        other_sale.branch = branch
        other_sale.client = client

        # Even with another sale, the query should be distinct
        self.assertEqual(
            [client_view_obj],
            list(ClientWithSalesView.find_by_birth_date(
                self.store, datetime.datetime(2015, 4, 21), branch=branch)))
        self.assertEqual(
            [client_view_obj],
            list(ClientWithSalesView.find_by_birth_date(
                self.store, (datetime.datetime(2015, 4, 10),
                             datetime.datetime(2015, 4, 28)), branch=branch)))
