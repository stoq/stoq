# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2007 Async Open Source <http://www.async.com.br>
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
from decimal import Decimal

from kiwi.currency import currency
import mock
from stoqdrivers.enum import TaxType

from stoqlib.exceptions import SellableError, TaxError
from stoqlib.domain.image import Image
from stoqlib.domain.product import Storable, StockTransactionHistory
from stoqlib.domain.sale import Sale
from stoqlib.domain.sellable import (Sellable,
                                     SellableCategory,
                                     SellableUnit,
                                     SellableTaxConstant,
                                     ClientCategoryPrice)
from stoqlib.domain.taxes import ProductTaxTemplate, ProductIcmsTemplate
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.domain.views import (ProductFullStockView,
                                  ProductFullWithClosedStockView,
                                  ProductClosedStockView)
from stoqlib.lib.dateutils import localdate
from stoqlib.lib.parameters import sysparam

__tests__ = 'stoqlib/domain/sellable.py'


class TestSellableUnit(DomainTest):
    def test_get_description(self):
        unit = SellableUnit(store=self.store,
                            description=u'foo')
        self.assertEqual(unit.get_description(), u'foo')


class TestSellableTaxConstant(DomainTest):
    def test_get_description(self):
        constant = SellableTaxConstant(store=self.store,
                                       description=u'foo')
        self.assertEqual(constant.get_description(), u'foo')

    def test_get_value(self):
        constant = SellableTaxConstant(store=self.store,
                                       tax_type=TaxType.NONE)
        self.assertEqual(constant.get_value(), 'TAX_NONE')

        constant = SellableTaxConstant(store=self.store,
                                       tax_type=TaxType.EXEMPTION)
        self.assertEqual(constant.get_value(), 'TAX_EXEMPTION')

        constant = SellableTaxConstant(store=self.store,
                                       tax_type=TaxType.SUBSTITUTION)
        self.assertEqual(constant.get_value(), 'TAX_SUBSTITUTION')

        constant = SellableTaxConstant(store=self.store,
                                       tax_type=TaxType.SERVICE)
        self.assertEqual(constant.get_value(), 'TAX_SERVICE')


class TestSellableCategory(DomainTest):
    def setUp(self):
        DomainTest.setUp(self)
        self._base_category = self._create_category(u'Monitor')

    def test_get_description(self):
        category = self._create_category(u'LCD', parent=self._base_category)
        self.assertEqual(category.get_description(), u"LCD")
        self.assertEqual(category.full_description, u"Monitor:LCD")

        sub_category = self._create_category(u"29'", category)
        self.assertEqual(sub_category.get_description(), u"29'")
        self.assertEqual(sub_category.full_description, u"Monitor:LCD:29'")

    def test_markup(self):
        self._base_category.suggested_markup = currency('10')
        category1 = self._create_category(u'LCD', parent=self._base_category)
        category2 = self._create_category(u'LCD', parent=self._base_category)
        category3 = self._create_category(u'LCD', parent=self._base_category)

        category1.suggested_markup = None
        category2.suggested_markup = currency(0)
        category3.suggested_markup = currency(5)

        self.assertEqual(category1.get_markup(), 10)
        self.assertEqual(category2.get_markup(), 0)
        self.assertEqual(category3.get_markup(), 5)

    def test_get_base_categories(self):
        categories = SellableCategory.get_base_categories(self.store)
        count = categories.count()
        base_category = SellableCategory(description=u"Monitor",
                                         store=self.store)
        category = SellableCategory(description=u"LCD Monitor",
                                    category=base_category,
                                    store=self.store)
        categories = SellableCategory.get_base_categories(self.store)
        self.assertTrue(base_category in categories)
        self.assertFalse(category in categories)
        self.assertEqual(categories.count(), count + 1)

    def test_get_tax_constant(self):
        category = self._create_category(u'LCD', parent=self._base_category)

        self.assertEqual(category.get_tax_constant(), None)

        constant = self.create_sellable_tax_constant()
        self._base_category.tax_constant = constant
        self.assertEqual(category.get_tax_constant(), constant)

        constant2 = self.create_sellable_tax_constant()
        category.tax_constant = constant2
        self.assertEqual(category.get_tax_constant(), constant2)

    def test_get_children_recursively(self):
        base_category = SellableCategory(description=u"Monitor",
                                         store=self.store)
        category = SellableCategory(description=u"LCD Monitor",
                                    category=base_category,
                                    store=self.store)

        self.assertEqual(category.get_children_recursively(), set())
        self.assertEqual(base_category.get_children_recursively(), set([category]))

    def test_on_create(self):
        category = self._create_category(u'cat')
        with mock.patch('stoqlib.domain.sellable.CategoryCreateEvent') as f:
            category.on_create()

        f.emit.assert_called_once_with(category)

    def test_on_update(self):
        category = self._create_category(u'cat')
        with mock.patch('stoqlib.domain.sellable.CategoryEditEvent') as f:
            category.on_update()

        f.emit.assert_called_once_with(category)

    def _create_category(self, description, parent=None):
        return SellableCategory(description=description,
                                category=parent,
                                store=self.store)


class TestClientCategoryPrice(DomainTest):
    def test_category_name(self):
        sellable = Sellable(category=None,
                            cost=50,
                            description=u"Test",
                            price=currency(100),
                            store=self.store)
        sellable.max_discount = 0
        cat = self.create_client_category(u'Cat 1')
        cat_price = ClientCategoryPrice(sellable=sellable, category=cat,
                                        price=150, max_discount=0,
                                        store=self.store)
        self.assertEqual(cat_price.category_name, u'Cat 1')

    def test_markup(self):
        sellable = Sellable(category=None,
                            cost=0,
                            store=self.store)
        cat = self.create_client_category(u'Cat 1')
        cat_price = ClientCategoryPrice(sellable=sellable, category=cat,
                                        price=150, max_discount=0,
                                        store=self.store)
        self.assertEqual(cat_price.markup, 0)
        sellable.cost = 10
        self.assertEqual(cat_price.markup, 1400)

        cat_price.markup = 10


class TestSellable(DomainTest):
    def setUp(self):
        DomainTest.setUp(self)
        self._base_category = SellableCategory(description=u"Cigarro",
                                               store=self.store)
        self._category = SellableCategory(description=u"Hollywood",
                                          category=self._base_category,
                                          suggested_markup=10,
                                          store=self.store)

    def test_get_description(self):
        sellable = self.create_sellable()
        sellable.category = self._category
        self.assertEqual(sellable.get_description(), 'Description')
        self.assertEqual(sellable.get_description(full_description=True),
                         '[Hollywood] Description')

    def test_get_category_description(self):
        sellable = self.create_sellable()
        sellable.category = self._category
        self.assertEqual(sellable.get_category_description(), 'Hollywood')

    def test_get_requires_kitchen_production_without_override(self):
        sellable = self.create_sellable()
        item = self.create_sale_item(sellable=sellable)

        sellable.requires_kitchen_production = True
        self.assertTrue(sellable.get_requires_kitchen_production(item.sale.branch))

        sellable.requires_kitchen_production = False
        self.assertFalse(sellable.get_requires_kitchen_production(item.sale.branch))

    def test_get_requires_kitchen_production_override_none(self):
        sellable = self.create_sellable()
        item = self.create_sale_item(sellable=sellable)
        sellable_branch_override = self.create_sellable_branch_override(
            sellable=sellable,
            branch=item.sale.branch)
        sellable_branch_override.requires_kitchen_production = None

        sellable.requires_kitchen_production = False
        self.assertFalse(sellable.get_requires_kitchen_production(item.sale.branch))

        sellable.requires_kitchen_production = True
        self.assertTrue(sellable.get_requires_kitchen_production(item.sale.branch))

    def test_get_requires_kitchen_production_override_false(self):
        sellable = self.create_sellable()
        item = self.create_sale_item(sellable=sellable)
        sellable_branch_override = self.create_sellable_branch_override(
            sellable=sellable,
            branch=item.sale.branch)
        sellable_branch_override.requires_kitchen_production = False

        sellable.requires_kitchen_production = False
        self.assertFalse(sellable.get_requires_kitchen_production(item.sale.branch))

        sellable.requires_kitchen_production = True
        self.assertFalse(sellable.get_requires_kitchen_production(item.sale.branch))

    def test_get_requires_kitchen_production_override_true(self):
        sellable = self.create_sellable()
        item = self.create_sale_item(sellable=sellable)
        sellable_branch_override = self.create_sellable_branch_override(
            sellable=sellable,
            branch=item.sale.branch)
        sellable_branch_override.requires_kitchen_production = True

        sellable.requires_kitchen_production = False
        self.assertTrue(sellable.get_requires_kitchen_production(item.sale.branch))

        sellable.requires_kitchen_production = True
        self.assertTrue(sellable.get_requires_kitchen_production(item.sale.branch))

    def test_price_based_on_category_markup(self):
        # When the price isn't defined, but the category and the cost. In this
        # case the sellable must have the price calculated applying the category's
        # markup in the sellable's cost.
        self._category.suggested_markup = 0
        sellable = Sellable(description=u"MX123",
                            commission=0,
                            cost=100,
                            category=self._category,
                            store=self.store)
        sellable.max_discount = 0
        self.assertTrue(sellable.markup == self._category.get_markup(),
                        (u"Expected markup: %r, got %r"
                         % (self._category.get_markup(),
                            sellable.markup)))
        price = sellable.cost * (sellable.markup / currency(100) + 1)
        self.assertTrue(sellable.price == price,
                        (u"Expected price: %r, got %r"
                         % (price, sellable.price)))

    def test_price_based_on_specified_markup(self):
        # When the price isn't defined, but the category, markup and the cost.
        # In this case the category's markup must be ignored and the price
        # calculated applying the markup specified in the sellable's cost.
        sellable = Sellable(description=u"FY123",
                            category=self._category,
                            cost=100,
                            store=self.store)
        sellable.markup = 5
        self.assertEqual(sellable.markup, 5)
        self.assertEqual(sellable.price, 105)

        sellable.cost = Decimal('100.33')
        sellable.markup = 7
        self.assertEqual(sellable.price, currency('107.35'))

        sellable.markup = 8
        self.assertEqual(sellable.price, currency('108.36'))

    def test_commission(self):
        self._category.salesperson_commission = 10
        sellable = Sellable(description=u"TX342",
                            category=self._category,
                            store=self.store)
        self.assertTrue(sellable.commission
                        == self._category.salesperson_commission,
                        (u"Expected salesperson commission: %r, got %r"
                         % (self._category.salesperson_commission,
                            sellable.commission)))

    def test_prices_and_markups(self):
        self._category.markup = 0
        sellable = Sellable(category=self._category, cost=50,
                            description=u"Test", price=currency(100),
                            store=self.store)
        self.assertTrue(sellable.price == 100,
                        u"Expected price: %r, got %r" % (100, sellable.price))
        self.assertTrue(sellable.markup == 100,
                        u"Expected markup: %r, got %r" % (100, sellable.markup))
        sellable.markup = 10
        self.assertTrue(sellable.price == 55,
                        u"Expected price: %r, got %r" % (55, sellable.price))
        sellable.price = 50
        self.assertTrue(sellable.markup == 0,
                        u"Expected markup %r, got %r" % (0, sellable.markup))

        # When the price specified isn't equivalent to the markup specified.
        # In this case the price don't must be updated based on the markup.
        sellable = Sellable(cost=50,
                            description=u"Test", price=currency(100),
                            store=self.store)
        self.assertTrue(sellable.price == 100)

        # A simple test: product without cost and price, markup must be 0
        sellable.cost = currency(0)
        sellable.price = currency(0)
        self.assertTrue(sellable.markup == 0,
                        u"Expected markup %r, got %r" % (0, sellable.markup))

    def test_price_on_sale_price_getter(self):
        sellable = Sellable(category=self._category,
                            cost=50,
                            description=u"Test",
                            price=100,
                            store=self.store)

        # - Sale period is undefined.
        sellable.on_sale_start_date = None
        sellable.on_sale_end_date = None
        self.assertEqual(sellable.price, 100)
        sellable.on_sale_price = 80
        self.assertEqual(sellable.price, 100)

        # - Sale has no start_date but has end_date in the future.
        sellable.on_sale_start_date = None
        sellable.on_sale_end_date = localdate(3002, 1, 1)
        self.assertEqual(sellable.price, 80)

        # - Sale has no end_date but has start_date in the past.
        sellable.on_sale_start_date = localdate(2001, 1, 1)
        sellable.on_sale_end_date = None
        self.assertEqual(sellable.price, 80)

        # - Sale is in the past.
        sellable.on_sale_start_date = localdate(2001, 1, 1)
        sellable.on_sale_end_date = localdate(2002, 1, 1)
        self.assertEqual(sellable.price, 100)

        # - Sale is in the future.
        sellable.on_sale_start_date = localdate(3001, 1, 1)
        sellable.on_sale_end_date = localdate(3002, 1, 1)
        self.assertEqual(sellable.price, 100)

        # - Sale is on (for a long time, by the way).
        sellable.on_sale_start_date = localdate(2001, 1, 1)
        sellable.on_sale_end_date = localdate(3002, 1, 1)
        self.assertEqual(sellable.price, 80)

    def test_price_on_sale_price_setter(self):
        sellable = Sellable(category=self._category,
                            cost=50,
                            description=u"Test",
                            price=100,
                            store=self.store)
        sellable.on_sale_price = 100

        # - Sale period is undefined.
        sellable.on_sale_start_date = None
        sellable.on_sale_end_date = None
        sellable.price = 10
        self.assertEqual(sellable.base_price, 10)
        self.assertEqual(sellable.on_sale_price, 100)

        # - Sale is in the past.
        sellable.on_sale_start_date = localdate(2001, 1, 1)
        sellable.on_sale_end_date = localdate(2002, 1, 1)
        sellable.price = 20
        self.assertEqual(sellable.base_price, 20)
        self.assertEqual(sellable.on_sale_price, 100)

        # - Sale is in the future.
        sellable.on_sale_start_date = localdate(3001, 1, 1)
        sellable.on_sale_end_date = localdate(3002, 1, 1)
        sellable.price = 30
        self.assertEqual(sellable.base_price, 30)
        self.assertEqual(sellable.on_sale_price, 100)

        sellable.price = 100
        # - Sale has no start_date but has end_date in the future.
        sellable.on_sale_start_date = None
        sellable.on_sale_end_date = localdate(3002, 1, 1)
        sellable.price = 40
        self.assertEqual(sellable.base_price, 100)
        self.assertEqual(sellable.on_sale_price, 40)

        # - Sale has no end_date but has start_date in the past.
        sellable.on_sale_start_date = localdate(2001, 1, 1)
        sellable.on_sale_end_date = None
        sellable.price = 50
        self.assertEqual(sellable.base_price, 100)
        self.assertEqual(sellable.on_sale_price, 50)

        # - Sale is on.
        sellable.on_sale_start_date = localdate(2001, 1, 1)
        sellable.on_sale_end_date = localdate(3002, 1, 1)
        sellable.price = 60
        self.assertEqual(sellable.base_price, 100)
        self.assertEqual(sellable.on_sale_price, 60)

        sellable.price = -80
        self.assertEqual(sellable.base_price, 100)
        self.assertEqual(sellable.on_sale_price, 0)

    def test_get_available_sellables_query(self):
        # Sellable and query without supplier
        sellable = self.create_sellable()
        self.create_storable(product=sellable.product,
                             branch=self.create_branch())

        self.assertIn(
            sellable,
            self.store.find(Sellable,
                            Sellable.get_available_sellables_query(self.store)))

        sellable.close(self.current_branch)
        self.assertNotIn(
            sellable,
            self.store.find(Sellable,
                            Sellable.get_available_sellables_query(self.store)))

        delivery_sellable = sysparam.get_object(self.store, 'DELIVERY_SERVICE').sellable
        delivery_sellable.status = Sellable.STATUS_AVAILABLE
        # Deliveries are treated differently, that's why they should
        # not be present here
        self.assertNotIn(
            sellable,
            self.store.find(Sellable,
                            Sellable.get_available_sellables_query(self.store)))

    def test_set_available(self):
        sellable = self.create_sellable()
        with self.assertRaisesRegex(ValueError,
                                    'This sellable is already available'):
                sellable.set_available(self.current_branch)

    def test_get_unblocked_sellables(self):
        # Sellable and query without supplier
        sellable = self.create_sellable()
        available = Sellable.get_unblocked_sellables(self.store)
        self.assertTrue(sellable in list(available))

        # Sellable without supplier, but querying with one
        supplier = self.create_supplier()
        available = Sellable.get_unblocked_sellables(self.store,
                                                     supplier=supplier)
        self.assertFalse(sellable in list(available))

        # Relate the two
        from stoqlib.domain.product import ProductSupplierInfo
        ProductSupplierInfo(store=self.store,
                            supplier=supplier,
                            product=sellable.product,
                            is_main_supplier=True)

        # Now the sellable should appear in the results
        available = Sellable.get_unblocked_sellables(self.store,
                                                     supplier=supplier)
        self.assertTrue(sellable in list(available))

        # Now the sellable should appear in the results
        storable = Storable(product=sellable.product, store=self.store)
        available = Sellable.get_unblocked_sellables(self.store,
                                                     storable=storable)
        self.assertTrue(sellable in list(available))

    def test_get_unblocked_by_category_query(self):
        s1 = self.create_sellable()
        s2 = self.create_sellable()
        s3 = self.create_sellable()

        c1 = self.create_sellable_category()
        c2 = self.create_sellable_category()
        s1.category = c1
        s2.category = c2

        query = Sellable.get_unblocked_by_categories_query(
            self.store, [c1, c2], include_uncategorized=True)
        self.assertEqual(
            set([s1, s2, s3]),
            set(self.store.find(Sellable, query)))

        query = Sellable.get_unblocked_by_categories_query(
            self.store, [c1], include_uncategorized=True)
        self.assertEqual(
            set([s1, s3]),
            set(self.store.find(Sellable, query)))

        query = Sellable.get_unblocked_by_categories_query(
            self.store, [c1], include_uncategorized=True)
        self.assertEqual(
            set([s1, s3]),
            set(self.store.find(Sellable, query)))

        query = Sellable.get_unblocked_by_categories_query(
            self.store, [c1], include_uncategorized=False)
        self.assertEqual(
            set([s1]),
            set(self.store.find(Sellable, query)))

        query = Sellable.get_unblocked_by_categories_query(
            self.store, [], include_uncategorized=True)
        self.assertEqual(
            set([s3]),
            set(self.store.find(Sellable, query)))

    @mock.patch('stoqlib.domain.sellable.localnow')
    def test_is_on_sale(self, localnow):
        localnow.return_value = datetime.datetime(2015, 12, 10)

        sellable = self.create_sellable()
        self.assertFalse(sellable.is_on_sale())

        sellable.on_sale_start_date = datetime.datetime(2015, 12, 5)
        sellable.on_sale_end_date = datetime.datetime(2015, 12, 11)
        self.assertFalse(sellable.is_on_sale())

        sellable.on_sale_price = 100
        self.assertTrue(sellable.is_on_sale())

        sellable.on_sale_end_date = datetime.datetime(2015, 12, 9)
        self.assertFalse(sellable.is_on_sale())

    def test_is_valid_quantity(self):
        sellable = self.create_sellable()
        unit = self.create_sellable_unit()
        sellable.unit = unit

        unit.allow_fraction = True
        self.assertTrue(sellable.is_valid_quantity(0))
        self.assertTrue(sellable.is_valid_quantity(10))
        self.assertTrue(sellable.is_valid_quantity(Decimal('0')))
        self.assertTrue(sellable.is_valid_quantity(Decimal('10')))

        self.assertTrue(sellable.is_valid_quantity(5.5))
        self.assertTrue(sellable.is_valid_quantity(Decimal('5.5')))

        unit.allow_fraction = False
        self.assertTrue(sellable.is_valid_quantity(0))
        self.assertTrue(sellable.is_valid_quantity(10))
        self.assertTrue(sellable.is_valid_quantity(Decimal('0')))
        self.assertTrue(sellable.is_valid_quantity(Decimal('10')))

        self.assertFalse(sellable.is_valid_quantity(5.5))
        self.assertFalse(sellable.is_valid_quantity(Decimal('5.5')))

    def test_is_valid_price(self):

        def isValidPriceAssert(valid_data, expected_validity, min_price,
                               max_discount):
            self.assertEqual(valid_data['is_valid'], expected_validity)
            self.assertEqual(valid_data['min_price'], min_price)
            self.assertEqual(valid_data['max_discount'], max_discount)

        sellable = Sellable(category=self._category, cost=50,
                            description=u"Test",
                            price=currency(100),
                            store=self.store)
        sellable.max_discount = 0
        cat = self.create_client_category(u'Cat 1')
        cat_price = ClientCategoryPrice(sellable=sellable, category=cat,
                                        price=150, max_discount=0,
                                        store=self.store)
        user = self.create_user()
        user.profile.max_discount = 50

        # without a category, and max_discount = 0, user = None
        valid_data = sellable.is_valid_price(-10)
        isValidPriceAssert(valid_data, False, sellable.price, 0)

        valid_data = sellable.is_valid_price(0)
        isValidPriceAssert(valid_data, False, sellable.price, 0)

        valid_data = sellable.is_valid_price(99)
        isValidPriceAssert(valid_data, False, sellable.price, 0)

        valid_data = sellable.is_valid_price(100)
        isValidPriceAssert(valid_data, True, sellable.price, 0)

        valid_data = sellable.is_valid_price(101)
        isValidPriceAssert(valid_data, True, sellable.price, 0)

        # without a category, and max_discount = 10%
        sellable.max_discount = 10

        valid_data = sellable.is_valid_price(-1)
        isValidPriceAssert(valid_data, False, currency(90), 10)

        valid_data = sellable.is_valid_price(0)
        isValidPriceAssert(valid_data, False, currency(90), 10)

        valid_data = sellable.is_valid_price(89)
        isValidPriceAssert(valid_data, False, currency(90), 10)

        valid_data = sellable.is_valid_price(90)
        isValidPriceAssert(valid_data, True, currency(90), 10)

        valid_data = sellable.is_valid_price(91)
        isValidPriceAssert(valid_data, True, currency(90), 10)

        # Now with a category, max_discount = 0
        valid_data = sellable.is_valid_price(0, cat)
        isValidPriceAssert(valid_data, False, currency(150), 0)

        valid_data = sellable.is_valid_price(-10, cat)
        isValidPriceAssert(valid_data, False, currency(150), 0)

        valid_data = sellable.is_valid_price(Decimal('149.99'), cat)
        isValidPriceAssert(valid_data, False, currency(150), 0)

        valid_data = sellable.is_valid_price(150, cat)
        isValidPriceAssert(valid_data, True, currency(150), 0)

        valid_data = sellable.is_valid_price(151, cat)
        isValidPriceAssert(valid_data, True, currency(150), 0)

        # Now with a category, max_discount = 10%
        cat_price.max_discount = 10

        valid_data = sellable.is_valid_price(Decimal('149.99'), cat)
        isValidPriceAssert(valid_data, True, currency(135), 10)

        valid_data = sellable.is_valid_price(135, cat)
        isValidPriceAssert(valid_data, True, currency(135), 10)

        valid_data = sellable.is_valid_price(134, cat)
        isValidPriceAssert(valid_data, False, currency(135), 10)

        # with a user
        valid_data = sellable.is_valid_price(49, None, user)
        isValidPriceAssert(valid_data, False, currency(50), 50)

        valid_data = sellable.is_valid_price(50, None, user)
        isValidPriceAssert(valid_data, True, currency(50), 50)

        # with discount
        valid_data = sellable.is_valid_price(50, None, user, extra_discount=10)
        isValidPriceAssert(valid_data, True, currency(40), 50)

    def test_get_tax_constant(self):
        base_category = SellableCategory(description=u"Monitor",
                                         store=self.store)
        category = SellableCategory(description=u"LCD Monitor",
                                    category=base_category,
                                    store=self.store)
        sellable = self.create_sellable()
        sellable.tax_constant = None
        sellable.category = category

        self.assertEqual(sellable.get_tax_constant(), None)

        constant = self.create_sellable_tax_constant()
        base_category.tax_constant = constant
        self.assertEqual(sellable.get_tax_constant(), constant)

        constant2 = self.create_sellable_tax_constant()
        category.tax_constant = constant2
        self.assertEqual(sellable.get_tax_constant(), constant2)

        constant3 = self.create_sellable_tax_constant()
        sellable.tax_constant = constant3
        self.assertEqual(sellable.get_tax_constant(), constant3)

    def test_close(self):
        results_not_closed = self.store.find(ProductFullStockView)
        results_with_closed = self.store.find(ProductFullWithClosedStockView)
        results_only_closed = self.store.find(ProductClosedStockView)
        # Count the already there results. ProductClosedStockView should
        # not have any.
        # obs. Using len(list(res)) instead of res.count() because of a bug
        #      on sqlobject that returns wrong count() on that views.
        count_not_closed = len(list(results_not_closed))
        count_with_closed = len(list(results_with_closed))
        count_only_closed = len(list(results_only_closed))
        self.assertEqual(count_only_closed, 0)

        # Here we create a sellable. It should show on
        # ProductFullStockView and ProductFullWithClosedStock View,
        # but not on ProductClosedStockView.
        sellable = self.create_sellable()
        branch = self.create_branch()
        self.create_storable(product=sellable.product, branch=branch)
        results_not_closed = self.store.find(ProductFullStockView)
        results_with_closed = self.store.find(ProductFullWithClosedStockView)
        results_only_closed = self.store.find(ProductClosedStockView)

        self.assertEqual(len(list(results_not_closed)), count_not_closed + 1)
        self.assertEqual(len(list(results_with_closed)), count_with_closed + 1)
        self.assertEqual(len(list(results_only_closed)), count_only_closed)
        ids = [result.id for result in results_not_closed]
        self.assertFalse(sellable.id not in ids)
        ids = [result.id for result in results_with_closed]
        self.assertFalse(sellable.id not in ids)
        ids = [result.id for result in results_only_closed]
        self.assertFalse(sellable.id in ids)

        # Here we close that sellable. It should now show on
        # ProductClosedStockViewand ProductFullWithClosedStock View,
        # but not on ProductFullStockView.
        sellable.close(branch)
        results_not_closed = self.store.find(ProductFullStockView)
        results_with_closed = self.store.find(ProductFullWithClosedStockView)
        results_only_closed = self.store.find(ProductClosedStockView)

        self.assertEqual(sellable.status, Sellable.STATUS_CLOSED)
        self.assertTrue(sellable.is_closed(branch))
        self.assertEqual(len(list(results_not_closed)), count_not_closed)
        self.assertEqual(len(list(results_with_closed)), count_with_closed + 1)
        self.assertEqual(len(list(results_only_closed)), count_only_closed + 1)
        ids = [result.id for result in results_not_closed]
        self.assertFalse(sellable.id in ids)
        ids = [result.id for result in results_with_closed]
        self.assertFalse(sellable.id not in ids)
        ids = [result.id for result in results_only_closed]
        self.assertFalse(sellable.id not in ids)

        # When trying to close an already closed sellable, it should
        # raise a ValueError.
        self.assertRaises(ValueError, sellable.close, branch)

    def test_can_close(self):
        sellable = self.create_sellable()
        storable = self.create_storable(sellable.product, self.current_branch, 0)
        # There's a storable, but we can still close because there's no stock
        self.assertTrue(sellable.can_close())

        storable.increase_stock(1, self.current_branch, StockTransactionHistory.TYPE_INITIAL,
                                None, self.current_user)
        # Now that there's stock we should not be able to close anymore
        self.assertFalse(sellable.can_close())

        storable.decrease_stock(1, self.current_branch, StockTransactionHistory.TYPE_INITIAL,
                                None, self.current_user)
        # But decreasing the stock should make it possible to close again
        self.assertTrue(sellable.can_close())

        # The delivery service cannot be closed.
        sellable = sysparam.get_object(self.store, 'DELIVERY_SERVICE').sellable
        self.assertFalse(sellable.can_close())

    def test_can_remove(self):
        sellable = Sellable(store=self.store)
        self.assertTrue(sellable.can_remove())

        sellable = self.create_sellable()
        storable = Storable(product=sellable.product, store=self.store)
        self.assertTrue(sellable.can_remove())

        storable.increase_stock(1, self.current_branch, StockTransactionHistory.TYPE_INITIAL,
                                None, self.current_user)
        sale = self.create_sale()
        sale.status = Sale.STATUS_QUOTE
        sale.branch = self.current_branch
        sale.add_sellable(sellable)
        self.assertFalse(sellable.can_remove())

        # Can't remove the sellable if it's in a purchase.
        from stoqlib.domain.purchase import PurchaseItem
        sellable = self.create_sellable()
        Storable(product=sellable.product, store=self.store)
        self.assertTrue(sellable.can_remove())
        PurchaseItem(store=self.store,
                     quantity=8, quantity_received=0,
                     cost=125, base_cost=125,
                     sellable=sellable,
                     order=self.create_purchase_order())
        self.assertFalse(sellable.can_remove())

        # The delivery service cannot be removed.
        sellable = sysparam.get_object(self.store, 'DELIVERY_SERVICE').sellable
        self.assertFalse(sellable.can_remove())

    def test_remove(self):
        # Remove category price and sellable
        sellable = self.create_sellable()
        Storable(product=sellable.product, store=self.store)
        for i in range(10):
            image = self.create_image()
            image.sellable = sellable

        ClientCategoryPrice(sellable=sellable,
                            category=self.create_client_category(),
                            price=100,
                            store=self.store)

        total = self.store.find(ClientCategoryPrice, sellable=sellable.id).count()
        total_sellable = self.store.find(Sellable, id=sellable.id).count()
        total_images = self.store.find(Image, sellable_id=sellable.id).count()

        self.assertEqual(total, 1)
        self.assertEqual(total_sellable, 1)
        self.assertEqual(total_images, 10)

        sellable.remove()
        total = self.store.find(ClientCategoryPrice,
                                sellable=sellable.id).count()
        total_sellable = self.store.find(Sellable, id=sellable.id).count()
        total_images = self.store.find(Image, sellable_id=sellable.id).count()

        self.assertEqual(total, 0)
        self.assertEqual(total_sellable, 0)
        self.assertEqual(total_images, 0)

    def test_category_price(self):
        sellable = self.create_sellable(price=100)
        category1 = self.create_client_category(u'Cat 1')
        category_price = ClientCategoryPrice(sellable=sellable,
                                             category=category1,
                                             price=155,
                                             store=self.store)
        category2 = self.create_client_category(u'Cat 2')

        cats = sellable.get_category_prices()
        self.assertEqual(cats.count(), 1)
        self.assertTrue(cats[0] == category_price)

        self.assertEqual(sellable.get_price_for_category(category1), 155)
        self.assertEqual(sellable.get_price_for_category(category2), 100)

    def test_default_category_price(self):
        sellable = self.create_sellable(price=100)
        category = self.create_client_category(u'Cat 1')
        ClientCategoryPrice(sellable=sellable, category=category, price=155, store=self.store)

        self.assertEqual(sellable.price, 100)
        with self.sysparam(DEFAULT_TABLE_PRICE=category):
            # Setting the parameter DEFAULT_TABLE_PRICE will change the sellable price if that
            # sellable has a special price for that category
            self.assertEqual(sellable.price, 155)

        # When a branch as another category price, that one should be used
        category = self.create_client_category(u'Cat 2')
        branch = self.create_branch()
        branch.default_client_category = category
        ClientCategoryPrice(sellable=sellable, category=category, price=200, store=self.store)
        self.assertEqual(sellable.get_price(branch), 200)

    def test_remove_category_price(self):
        category_price = self.create_client_category_price()

        total = self.store.find(ClientCategoryPrice).count()
        self.assertEqual(total, 1)

        category_price.remove()
        total = self.store.find(ClientCategoryPrice).count()
        self.assertEqual(total, 0)

    def test_code(self):
        sellable = self.create_sellable(price=100)
        sellable.code = u'code'
        self.assertEqual(sellable.code, u'code')
        sellable2 = self.create_sellable(price=100)
        self.assertRaises(SellableError, setattr, sellable2, u'code', u'code')

    def test_barcode(self):
        sellable = self.create_sellable(price=100)
        sellable.barcode = u'barcode'
        self.assertEqual(sellable.barcode, u'barcode')
        sellable2 = self.create_sellable(price=100)
        self.assertRaises(SellableError, setattr, sellable2, u'barcode', u'barcode')

    def test_get_suggested_markup(self):
        sellable = self.create_sellable()
        self.assertEqual(sellable.get_suggested_markup(), None)

        category = SellableCategory(description=u"LCD Monitor",
                                    store=self.store)
        sellable.category = category
        self.assertEqual(sellable.get_suggested_markup(), 0)

        category.suggested_markup = 10

        self.assertEqual(sellable.get_suggested_markup(), 10)

    def test_check_taxes_validity(self):
        sellable = self.create_sellable()
        sellable.check_taxes_validity(self.current_branch)

        tax = ProductTaxTemplate(store=self.store, name=u'foo')
        template = ProductIcmsTemplate(store=self.store, product_tax_template=tax)
        sellable.product.set_icms_template(template)

        sellable.check_taxes_validity(self.current_branch)

        template.p_cred_sn = 10
        template.p_cred_sn_valid_until = localdate(2000, 1, 1)

        with self.assertRaises(TaxError) as e:
            sellable.check_taxes_validity(self.current_branch)
            self.assertEqual(str(e), ("You cannot sell this item before updating "
                                      "the 'ICMS tax rate credit' field on 'foo' "
                                      "Tax Class.\n"
                                      "If you don't know what this means, contact "
                                      "the system administrator."))

    def test_copy_sellable(self):
        sellable = self.create_sellable()
        new_sellable = sellable.copy_sellable()
        props = ['base_price', 'category_id', 'cost', 'on_sale_price',
                 'max_discount', 'commission', 'notes', 'unit_id',
                 'tax_constant_id', 'default_sale_cfop_id',
                 'on_sale_start_date', 'on_sale_end_date']

        for prop in props:
            # Checking that all attributes have the same value
            self.assertEqual(getattr(sellable, prop), getattr(new_sellable, prop))
