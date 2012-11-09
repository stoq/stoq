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

from stoqlib.domain.transfer import TransferOrder, TransferOrderItem
from stoqlib.gui.dialogs.transferorderdialog import TransferOrderDetailsDialog
from stoqlib.gui.search.transfersearch import TransferOrderSearch
from stoqlib.gui.uitestutils import GUITest
from stoqlib.reporting.transfer_receipt import TransferOrderReceipt


class TestTransferOrderSearch(GUITest):
    def _show_search(self):
        search = TransferOrderSearch(self.trans)
        search.search.refresh()
        search.results.select(search.results[0])
        return search

    def _create_domain(self):
        self.clean_domain([TransferOrderItem, TransferOrder])

        source_branch = self.create_branch('Riachuelo')
        dest_branch = self.create_branch('Marisa')
        order = self.create_transfer_order(source_branch=source_branch,
                                           dest_branch=dest_branch)
        self.create_transfer_order_item(order=order)
        order.identifier = 75168
        order.open_date = datetime.datetime(2012, 1, 1)

        source_branch = self.create_branch('Opera Rock')
        dest_branch = self.create_branch('Cavalera')
        order = self.create_transfer_order(source_branch=source_branch,
                                           dest_branch=dest_branch)
        self.create_transfer_order_item(order=order)
        order.identifier = 56832
        order.open_date = datetime.datetime(2012, 2, 2)

    def testSearch(self):
        self._create_domain()
        search = self._show_search()

        self.check_search(search, 'transfer-no-filter')

        search.set_searchbar_search_string('mar')
        search.search.refresh()
        self.check_search(search, 'transfer-string-filter')

        search.set_searchbar_search_string('')
        search.date_filter.select(DateSearchFilter.Type.USER_DAY)
        search.date_filter.start_date.update(datetime.date(2012, 1, 1))
        search.search.refresh()
        self.check_search(search, 'transfer-date-day-filter')

        search.date_filter.select(DateSearchFilter.Type.USER_INTERVAL)
        search.date_filter.start_date.update(datetime.date(2012, 1, 10))
        search.date_filter.end_date.update(datetime.date(2012, 2, 20))
        search.search.refresh()
        self.check_search(search, 'transfer-date-interval-filter')

    @mock.patch('stoqlib.gui.search.transfersearch.print_report')
    @mock.patch('stoqlib.gui.search.transfersearch.run_dialog')
    def testButtons(self, run_dialog, print_report):
        self._create_domain()
        search = self._show_search()

        search.results.emit('row_activated', search.results[0])
        run_dialog.assert_called_once_with(TransferOrderDetailsDialog, search,
                                           self.trans,
                                           search.results[0].transfer_order)

        self.assertSensitive(search._details_slave, ['print_button'])
        self.click(search._details_slave.print_button)
        print_report.assert_called_once_with(TransferOrderReceipt,
                                             search.results[0].transfer_order)

        run_dialog.reset_mock()
        self.assertSensitive(search._details_slave, ['details_button'])
        self.click(search._details_slave.details_button)
        run_dialog.assert_called_once_with(TransferOrderDetailsDialog, search,
                                           self.trans,
                                           search.results[0].transfer_order)
