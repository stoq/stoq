# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
## Author(s):     Henrique Romano <henrique@async.com.br>
##

from kiwi.datatypes import currency

from stoqlib.domain.sellable import (SellableCategory,
                                     BaseSellableCategory,
                                     BaseSellableInfo)
from stoqlib.domain.product import Product
from stoqlib.domain.interfaces import ISellable
from stoqlib.domain.test.domaintest import DomainTest

class TestSellableCategory(DomainTest):
    def setUp(self):
        DomainTest.setUp(self)
        base_category = BaseSellableCategory(description="Monitor",
                                             connection=self.trans)
        self._category = SellableCategory(description="LCD",
                                          base_category=base_category,
                                          connection=self.trans)

    def test_description(self):
        self.failUnless(self._category.get_description() == "LCD")
        self.failUnless(self._category.get_full_description() == "Monitor LCD")

    def test_markup(self):
        self._category.suggested_markup = currency(10)
        self._category.base_category.suggested_markup = currency(20)
        self.failUnless(self._category.get_markup() == currency(10))
        self._category.suggested_markup = None
        self.failUnless(self._category.get_markup() == currency(20))

class TestASellable(DomainTest):
    def setUp(self):
        DomainTest.setUp(self)
        self._base_category = BaseSellableCategory(description="Cigarro",
                                                   connection=self.trans)
        self._category = SellableCategory(description="Hollywood",
                                          base_category=self._base_category,
                                          suggested_markup=10,
                                          connection=self.trans)

    def test_price_based_on_category_markup(self):
        # When the price isn't defined, but the category and the cost. In this
        # case the sellable must have the price calculated applying the category's
        # markup in the sellable's cost.
        product = Product(connection=self.trans)
        self._category.suggested_markup = 0
        sellable_info = BaseSellableInfo(description=u"MX123",
                                         max_discount=0,
                                         commission=0,
                                         connection=self.trans)
        sellable = product.addFacet(ISellable,
                                    base_sellable_info=sellable_info,
                                    cost=100,
                                    category=self._category,
                                    connection=self.trans)
        self.failUnless(sellable.markup == self._category.get_markup(),
                        ("Expected markup: %r, got %r"
                         % (self._category.get_markup(),
                            sellable.markup)))
        price = sellable.cost * (sellable.markup / currency(100) + 1)
        self.failUnless(sellable.price == price,
                        ("Expected price: %r, got %r"
                         % (price, sellable.price)))

    def test_price_based_on_specified_markup(self):
        # When the price isn't defined, but the category, markup and the cost.
        # In this case the category's markup must be ignored and the price
        # calculated applying the markup specified in the sellable's cost.
        product = Product(connection=self.trans)
        sellable_info = BaseSellableInfo(description=u"FY123",
                                         connection=self.trans)
        markup = 5
        sellable = product.addFacet(ISellable,
                                    base_sellable_info=sellable_info,
                                    category=self._category,
                                    markup=markup,
                                    cost=100,
                                    connection=self.trans)
        self.failUnless(sellable.markup == markup,
                        ("Expected markup: %r, got %r"
                         % (markup, sellable.markup)))
        price = sellable.cost * (markup / currency(100) + 1)
        self.failUnless(sellable.price == price,
                        ("Expected price: %r, got %r"
                         % (price, sellable.price)))

    def test_commission(self):
        product = Product(connection=self.trans)
        sellable_info = BaseSellableInfo(description=u"TX342",
                                         connection=self.trans)
        self._category.salesperson_commission = 10
        sellable = product.addFacet(ISellable,
                                    base_sellable_info=sellable_info,
                                    category=self._category,
                                    connection=self.trans)
        self.failUnless(sellable.commission
                        == self._category.salesperson_commission,
                        ("Expected salesperson commission: %r, got %r"
                         % (self._category.salesperson_commission,
                            sellable.commission)))

    def test_prices_and_markups(self):
        product = Product(connection=self.trans)
        sellable_info = BaseSellableInfo(description="Test", price=currency(100),
                                         connection=self.trans)
        self._category.markup = 0
        sellable = product.addFacet(ISellable, category=self._category, cost=50,
                                    base_sellable_info=sellable_info,
                                    connection=self.trans)
        self.failUnless(sellable.price == 100,
                        "Expected price: %r, got %r" % (100, sellable.price))
        self.failUnless(sellable.markup == 100,
                        "Expected markup: %r, got %r" % (100, sellable.markup))
        sellable.markup = 10
        self.failUnless(sellable.price == 55,
                        "Expected price: %r, got %r" % (55, sellable.price))
        sellable.price = 50
        self.failUnless(sellable.markup == 0,
                        "Expected markup %r, got %r" % (0, sellable.markup))

        # When the price specified isn't equivalent to the markup specified.
        # In this case the price don't must be updated based on the markup.
        product = Product(connection=self.trans)
        sellable_info = BaseSellableInfo(description="Test", price=currency(100),
                                         connection=self.trans)
        sellable = product.addFacet(ISellable, markup=10, cost=50,
                                    base_sellable_info=sellable_info,
                                    connection=self.trans)
        self.failUnless(sellable.price == 100)

        # A simple test: product without cost and price, markup must be 0
        sellable.cost = currency(0)
        sellable.price = currency(0)
        self.failUnless(sellable.markup == 0,
                        "Expected markup %r, got %r" % (0, sellable.markup))
