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

from decimal import Decimal

from kiwi.currency import currency
import mock

from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.product import StockTransactionHistory
from stoqlib.domain.returnedsale import ReturnedSale, ReturnedSaleItem
from stoqlib.domain.sale import Sale
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib.dateutils import localdatetime

__tests__ = 'stoqlib/domain/returnedsale.py'


class TestReturnedSale(DomainTest):
    def test_remove(self):
        sale = self.create_sale()
        self.add_product(sale)
        self.add_product(sale)
        self.add_payments(sale)
        sale.order(self.current_user)
        sale.confirm(self.current_user)
        returned_sale = sale.create_sale_return_adapter(self.current_branch, self.current_user,
                                                        self.current_station)

        total = self.store.find(ReturnedSale, id=returned_sale.id).count()
        total_items = self.store.find(ReturnedSaleItem,
                                      returned_sale_id=returned_sale.id).count()

        self.assertEqual(total, 1)
        self.assertEqual(total_items, 2)

        returned_sale.remove()

        total = self.store.find(ReturnedSale, id=returned_sale.id).count()
        total_items = self.store.find(ReturnedSaleItem,
                                      returned_sale_id=returned_sale.id).count()

        self.assertEqual(total, 0)
        self.assertEqual(total_items, 0)

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
            self.assertEqual(self.store.find(ReturnedSaleItem, returned_sale=order).count(), 0)

    def test_client(self):
        branch = self.create_branch()
        client = self.create_client()
        sale = self.create_sale(branch=branch)
        sale.client = client
        rsale = ReturnedSale(store=self.store, branch=branch, station=self.current_station)
        self.assertIsNone(rsale.client)
        rsale.sale = sale
        self.assertEqual(rsale.client, client)

    def test_group(self):
        branch = self.create_branch()
        client = self.create_client()
        sale = self.create_sale(branch=branch)
        sale.client = client
        rsale = ReturnedSale(branch=branch, station=self.current_station,
                             store=self.store)
        self.assertIsNone(rsale.group)
        rsale.sale = sale
        self.assertEqual(rsale.group, sale.group)

        rsale.sale = None
        rsale.new_sale = sale
        self.assertEqual(rsale.group, sale.group)

    def test_sale_total(self):
        branch = self.create_branch()

        rsale = ReturnedSale(branch=branch, station=self.current_station,
                             store=self.store)
        self.assertEqual(rsale.sale_total, currency(0))

        sale = self.create_sale(branch=branch)
        sellable = self.add_product(sale)
        self.add_payments(sale)
        rsale1 = ReturnedSale(branch=branch, station=self.current_station,
                              status=ReturnedSale.STATUS_CONFIRMED,
                              sale=sale,
                              store=self.store)
        rsale2 = ReturnedSale(branch=branch, station=self.current_station,
                              status=ReturnedSale.STATUS_CONFIRMED,
                              sale=sale,
                              store=self.store)
        self.assertEqual(rsale1.sale_total, currency(0))

        item = ReturnedSaleItem(store=self.store,
                                returned_sale=rsale2,
                                sellable=sellable)
        item.quantity = 10
        item.price = 10

        self.assertEqual(rsale1.sale_total, currency(-100))

    def test_sale_total_with_rounding(self):
        branch = self.create_branch()

        sale = self.create_sale(branch=branch)
        self.add_product(sale, price=2, quantity=Decimal('0.527'))
        self.add_product(sale, price=2, quantity=Decimal('0.527'))
        self.add_payments(sale)
        sale.order(self.current_user)
        sale.confirm(self.current_user)
        rsale = ReturnedSale(branch=branch, station=self.current_station,
                             sale=sale,
                             store=self.store)
        # Here, if the rounding was made before adding both products, we would actually
        # end up with a sale_total of 2.11 instead of 2.10, which is the expected value.
        self.assertEqual(rsale.sale_total, currency(Decimal('2.10')))

    def test_paid_total(self):
        branch = self.create_branch()
        rsale = ReturnedSale(branch=branch, station=self.current_station,
                             store=self.store)
        self.assertEqual(rsale.paid_total, currency(0))

        sale = self.create_sale(branch=branch)
        self.add_product(sale)
        rsale = ReturnedSale(branch=branch, station=self.current_station,
                             sale=sale,
                             store=self.store)
        self.add_payments(sale)
        sale.order(self.current_user)
        sale.confirm(self.current_user)
        self.assertEqual(rsale.paid_total, currency(10))

    def test_total_amount(self):
        branch = self.create_branch()
        sale = self.create_sale(branch=branch)
        self.add_product(sale)
        rsale = ReturnedSale(branch=branch, station=self.current_station,
                             sale=sale,
                             store=self.store)
        self.assertEqual(rsale.total_amount, currency(0))

    def test_total_amount_abs(self):
        branch = self.create_branch()
        sale = self.create_sale(branch=branch)
        self.add_product(sale)
        rsale = ReturnedSale(branch=branch, station=self.current_station,
                             sale=sale,
                             store=self.store)
        self.assertEqual(rsale.total_amount_abs, currency(0))

    def test_return_with_credit(self):
        sale_item = self.create_sale_item()
        sale = sale_item.sale
        sellable = sale_item.sellable
        self.create_storable(product=sellable.product, branch=self.current_branch, stock=10)
        payments = self.add_payments(sale, method_type=u'bill',
                                     installments=2)
        payments[0].status = Payment.STATUS_PENDING
        self.add_payments(sale, method_type=u'money')
        sale.order(self.current_user)
        sale.confirm(self.current_user)

        rsale = ReturnedSale(branch=self.current_branch, station=self.current_station,
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
        rsale.return_(self.current_user, 'credit')

    def test_return_unpaid_with_credit(self):
        sale_item = self.create_sale_item()
        sale = sale_item.sale
        sellable = sale_item.sellable
        self.create_storable(product=sellable.product, branch=self.current_branch, stock=10)
        self.add_payments(sale, method_type=u'bill', installments=1)
        sale.order(self.current_user)
        sale.confirm(self.current_user)

        rsale = ReturnedSale(branch=self.current_branch, station=self.current_station,
                             sale=sale,
                             store=self.store)
        ReturnedSaleItem(store=self.store,
                         returned_sale=rsale,
                         sale_item=sale_item,
                         quantity=1)

        # Before the return there is not out payment
        self.assertIsNone(sale.group.payments.find(payment_type=Payment.TYPE_OUT).one())
        rsale.return_(self.current_user, 'credit')

        # There should be one payment with a credit for the returned value
        self.assertIsNotNone(sale.group.payments.find(payment_type=Payment.TYPE_OUT).one())

    def test_trade_as_discount(self):
        sale = self.create_sale(branch=self.current_branch)
        self.assertEqual(sale.discount_value, currency(0))

        sellable = self.add_product(sale, price=50)
        storable = sellable.product_storable
        balance_before_confirm = storable.get_balance_for_branch(sale.branch)
        sale.order(self.current_user)

        self.add_payments(sale)
        sale.confirm(self.current_user)
        self.assertEqual(storable.get_balance_for_branch(sale.branch),
                         balance_before_confirm - 1)
        balance_before_trade = storable.get_balance_for_branch(sale.branch)

        returned_sale = sale.create_sale_return_adapter(self.current_branch, self.current_user,
                                                        self.current_station)
        new_sale = self.create_sale()
        returned_sale.new_sale = new_sale
        with self.sysparam(USE_TRADE_AS_DISCOUNT=True):
            returned_sale.trade(self.current_user)
            self.assertEqual(new_sale.discount_value, currency(50))
        self.assertEqual(returned_sale.status, ReturnedSale.STATUS_CONFIRMED)

        self.assertEqual(storable.get_balance_for_branch(sale.branch),
                         balance_before_trade + 1)

    def test_trade_on_another_branch(self):
        sale_branch = self.current_branch
        return_branch = self.create_branch()

        product = self.create_product(branch=sale_branch, stock=5)
        sale = self.create_sale(branch=sale_branch)
        sale_item = sale.add_sellable(sellable=product.sellable)
        storable = product.storable
        sale.order(self.current_user)

        self.add_payments(sale)
        sale.confirm(self.current_user)
        self.assertEqual(storable.get_balance_for_branch(sale_branch), 4)

        returned_sale = ReturnedSale(store=self.store, station=self.current_station,
                                     responsible=self.current_user,
                                     sale=sale,
                                     branch=return_branch)
        ReturnedSaleItem(store=self.store,
                         quantity=1,
                         price=10,
                         sale_item=sale_item,
                         returned_sale=returned_sale)
        new_sale = self.create_sale(branch=return_branch)
        returned_sale.new_sale = new_sale
        returned_sale.trade(self.current_user)

        self.assertEqual(returned_sale.status, ReturnedSale.STATUS_PENDING)
        self.assertEqual(storable.get_balance_for_branch(sale_branch), 4)
        self.assertEqual(storable.get_balance_for_branch(return_branch), 0)

        # This sale is returned in the return_branch, so the stock for the original sale branch is
        # the same, but the return branch has a new stock item
        returned_sale.confirm(self.current_user)
        self.assertEqual(returned_sale.status, ReturnedSale.STATUS_CONFIRMED)
        self.assertEqual(storable.get_balance_for_branch(sale_branch), 4)
        self.assertEqual(storable.get_balance_for_branch(return_branch), 1)

    def test_trade_without_sale(self):
        # With discount
        returned_sale = ReturnedSale(store=self.store, station=self.current_station,
                                     responsible=self.current_user,
                                     branch=self.current_branch)
        storable = self.create_storable(branch=self.current_branch,
                                        stock=10)
        ReturnedSaleItem(store=self.store,
                         quantity=1,
                         price=10,
                         sellable=storable.product.sellable,
                         returned_sale=returned_sale)
        new_sale = self.create_sale()
        returned_sale.new_sale = new_sale
        balance_before_trade = storable.get_balance_for_branch(self.current_branch)

        with self.sysparam(USE_TRADE_AS_DISCOUNT=True):
            returned_sale.trade(self.current_user)
            self.assertEqual(new_sale.discount_value, currency(10))

        self.assertEqual(returned_sale.status, ReturnedSale.STATUS_CONFIRMED)
        self.assertEqual(storable.get_balance_for_branch(self.current_branch),
                         balance_before_trade + 1)

        # Without discount
        returned_sale2 = ReturnedSale(store=self.store, station=self.current_station,
                                      responsible=self.current_user,
                                      branch=self.current_branch)
        storable = self.create_storable(branch=self.current_branch,
                                        stock=10)
        ReturnedSaleItem(store=self.store,
                         quantity=1,
                         price=10,
                         sellable=storable.product.sellable,
                         returned_sale=returned_sale2)
        new_sale = self.create_sale()
        returned_sale2.new_sale = new_sale
        balance_before_trade = storable.get_balance_for_branch(self.current_branch)

        returned_sale2.trade(self.current_user)
        self.assertEqual(returned_sale.status, ReturnedSale.STATUS_CONFIRMED)
        self.assertEqual(new_sale.discount_value, currency(0))

        group = new_sale.group
        payment = group.payments[0]
        self.assertEqual(group.payments.count(), 1)
        self.assertEqual(payment.value, returned_sale2.returned_total)
        self.assertEqual(storable.get_balance_for_branch(self.current_branch),
                         balance_before_trade + 1)

    def test_return_on_another_branch(self):
        # Branch where the sale was created
        sale_branch = self.current_branch

        # Branch where the sale was returned
        return_branch = self.create_branch()

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
        sale.order(self.current_user)
        sale.confirm(self.current_user)

        # Creating the returned_sale
        rsale = ReturnedSale(branch=return_branch, station=self.current_station,
                             sale=sale,
                             store=self.store)
        ReturnedSaleItem(store=self.store,
                         returned_sale=rsale,
                         sale_item=sale_item,
                         quantity=1)

        rsale.return_(self.current_user, 'credit')
        # Checking the status of sale and returned_sale
        self.assertEqual(rsale.status, ReturnedSale.STATUS_PENDING)
        self.assertEqual(sale.status, Sale.STATUS_RETURNED)
        # Checking the quantity on sale_branch
        self.assertEqual(product.storable.get_balance_for_branch(sale_branch), 1)
        # We should not increase the stock of that product on return_branch
        self.assertEqual(product.storable.get_balance_for_branch(return_branch), 0)

    # NF-e operations

    def test_comments(self):
        returned_sale = self.create_returned_sale()
        returned_sale.reason = u'Reason'
        self.assertEqual(returned_sale.comments, returned_sale.reason)

    def test_discount_value(self):
        returned_sale = self.create_returned_sale()
        self.assertEqual(returned_sale.discount_value, currency(0))

    def test_returned_sale_totals(self):
        # Verificar esse funcionamento no Stoq
        sale = self.create_sale()
        product = self.create_product(price=100)
        sale_item = sale.add_sellable(product.sellable)
        self.add_payments(sale)
        sale.order(self.current_user)
        sale.confirm(self.current_user)

        returned_sale = ReturnedSale(branch=sale.branch, station=self.current_station,
                                     sale=sale,
                                     store=self.store)
        ReturnedSaleItem(store=self.store, returned_sale=returned_sale,
                         sale_item=sale_item,
                         quantity=1)
        self.assertEqual(returned_sale.invoice_subtotal, 100)
        self.assertEqual(returned_sale.invoice_total, 100)

    def test_recipient(self):
        # Without client
        sale = self.create_sale()
        returned_sale = self.create_returned_sale(sale)
        self.assertEqual(returned_sale.recipient, None)

        # With client
        client = self.create_client()
        sale2 = self.create_sale(client=client)
        returned_sale = self.create_returned_sale(sale2)
        self.assertEqual(returned_sale.recipient, client.person)

        # without a sale (only new sale)
        returned_sale = self.create_trade()
        returned_sale.new_sale.client = client
        self.assertEqual(returned_sale.recipient, client.person)

    def test_cfop_code(self):
        # FIXME: Check using the operation_nature that will be saved in new field.
        returned_sale = self.create_returned_sale()
        self.assertEqual(returned_sale.operation_nature, u'Sale Return')

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

        returned_item.returned_sale.undo(self.current_user, reason=u'teste')

        self.assertEqual(sale.status, sale.STATUS_CONFIRMED)
        self.assertEqual(sale.return_date, None)
        self.assertEqual(returned_item.returned_sale.status,
                         ReturnedSale.STATUS_CANCELLED)

    def test_undo_with_pending_payment(self):
        # First, we create a sale_item and relate it to a sale.
        sale_item = self.create_sale_item()
        sale = sale_item.sale
        self.add_payments(sale)
        sale.order(self.current_user)
        # The sale is then completed and confirmed with its payment confirmed as well.
        sale.confirm(self.current_user)

        # Now, we create a return adapter to make the actual return.
        returned_sale = sale.create_sale_return_adapter(self.current_branch, self.current_user,
                                                        self.current_station)
        returned_sale.confirm(self.create_user())

        # A pending payment is then made for it to be cancelled when the sale return is
        # actually undone.
        payment = self.create_payment(date=localdatetime(2012, 1, 1),
                                      value=sale_item.price,
                                      group=sale.group)
        payment.set_pending()

        # There should be 2 payments at this point.
        n_payments1 = sale.payments.count()

        returned_sale.undo(self.current_user, reason='teste')

        # This test evaluates if the pending payment was actually cancelled and that, at
        # any point around the undoing of the sale return, no payments are added or
        # removed.
        self.assertEqual(payment.status, Payment.STATUS_CANCELLED)
        self.assertEqual(n_payments1, 2)
        self.assertEqual(sale.group.payments.count(), 2)


class TestReturnedSaleItem(DomainTest):
    def test_constructor(self):
        returned_sale = self.create_returned_sale()
        with self.assertRaisesRegex(
                ValueError,
                "A sale_item or a sellable is mandatory to create this object"):
            ReturnedSaleItem(returned_sale=returned_sale, store=self.store)

        sellable = self.create_sellable()
        sale_item = self.create_sale_item()
        with self.assertRaisesRegex(
                ValueError,
                "sellable must be the same as sale_item.sellable"):
            ReturnedSaleItem(sellable=sellable, returned_sale=returned_sale,
                             sale_item=sale_item,
                             store=self.store)
        returned_item = self.create_returned_sale_item()
        self.assertIsNotNone(returned_item.icms_info)
        self.assertIsNotNone(returned_item.ipi_info)
        self.assertIsNotNone(returned_item.pis_info)
        self.assertIsNotNone(returned_item.cofins_info)

    def test_total(self):
        item = self.create_returned_sale_item()
        item.quantity = 1
        self.assertEqual(item.total, 100)
        item.price = 10
        self.assertEqual(item.total, 10)
        item.quantity = 20
        self.assertEqual(item.total, 200)

    def test_get_total(self):
        returned_item = self.create_returned_sale_item()
        returned_item.quantity = 2
        returned_item.price = 100
        self.assertEqual(returned_item.get_total(), 200)

    def test_return_(self):
        sale = self.create_sale()
        self.add_product(sale)
        self.add_payments(sale)
        sale.order(self.current_user)
        sale.confirm(self.current_user)
        returned_sale = sale.create_sale_return_adapter(self.current_branch, self.current_user,
                                                        self.current_station)

        item = self.store.find(ReturnedSaleItem,
                               returned_sale=returned_sale).any()

        self.assertEqual(item.sale_item.quantity_decreased, 1)

        with mock.patch(
                'stoqlib.domain.product.Storable.increase_stock') as increase_stock:
            item.return_(self.current_user)
        self.assertEqual(item.sale_item.quantity_decreased, 0)

        increase_stock.assert_called_once_with(
            Decimal(1), self.current_branch, StockTransactionHistory.TYPE_RETURNED_SALE,
            item.id, self.current_user, batch=item.batch)

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
        sale.order(self.current_user)
        sale.confirm(self.current_user)
        r_sale = sale.create_sale_return_adapter(self.current_branch, self.current_user,
                                                 self.current_station)
        for item in r_sale.returned_items:
            for child in item.children_items:
                # Do not return the children of a package product
                child.quantity = 0
                item.quantity = 0
        r_sale.return_(self.current_user)
        self.assertEqual(len(list(r_sale.returned_items)), 1)

    def test_undo(self):
        sellable = self.create_sellable(product=True, storable=True)
        sale_item = self.create_sale_item(sellable=sellable)
        returned_item = self.create_returned_sale_item(sale_item=sale_item)

        # Lets supose this item is already returned
        self.assertEqual(sale_item.quantity, 1)
        self.assertEqual(sale_item.quantity_decreased, 0)

        # If there is not enought stock, we should raise an error
        from stoqlib.exceptions import StockError
        with self.assertRaisesRegex(
                StockError,
                "Quantity to decrease is greater than the available stock."):
            returned_item.undo(self.current_user)

        # Lets increase the stock
        storable = sale_item.sellable.product.storable
        storable.increase_stock(10, sale_item.sale.branch, StockTransactionHistory.TYPE_INITIAL,
                                None, self.current_user)

        # Now we should be able to undo the return
        returned_item.undo(self.current_user)
        # The quantity decreased should be 1
        self.assertEqual(sale_item.quantity_decreased, 1)
        # And there should be 9 itens in stock
        self.assertEqual(storable.get_balance_for_branch(sale_item.sale.branch), 9)

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

        self.assertEqual(r_child_item.get_component_quantity(r_item), 1)

    # NF-e operations

    def test_base_price(self):
        returned_item = self.create_returned_sale_item()
        returned_item.price = 150
        self.assertEqual(returned_item.base_price, 150)
        self.assertEqual(returned_item.item_discount, 0)

    def test_parent(self):
        returned_sale = self.create_returned_sale()
        returned_item = self.create_returned_sale_item(returned_sale)
        self.assertEqual(returned_item.parent, returned_sale)

    def test_cfop_code(self):
        client = self.create_client()

        sale = self.create_sale(client=client)
        returned_sale = self.create_returned_sale(sale)
        returned_sale_item = self.create_returned_sale_item(returned_sale)
        self.assertEqual(returned_sale_item.cfop_code, u'1202')
