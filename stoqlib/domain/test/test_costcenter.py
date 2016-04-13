# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2007 Async Open Source <http://www.async.com.br>
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

__tests__ = 'stoqlib/domain/costcenter.py'

from stoqlib.domain.costcenter import CostCenter, CostCenterEntry
from stoqlib.domain.product import StockTransactionHistory
from stoqlib.domain.test.domaintest import DomainTest


class TestCostCenter(DomainTest):
    def test_add_transaction(self):
        cost_center = self.create_cost_center()
        initial_trans = self.create_stock_transaction_history(quantity=1)
        stock_trans = self.create_stock_transaction_history(
            branch=initial_trans.branch, storable=initial_trans.storable,
            trans_type=StockTransactionHistory.TYPE_SELL, quantity=-1)

        entry = self.store.find(CostCenterEntry, stock_transaction=stock_trans)
        self.assertEquals(len(list(entry)), 0)

        cost_center.add_stock_transaction(stock_trans)

        entry = self.store.find(CostCenterEntry, stock_transaction=stock_trans)
        self.assertEquals(len(list(entry)), 1)
        self.assertEquals(entry[0].stock_transaction, stock_trans)

    def test_add_lonely_payment(self):
        cost_center = self.create_cost_center()
        payment = self.create_payment()

        entry = self.store.find(CostCenterEntry, payment=payment)
        self.assertEquals(len(list(entry)), 0)

        cost_center.add_lonely_payment(payment)

        entry = self.store.find(CostCenterEntry, payment=payment)
        self.assertEquals(len(list(entry)), 1)
        self.assertEquals(entry[0].payment, payment)

    def test_get_payment_entries(self):
        payment1 = self.create_payment()
        payment2 = self.create_payment()
        payment3 = self.create_payment()

        cost_center_entry1 = self.create_cost_center_entry(payment=payment1)
        cost_center1 = cost_center_entry1.cost_center
        cost_center_entry2 = self.create_cost_center_entry(cost_center1, payment2)

        cost_center_entry3 = self.create_cost_center_entry(payment=payment3)
        cost_center2 = cost_center_entry3.cost_center

        self.assertEquals(list(cost_center1.get_payment_entries()),
                          [cost_center_entry1, cost_center_entry2])
        self.assertEquals(list(cost_center2.get_payment_entries()),
                          [cost_center_entry3])

    def test_get_stock_transaction_entries(self):
        stock_trans1 = self.create_stock_transaction_history(
            trans_type=StockTransactionHistory.TYPE_SELL)
        stock_trans2 = self.create_stock_transaction_history(
            trans_type=StockTransactionHistory.TYPE_SELL)
        stock_trans3 = self.create_stock_transaction_history(
            trans_type=StockTransactionHistory.TYPE_SELL)

        cost_center_entry1 = self.create_cost_center_entry(
            stock_transaction=stock_trans1)
        cost_center1 = cost_center_entry1.cost_center
        cost_center_entry2 = self.create_cost_center_entry(
            cost_center1, stock_transaction=stock_trans2)

        cost_center_entry3 = self.create_cost_center_entry(
            stock_transaction=stock_trans3)
        cost_center2 = cost_center_entry3.cost_center

        self.assertEquals(list(cost_center1.get_stock_transaction_entries()),
                          [cost_center_entry1, cost_center_entry2])
        self.assertEquals(list(cost_center2.get_stock_transaction_entries()),
                          [cost_center_entry3])

    def test_stock_decreases(self):
        cost_center = self.create_cost_center()
        stock_decrease = self.create_stock_decrease()
        stock_decrease.cost_center = cost_center
        results = cost_center.get_stock_decreases()
        self.assertEquals(results.one(), stock_decrease)

    def test_get_sales(self):
        cost_center1 = self.create_cost_center()
        cost_center2 = self.create_cost_center()

        sale1 = self.create_sale()
        sale2 = self.create_sale()
        sale3 = self.create_sale()

        sale1.cost_center = cost_center1
        sale2.cost_center = cost_center1
        sale3.cost_center = cost_center2

        self.assertEquals(set(cost_center1.get_sales()), set([sale1, sale2]))
        self.assertEquals(list(cost_center2.get_sales()), [sale3])

    def test_get_entries(self):
        entry1 = self.create_cost_center_entry()
        cost_center1 = entry1.cost_center
        entry2 = self.create_cost_center_entry(cost_center1)

        entry3 = self.create_cost_center_entry()
        cost_center2 = entry3.cost_center

        self.assertEquals(list(cost_center1.get_entries()), [entry1, entry2])
        self.assertEquals(list(cost_center2.get_entries()), [entry3])

    def test_get_active(self):
        cost_center = self.create_cost_center()
        self.create_cost_center(is_active=False)

        cost_centers = CostCenter.get_active(self.store)

        self.assertEquals([cost_center], list(cost_centers))

    def test_get_payments(self):
        cost_center_entry = self.create_cost_center_entry()
        payment = cost_center_entry.payment
        results = cost_center_entry.cost_center.get_payments()
        self.assertEquals(results.one(), payment)
