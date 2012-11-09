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

import mock

from kiwi.ui.search import DateSearchFilter

from stoqlib.domain.loan import Loan
from stoqlib.gui.dialogs.loandetails import LoanDetailsDialog
from stoqlib.gui.search.loansearch import LoanSearch
from stoqlib.gui.uitestutils import GUITest
from stoqlib.reporting.loanreceipt import LoanReceipt


class TestLoanSearch(GUITest):
    def _show_search(self):
        search = LoanSearch(self.trans)
        search.search.refresh()
        search.results.select(search.results[0])
        return search

    def _create_domain(self):
        client = self.create_client(name='Dane Cook')
        loan = self.create_loan(client=client)
        self.create_loan_item(loan=loan)
        loan.identifier = 54952
        loan.open_date = datetime.datetime(2012, 1, 1)

        client = self.create_client(name='Carmen Sandiego')
        loan = self.create_loan(client=client)
        self.create_loan_item(loan=loan)
        loan.identifier = 45978
        loan.open_date = datetime.datetime(2012, 2, 2)

    def testSearch(self):
        self._create_domain()
        search = self._show_search()

        self.check_search(search, 'loan-no-filter')

        search.set_searchbar_search_string('dan')
        search.search.refresh()
        self.check_search(search, 'loan-string-filter')

        search.set_searchbar_search_string('')
        search.date_filter.select(DateSearchFilter.Type.USER_DAY)
        search.date_filter.start_date.update(datetime.date(2012, 2, 2))
        search.search.refresh()
        self.check_search(search, 'loan-date-filter')

    @mock.patch('stoqlib.gui.search.loansearch.run_dialog')
    @mock.patch('stoqlib.gui.search.loansearch.print_report')
    def testButtons(self, print_report, run_dialog):
        self._create_domain()
        search = self._show_search()

        search.search.refresh()
        self.assertNotSensitive(search._details_slave, ['print_button'])
        search.results.select(search.results[0])
        self.assertSensitive(search._details_slave, ['print_button'])
        self.click(search._details_slave.print_button)
        loan = Loan.get(search.results[0].id, connection=self.trans)
        print_report.assert_called_once_with(LoanReceipt, loan)

        search.search.refresh()
        self.assertNotSensitive(search._details_slave, ['details_button'])
        search.results.select(search.results[0])
        self.assertSensitive(search._details_slave, ['details_button'])
        self.click(search._details_slave.details_button)
        run_dialog.assert_called_once_with(LoanDetailsDialog, search,
                                           self.trans, loan)

        run_dialog.reset_mock()
        search.results.emit('row_activated', search.results[0])
        run_dialog.assert_called_once_with(LoanDetailsDialog, search,
                                           self.trans, loan)
