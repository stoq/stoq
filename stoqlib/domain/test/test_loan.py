# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2010 Async Open Source <http://www.async.com.br>
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

from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.loan import Loan
from stoqlib.domain.interfaces import IStorable
from stoqlib.domain.test.domaintest import DomainTest


class TestLoan(DomainTest):

    def testAddSellable(self):
        loan = self.create_loan()
        sellable = self.create_sellable()
        loan.add_sellable(sellable, quantity=1, price=10)
        items = list(loan.get_items())
        self.assertEquals(len(items), 1)
        self.failIf(items[0].sellable is not sellable)

    def testCanClose(self):
        loan_item = self.create_loan_item()
        loan = loan_item.loan
        self.assertEquals(loan.status, Loan.STATUS_OPEN)
        self.failIf(loan.can_close())

        loan_item.return_quantity = loan_item.quantity
        loan_item.return_product(loan_item.quantity)
        self.failUnless(loan.can_close())

    def testClose(self):
        loan_item = self.create_loan_item()
        loan = loan_item.loan
        self.assertEquals(loan.status, Loan.STATUS_OPEN)
        self.failIf(loan.can_close())

        loan_item.return_quantity = loan_item.quantity
        loan_item.return_product(loan_item.quantity)
        self.failUnless(loan.can_close())
        loan.close()
        self.assertEquals(loan.status, Loan.STATUS_CLOSED)


class TestLoanItem(DomainTest):

    def testDoLoan(self):
        loan = self.create_loan()
        product = self.create_product()
        storable = product.addFacet(IStorable, connection=self.trans)
        branch = get_current_branch(self.trans)
        storable.increase_stock(1, branch)
        initial = storable.get_full_balance(branch)
        sellable = product.sellable
        loan_item = loan.add_sellable(sellable, quantity=1, price=10)
        loan_item.do_loan(branch)
        final = storable.get_full_balance(branch)
        self.assertEquals(final, initial - 1)

    def testReturnProduct(self):
        loan = self.create_loan()
        product = self.create_product()
        storable = product.addFacet(IStorable, connection=self.trans)
        branch = get_current_branch(self.trans)
        loan.branch = branch
        initial = storable.get_full_balance(branch)
        sellable = product.sellable
        loan_item = loan.add_sellable(sellable, quantity=1, price=10)
        loan_item.return_quantity = loan_item.quantity
        loan_item.return_product(loan_item.quantity)
        final = storable.get_full_balance(branch)
        self.assertEquals(final, initial + 1)
