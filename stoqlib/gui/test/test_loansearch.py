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

from stoqlib.gui.search.loansearch import LoanSearch
from stoqlib.gui.uitestutils import GUITest


class TestLoanSearch(GUITest):
    def testSearch(self):
        loan = self.create_loan()
        self.create_loan_item(loan=loan)

        loan.identifier = 54952
        loan.open_date = datetime.datetime(2012, 1, 1)

        search = LoanSearch(self.trans)

        search.search.refresh()
        self.check_search(search, 'loan-no-filter')
