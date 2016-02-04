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

import mock

from stoqlib.api import api
from stoqlib.domain.person import Branch
from stoqlib.domain.transfer import TransferOrder, TransferOrderItem
from stoqlib.lib.dateutils import localdate, localdatetime
from stoqlib.gui.dialogs.transferorderdialog import TransferOrderDetailsDialog
from stoqlib.gui.search.searchfilters import DateSearchFilter
from stoqlib.gui.search.transfersearch import (TransferOrderSearch,
                                               TransferItemSearch)
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.reporting.transfer import TransferOrderReport, TransferItemReport


class TestTransferOrderSearch(GUITest):
    def _show_search(self):
        search = TransferOrderSearch(self.store)
        search.search.refresh()
        search.results.select(search.results[0])
        return search

    def _create_domain(self):
        self.clean_domain([TransferOrderItem, TransferOrder])
        responsible = self.create_employee()

        other_branch = Branch.get_active_remote_branches(self.store)[0]
        current_branch = api.get_current_branch(self.store)

        # One transfer that we did not receive yet
        order = self.create_transfer_order(source_branch=other_branch,
                                           dest_branch=current_branch)
        self.create_transfer_order_item(order=order)
        order.identifier = 75168
        order.open_date = localdatetime(2012, 1, 1)
        order.send()

        # One that we have already received
        order = self.create_transfer_order(source_branch=other_branch,
                                           dest_branch=current_branch)
        self.create_transfer_order_item(order=order)
        order.identifier = 56832
        order.open_date = localdatetime(2012, 2, 2)
        order.send()
        order.receive(responsible)
        order.receival_date = localdatetime(2012, 2, 2)

        # One that we have sent but is not received yet
        order = self.create_transfer_order(source_branch=current_branch,
                                           dest_branch=other_branch)
        self.create_transfer_order_item(order=order)
        order.identifier = 20486
        order.open_date = localdatetime(2012, 3, 3)
        order.send()

        # One that we have sent and is recived
        order = self.create_transfer_order(source_branch=current_branch,
                                           dest_branch=other_branch)
        self.create_transfer_order_item(order=order)
        order.identifier = 20489
        order.open_date = localdatetime(2012, 3, 4)
        order.send()

        order.receive(responsible)
        order.receival_date = localdatetime(2012, 3, 5)

        # And another one that is cancelled
        order = self.create_transfer_order(source_branch=current_branch,
                                           dest_branch=other_branch)
        self.create_transfer_order_item(order=order)
        order.identifier = 20491
        order.open_date = localdatetime(2012, 4, 5)
        order.send()

        order.cancel(responsible, cancel_date=localdatetime(2012, 4, 6))

    def test_search(self):
        self._create_domain()
        search = self._show_search()

        # Pending searches
        search.status_filter.select('pending')
        self.check_search(search, 'transfer-pending')

        # Sent transfers
        search.status_filter.select('sent')
        self.check_search(search, 'transfer-sent')

        # Received transfers
        search.status_filter.select('received')
        self.check_search(search, 'transfer-received')

        # Cancelled transfers
        search.status_filter.select('cancelled')
        self.check_search(search, 'transfer-cancelled')

        # Show all transfers
        search.status_filter.select(None)
        self.check_search(search, 'transfer-no-filter')

        search.set_searchbar_search_string('mar')
        search.search.refresh()
        self.check_search(search, 'transfer-string-filter')

        search.set_searchbar_search_string('')
        search.date_filter.select(DateSearchFilter.Type.USER_DAY)
        search.date_filter.start_date.update(localdate(2012, 1, 1).date())
        search.search.refresh()
        self.check_search(search, 'transfer-date-day-filter')

        search.date_filter.select(DateSearchFilter.Type.USER_INTERVAL)
        search.date_filter.start_date.update(localdate(2012, 1, 10).date())
        search.date_filter.end_date.update(localdate(2012, 2, 20).date())
        search.search.refresh()
        search.status_filter.select(None)
        self.check_search(search, 'transfer-date-interval-filter')

    @mock.patch('stoqlib.gui.search.searchdialog.print_report')
    @mock.patch('stoqlib.gui.search.transfersearch.run_dialog')
    def test_buttons(self, run_dialog, print_report):
        self._create_domain()
        search = self._show_search()

        search.results.emit('row_activated', search.results[0])
        run_dialog.assert_called_once_with(TransferOrderDetailsDialog, search,
                                           self.store,
                                           search.results[0].transfer_order)

        self.assertSensitive(search._details_slave, ['print_button'])
        self.click(search._details_slave.print_button)
        print_report.assert_called_once_with(TransferOrderReport, search.results,
                                             list(search.results),
                                             filters=search.search.get_search_filters())

        run_dialog.reset_mock()
        self.assertSensitive(search._details_slave, ['details_button'])
        self.click(search._details_slave.details_button)
        run_dialog.assert_called_once_with(TransferOrderDetailsDialog, search,
                                           self.store,
                                           search.results[0].transfer_order)


class TestTransferItemSearch(GUITest):
    def _create_domain(self):
        self.clean_domain([TransferOrderItem, TransferOrder])

        other_branch = Branch.get_active_remote_branches(self.store)[0]
        current_branch = api.get_current_branch(self.store)

        # One transfer that we did not receive yet
        order = self.create_transfer_order(source_branch=other_branch,
                                           dest_branch=current_branch)
        self.create_transfer_order_item(order=order)
        order.identifier = 75168
        order.open_date = localdatetime(2012, 1, 1)
        order.send()

    def test_search(self):
        self._create_domain()

        search = TransferItemSearch(self.store)
        # At this point none of the button should be sensitive
        self.assertNotSensitive(search._details_slave, ['details_button'])
        self.assertNotSensitive(search._details_slave, ['print_button'])
        search.search.refresh()
        # After the search is made, print_button should be available
        self.assertNotSensitive(search._details_slave, ['details_button'])
        self.assertSensitive(search._details_slave, ['print_button'])
        search.results.select(search.results[0])
        # details_button will be sensitive only after the user select a row
        self.assertSensitive(search._details_slave, ['details_button'])
        self.assertSensitive(search._details_slave, ['print_button'])
        self.check_search(search, 'transfer-item-pending')

    @mock.patch('stoqlib.gui.search.searchdialog.print_report')
    @mock.patch('stoqlib.gui.search.transfersearch.run_dialog')
    def test_button(self, run_dialog, print_report):
        self._create_domain()

        search = TransferItemSearch(self.store)
        search.search.refresh()
        search.results.select(search.results[0])

        # Testing double click on the row
        search.results.emit('row_activated', search.results[0])
        run_dialog.assert_called_once_with(TransferOrderDetailsDialog, search,
                                           self.store,
                                           search.results[0].transfer_order)
        # Testing clicking on details button
        run_dialog.reset_mock()
        self.click(search._details_slave.details_button)
        run_dialog.assert_called_once_with(TransferOrderDetailsDialog, search,
                                           self.store,
                                           search.results[0].transfer_order)
        # Testing clicking on print button
        self.click(search._details_slave.print_button)
        print_report.assert_called_once_with(TransferItemReport, search.results,
                                             list(search.results),
                                             filters=search.search.get_search_filters())
