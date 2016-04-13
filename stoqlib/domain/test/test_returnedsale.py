# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2016 Async Open Source <http://www.async.com.br>
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

from stoqlib.database.runtime import get_current_branch, get_current_user
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.product import StockTransactionHistory
from stoqlib.domain.returnedsale import ReturnedSale, ReturnedSaleItem
from stoqlib.domain.sale import Sale
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

    def test_remove_item(self):
        item = self.create_returned_sale_item()
        order = item.returned_sale

        before_remove = self.store.find(ReturnedSaleItem).count()
        order.remove_item(item)
        after_remove = self.store.find(ReturnedSaleItem).count()

        self.assertEqual(before_remove, after_remove + 1)

        with self.sysparam(SYNCHRONIZED_MODE=True):
            item = self.create_returned_sale_item()
            order = item.returned_sale

            before_remove = self.store.find(ReturnedSaleItem).count()
            order.remove_item(item)
            after_remove = self.store.find(ReturnedSaleItem).count()

            # The item should still be on the database
            self.assertEqual(before_remove, after_remove)

            # But not related to the loan
            self.assertEquals(self.store.find(ReturnedSaleItem, returned_sale=order).count(), 0)

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

    def test_trade_as_discount(self):
        sale = self.create_sale(branch=get_current_branch(self.store))
        self.assertEqual(sale.discount_value, currency(0))

        sellable = self.add_product(sale, price=50)
        storable = sellable.product_storable
        balance_before_confirm = storable.get_balance_for_branch(sale.branch)
        sale.order()

        self.add_payments(sale)
        sale.confirm()
        self.assertEqual(storable.get_balance_for_branch(sale.branch),
                         balance_before_confirm - 1)
        balance_before_trade = storable.get_balance_for_branch(sale.branch)

        returned_sale = sale.create_sale_return_adapter()
        new_sale = self.create_sale()
        returned_sale.new_sale = new_sale
        with self.sysparam(USE_TRADE_AS_DISCOUNT=True):
            returned_sale.trade()
            self.assertEqual(new_sale.discount_value, currency(50))
        self.assertEqual(returned_sale.status, ReturnedSale.STATUS_CONFIRMED)

        self.assertEqual(storable.get_balance_for_branch(sale.branch),
                         balance_before_trade + 1)

    def test_trade_on_another_branch(self):
        sale_branch = get_current_branch(self.store)
        return_branch = self.create_branch()
        current_user = get_current_user(self.store)

        product = self.create_product(branch=sale_branch, stock=5)
        sale = self.create_sale(branch=sale_branch)
        sale_item = sale.add_sellable(sellable=product.sellable)
        storable = product.storable
        sale.order()

        self.add_payments(sale)
        sale.confirm()
        self.assertEqual(storable.get_balance_for_branch(sale_branch), 4)

        returned_sale = ReturnedSale(store=self.store,
                                     responsible=current_user,
                                     sale=sale,
                                     branch=return_branch)
        ReturnedSaleItem(store=self.store,
                         quantity=1,
                         price=10,
                         sale_item=sale_item,
                         returned_sale=returned_sale)
        new_sale = self.create_sale(branch=return_branch)
        returned_sale.new_sale = new_sale
        returned_sale.trade()

        self.assertEqual(returned_sale.status, ReturnedSale.STATUS_PENDING)
        self.assertEqual(storable.get_balance_for_branch(sale_branch), 4)
        self.assertEqual(storable.get_balance_for_branch(return_branch), 0)

        returned_sale.confirm(current_user)
        self.assertEqual(returned_sale.status, ReturnedSale.STATUS_CONFIRMED)
        self.assertEqual(storable.get_balance_for_branch(sale_branch), 5)
        self.assertEqual(storable.get_balance_for_branch(return_branch), 0)

    def test_trade_without_sale(self):
        # With discount
        branch = get_current_branch(self.store)
        returned_sale = ReturnedSale(store=self.store,
                                     responsible=get_current_user(self.store),
                                     branch=branch)
        storable = self.create_storable(branch=branch,
                                        stock=10)
        ReturnedSaleItem(store=self.store,
                         quantity=1,
                         price=10,
                         sellable=storable.product.sellable,
                         returned_sale=returned_sale)
        new_sale = self.create_sale()
        returned_sale.new_sale = new_sale
        balance_before_trade = storable.get_balance_for_branch(branch)

        with self.sysparam(USE_TRADE_AS_DISCOUNT=True):
            returned_sale.trade()
            self.assertEqual(new_sale.discount_value, currency(10))

        self.assertEqual(returned_sale.status, ReturnedSale.STATUS_CONFIRMED)
        self.assertEqual(storable.get_balance_for_branch(branch),
                         balance_before_trade + 1)

        # Without discount
        returned_sale2 = ReturnedSale(store=self.store,
                                      responsible=get_current_user(self.store),
                                      branch=branch)
        storable = self.create_storable(branch=branch,
                                        stock=10)
        ReturnedSaleItem(store=self.store,
                         quantity=1,
                         price=10,
                         sellable=storable.product.sellable,
                         returned_sale=returned_sale2)
        new_sale = self.create_sale()
        returned_sale2.new_sale = new_sale
        balance_before_trade = storable.get_balance_for_branch(branch)

        returned_sale2.trade()
        self.assertEqual(returned_sale.status, ReturnedSale.STATUS_CONFIRMED)
        self.assertEqual(new_sale.discount_value, currency(0))

        group = new_sale.group
        payment = group.payments[0]
        self.assertEqual(group.payments.count(), 1)
        self.assertEqual(payment.value, returned_sale2.returned_total)
        self.assertEqual(storable.get_balance_for_branch(branch),
                         balance_before_trade + 1)

    @mock.patch('stoqlib.domain.returnedsale.get_current_branch')
    def test_return_on_another_branch(self, gcb):
        # Branch where the sale was created
        sale_branch = get_current_branch(self.store)
        # Branch where the sale was returned
        return_branch = self.create_branch()
        gcb.return_value = return_branch

        product = self.create_product(branch=sale_branch, stock=2)
        client = self.create_client()
        # Creating a sale on sale_branch
        sale = self.create_sale(branch=sale_branch, client=client)
        sale_item = sale.add_sellable(sellable=product.sellable)

        # Adding payments and confirming the sale
        payments = self.add_payments(sale, method_type=u'bill',
                                     installments=2)
        payments[0].status = Payment.STATUS_PENDING
        self.add_payments(sale, method_type=u'money')
        sale.order()
        sale.confirm()

        # Creating the returned_sale
        rsale = ReturnedSale(branch=return_branch,
                             sale=sale,
                             store=self.store)
        ReturnedSaleItem(store=self.store,
                         returned_sale=rsale,
                         sale_item=sale_item,
                         quantity=1)

        rsale.return_(u'credit')
        # Checking the status of sale and returned_sale
        self.assertEquals(rsale.status, ReturnedSale.STATUS_PENDING)
        self.assertEquals(sale.status, Sale.STATUS_RETURNED)
        # Checking the quantity on sale_branch
        self.assertEquals(product.storable.get_balance_for_branch(sale_branch), 1)
        # We should not increase the stock of that product on return_branch
        self.assertEquals(product.storable.get_balance_for_branch(return_branch), 0)

    # NF-e operations

    def test_comments(self):
        returned_sale = self.create_returned_sale()
        returned_sale.reason = u'Reason'
        self.assertEquals(returned_sale.comments, returned_sale.reason)

    def test_discount_value(self):
        returned_sale = self.create_returned_sale()
        self.assertEquals(returned_sale.discount_value, currency(0))

    def test_returned_sale_totals(self):
        # Verificar esse funcionamento no Stoq
        sale = self.create_sale()
        product = self.create_product(price=100)
        sale_item = sale.add_sellable(product.sellable)
        self.add_payments(sale)
        sale.order()
        sale.confirm()

        returned_sale = ReturnedSale(branch=sale.branch,
                                     sale=sale,
                                     store=self.store)
        ReturnedSaleItem(returned_sale=returned_sale,
                         sale_item=sale_item,
                         quantity=1)
        self.assertEquals(returned_sale.invoice_subtotal, 100)
        self.assertEquals(returned_sale.invoice_total, 100)

    def test_recipient(self):
        # Without client
        sale = self.create_sale()
        returned_sale = self.create_returned_sale(sale)
        self.assertEquals(returned_sale.recipient, None)

        # With client
        client = self.create_client()
        sale2 = self.create_sale(client=client)
        returned_sale = self.create_returned_sale(sale2)
        self.assertEquals(returned_sale.recipient, client.person)

    def test_nfe_cfop_code(self):
        # FIXME: Check using the operation_nature that will be saved in new field.
        returned_sale = self.create_returned_sale()
        self.assertEquals(returned_sale.operation_nature, u'Sale Return')

    def test_status(self):
        rsale = self.create_returned_sale()
        rsale.status = ReturnedSale.STATUS_PENDING
        self.assertTrue(rsale.is_pending())

        rsale.status = ReturnedSale.STATUS_CONFIRMED
        self.assertTrue(rsale.can_undo())

        rsale.status = ReturnedSale.STATUS_CANCELLED
        self.assertTrue(rsale.is_undone())

    def test_undo(self):
        sale_item = self.create_sale_item()
        sale = sale_item.sale
        sale.status = Sale.STATUS_RETURNED
        sale.return_date = sale_item.sale.open_date

        returned_item = self.create_returned_sale_item(sale_item=sale_item)
        returned_sale = returned_item.returned_sale
        returned_sale.status = ReturnedSale.STATUS_CONFIRMED
        returned_sale.sale = sale

        returned_item.returned_sale.undo(reason=u'teste')

        self.assertEquals(sale.status, sale.STATUS_CONFIRMED)
        self.assertEquals(sale.return_date, None)
        self.assertEquals(returned_item.returned_sale.status,
                          ReturnedSale.STATUS_CANCELLED)

    def test_guess_payment_method(self):
        # Note that this is not testing the real return process, only the guess
        # payment method method
        rsale = self.create_returned_sale()
        self.create_returned_sale_item(rsale)

        credit_method = self.get_payment_method(u'credit')
        bill_method = self.get_payment_method(u'bill')

        # Without payments we should have guessed 'money'
        method = rsale._guess_payment_method()
        self.assertEquals(method, 'money')

        payment = self.create_payment(method=credit_method,
                                      value=rsale.returned_total,
                                      group=rsale.group)
        payment.set_pending()
        self.assertEquals(rsale._guess_payment_method(), 'credit')

        # Now add another credit payment. The guessed should still be credit
        payment = self.create_payment(method=credit_method,
                                      value=rsale.returned_total,
                                      group=rsale.group)
        payment.set_pending()
        self.assertEquals(rsale._guess_payment_method(), 'credit')

        # If we now add a different method, the guessed type should be money
        payment = self.create_payment(method=bill_method,
                                      value=rsale.returned_total,
                                      group=rsale.group)
        payment.set_pending()
        self.assertEquals(rsale._guess_payment_method(), 'money')


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
        returned_item = self.create_returned_sale_item()
        self.assertIsNotNone(returned_item.icms_info)
        self.assertIsNotNone(returned_item.ipi_info)
        self.assertIsNotNone(returned_item.pis_info)
        self.assertIsNotNone(returned_item.cofins_info)

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

    def test_get_total(self):
        sale_item = self.create_sale_item()
        returned_item = ReturnedSaleItem(store=self.store,
                                         sale_item=sale_item)
        returned_item.quantity = 2
        returned_item.price = 100
        self.assertEquals(returned_item.get_total(), 200)

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

    def test_return_with_component(self):
        sale = self.create_sale()
        normal = self.create_product(description=u'Normal', storable=True,
                                     stock=3)
        package = self.create_product(description=u'Package', is_package=True)
        component = self.create_product(description=u'Component',
                                        storable=True,
                                        stock=5)
        component2 = self.create_product(description=u'Component 2',
                                         storable=True,
                                         stock=1)
        p_comp = self.create_product_component(product=package,
                                               component=component,
                                               component_quantity=5,
                                               price=2)
        p_comp2 = self.create_product_component(product=package,
                                                component=component2,
                                                component_quantity=1,
                                                price=5)
        parent_item = sale.add_sellable(package.sellable, price=0)
        sale.add_sellable(normal.sellable,
                          quantity=1)
        sale.add_sellable(component.sellable,
                          price=p_comp.price,
                          parent=parent_item,
                          quantity=p_comp.quantity * parent_item.quantity)
        sale.add_sellable(component2.sellable,
                          price=p_comp2.price,
                          parent=parent_item,
                          quantity=p_comp2.quantity * parent_item.quantity)

        self.add_payments(sale)
        sale.order()
        sale.confirm()
        r_sale = sale.create_sale_return_adapter()
        for item in r_sale.returned_items:
            for child in item.children_items:
                # Do not return the children of a package product
                child.quantity = 0
                item.quantity = 0
        r_sale.return_()
        self.assertEquals(len(list(r_sale.returned_items)), 1)

    def test_undo(self):
        sellable = self.create_sellable(product=True, storable=True)
        sale_item = self.create_sale_item(sellable=sellable)
        returned_item = self.create_returned_sale_item(sale_item=sale_item)

        # Lets supose this item is already returned
        self.assertEquals(sale_item.quantity, 1)
        self.assertEquals(sale_item.quantity_decreased, 0)

        # If there is not enought stock, we should raise an error
        from stoqlib.exceptions import StockError
        with self.assertRaisesRegexp(
                StockError,
                "Quantity to sell is greater than the available stock."):
            returned_item.undo()

        # Lets increase the stock
        storable = sale_item.sellable.product.storable
        storable.increase_stock(10, sale_item.sale.branch,
                                type=StockTransactionHistory.TYPE_INITIAL,
                                object_id=None)

        # Now we should be able to undo the return
        returned_item.undo()
        # The quantity decreased should be 1
        self.assertEquals(sale_item.quantity_decreased, 1)
        # And there should be 9 itens in stock
        self.assertEquals(storable.get_balance_for_branch(sale_item.sale.branch), 9)

    def test_get_component_quantity(self):
        package = self.create_product(description=u"Package", is_package=True)
        component = self.create_product(description=u"Component", stock=2)
        self.create_product_component(product=package, component=component)
        sale_item = self.create_sale_item(sellable=package.sellable)
        child_item = self.create_sale_item(sellable=component.sellable,
                                           parent_item=sale_item)

        r_item = self.create_returned_sale_item(sale_item=sale_item)
        r_child_item = self.create_returned_sale_item(sale_item=child_item,
                                                      parent_item=r_item)

        self.assertEquals(r_child_item.get_component_quantity(r_item), 1)

    # NF-e operations

    def test_base_price(self):
        returned_item = self.create_returned_sale_item()
        returned_item.price = 150
        self.assertEquals(returned_item.base_price, 150)
        self.assertEquals(returned_item.item_discount, 0)

    def test_parent(self):
        returned_sale = self.create_returned_sale()
        returned_item = self.create_returned_sale_item(returned_sale)
        self.assertEquals(returned_item.parent, returned_sale)

    def test_nfe_cfop_code(self):
        client = self.create_client()
        self.create_address(person=client.person)

        sale = self.create_sale(client=client)
        returned_sale = self.create_returned_sale(sale)
        returned_sale_item = self.create_returned_sale_item(returned_sale)
        # Branch address isn't the same of client
        self.assertEquals(returned_sale_item.nfe_cfop_code, u'2202')
        #Branch address is the same of client
        returned_sale.branch.person = client.person
        self.assertEquals(returned_sale_item.nfe_cfop_code, u'1202')
