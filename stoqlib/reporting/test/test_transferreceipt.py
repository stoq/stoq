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

from stoqlib.api import api
from stoqlib.gui.search.transfersearch import TransferOrderSearch
from stoqlib.lib.dateutils import localdatetime
from stoqlib.reporting.test.reporttest import ReportTest
from stoqlib.reporting.transfer import TransferOrderReceipt, TransferOrderReport


class TestTransferReceipt(ReportTest):
    """Transfer Receipt tests"""

    def test_transfer_receipt(self):
        source_branch = self.create_branch(name=u'Stoq Roupas')
        destination_branch = self.create_branch(name=u'Stoq Sapatos')
        order = self.create_transfer_order(source_branch=source_branch,
                                           dest_branch=destination_branch)
        for i in range(5):
            self.create_transfer_order_item(order)

        order.send()
        order.receive(self.create_employee())
        self._diff_expected(TransferOrderReceipt, 'transfer-receipt', order)

    def test_transfer_receipt_cancelled(self):
        source_branch = self.create_branch(name=u'Stoq Roupas')
        destination_branch = self.create_branch(name=u'Stoq Sapatos')
        order = self.create_transfer_order(source_branch=source_branch,
                                           dest_branch=destination_branch)
        for i in range(5):
            self.create_transfer_order_item(order)

        order.send()
        order.cancel(self.create_employee())
        self._diff_expected(TransferOrderReceipt,
                            'transfer-receipt-cancelled', order)


class TestTransferReport(ReportTest):
    """Transfer Report tests"""

    def test_transfer_report(self):
        source_branch = self.create_branch(name=u'Stoq Sapatos')
        destination_branch = api.get_current_branch(self.store)
        order = self.create_transfer_order(source_branch=source_branch,
                                           dest_branch=destination_branch)

        for i in range(5):
            self.create_transfer_order_item(order)

        order.send()
        order.identifier = 1337
        order.open_date = localdatetime(2012, 12, 12)
        dialog = TransferOrderSearch(self.store)
        dialog.search.refresh()
        self._diff_expected(TransferOrderReport, 'transfer-report', dialog.results,
                            list(dialog.results))
