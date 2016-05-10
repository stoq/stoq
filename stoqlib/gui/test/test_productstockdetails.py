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
import unittest

from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.gui.dialogs.productstockdetails import ProductStockHistoryDialog
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.database.runtime import get_current_branch, get_current_user


class TestProductStockHistoryDialog(GUITest):

    def test_show(self):
        with self.sysparam(SYNCHRONIZED_MODE=True):
            self._test_show()

    def _test_show(self):
        date = datetime.date(2012, 1, 1)
        today = datetime.date.today()
        branch = get_current_branch(self.store)
        branch2 = self.create_branch(name=u"Branch2")
        user = get_current_user(self.store)
        storable = self.create_storable(is_batch=True)
        product = storable.product
        batch = self.create_storable_batch(storable)
        batch.create_date = datetime.datetime(2013, 1, 27)

        # Purchase
        order = self.create_purchase_order(branch=branch)
        order.identifier = 111
        order.open_date = today
        order.status = PurchaseOrder.ORDER_PENDING
        p_item = order.add_item(product.sellable, 10)
        order.confirm()

        # Receiving
        receiving = self.create_receiving_order(order, branch, user)
        receiving.identifier = 222
        receiving.receival_date = date
        r_item = self.create_receiving_order_item(receiving, product.sellable, p_item)
        r_item.quantity_received = 8
        r_item.batch = batch
        receiving.confirm()

        # Sale
        sale = self.create_sale(branch=branch)
        sale.identifier = 123
        sale.open_date = today
        sale.add_sellable(product.sellable, 3, batch=batch)
        sale.order()
        self.add_payments(sale, date=today)
        sale.confirm()

        # Transfer from branch to another
        transfer1 = self.create_transfer_order(source_branch=branch)
        transfer1.open_date = date
        transfer1.identifier = 55
        self.create_transfer_order_item(transfer1, 2, product.sellable,
                                        batch=batch)
        transfer1.send()
        transfer1.receive(self.create_employee())

        # Transfer from another to branch
        transfer2 = self.create_transfer_order(source_branch=transfer1.destination_branch,
                                               dest_branch=branch)
        transfer2.open_date = date
        transfer2.identifier = 66
        self.create_transfer_order_item(transfer2, 1, product.sellable,
                                        batch=batch)
        transfer2.send()
        transfer2.receive(self.create_employee())

        # Transfer without the current branch
        transfer3 = self.create_transfer_order(source_branch=transfer2.source_branch,
                                               dest_branch=branch2)
        transfer3.identifier = 67
        self.create_transfer_order_item(transfer3, 1, product.sellable,
                                        batch=batch)
        transfer3.send()
        transfer3.receive(self.create_employee())

        # Loan
        loan = self.create_loan(branch)
        loan.identifier = 33
        loan.open_date = date
        loan.add_sellable(product.sellable, 2, batch=batch)
        loan.sync_stock()

        # Stock Decrease
        decrease = self.create_stock_decrease(branch, user)
        decrease.identifier = 4
        decrease.confirm_date = date
        decrease.add_sellable(product.sellable, batch=batch)
        decrease.confirm()

        dialog = ProductStockHistoryDialog(self.store, product.sellable, branch)
        # Show only the transfers where the current branch was used
        transfer_list = dialog.transfer_list
        self.assertEqual(len(transfer_list), 2)
        for transfer in transfer_list:
            self.assertTrue(branch.id in [transfer.source_branch_id,
                                          transfer.destination_branch_id])

        self.check_editor(dialog, 'dialog-product-stock-history')


if __name__ == '__main__':
    from stoqlib.api import api
    c = api.prepare_test()
    unittest.main()
