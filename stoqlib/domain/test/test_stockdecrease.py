# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2010-2013 Async Open Source <http://www.async.com.br>
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

from kiwi.currency import currency

from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.stockdecrease import StockDecrease, StockDecreaseItem
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.exceptions import DatabaseInconsistency

__tests__ = 'stoqlib/domain/stockdecrease.py'


class TestStockDecrease(DomainTest):

    def test_get_status_name(self):
        self.assertEquals(
            StockDecrease.get_status_name(StockDecrease.STATUS_INITIAL),
            u'Opened')
        self.assertEquals(
            StockDecrease.get_status_name(StockDecrease.STATUS_CONFIRMED),
            u'Confirmed')

        with self.assertRaises(DatabaseInconsistency):
            StockDecrease.get_status_name(-1)

    def test_add_item(self):
        decrease = self.create_stock_decrease()
        sellable = self.create_sellable()

        item = StockDecreaseItem(store=self.store,
                                 sellable=sellable)
        self.assertEquals(item.stock_decrease, None)
        decrease.add_item(item)
        self.assertEquals(item.stock_decrease, decrease)

    def test_remove_item(self):
        decrease = self.create_stock_decrease()
        sellable = self.create_sellable()
        decrease.add_sellable(sellable, quantity=5)

        item = decrease.get_items()[0]
        decrease.remove_item(item)
        self.assertEqual(decrease.get_items().count(), 0)

        with self.sysparam(SYNCHRONIZED_MODE=True):
            item = self.create_stock_decrease_item()
            order = item.stock_decrease

            before_remove = self.store.find(StockDecreaseItem).count()
            order.remove_item(item)
            after_remove = self.store.find(StockDecreaseItem).count()

            # The item should still be on the database
            self.assertEqual(before_remove, after_remove)

            # But not related to the loan
            self.assertEquals(self.store.find(StockDecreaseItem, stock_decrease=order).count(), 0)

    def test_get_items(self):
        decrease = self.create_stock_decrease()
        sellable = self.create_sellable()
        decrease.add_sellable(sellable, quantity=5)

        items = decrease.get_items()
        self.assertEqual(items.count(), 1)
        self.assertEqual(sellable, items[0].sellable)

    def test_confirm(self):
        decrease = self.create_stock_decrease()
        decrease.group = self.create_payment_group()
        payment = self.create_payment(group=decrease.group)
        sellable = self.create_sellable()
        decrease.add_sellable(sellable, quantity=5)

        branch = decrease.branch
        storable = self.create_storable(sellable.product, branch, 100)

        self.assertEqual(storable.get_stock_item(branch, None).quantity, 100)

        self.failUnless(decrease.can_confirm())
        decrease.confirm()
        self.failIf(decrease.can_confirm())

        self.assertEqual(storable.get_stock_item(branch, None).quantity, 95)

        self.assertEquals(payment.status, Payment.STATUS_PENDING)

    def test_get_branch_name(self):
        branch = self.create_branch()
        branch.person.company.fancy_name = u'foo'
        decrease = self.create_stock_decrease(branch=branch)
        self.assertEquals(decrease.get_branch_name(), u'foo')

    def test_get_responsible_name(self):
        decrease = self.create_stock_decrease()
        user = self.create_user()
        user.person.name = u'foo'
        decrease.responsible = user
        self.assertEquals(decrease.get_responsible_name(), u'foo')

    def test_get_removed_by_name(self):
        decrease = self.create_stock_decrease()
        decrease.removed_by = None
        self.assertEquals(decrease.get_removed_by_name(), u'')

        employee = self.create_employee()
        employee.person.name = u'foo'
        decrease.removed_by = employee
        self.assertEquals(decrease.get_removed_by_name(), u'foo')

    def test_get_total_items_removed(self):
        decrease = self.create_stock_decrease()
        self.assertEquals(0, decrease.get_total_items_removed())

        item1 = self.create_stock_decrease_item(stock_decrease=decrease)
        item1.quantity = 10
        self.assertEquals(10, decrease.get_total_items_removed())

        item2 = self.create_stock_decrease_item(stock_decrease=decrease)
        item2.quantity = 20
        self.assertEquals(30, decrease.get_total_items_removed())

    def test_get_cfop_description(self):
        decrease = self.create_stock_decrease()
        decrease.cfop.code = u'1.234'
        decrease.cfop.description = u'foo'
        self.assertEquals(decrease.get_cfop_description(), u'1.234 foo')

    def test_get_total_cost(self):
        decrease = self.create_stock_decrease()
        sellable1 = self.create_sellable()
        sellable1.cost = currency('100')
        sellable2 = self.create_sellable()
        sellable2.cost = currency('10')
        decrease.add_sellable(sellable1, quantity=2)
        decrease.add_sellable(sellable2, quantity=5)
        self.assertEquals(decrease.get_total_cost(), 250)

    # NF-e operations

    def test_comments(self):
        decrease = self.create_stock_decrease(reason=u'Reason')
        self.assertEquals(decrease.comments, decrease.reason)

    def test_discount_value(self):
        decrease = self.create_stock_decrease()
        self.assertEquals(decrease.discount_value, currency(0))

    def test_invoice_totals(self):
        decrease = self.create_stock_decrease()
        decrease_item = self.create_stock_decrease_item(decrease, quantity=2)
        decrease_item.cost = 50
        self.assertEquals(decrease.invoice_subtotal, 100)
        self.assertEquals(decrease.invoice_total, 100)

    def test_payments(self):
        decrease = self.create_stock_decrease()
        self.assertEquals(decrease.payments, None)

        group = self.create_payment_group()
        decrease.group = group
        self.assertEquals(decrease.payments.count(), 0)

        payment = self.create_payment()
        group.add_item(payment)
        self.assertEquals(decrease.payments.count(), 1)
        payment2 = self.create_payment()
        group.add_item(payment2)
        self.assertEquals(decrease.payments.count(), 2)

    def test_recipient(self):
        person = self.create_person()
        decrease = self.create_stock_decrease(destination=person)
        self.assertEquals(decrease.recipient, person)

    def test_operation_nature(self):
        # FIXME: Check using the operation_nature that will be save in new field
        decrease = self.create_stock_decrease()
        self.assertEquals(decrease.operation_nature, u'Stock decrease')


class TestStockDecreaseItem(DomainTest):
    def test_constructor(self):
        with self.assertRaisesRegexp(
                TypeError, 'You must provide a sellable argument'):
            StockDecreaseItem(store=self.store)

        with self.assertRaisesRegexp(
                TypeError, 'You must provide a sellable argument'):
            StockDecreaseItem(store=self.store,
                              sellable=None)
        item = self.create_stock_decrease_item()
        self.assertIsNotNone(item.icms_info)
        self.assertIsNotNone(item.ipi_info)
        self.assertIsNotNone(item.pis_info)
        self.assertIsNotNone(item.cofins_info)

    def test_get_description(self):
        decrease = self.create_stock_decrease()
        product = self.create_product()
        decrease_item = decrease.add_sellable(product.sellable)
        self.assertEqual(decrease_item.get_description(), u'Description')

    def test_get_total(self):
        item = self.create_stock_decrease_item()
        item.cost = currency('100')
        item.quantity = 10
        self.assertEqual(item.get_total(), 1000)

    def test_get_quantity_unit_string(self):
        item = self.create_stock_decrease_item(quantity=1)
        item.sellable.unit = None
        self.assertEquals(item.get_quantity_unit_string(), u'1.000')
        item.sellable.unit = self.create_sellable_unit(description=u'U')
        self.assertEquals(item.get_quantity_unit_string(), u'1.000 U')

    # NF-e operations

    def test_parent(self):
        order = self.create_stock_decrease()
        item = self.create_stock_decrease_item(order)
        self.assertEquals(item.parent, order)

    def test_base_price(self):
        decrease_item = self.create_stock_decrease_item()
        decrease_item.cost = 140
        self.assertEquals(decrease_item.base_price, 140)

    def test_price(self):
        decrease_item = self.create_stock_decrease_item()
        decrease_item.cost = 100
        self.assertEquals(decrease_item.price, decrease_item.cost)

    def test_nfe_cfop_code(self):
        decrease = self.create_stock_decrease()
        decrease_item = self.create_stock_decrease_item(decrease)
        cfop = decrease.cfop.code.replace('.', '')
        self.assertEquals(decrease_item.nfe_cfop_code, cfop)
