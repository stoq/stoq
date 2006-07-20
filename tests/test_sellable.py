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

from stoqlib.domain.sellable import SellableCategory, BaseSellableCategory
from tests.base import BaseDomainTest

class TestSellableCategory(BaseDomainTest):
    _table = SellableCategory

    def setUp(self):
        BaseDomainTest.setUp(self)
        base_category = BaseSellableCategory(description="Monitor",
                                             connection=self.conn)
        self._category = SellableCategory(description="LCD",
                                          base_category=base_category,
                                          connection=self.conn)

    def test_description(self):
        self.failUnless(self._category.get_description() == "LCD")
        self.failUnless(self._category.get_full_description() == "Monitor LCD")

    def test_markup(self):
        self._category.suggested_markup = currency(10)
        self._category.base_category.suggested_markup = currency(20)
        self.failUnless(self._category.get_markup() == currency(10))
        self._category.suggested_markup = None
        self.failUnless(self._category.get_markup() == currency(20))
