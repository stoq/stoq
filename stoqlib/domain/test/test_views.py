# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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
## Author(s):       Johan Dahlin <jdahlin@async.com.br>
##

from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.domain.views import SellableFullStockView
from stoqlib.database.runtime import get_current_branch

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

