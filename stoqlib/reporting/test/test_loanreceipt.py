# -*- Mode: Python; coding: utf-8 -*-
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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##

import mock

from stoqlib.api import api
from stoqlib.reporting.test.reporttest import ReportTest
from stoqlib.reporting.loanreceipt import LoanReceipt


class TestLoanReceipt(ReportTest):
    @mock.patch('stoqlib.reporting.loanreceipt.datetime', ReportTest.fake.datetime)
    def test_loan_receipt(self):
        client = self.create_client()
        address = self.create_address()
        address.person = client.person
        loan = self.create_loan(client=client)

        for i in range(3):
            self.create_loan_item(loan=loan, quantity=i)

        api.sysparam.set_bool(self.store, 'PRINT_PROMISSORY_NOTE_ON_LOAN', False)
        self._diff_expected(LoanReceipt, 'loan-receipt', loan)

        api.sysparam.set_bool(self.store, 'PRINT_PROMISSORY_NOTE_ON_LOAN', True)
        self._diff_expected(LoanReceipt, 'loan-receipt-with-pn', loan)
