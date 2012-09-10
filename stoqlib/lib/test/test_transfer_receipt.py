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

from stoqlib.reporting.tests.reporttest import ReportTest
from stoqlib.reporting.transfer_receipt import TransferOrderReceipt


class TestTransferReceipt(ReportTest):
    """Transfer Receipt tests"""

    def test_transfer_receipt(self):
        source_branch = self.create_branch(name='Stoq Roupas')
        destination_branch = self.create_branch(name='Stoq Sapatos')
        order = self.create_transfer_order(source_branch=source_branch,
                                           dest_branch=destination_branch)
        for i in range(5):
            item = self.create_transfer_order_item(order)
            order.send_item(item)

        order.receive()

        self._diff_expected(TransferOrderReceipt, 'transfer-receipt', order)
