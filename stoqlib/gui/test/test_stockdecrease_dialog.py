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

from stoqlib.domain.payment.renegotiation import PaymentRenegotiation
from stoqlib.gui.dialogs.stockdecreasedialog import StockDecreaseDetailsDialog
from stoqlib.gui.uitestutils import GUITest

PaymentRenegotiation  # pyflakes


class TestStockDecreaseDetailsDialog(GUITest):
    def test_create(self):
        stock_decrease = self.create_stock_decrease(group=self.create_payment_group())
        stock_decrease.identifier = 8888
        self.create_stock_decrease_item(stock_decrease)

        payments = self.add_payments(stock_decrease, date=datetime.date.today())
        payments[0].identifier = 7777

        dialog = StockDecreaseDetailsDialog(self.store, stock_decrease)

        self.check_dialog(dialog, 'stock-decrease-dialog-create')

    def test_without_payments(self):
        item = self.create_stock_decrease_item()
        stock_decrease = item.stock_decrease
        stock_decrease.identifier = 8888

        dialog = StockDecreaseDetailsDialog(self.store, stock_decrease)

        self.check_dialog(dialog, 'stock-decrease-dialog-without-payments')
