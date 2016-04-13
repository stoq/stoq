# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
##

from kiwi.currency import currency

from stoqlib.domain.product import StockTransactionHistory
from stoqlib.gui.dialogs.costcenterdialog import CostCenterDialog
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.lib.dateutils import localtoday


class TestCostCenterDialog(GUITest):
    def test_show(self):
        stock_transaction = self.create_stock_transaction_history(
            trans_type=StockTransactionHistory.TYPE_SELL)
        entry = self.create_cost_center_entry(stock_transaction=stock_transaction)
        cost_center = entry.cost_center
        sale_item = self.create_sale_item()
        sale = sale_item.sale
        stock_decrease = self.create_stock_decrease()
        # The decrease needs an item to be shown in the dialog
        self.create_stock_decrease_item(stock_decrease=stock_decrease)

        stock_transaction.type = StockTransactionHistory.TYPE_SELL
        stock_transaction.object_id = sale_item.id
        stock_transaction.date = localtoday().date()
        stock_transaction.quantity = 5
        stock_transaction.stock_cost = currency('10.50')

        entry.stock_transaction = stock_transaction

        sale.cost_center = cost_center
        sale.identifier = 1234
        sale.open_date = localtoday().date()
        sale.total_amount = sale.get_total_sale_amount()

        stock_decrease.cost_center = cost_center
        stock_decrease.identifier = 5678
        stock_decrease.confirm_date = localtoday().date()

        dialog = CostCenterDialog(self.store, cost_center)
        self.check_dialog(dialog, 'dialog-cost-center-details')
