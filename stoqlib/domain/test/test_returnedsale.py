# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2009 Async Open Source <http://www.async.com.br>
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

import decimal

from kiwi.currency import currency
import mock

from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.product import StockTransactionHistory
from stoqlib.domain.returnedsale import ReturnedSale, ReturnedSaleItem
from stoqlib.domain.test.domaintest import DomainTest

__tests__ = 'stoqlib/domain/returnedsale.py'


class TestReturnedSale(DomainTest):
    def test_remove(self):
        sale = self.create_sale()
        self.add_product(sale)
        self.add_product(sale)
        self.add_payments(sale)
        sale.order()
        sale.confirm()
        returned_sale = sale.create_sale_return_adapter()

        total = self.store.find(ReturnedSale, id=returned_sale.id).count()
        total_items = self.store.find(ReturnedSaleItem,
                                      returned_sale_id=returned_sale.id).count()

        self.assertEquals(total, 1)
        self.assertEquals(total_items, 2)

        returned_sale.remove()

        total = self.store.find(ReturnedSale, id=returned_sale.id).count()
        total_items = self.store.find(ReturnedSaleItem,
                                      returned_sale_id=returned_sale.id).count()

        self.assertEquals(total, 0)
        self.assertEquals(total_items, 0)

    def test_client(self):
        branch = self.create_branch()
        client = self.create_client()
        sale = self.create_sale(branch=branch)
        sale.client = client
        rsale = ReturnedSale(store=self.store)
        self.assertIsNone(rsale.client)
        rsale.sale = sale
        self.assertEquals(rsale.client, client)

    def test_group(self):
        branch = self.create_branch()
        client = self.create_client()
        sale = self.create_sale(branch=branch)
        sale.client = client
        rsale = ReturnedSale(branch=branch,
                             store=self.store)
        self.assertIsNone(rsale.group)
        rsale.sale = sale
        self.assertEquals(rsale.group, sale.group)

        rsale.sale = None
        rsale.new_sale = sale
        self.assertEquals(rsale.group, sale.group)

    def test_sale_total(self):
        branch = self.create_branch()

        rsale = ReturnedSale(branch=branch,
                             store=self.store)
        self.assertEquals(rsale.sale_total, currency(0))

        sale = self.create_sale(branch=branch)
        sellable = self.add_product(sale)
        self.add_payments(sale)
        rsale1 = ReturnedSale(branch=branch,
                              sale=sale,
                              store=self.store)
        rsale2 = ReturnedSale(branch=branch,
                              sale=sale,
                              store=self.store)
        self.assertEquals(rsale1.sale_total, currency(0))

        item = ReturnedSaleItem(store=self.store,
                                returned_sale=rsale2,
                                sellable=sellable)
        item.quantity = 10
        item.price = 10

        self.assertEquals(rsale1.sale_total, currency(-100))

    def test_paid_total(self):
        branch = self.create_branch()
        rsale = ReturnedSale(branch=branch,
                             store=self.store)
        self.assertEquals(rsale.paid_total, currency(0))

        sale = self.create_sale(branch=branch)
        self.add_product(sale)
        rsale = ReturnedSale(branch=branch,
                             sale=sale,
                             store=self.store)
        self.add_payments(sale)
        sale.order()
        sale.confirm()
        self.assertEquals(rsale.paid_total, currency(10))

    def test_total_amount(self):
        branch = self.create_branch()
        sale = self.create_sale(branch=branch)
        self.add_product(sale)
        rsale = ReturnedSale(branch=branch,
                             sale=sale,
                             store=self.store)
        self.assertEquals(rsale.total_amount, currency(0))

    def test_total_amount_abs(self):
        branch = self.create_branch()
        sale = self.create_sale(branch=branch)
        self.add_product(sale)
        rsale = ReturnedSale(branch=branch,
                             sale=sale,
                             store=self.store)
        self.assertEquals(rsale.total_amount_abs, currency(0))

    def test_add_item(self):
        sale_item = self.create_sale_item()
        item = ReturnedSaleItem(store=self.store,
                                sale_item=sale_item)
        rsale = ReturnedSale(store=self.store)
        rsale.add_item(item)

    def test_return_with_credit(self):
        branch = get_current_branch(self.store)
        sale_item = self.create_sale_item()
        sale = sale_item.sale
        sellable = sale_item.sellable
        self.create_storable(product=sellable.product, branch=branch, stock=10)
        payments = self.add_payments(sale, method_type=u'bill',
                                     installments=2)
        payments[0].status = Payment.STATUS_PENDING
        self.add_payments(sale, method_type=u'money')
        sale.order()
        sale.confirm()

        rsale = ReturnedSale(branch=branch,
                             sale=sale,
                             store=self.store)
        ReturnedSaleItem(store=self.store,
                         returned_sale=rsale,
                         sale_item=sale_item,
                         quantity=1)
        # Create an unused to test the removal of unused items,
        # should probably be removed.
        ReturnedSaleItem(store=self.store,
                         returned_sale=rsale,
                         sale_item=sale_item,
                         quantity=0)
        rsale.return_(u'credit')

    def test_trade(self):
        pass


class TestReturnedSaleItem(DomainTest):
    def test_constructor(self):
        with self.assertRaisesRegexp(
            ValueError,
            "A sale_item or a sellable is mandatory to create this object"):
            ReturnedSaleItem(store=self.store)

        sellable = self.create_sellable()
        sale_item = self.create_sale_item()
        with self.assertRaisesRegexp(
            ValueError,
            "sellable must be the same as sale_item.sellable"):
            ReturnedSaleItem(sellable=sellable,
                             sale_item=sale_item,
                             store=self.store)

    def test_total(self):
        sale_item = self.create_sale_item()
        item = ReturnedSaleItem(store=self.store,
                                sale_item=sale_item)
        item.quantity = 1
        self.assertEquals(item.total, 100)
        item.price = 10
        self.assertEquals(item.total, 10)
        item.quantity = 20
        self.assertEquals(item.total, 200)

    def test_return_(self):
        sale = self.create_sale()
        self.add_product(sale)
        self.add_payments(sale)
        sale.order()
        sale.confirm()
        returned_sale = sale.create_sale_return_adapter()

        item = self.store.find(ReturnedSaleItem,
                               returned_sale=returned_sale).any()

        self.assertEquals(item.sale_item.quantity_decreased, 1)
        branch = self.create_branch()

        with mock.patch(
            'stoqlib.domain.product.Storable.increase_stock') as increase_stock:
            item.return_(branch)
        self.assertEquals(item.sale_item.quantity_decreased, 0)

        increase_stock.assert_called_once_with(
            decimal.Decimal(1), branch, StockTransactionHistory.TYPE_RETURNED_SALE,
            item.id, batch=item.batch)
