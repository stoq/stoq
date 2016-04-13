# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2013 Async Open Source <http://www.async.com.br>
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

__tests__ = 'stoqlib/domain/sale.py'

import datetime
from decimal import Decimal

from kiwi.currency import currency
import mock
from nose.exc import SkipTest
from storm.expr import And, Eq, Ne

from stoqlib.api import api
from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.commission import CommissionSource, Commission
from stoqlib.domain.event import Event
from stoqlib.domain.events import SaleIsExternalEvent
from stoqlib.domain.fiscal import FiscalBookEntry
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment, PaymentChangeHistory
from stoqlib.domain.product import Storable, StockTransactionHistory
from stoqlib.domain.returnedsale import ReturnedSaleItem
from stoqlib.domain.sale import (Sale, SalePaymentMethodView,
                                 ReturnedSaleView,
                                 ReturnedSaleItemsView, SaleItem,
                                 SaleView, SalesPersonSalesView,
                                 ClientsWithSaleView, SaleToken)
from stoqlib.domain.sellable import Sellable
from stoqlib.domain.till import TillEntry
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.domain.workorder import WorkOrder
from stoqlib.exceptions import SellError, DatabaseInconsistency
from stoqlib.lib.dateutils import localdate, localdatetime, localtoday
from stoqlib.lib.formatters import format_quantity
from stoqlib.lib.parameters import sysparam


class TestSale(DomainTest):
    def test_status_str(self):
        sale = Sale(store=self.store, branch=self.create_branch(),
                    status=Sale.STATUS_CONFIRMED)
        self.assertEquals(sale.status_str, 'Confirmed')

    def test_constructor_without_cfop(self):
        sale = Sale(store=self.store, branch=self.create_branch())
        self.assertTrue(sysparam.compare_object('DEFAULT_SALES_CFOP', sale.cfop))

    def test_get_client_document(self):
        sale = self.create_sale()
        self.assertEquals(sale.get_client_document(), None)

        sale.client = self.create_client()
        sale.client.person.individual.cpf = u'444'
        self.assertEquals(sale.get_client_document(), u'444')

    def test_sale_payments_ordered(self):
        sale = self.create_sale()
        self.add_payments(sale, method_type=u'check', installments=10)
        initial_date = localdatetime(2012, 10, 15)
        for i, p in enumerate(sale.payments):
            p.open_date = initial_date - datetime.timedelta(i)

        prev_p = None
        for p in sale.payments:
            if prev_p is None:
                prev_p = p
                continue
            self.assertGreater(p.open_date, prev_p.open_date)
            prev_p = p

    def test_get_percentage_value(self):
        sale = self.create_sale()
        sellable = self.create_sellable()
        sale.add_sellable(sellable, quantity=5)

        self.assertEqual(sale._get_percentage_value(0), currency(0))
        self.assertEqual(sale._get_percentage_value(10), currency(5))

    def test_set_discount_by_percentage(self):
        sale = self.create_sale()
        sellable = self.create_sellable(price=10)
        sale.add_sellable(sellable, quantity=5)

        sale.discount_percentage = 10
        self.assertEqual(sale.discount_value, currency(5))

        sale = self.create_sale()
        sellable = self.create_sellable(price=Decimal('1.49'))
        sale.add_sellable(sellable, quantity=1)
        sale.discount_percentage = 10
        # 10% of 1,49 = 0.149, but the calculation should be rounded
        # since we cannot have 3 decimal points on discount
        self.assertEqual(sale.discount_value, Decimal('0.15'))

    def test_get_discount_by_percentage(self):
        sale = self.create_sale()
        sellable = self.create_sellable()
        sale.add_sellable(sellable, quantity=5)

        self.assertEqual(sale.discount_percentage, Decimal('0.0'))
        sale.discount_percentage = 10
        self.assertEqual(sale.discount_percentage, 10)

    def test_set_surcharge_by_percentage(self):
        sale = self.create_sale()
        sellable = self.create_sellable()
        sale.add_sellable(sellable, quantity=5)

        sale.surcharge_percentage = 10
        self.assertEqual(sale.surcharge_value, currency(5))

        sale = self.create_sale()
        sellable = self.create_sellable(price=Decimal('1.49'))
        sale.add_sellable(sellable, quantity=1)
        sale.surcharge_percentage = 10
        # 10% of 1,49 = 0.149, but the calculation should be rounded
        # since we cannot have 3 decimal points on surcharge
        self.assertEqual(sale.surcharge_value, Decimal('0.15'))

    def test_get_surcharge_by_percentage(self):
        sale = self.create_sale()
        sellable = self.create_sellable()
        sale.add_sellable(sellable, quantity=5)

        self.assertEqual(sale.surcharge_percentage, currency(0))
        sale.surcharge_percentage = 15
        self.assertEqual(sale.surcharge_percentage, 15)

    def test_get_items(self):
        sale = self.create_sale()
        sellable = self.create_sellable()
        sale.add_sellable(sellable, quantity=5)

        items = sale.get_items()
        self.assertEqual(items.count(), 1)
        self.assertEqual(sellable, items[0].sellable)

    def test_get_items_with_children(self):
        sale = self.create_sale()
        package = self.create_product(description=u'Package', is_package=True)
        component = self.create_product(description=u'Component', stock=2)
        self.create_product_component(product=package, component=component)
        parent = sale.add_sellable(package.sellable, quantity=1)
        sale.add_sellable(component.sellable, quantity=1, parent=parent)

        items = sale.get_items(with_children=False)
        self.assertEquals(items.count(), 1)

    def test_remove_item(self):
        sale = self.create_sale()
        sellable = self.create_sellable()
        sale.add_sellable(sellable, quantity=5)

        item = sale.get_items()[0]
        sale.remove_item(item)
        self.assertEqual(sale.get_items().count(), 0)

        with self.sysparam(SYNCHRONIZED_MODE=True):
            item = self.create_sale_item()
            sale = item.sale

            before_remove = self.store.find(SaleItem).count()
            sale.remove_item(item)
            after_remove = self.store.find(SaleItem).count()

            # The item should still be on the database
            self.assertEqual(before_remove, after_remove)

            # But not related to the loan
            self.assertEquals(self.store.find(SaleItem, sale=sale).count(), 0)

    def test_remove_item_reserved(self):
        sale = self.create_sale()
        storable = self.create_storable(branch=sale.branch, stock=10)
        item = sale.add_sellable(storable.product.sellable, quantity=5)
        item.reserve(4)
        self.assertEqual(storable.get_balance_for_branch(sale.branch), 6)

        # When we remove an item, the reserved quantity should go back to stock
        sale.remove_item(item)
        self.assertEqual(storable.get_balance_for_branch(sale.branch), 10)

    def test_get_status_name(self):
        sale = self.create_sale()
        self.assertEquals(sale.get_status_name(sale.STATUS_CONFIRMED),
                          u'Confirmed')

        self.failUnlessRaises(TypeError,
                              sale.get_status_name, u'invalid status')

    def test_add_item(self):
        sale = self.create_sale()
        item = self.create_sale_item()
        with self.assertRaises(AssertionError):
            sale.add_item(item)

        self.assertIsNone(sale.get_items().one())
        item.sale = None
        sale.add_item(item)
        self.assertEquals(sale.get_items().one(), item)

    def test_get_items_missing_batch(self):
        product1_with_batch = self.create_product()
        storable1_with_batch = self.create_storable(product=product1_with_batch)
        storable1_with_batch.is_batch = True
        product2_with_batch = self.create_product()
        storable2_with_batch = self.create_storable(product=product2_with_batch)
        storable2_with_batch.is_batch = True

        sale = self.create_sale()
        # This can only happen for quotes
        sale.status = Sale.STATUS_QUOTE
        sale.add_sellable(self.create_sellable())
        item1 = sale.add_sellable(product1_with_batch.sellable)
        item2 = sale.add_sellable(product2_with_batch.sellable)

        self.assertEqual(set(sale.get_items_missing_batch()),
                         set([item1, item2]))

    def test_need_adjust_batches(self):
        product_with_batch = self.create_product()
        storable_with_batch = self.create_storable(product=product_with_batch)
        storable_with_batch.is_batch = True

        sale = self.create_sale()
        # This can only happen for quotes
        sale.status = Sale.STATUS_QUOTE
        sale.add_sellable(self.create_sellable())
        self.assertFalse(sale.need_adjust_batches())
        sale.add_sellable(product_with_batch.sellable)
        self.assertTrue(sale.need_adjust_batches())

    def test_check_and_adjust_batches(self):
        branch = get_current_branch(self.store)
        sale = self.create_sale()

        # Product without batch
        product = self.create_product()
        self.create_storable(product=product, branch=branch, stock=1)
        sale.add_sellable(product.sellable)
        self.assertEquals(sale.need_adjust_batches(), False)
        adjusted_batches = sale.check_and_adjust_batches()
        self.assertEquals(adjusted_batches, True)

        # Product with 1 batch
        product = self.create_product()
        self.create_storable(product=product, is_batch=True, branch=branch,
                             stock=1)
        sale.status = Sale.STATUS_QUOTE
        sale.add_sellable(product.sellable)
        self.assertEquals(sale.need_adjust_batches(), True)
        # Try adjust batches
        adjusted_batches = sale.check_and_adjust_batches()
        # Verify if the batches were adjusted
        self.assertEquals(adjusted_batches, True)
        self.assertEquals(sale.need_adjust_batches(), False)

        # Product with 2 batches
        product2 = self.create_product()
        storable = self.create_storable(product=product2, branch=branch)
        storable.is_batch = True
        batch1 = self.create_storable_batch(storable=storable, batch_number=u'2')
        batch2 = self.create_storable_batch(storable=storable, batch_number=u'3')
        storable.increase_stock(1, branch,
                                StockTransactionHistory.TYPE_INITIAL,
                                None, batch=batch1)
        storable.increase_stock(1, branch,
                                StockTransactionHistory.TYPE_INITIAL,
                                None, batch=batch2)
        sale.add_sellable(product2.sellable)
        self.assertEquals(sale.need_adjust_batches(), True)
        # Try adjust batches
        adjusted_batches = sale.check_and_adjust_batches()
        # Verify if the batches not were adjusted
        self.assertEquals(adjusted_batches, False)
        self.assertEquals(sale.need_adjust_batches(), True)

    def test_has_children(self):
        parent = self.create_sale_item()
        self.assertFalse(parent.has_children())

        self.create_sale_item(parent_item=parent)
        self.assertTrue(parent.has_children())

    def test_get_component(self):
        package = self.create_product(is_package=True)
        component = self.create_product(stock=2)
        self.create_product_component(product=package, component=component,
                                      component_quantity=2)
        sale_item = self.create_sale_item(sellable=package.sellable)
        child = self.create_sale_item(sellable=component.sellable,
                                      parent_item=sale_item)
        self.assertEquals(child.get_component(sale_item).quantity, 2)
        self.assertEquals(child.parent_item, sale_item)

    def test_get_component_returning_none(self):
        product = self.create_product(storable=True, stock=5)
        sale = self.create_sale()
        sale_item = sale.add_sellable(sellable=product.sellable)
        self.assertTrue(sale_item.get_component(sale_item) is None)

    def test_order(self):
        sale = self.create_sale()
        sellable = self.create_sellable()

        with self.assertRaisesRegexp(SellError, 'The sale must have sellable '
                                                'items'):
            sale.order()

        sale.add_sellable(sellable, quantity=5)

        self.failUnless(sale.can_order())
        sale.order()
        self.failIf(sale.can_order())

        # We can also order sales with QUOTE status
        sale = self.create_sale()
        sale.status = Sale.STATUS_QUOTE
        sellable = self.create_sellable()
        sale.add_sellable(sellable, quantity=5)
        self.failUnless(sale.can_order())
        sale.order()
        self.failIf(sale.can_order())

        sale.client = self.create_client()
        sale.client.is_active = False
        sale.status = sale.STATUS_INITIAL
        expected = ('Unable to make sales for clients with status %s' %
                    sale.client.get_status_string())
        with self.assertRaisesRegexp(SellError, expected):
            sale.order()

    def test_confirm_with_sale_token(self):
        token = self.create_sale_token(code=u'Token')
        sale = self.create_sale(sale_token=token)

        self.add_product(sale)
        self.add_payments(sale, u'money')
        sale.status = Sale.STATUS_QUOTE
        token.status = SaleToken.STATUS_OCCUPIED

        sale.confirm()
        self.assertEquals(token.status, SaleToken.STATUS_AVAILABLE)

    def test_confirm_money(self):
        sale = self.create_sale()
        self.add_product(sale)
        sale.order()

        self.add_payments(sale, u'money')
        self.failIf(self.store.find(FiscalBookEntry,
                                    entry_type=FiscalBookEntry.TYPE_PRODUCT,
                                    payment_group=sale.group).one())
        self.failUnless(sale.can_confirm())
        sale.confirm()
        self.failIf(sale.can_confirm())
        self.assertEqual(sale.status, Sale.STATUS_CONFIRMED)
        self.assertEqual(sale.confirm_date.date(), datetime.date.today())
        # Paying all payments, the sale status changes to STATUS_PAID
        # automatically.
        sale.group.pay()

        book_entry = self.store.find(FiscalBookEntry,
                                     entry_type=FiscalBookEntry.TYPE_PRODUCT,
                                     payment_group=sale.group).one()
        self.failUnless(book_entry)
        self.assertEqual(book_entry.cfop.code, u'5.102')
        self.assertEqual(book_entry.icms_value, Decimal("1.8"))

    def test_confirm_money_with_till(self):
        sale = self.create_sale()
        self.add_product(sale)
        sale.order()

        self.add_payments(sale, u'money')
        self.assertIsNone(
            self.store.find(FiscalBookEntry,
                            entry_type=FiscalBookEntry.TYPE_PRODUCT,
                            payment_group=sale.group).one())

        self.assertTrue(sale.can_confirm())
        sale.confirm(till=self.create_till())
        self.assertFalse(sale.can_confirm())
        self.assertEqual(sale.status, Sale.STATUS_CONFIRMED)
        self.assertEqual(sale.confirm_date.date(), datetime.date.today())
        # Paying all payments, the sale status changes to STATUS_PAID
        # automatically.
        sale.group.pay()

        book_entry = self.store.find(FiscalBookEntry,
                                     entry_type=FiscalBookEntry.TYPE_PRODUCT,
                                     payment_group=sale.group).one()
        self.assertEqual(book_entry.cfop.code, u'5.102')
        self.assertEqual(book_entry.icms_value, Decimal("1.8"))

        for payment in sale.payments:
            self.assertEquals(payment.status, Payment.STATUS_PAID)
            entry = self.store.find(TillEntry, payment=payment).one()
            self.assertEquals(entry.value, payment.value)

    def test_confirm_check(self):
        sale = self.create_sale()
        self.add_product(sale)
        sale.order()

        self.add_payments(sale, method_type=u'check')
        self.failIf(self.store.find(FiscalBookEntry,
                                    entry_type=FiscalBookEntry.TYPE_PRODUCT,
                                    payment_group=sale.group).one())
        self.failUnless(sale.can_confirm())
        sale.confirm()
        self.failIf(sale.can_confirm())
        self.assertEqual(sale.status, Sale.STATUS_CONFIRMED)
        self.assertEqual(sale.confirm_date.date(), datetime.date.today())

        book_entry = self.store.find(FiscalBookEntry,
                                     entry_type=FiscalBookEntry.TYPE_PRODUCT,
                                     payment_group=sale.group).one()
        self.failUnless(book_entry)
        self.assertEqual(book_entry.cfop.code, u'5.102')
        self.assertEqual(book_entry.icms_value, Decimal("1.8"))

    def test_confirm_check_with_till(self):
        sale = self.create_sale()
        self.add_product(sale)
        sale.order()

        self.add_payments(sale, u'check')
        self.assertIsNone(
            self.store.find(FiscalBookEntry,
                            entry_type=FiscalBookEntry.TYPE_PRODUCT,
                            payment_group=sale.group).one())

        self.assertTrue(sale.can_confirm())
        sale.confirm(till=self.create_till())
        self.assertFalse(sale.can_confirm())
        self.assertEqual(sale.status, Sale.STATUS_CONFIRMED)
        self.assertEqual(sale.confirm_date.date(), datetime.date.today())
        # Paying all payments, the sale status changes to STATUS_PAID
        # automatically.
        sale.group.pay()

        book_entry = self.store.find(FiscalBookEntry,
                                     entry_type=FiscalBookEntry.TYPE_PRODUCT,
                                     payment_group=sale.group).one()
        self.assertEqual(book_entry.cfop.code, u'5.102')
        self.assertEqual(book_entry.icms_value, Decimal("1.8"))

        for payment in sale.payments:
            self.assertEquals(payment.status, Payment.STATUS_PAID)
            entry = self.store.find(TillEntry, payment=payment).one()
            self.assertEquals(entry.value, payment.value)

    def test_confirm_paid_payments(self):
        client = self.create_client()
        sale = self.create_sale()
        sale.client = client
        self.add_product(sale)
        sale.order()
        payment = self.add_payments(sale, method_type=u'credit')[0]

        # The client does not have enought credit
        with self.assertRaises(SellError):
            sale.can_confirm()

        # But if we confirm the payment (ie, mark as paid), then it should be
        # possible to confirm the sale now
        payment.set_pending()
        payment.pay()
        self.assertTrue(sale.can_confirm())

        # If we change it back to not paid, than it should fail again
        entry = PaymentChangeHistory(self.store)
        payment.set_not_paid(entry)
        with self.assertRaises(SellError):
            sale.can_confirm()

        # Now lets create some credit for the client. And he should be able to
        # confirm again
        method = PaymentMethod.get_by_name(self.store, u'credit')
        group = self.create_payment_group(payer=client.person)
        payment = self.create_payment(payment_type=Payment.TYPE_OUT, value=10,
                                      method=method, group=group)
        payment.set_pending()
        payment.pay()
        self.assertTrue(sale.can_confirm())

    def test_confirm_client(self):
        sale = self.create_sale()
        self.add_product(sale)
        sale.order()
        self.add_payments(sale)

        sale.client = self.create_client()
        sale.confirm()
        self.assertEquals(sale.group.payer, sale.client.person)

    def test_confirm_quantity_decreased(self):
        sale = self.create_sale()
        branch = sale.branch
        sellable1 = self.add_product(sale, quantity=10)
        sellable2 = self.add_product(sale, quantity=10)
        sellable3 = self.add_product(sale, quantity=10)
        sale.order()
        self.add_payments(sale)

        storable1 = sellable1.product_storable
        storable2 = sellable2.product_storable
        storable3 = sellable3.product_storable
        stock1 = storable1.get_balance_for_branch(branch)
        stock2 = storable2.get_balance_for_branch(branch)
        stock3 = storable3.get_balance_for_branch(branch)

        # Decrease all stock from 1 and half from 2 and nothing from 3
        storable1.decrease_stock(10, branch,
                                 StockTransactionHistory.TYPE_INITIAL, None)
        storable2.decrease_stock(5, branch,
                                 StockTransactionHistory.TYPE_INITIAL, None)
        # Indicate on the items that those quantities were already decreased
        for item in sale.get_items():
            if item.sellable == sellable1:
                item.quantity_decreased = 10
            if item.sellable == sellable2:
                item.quantity_decreased = 5

        sale.confirm()

        # Check that, in the end, everything was decreased by 10,
        # that is the amount that was sold
        self.assertEqual(storable1.get_balance_for_branch(branch),
                         stock1 - 10)
        self.assertEqual(storable2.get_balance_for_branch(branch),
                         stock2 - 10)
        self.assertEqual(storable3.get_balance_for_branch(branch),
                         stock3 - 10)

    def test_pay(self):
        sale = self.create_sale()
        self.failIf(sale.can_set_paid())

        sale.status = sale.STATUS_CONFIRMED

        self.assertFalse(sale.can_set_paid())
        sale.status = sale.STATUS_INITIAL

        self.add_product(sale)
        sale.order()
        self.failIf(sale.can_set_paid())

        self.add_payments(sale, u'check')
        sale.confirm()
        sale.group.pay()

        self.failIf(sale.can_set_paid())
        self.failUnless(sale.close_date)
        self.assertEqual(sale.status, Sale.STATUS_CONFIRMED)
        self.assertTrue(sale.paid)
        self.assertEqual(sale.close_date.date(), datetime.date.today())

    def test_get_total_paid(self):
        sale = self.create_sale()
        payment = self.add_payments(sale)
        payment[0].value = Decimal(35)
        payment[0].payment_type = Payment.TYPE_OUT
        self.assertEquals(sale.get_total_paid(), -35)

    @mock.patch('stoqlib.domain.sale.Event.log')
    def test_set_paid(self, log_):
        sale = self.create_sale()
        sale.client = self.create_client()
        sale.status = Sale.STATUS_CONFIRMED

        log_.return_value = None

        payment = self.add_payments(sale, method_type=u'card')
        payment[0].status = Payment.STATUS_PAID
        sale.set_paid()
        expected = ((u"Sale {sale_number} to client {client_name} was paid "
                     u"with value {total_value:.2f}.").format(
                    sale_number=sale.identifier,
                    client_name=sale.client.person.name,
                    total_value=sale.get_total_sale_amount()))
        log_.assert_called_once_with(self.store, Event.TYPE_SALE, expected)

    @mock.patch('stoqlib.domain.sale.Event.log')
    def test_return_(self, log_):
        returned = self.create_returned_sale()
        sale = returned.sale
        sale.client = self.create_client()
        sale.status = Sale.STATUS_CONFIRMED

        item = self.create_sale_item(sale=sale)
        item.quantity += item.returned_quantity

        self.add_payments(sale)

        log_.return_value = None

        sale.return_(returned)
        expected = (u"Sale {sale_number} to client {client_name} was "
                    u"partially returned with value {total_value:.2f}. "
                    u"Reason: {reason}")
        expected = expected.format(sale_number=sale.identifier,
                                   client_name=sale.client.person.name,
                                   total_value=returned.returned_total,
                                   reason=returned.reason)
        log_.assert_called_once_with(self.store, Event.TYPE_SALE, expected)

    def test_total_return(self):
        sale = self.create_sale(branch=get_current_branch(self.store))
        sellable = self.add_product(sale)
        storable = sellable.product_storable
        balance_before_confirm = storable.get_balance_for_branch(sale.branch)

        sale.order()
        self.add_payments(sale)
        sale.confirm()
        self.assertEqual(storable.get_balance_for_branch(sale.branch),
                         balance_before_confirm - 1)
        balance_before_return = storable.get_balance_for_branch(sale.branch)

        self.failUnless(sale.can_return())
        returned_sale = sale.create_sale_return_adapter()
        returned_sale.return_()

        self.failIf(sale.can_return())
        self.assertEqual(sale.status, Sale.STATUS_RETURNED)
        self.assertEqual(sale.return_date.date(), datetime.date.today())
        self.assertEqual(storable.get_balance_for_branch(sale.branch),
                         balance_before_return + 1)
        # Since this is a total return, balance should be
        # as it wasn't ever confirmed
        self.assertEqual(storable.get_balance_for_branch(sale.branch),
                         balance_before_confirm)

    def test_partial_return(self):
        sale = self.create_sale(branch=get_current_branch(self.store))
        sellable = self.add_product(sale, quantity=5)
        storable = sellable.product_storable
        balance_before_confirm = storable.get_balance_for_branch(sale.branch)

        sale.order()
        self.add_payments(sale, u'check')
        sale.confirm()
        self.assertEqual(storable.get_balance_for_branch(sale.branch),
                         balance_before_confirm - 5)
        balance_before_return = storable.get_balance_for_branch(sale.branch)

        self.failUnless(sale.can_return())
        returned_sale = sale.create_sale_return_adapter()
        list(returned_sale.returned_items)[0].quantity = 2
        returned_sale.return_()
        self.failUnless(sale.can_return())
        self.assertEqual(sale.status, Sale.STATUS_CONFIRMED)
        # 2 of 5 returned
        self.assertEqual(storable.get_balance_for_branch(sale.branch),
                         balance_before_return + 2)
        # Since we return 2, it's like we sold 3 instead of 5
        self.assertEqual(storable.get_balance_for_branch(sale.branch),
                         balance_before_confirm - 3)

        returned_sale = sale.create_sale_return_adapter()
        # Since we already returned 2 above, this should be created with 3
        self.assertEqual(list(returned_sale.returned_items)[0].quantity, 3)
        # Now this is the final return and will be considered as a total return
        returned_sale.return_()
        self.failIf(sale.can_return())
        self.assertEqual(sale.status, Sale.STATUS_RETURNED)
        self.assertEqual(sale.return_date.date(), datetime.date.today())
        # All 5 returned (2 before plus 3 above)
        self.assertEqual(storable.get_balance_for_branch(sale.branch),
                         balance_before_return + 5)
        # Since everything was returned, balance should be
        # as it wasn't ever confirmed
        self.assertEqual(storable.get_balance_for_branch(sale.branch),
                         balance_before_confirm)

    def test_create_sale_return_adapter_with_package(self):
        package = self.create_product(description=u'Package', is_package=True)
        component = self.create_product(description=u'Component', stock=2)
        sale = self.create_sale()
        sale_item = self.create_sale_item(sale=sale, sellable=package.sellable)
        self.create_sale_item(sale=sale, sellable=component.sellable,
                              parent_item=sale_item)

        r_sale = sale.create_sale_return_adapter()
        self.assertEquals(len(list(r_sale.returned_items)), 2)

    def test_total_return_paid(self):
        sale = self.create_sale()
        self.failIf(sale.can_return())

        self.add_product(sale)
        sale.order()
        self.failIf(sale.can_return())

        self.add_payments(sale)
        sale.confirm()
        self.failUnless(sale.can_return())

        sale.group.pay()
        self.failUnless(sale.can_return())

        item = self.create_sale_item(sale=sale)
        item.quantity = item.returned_quantity

        returned_sale = sale.create_sale_return_adapter()
        returned_sale.return_()
        self.failIf(sale.can_return())
        self.assertEqual(sale.status, Sale.STATUS_RETURNED)
        self.assertEqual(sale.return_date.date(), datetime.date.today())

        paid_payment = sale.payments[0]
        payment = sale.payments[1]
        self.assertEqual(payment.value, paid_payment.value)
        self.assertEqual(payment.status, Payment.STATUS_PENDING)
        self.assertEqual(payment.method.method_name, u'money')

        fbe = self.store.find(FiscalBookEntry,
                              payment_group=sale.group,
                              is_reversal=False).one()
        rfbe = self.store.find(FiscalBookEntry,
                               payment_group=sale.group,
                               is_reversal=True).one()
        # The fiscal entries should be totally reversed
        self.assertEqual(fbe.icms_value - rfbe.icms_value, 0)
        self.assertEqual(fbe.iss_value - rfbe.iss_value, 0)
        self.assertEqual(fbe.ipi_value - rfbe.ipi_value, 0)

    def test_partial_return_paid(self):
        sale = self.create_sale()
        self.failIf(sale.can_return())

        self.add_product(sale, quantity=2)
        sale.order()
        self.failIf(sale.can_return())

        self.add_payments(sale, u'check')
        sale.confirm()
        self.failUnless(sale.can_return())

        sale.group.pay()
        self.failUnless(sale.can_return())

        payment = sale.payments[0]
        self.assertEqual(payment.value, 20)

        returned_sale = sale.create_sale_return_adapter()
        list(returned_sale.returned_items)[0].quantity = 1
        returned_sale.return_()
        self.assertTrue(sale.can_return())
        self.assertEqual(sale.status, Sale.STATUS_CONFIRMED)
        self.assertTrue(sale.paid)

        paid_payment = sale.payments[0]
        returned_payment = sale.payments[1]
        self.assertTrue(returned_payment.payment_type, Payment.TYPE_OUT)
        # Since a half of the products were returned, half of the paid
        # value should be reverted to the client
        self.assertEqual(returned_payment.value, paid_payment.value / 2)
        self.assertEqual(returned_payment.status, Payment.STATUS_PENDING)
        self.assertEqual(returned_payment.method.method_name, u'money')

        fbe = self.store.find(FiscalBookEntry,
                              payment_group=sale.group,
                              is_reversal=False).one()
        rfbe = self.store.find(FiscalBookEntry,
                               payment_group=sale.group,
                               is_reversal=True).one()
        # Since a half of the products were returned, half of the
        # taxes should be reverted. That is,
        # actual_value - reverted_value = actual_value / 2
        self.assertEqual(fbe.icms_value - rfbe.icms_value,
                         fbe.icms_value / 2)
        self.assertEqual(fbe.iss_value - rfbe.iss_value,
                         fbe.iss_value / 2)
        self.assertEqual(fbe.ipi_value - rfbe.ipi_value,
                         fbe.ipi_value / 2)

    def test_total_return_not_paid(self):
        sale = self.create_sale()
        self.failIf(sale.can_return())

        self.add_product(sale, price=300)
        sale.order()
        self.failIf(sale.can_return())

        method = PaymentMethod.get_by_name(self.store, u'check')
        payment = method.create_payment(Payment.TYPE_IN, sale.group, sale.branch, Decimal(300))
        sale.confirm()
        self.failUnless(sale.can_return())

        returned_sale = sale.create_sale_return_adapter()
        returned_sale.return_()
        self.failIf(sale.can_return())
        self.assertEqual(sale.status, Sale.STATUS_RETURNED)
        self.assertEqual(sale.return_date.date(), datetime.date.today())

        returned_amount = 0
        for payment in sale.payments:
            if payment.is_outpayment():
                returned_amount += payment.value
        self.assertEqual(returned_amount, currency(0))

    def test_partial_return_not_paid(self):
        sale = self.create_sale()
        self.failIf(sale.can_return())

        self.add_product(sale, quantity=2, price=300)
        sale.order()
        self.failIf(sale.can_return())

        method = PaymentMethod.get_by_name(self.store, u'check')
        payment = method.create_payment(Payment.TYPE_IN, sale.group, sale.branch, Decimal(600))
        sale.confirm()
        self.failUnless(sale.can_return())

        returned_sale = sale.create_sale_return_adapter()
        list(returned_sale.returned_items)[0].quantity = 1

        # Mimic what is done on sale return wizard that is to cancel
        # the existing payment and create another one with the new
        # total (in this case, 300)
        method.create_payment(Payment.TYPE_IN, sale.group, sale.branch, Decimal(300))
        payment.cancel()

        returned_sale.return_()
        self.failUnless(sale.can_return())
        self.assertEqual(sale.status, Sale.STATUS_CONFIRMED)

        returned_amount = 0
        for payment in sale.payments:
            if payment.is_outpayment():
                returned_amount += payment.value
        self.assertEqual(returned_amount, currency(0))

    def test_total_return_not_entirely_paid(self):
        sale = self.create_sale()
        self.failIf(sale.can_return())

        self.add_product(sale, price=300)
        sale.order()
        self.failIf(sale.can_return())

        # Add 3 check payments of 100 each
        method = PaymentMethod.get_by_name(self.store, u'check')
        payment1 = method.create_payment(Payment.TYPE_IN, sale.group, sale.branch, Decimal(100))
        method.create_payment(Payment.TYPE_IN, sale.group, sale.branch, Decimal(100))
        method.create_payment(Payment.TYPE_IN, sale.group, sale.branch, Decimal(100))
        sale.confirm()

        # Pay the first payment.
        payment = payment1
        payment.pay()
        self.failUnless(sale.can_return())

        self.failUnless(sale.can_return())
        returned_sale = sale.create_sale_return_adapter()
        returned_sale.return_()
        self.failIf(sale.can_return())
        self.assertEqual(sale.status, Sale.STATUS_RETURNED)
        self.assertEqual(sale.return_date.date(), datetime.date.today())

        returned_amount = 0
        for payment in sale.payments:
            if payment.is_inpayment():
                # At this point, inpayments should be either paid or cancelled
                self.assertFalse(payment.is_pending())
                self.assertTrue(payment.is_paid() or payment.is_cancelled())
            if payment.is_outpayment():
                returned_amount += payment.value
        self.assertEqual(payment.value, returned_amount)

    def test_partial_return_not_entirely_paid(self):
        sale = self.create_sale()
        self.failIf(sale.can_return())

        self.add_product(sale, price=300)
        sale.order()
        self.failIf(sale.can_return())

        # Add 3 check payments of 100 each
        method = PaymentMethod.get_by_name(self.store, u'check')
        payment1 = method.create_payment(Payment.TYPE_IN, sale.group, sale.branch, Decimal(100))
        method.create_payment(Payment.TYPE_IN, sale.group, sale.branch, Decimal(100))
        method.create_payment(Payment.TYPE_IN, sale.group, sale.branch, Decimal(100))
        sale.confirm()

        # Pay the first payment.
        payment = payment1
        payment.pay()
        self.failUnless(sale.can_return())

        self.failUnless(sale.can_return())
        returned_sale = sale.create_sale_return_adapter()
        returned_sale.return_()
        self.failIf(sale.can_return())
        self.assertEqual(sale.status, Sale.STATUS_RETURNED)
        self.assertEqual(sale.return_date.date(), datetime.date.today())

        returned_amount = 0
        for payment in sale.payments:
            if payment.is_inpayment():
                # At this point, inpayments should be either paid or cancelled
                self.assertTrue(payment.is_paid() or payment.is_cancelled())
            if payment.is_outpayment():
                returned_amount += payment.value
        self.assertEqual(payment.value, returned_amount)

    def test_trade(self):
        sale = self.create_sale(branch=get_current_branch(self.store))
        self.failIf(sale.can_return())

        sellable = self.add_product(sale)
        storable = sellable.product_storable
        balance_before_confirm = storable.get_balance_for_branch(sale.branch)
        sale.order()
        self.failIf(sale.can_return())

        self.add_payments(sale)
        sale.confirm()
        self.failUnless(sale.can_return())
        self.assertEqual(storable.get_balance_for_branch(sale.branch),
                         balance_before_confirm - 1)
        balance_before_trade = storable.get_balance_for_branch(sale.branch)

        sale.group.pay()
        self.failUnless(sale.can_return())

        returned_sale = sale.create_sale_return_adapter()
        self.assertRaises(AssertionError, returned_sale.trade)
        new_sale = self.create_sale()
        returned_sale.new_sale = new_sale
        returned_sale.trade()

        group = returned_sale.group
        payment = group.payments[0]
        self.assertTrue(payment.is_paid())
        self.assertEqual(group, new_sale.group)
        self.assertEqual(group.payments.count(), 1)
        self.assertEqual(payment.value, returned_sale.returned_total)
        self.assertEqual(storable.get_balance_for_branch(sale.branch),
                         balance_before_trade + 1)
        # Since this is a total return, balance should be
        # as it wasn't ever confirmed
        self.assertEqual(storable.get_balance_for_branch(sale.branch),
                         balance_before_confirm)

    def test_can_edit(self):
        sale = self.create_sale()
        self.add_product(sale)
        sale.order()
        sale.status = Sale.STATUS_QUOTE
        self.failUnless(sale.can_edit())
        with mock.patch.object(sale, 'is_external') as is_external:
            is_external.return_value = True
            self.assertFalse(sale.can_edit())

        sale.status = Sale.STATUS_ORDERED
        self.failUnless(sale.can_edit())
        with mock.patch.object(sale, 'is_external') as is_external:
            is_external.return_value = True
            self.assertFalse(sale.can_edit())

        self.add_payments(sale, u'check')
        sale.confirm()
        self.assertEqual(sale.status, Sale.STATUS_CONFIRMED)
        self.failIf(sale.can_edit())
        with mock.patch.object(sale, 'is_external') as is_external:
            is_external.return_value = True
            self.assertFalse(sale.can_edit())

    @mock.patch('stoqlib.domain.sale.SaleCanCancelEvent.emit')
    def test_can_cancel(self, can_cancel_emit):
        sale = self.create_sale()
        for can_cancel in [True, False, None]:
            can_cancel_emit.return_value = can_cancel
            self.assertFalse(sale.can_cancel())

        self.add_product(sale)
        sale.order()
        can_cancel_emit.return_value = False
        self.assertFalse(sale.can_cancel())
        with self.sysparam(ALLOW_CANCEL_CONFIRMED_SALES=False):
            for can_cancel in [True, None]:
                can_cancel_emit.return_value = can_cancel
                self.assertFalse(sale.can_cancel())

            sale.status = Sale.STATUS_QUOTE
            can_cancel_emit.return_value = False
            self.assertFalse(sale.can_cancel())
            for can_cancel in [True, None]:
                can_cancel_emit.return_value = can_cancel
                self.assertTrue(sale.can_cancel())

            self.add_payments(sale)
            sale.confirm()
            can_cancel_emit.return_value = False
            self.assertFalse(sale.can_cancel())
            for can_cancel in [True, None]:
                can_cancel_emit.return_value = can_cancel
                self.assertFalse(sale.can_cancel())

            sale.group.pay()
            can_cancel_emit.return_value = False
            self.assertFalse(sale.can_cancel())
            for can_cancel in [True, None]:
                can_cancel_emit.return_value = can_cancel
                self.assertFalse(sale.can_cancel())

            sale.return_(sale.create_sale_return_adapter())
            for can_cancel in [True, False, None]:
                can_cancel_emit.return_value = can_cancel
                self.assertFalse(sale.can_cancel())

    @mock.patch('stoqlib.domain.sale.SaleCanCancelEvent.emit')
    def test_cancel(self, can_cancel_emit):
        sale = self.create_sale()
        sellable = self.add_product(sale)
        storable = sellable.product_storable
        inital_quantity = storable.get_balance_for_branch(sale.branch)
        sale.status = Sale.STATUS_QUOTE
        sale.cancel()
        can_cancel_emit.assert_called_once_with(sale)
        self.assertEquals(sale.status, Sale.STATUS_CANCELLED)
        final_quantity = storable.get_balance_for_branch(sale.branch)
        self.assertEquals(inital_quantity, final_quantity)

    def test_cancel_force(self):
        sale = self.create_sale()
        sellable = self.add_product(sale)
        storable = sellable.product_storable
        inital_quantity = storable.get_balance_for_branch(sale.branch)
        sale.order()
        with mock.patch.object(sale, 'can_cancel') as can_cancel:
            sale.cancel(force=True)
            self.assertEqual(can_cancel.call_count, 0)
        self.assertEquals(sale.status, Sale.STATUS_CANCELLED)
        final_quantity = storable.get_balance_for_branch(sale.branch)
        self.assertEquals(inital_quantity, final_quantity)

    def test_cancel_with_work_order(self):
        sale = self.create_sale()
        self.add_product(sale)
        sale.order()
        work_order = self.create_workorder()
        work_order.sale = sale

        with self.sysparam(ALLOW_CANCEL_CONFIRMED_SALES=True):
            with mock.patch.object(work_order, 'cancel') as cancel:
                sale.cancel()
                cancel.assert_called_once_with(
                    reason="The sale was cancelled",
                    ignore_sale=True)

    def test_cancel_with_payments(self):
        sale = self.create_sale()
        self.add_product(sale)
        sale.order()
        work_order = self.create_workorder()
        work_order.sale = sale
        self.add_payments(sale, method_type=u'card', installments=2)
        sale.confirm()
        sale.group.pay()

        with self.sysparam(ALLOW_CANCEL_CONFIRMED_SALES=True):
            sale.cancel()
            self.assertEquals(sale.status, Sale.STATUS_CANCELLED)
            self.assertEquals(work_order.status, WorkOrder.STATUS_CANCELLED)
            for payment in sale.payments:
                self.failUnless(payment.is_cancelled())

    def test_cancel_decreased_quantity(self):
        sale = self.create_sale()
        branch = sale.branch
        sellable1 = self.add_product(sale, quantity=10)
        sellable2 = self.add_product(sale, quantity=10)
        sellable3 = self.add_product(sale, quantity=10)
        sale.status = sale.STATUS_QUOTE
        self.add_payments(sale)

        storable1 = sellable1.product_storable
        storable2 = sellable2.product_storable
        storable3 = sellable3.product_storable
        stock1 = storable1.get_balance_for_branch(branch)
        stock2 = storable2.get_balance_for_branch(branch)
        stock3 = storable3.get_balance_for_branch(branch)

        # Decrease all stock from 1 and half from 2 and nothing from 3
        storable1.decrease_stock(10, branch,
                                 StockTransactionHistory.TYPE_INITIAL, None)
        storable2.decrease_stock(5, branch,
                                 StockTransactionHistory.TYPE_INITIAL, None)
        # Indicate on the items that those quantities were already decreased
        for item in sale.get_items():
            if item.sellable == sellable1:
                item.quantity_decreased = 10
            if item.sellable == sellable2:
                item.quantity_decreased = 5

        sale.cancel()

        # Check that, in the end, everything was increased by 10,
        # that is the amount that was marked to be sold
        self.assertEqual(storable1.get_balance_for_branch(branch), stock1)
        self.assertEqual(storable2.get_balance_for_branch(branch), stock2)
        self.assertEqual(storable3.get_balance_for_branch(branch), stock3)

    def test_cancel_paid(self):
        sale = self.create_sale()
        sellable = self.add_product(sale)
        storable = sellable.product_storable
        branch = api.get_current_branch(self.store)
        initial_quantity = storable.get_balance_for_branch(branch)
        sale.order()

        self.add_payments(sale)
        sale.confirm()
        sale.group.pay()
        with self.sysparam(ALLOW_CANCEL_CONFIRMED_SALES=True):
            self.failUnless(sale.can_cancel())

            after_confirmed_quantity = storable.get_balance_for_branch(branch)
            self.assertEquals(initial_quantity - 1, after_confirmed_quantity)

            self.failUnless(sale.can_cancel())
            sale.cancel()
            self.assertEquals(sale.status, Sale.STATUS_CANCELLED)

            final_quantity = storable.get_balance_for_branch(branch)
            self.assertEquals(initial_quantity, final_quantity)

    def test_cancel_not_paid(self):
        branch = api.get_current_branch(self.store)
        sale = self.create_sale()
        sellable = self.add_product(sale, price=300)
        storable = sellable.product_storable
        initial_quantity = storable.get_balance_for_branch(branch)
        sale.status = sale.STATUS_QUOTE
        self.failUnless(sale.can_cancel())

        self.add_payments(sale)
        sale.confirm()

        with self.sysparam(ALLOW_CANCEL_CONFIRMED_SALES=True):
            after_confirmed_quantity = storable.get_balance_for_branch(branch)
            self.assertEquals(initial_quantity - 1, after_confirmed_quantity)

            self.failUnless(sale.can_cancel())
            sale.cancel()
            self.assertEquals(sale.status, Sale.STATUS_CANCELLED)

        final_quantity = storable.get_balance_for_branch(branch)
        self.assertEquals(initial_quantity, final_quantity)

    def test_cancel_quote(self):
        sale = self.create_sale()
        sellable = self.add_product(sale)
        storable = sellable.product_storable
        inital_quantity = storable.get_balance_for_branch(sale.branch)
        sale.status = Sale.STATUS_QUOTE
        sale.cancel()
        self.assertEquals(sale.status, Sale.STATUS_CANCELLED)
        final_quantity = storable.get_balance_for_branch(sale.branch)
        self.assertEquals(inital_quantity, final_quantity)

    def test_can_set_renegotiated(self):
        sale = self.create_sale()
        self.add_product(sale)
        sale.order()

        self.add_payments(sale, method_type=u'check')
        sale.confirm()

        self.failUnless(sale.can_set_renegotiated())

        for payment in sale.payments:
            payment.pay()

        self.failIf(sale.can_set_renegotiated())

    def test_set_renegotiated(self):
        sale = self.create_sale()
        self.add_product(sale)
        sale.order()

        self.add_payments(sale, method_type=u'check')
        sale.confirm()

        self.failUnless(sale.can_set_renegotiated())
        sale.set_renegotiated()
        self.assertEqual(sale.status, Sale.STATUS_RENEGOTIATED)

        for payment in sale.payments:
            payment.cancel()

        self.failIf(sale.can_set_renegotiated())

    def test_set_not_returned(self):
        sale = self.create_sale()
        sale.status = Sale.STATUS_RETURNED
        sale.return_date = localtoday()

        self.assertTrue(sale.is_returned())
        sale.set_not_returned()
        self.assertFalse(sale.is_returned())

        self.assertEquals(sale.status, Sale.STATUS_CONFIRMED)
        self.assertEquals(sale.return_date, None)

    def test_products(self):
        sale = self.create_sale()
        self.assertTrue(sale.products.is_empty())

        service = self.create_service()
        sellable = service.sellable
        sale.add_sellable(sellable, quantity=1)

        self.assertTrue(sale.products.is_empty())

        for code in [u'123', u'124', u'125', u'222', u'111']:
            product = self.create_product()
            sellable = product.sellable
            sellable.code = code
            sale.add_sellable(sellable, quantity=1)

        self.assertFalse(sale.products.is_empty())
        # Make sure that the items and only them are on the results,
        # and ordered by the code
        self.assertEqual([u'111', u'123', u'124', u'125', u'222'],
                         [i.sellable.code for i in sale.products])

    def test_services(self):
        sale = self.create_sale()
        self.assertTrue(sale.services.is_empty())

        product = self.create_product()
        sellable = product.sellable
        sale.add_sellable(sellable, quantity=1)

        self.assertTrue(sale.services.is_empty())

        for code in [u'123', u'124', u'125', u'222', u'111']:
            service = self.create_service()
            sellable = service.sellable
            sellable.code = code
            sale.add_sellable(sellable, quantity=1)

        self.assertFalse(sale.services.is_empty())
        # Make sure that the items and only them are on the results,
        # and ordered by the code
        self.assertEqual([u'111', u'123', u'124', u'125', u'222'],
                         [i.sellable.code for i in sale.services])

    def test_set_not_paid(self):
        sale = self.create_sale()
        self.add_payments(sale)
        sale.status = Sale.STATUS_CONFIRMED
        sale.paid = True
        sale.set_not_paid()
        self.assertFalse(sale.paid)

    def test_sale_with_delivery(self):
        sale = self.create_sale()
        self.failIf(sale.can_set_paid())

        self.add_product(sale)

        sellable = sysparam.get_object(self.store, 'DELIVERY_SERVICE').sellable
        sale.add_sellable(sellable, quantity=1)
        sale.order()
        self.failIf(sale.can_set_paid())

        self.add_payments(sale)
        sale.confirm()

    def test_commission_amount(self):
        sale = self.create_sale()
        sellable = self.add_product(sale, price=200)
        CommissionSource(sellable=sellable,
                         direct_value=10,
                         installments_value=5,
                         store=self.store)
        sale.order()
        # payment method: money
        # installments number: 1
        self.add_payments(sale)
        self.assertTrue(self.store.find(Commission, sale=sale).is_empty())
        sale.confirm()
        commissions = self.store.find(Commission, sale=sale)
        self.assertEquals(commissions.count(), 1)
        self.assertEquals(commissions[0].value, Decimal('20.00'))

    def test_commission_amount_multiple(self):
        sale = self.create_sale()
        sellable = self.add_product(sale, price=200)
        CommissionSource(sellable=sellable,
                         direct_value=10,
                         installments_value=5,
                         store=self.store)
        sellable = self.add_product(sale, price=300)
        CommissionSource(sellable=sellable,
                         direct_value=12,
                         installments_value=5,
                         store=self.store)
        sale.order()
        # payment method: money
        # installments number: 1
        self.add_payments(sale)
        self.assertTrue(self.store.find(Commission, sale=sale).is_empty())
        sale.confirm()
        commissions = self.store.find(Commission, sale=sale)
        self.assertEquals(commissions.count(), 1)
        self.assertEquals(commissions[0].value, Decimal('56.00'))

    def test_commission_amount_when_sale_returns_completly(self):
        if True:
            raise SkipTest(u"See stoqlib.domain.returned_sale.ReturnedSale.return_ "
                           u"and bug 5215.")

        sale = self.create_sale()
        sellable = self.add_product(sale, price=200)
        CommissionSource(sellable=sellable,
                         direct_value=10,
                         installments_value=5,
                         store=self.store)
        sale.order()
        # payment method: money
        # installments number: 1
        self.add_payments(sale)
        self.failIf(self.store.find(Commission, sale=sale))
        sale.confirm()
        returned_sale = sale.create_sale_return_adapter()
        returned_sale.return_()
        self.assertEqual(sale.status, Sale.STATUS_RETURNED)

        commissions = self.store.find(Commission, sale=sale,
                                      )
        value = sum([c.value for c in commissions])
        self.assertEqual(value, Decimal(0))
        self.assertEqual(commissions.count(), 2)
        self.failIf(commissions[-1].value >= 0)

    def test_commission_amount_when_sale_returns_partially(self):
        if True:
            raise SkipTest(u"See stoqlib.domain.returnedsale.ReturnedSale.return_ "
                           u"and bug 5215.")

        sale = self.create_sale()
        sellable = self.add_product(sale, quantity=2, price=200)
        CommissionSource(sellable=sellable,
                         direct_value=10,
                         installments_value=5,
                         store=self.store)
        sale.order()
        # payment method: money
        # installments number: 1
        self.add_payments(sale)
        self.failIf(self.store.find(Commission, sale=sale))
        sale.confirm()
        commission_value_before_return = self.store.find(Commission,
                                                         sale=sale).sum(Commission.value)

        returned_sale = sale.create_sale_return_adapter()
        list(returned_sale.returned_items)[0].quantity = 1
        returned_sale.return_()
        self.assertEqual(sale.status, Sale.STATUS_CONFIRMED)

        commissions = self.store.find(Commission, sale=sale)
        # Since we returned half of the products, commission should
        # be reverted by half too
        self.assertEqual(commissions.sum(Commission.value),
                         commission_value_before_return / 2)
        self.assertEqual(commissions.count(), 2)
        self.failIf(commissions[-1].value >= 0)

    def test_commission_create_on_confirm(self):
        api.sysparam.set_bool(
            self.store, 'SALE_PAY_COMMISSION_WHEN_CONFIRMED', True)

        sale = self.create_sale()
        self.add_product(sale, quantity=1, price=200)
        sale.order()
        self.add_payments(sale, method_type=u'bill', installments=10)

        for p in sale.payments:
            self.assertEqual(
                self.store.find(Commission, payment=p).count(), 0)

        sale.confirm()
        for p in sale.payments:
            # Confirming should create commissions
            self.assertEqual(
                self.store.find(Commission, payment=p).count(), 1)
            # Paying should not create another commission
            p.pay()
            self.assertEqual(
                self.store.find(Commission, payment=p).count(), 1)

        # Setting all payments as paid above should have raised the flag
        # paid to True
        self.assertEquals(sale.status, Sale.STATUS_CONFIRMED)
        self.assertTrue(sale.paid)

        for p in sale.payments:
            self.assertEqual(
                self.store.find(Commission, payment=p).count(), 1)

    def test_commission_create_on_pay(self):
        api.sysparam.set_bool(
            self.store, 'SALE_PAY_COMMISSION_WHEN_CONFIRMED', False)

        sale = self.create_sale()
        self.add_product(sale, quantity=1, price=200)
        sale.order()
        self.add_payments(sale, method_type=u'bill', installments=10)

        for p in sale.payments:
            self.assertEqual(
                self.store.find(Commission, payment=p).count(), 0)

        sale.confirm()
        for p in sale.payments:
            # Confirming should not create commissions
            self.assertEqual(
                self.store.find(Commission, payment=p).count(), 0)
            # Paying should create the commission
            p.pay()
            self.assertEqual(
                self.store.find(Commission, payment=p).count(), 1)

        # Setting all payments as paid above should have raised the flag
        # paid to True
        self.assertEquals(sale.status, Sale.STATUS_CONFIRMED)
        self.assertTrue(sale.paid)

        for p in sale.payments:
            self.assertEqual(
                self.store.find(Commission, payment=p).count(), 1)

    def test_commission_create_at_end(self):
        api.sysparam.set_bool(
            self.store, 'SALE_PAY_COMMISSION_WHEN_CONFIRMED', False)

        commissions_before = self.store.find(Commission).count()

        sale = self.create_sale()
        self.add_product(sale, quantity=1, price=200)
        sale.order()
        self.add_payments(sale, method_type=u'bill', installments=10)

        for p in sale.payments:
            self.assertEqual(
                self.store.find(Commission, payment=p).count(), 0)

        sale.confirm()
        fake = lambda p: None

        payments = list(sale.payments)
        # Mimic out old behaviour of only creating commissions for payments
        # when all payments on a sale are set as paid.
        with mock.patch.object(sale, 'create_commission', new=fake):
            for p in payments[:-1]:
                # Confirming should not create commissions
                self.assertEqual(
                    self.store.find(Commission, payment=p).count(), 0)
                # Since we are mimicking the old behaviour, commission
                # should not be created here.
                p.pay()
                self.assertEqual(
                    self.store.find(Commission, payment=p).count(), 0)

        # When this bug happened, there was no commission for the paid payments
        # (when there should be)
        self.assertEquals(self.store.find(Commission).count(),
                          commissions_before)

        # Pay the last payment.
        last_payment = payments[-1]
        last_payment.pay()

        # This should create all the missing commissions and change the sale
        # status
        self.assertEquals(self.store.find(Commission).count(),
                          commissions_before + len(payments))
        self.assertEquals(sale.status, Sale.STATUS_CONFIRMED)
        self.assertTrue(sale.paid)

        for p in sale.payments:
            self.assertEqual(
                self.store.find(Commission, payment=p).count(), 1)

    def test_get_client_role(self):
        sale = self.create_sale()
        client_role = sale.get_client_role()
        self.failUnless(client_role is None)

        sale.client = self.create_client()
        client_role = sale.get_client_role()
        self.failIf(client_role is None)

        sale.client.person.individual = None

        with self.assertRaises(DatabaseInconsistency):
            sale.get_client_role()

    def test_only_paid_with_money(self):
        sale = self.create_sale()
        self.add_product(sale)
        sale.order()

        self.assertFalse(sale.only_paid_with_money())

        self.add_payments(sale, method_type=u'money')
        sale.confirm()

        self.failUnless(sale.only_paid_with_money())

        sale = self.create_sale()
        self.add_product(sale)
        sale.order()
        self.add_payments(sale, method_type=u'check')
        sale.confirm()

        self.failIf(sale.only_paid_with_money())

    def test_quote_sale(self):
        sale = self.create_sale()
        sale.status = Sale.STATUS_QUOTE
        self.add_product(sale)

        self.failUnless(sale.can_confirm())
        self.add_payments(sale, u'check')
        sale.confirm()
        self.failIf(sale.can_confirm())
        self.assertEqual(sale.status, Sale.STATUS_CONFIRMED)

    def test_account_transaction_check(self):
        sale = self.create_sale()
        self.add_product(sale)
        sale.order()

        payment = self.add_payments(sale, method_type=u'check')[0]

        account = self.create_account()
        payment.method.destination_account = account

        self.assertTrue(account.transactions.is_empty())

        paid_date = localdatetime(2010, 1, 2)
        sale.confirm()
        payment.pay(paid_date)

        self.assertFalse(account.transactions.is_empty())
        self.assertEquals(account.transactions.count(), 1)

        t = account.transactions[0]
        self.assertEquals(t.payment, payment)
        self.assertEquals(t.value, payment.value)
        self.assertEquals(t.date, payment.paid_date)

    def test_account_transaction_money(self):
        sale = self.create_sale()
        self.add_product(sale)
        sale.order()
        payment = self.add_payments(sale, method_type=u'money')[0]
        account = self.create_account()
        payment.method.destination_account = account
        self.assertTrue(account.transactions.is_empty())
        sale.confirm()
        self.assertFalse(account.transactions.is_empty())

    def test_payments(self):
        sale = self.create_sale()
        self.add_product(sale)
        sale.order()

        check_payment = self.add_payments(sale, method_type=u'check')[0]
        self.assertEqual(sale.payments.count(), 1)
        self.assertTrue(check_payment in sale.payments)
        self.assertEqual(sale.group.payments.count(), 1)
        self.assertTrue(check_payment in sale.group.payments)

        check_payment.cancel()
        # Cancelled payments should not appear on sale, just on group
        self.assertEqual(sale.payments.count(), 0)
        self.assertFalse(check_payment in sale.payments)
        self.assertEqual(sale.group.payments.count(), 1)
        self.assertTrue(check_payment in sale.group.payments)

        money_payment = self.add_payments(sale, method_type=u'money')[0]
        self.assertEqual(sale.payments.count(), 1)
        self.assertTrue(money_payment in sale.payments)
        self.assertEqual(sale.group.payments.count(), 2)
        self.assertTrue(money_payment in sale.group.payments)

    def test_get_total_sale_amount(self):
        sale = self.create_sale()
        product = self.create_product(price=10)
        sale.add_sellable(product.sellable, quantity=5)

        # Normal
        self.assertEqual(sale.get_total_sale_amount(), 50)
        sale.discount_value = 10
        self.assertEqual(sale.get_total_sale_amount(), 40)
        sale.surcharge_value = 5
        self.assertEqual(sale.get_total_sale_amount(), 45)

        # Pre-calculated
        subtotal = 50
        sale.surcharge_value = 0
        sale.discount_value = 0
        self.assertEqual(sale.get_total_sale_amount(subtotal), 50)
        sale.discount_value = 10
        self.assertEqual(sale.get_total_sale_amount(subtotal), 40)
        sale.surcharge_value = 5
        self.assertEqual(sale.get_total_sale_amount(subtotal), 45)

    def test_get_total_to_pay(self):
        item = self.create_sale_item()
        self.add_payments(item.sale)
        self.assertEquals(item.sale.get_total_to_pay(), 100)

    def test_set_items_discount(self):
        sale = self.create_sale()
        sale_item1 = sale.add_sellable(self.store.find(Sellable, code=u'01').one())
        self.assertEqual(sale_item1.price, currency('149'))
        sale_item2 = sale.add_sellable(self.store.find(Sellable, code=u'02').one())
        self.assertEqual(sale_item2.price, currency('198'))
        self.assertEqual(sale.get_sale_subtotal(), currency('347'))

        # 10% discount
        sale.set_items_discount(Decimal('10'))
        self.assertEqual(sale.get_sale_subtotal(), currency('312.3'))
        self.assertEqual(sale_item1.price, currency('134.1'))
        self.assertEqual(sale_item2.price, currency('178.2'))

        # $10 discount (represented as it's percentage)
        sale.set_items_discount(Decimal('2.881844380403458213256484150'))
        self.assertEqual(sale.get_sale_subtotal(), currency('337'))
        self.assertEqual(sale_item1.price, currency('144.71'))
        self.assertEqual(sale_item2.price, currency('192.29'))

        item = self.create_sale_item(sale)
        item.base_price = Decimal(999)
        sale.set_items_discount(20)

    def test_set_items_discount_with_package(self):
        sale = self.create_sale()
        package = self.create_product(description=u'Package', is_package=True)
        component = self.create_product(description=u'Component', stock=2,
                                        storable=True)
        p_comp = self.create_product_component(product=package, component=component,
                                               price=2, component_quantity=5)
        parent = sale.add_sellable(package.sellable, price=0, quantity=1)
        sale.add_sellable(component.sellable,
                          quantity=parent.quantity * p_comp.quantity,
                          price=p_comp.price,
                          parent=parent)

        # Applying 20% discount
        sale.set_items_discount(currency('20'))
        self.assertEquals(sale.get_sale_subtotal(), currency('8'))

    def test_set_items_discount_with_negative_diff(self):
        sale = self.create_sale()
        sellable1 = self.create_sellable(price=currency('10'))
        sale_item1 = sale.add_sellable(sellable1, quantity=10)

        sellable2 = self.create_sellable(price=currency('0.99'))
        sale_item2 = sale.add_sellable(sellable2)

        self.assertEqual(sale.get_sale_subtotal(), Decimal('100.99'))
        # $0,99 of discount (represented as it's percentage)
        sale.set_items_discount(Decimal('0.980295079'))

        self.assertEqual(sale.get_sale_subtotal(), Decimal('100'))
        # The percentage discount would make sale_item2/price = 0.98, but
        # that would make the discount be 1.01 instead of 0.99.
        # The diff should have been applied to it, making it 1.00
        self.assertEqual(sale_item2.price, Decimal('1'))
        self.assertEqual(sale_item1.price, Decimal('9.9'))

    def test_set_items_discount_with_positive_diff(self):
        sale = self.create_sale()
        sellable1 = self.create_sellable(price=currency('10'))
        sale_item1 = sale.add_sellable(sellable1, quantity=10)

        sellable2 = self.create_sellable(price=currency('0.02'))
        sale_item2 = sale.add_sellable(sellable2)

        self.assertEqual(sale.get_sale_subtotal(), Decimal('100.02'))
        # $0.02 of discount (represented as it's percentage)
        sale.set_items_discount(Decimal('0.019996001'))

        # Only 0.01 can be applied because sale_item needs to be >= 0.01.
        self.assertEqual(sale.get_sale_subtotal(), Decimal('100.01'))
        self.assertEqual(sale_item2.price, Decimal('0.01'))
        self.assertEqual(sale_item1.price, Decimal('10'))

    def test_get_available_discount_for_items(self):
        item = self.create_sale_item()
        item2 = self.create_sale_item(sale=item.sale)
        self.create_sale_item(sale=item.sale)

        item.price = (item.base_price - (item.base_price / 2))
        item.sale.get_available_discount_for_items(exclude_item=item2)

    def test_get_details_str(self):
        details = []
        item = self.create_sale_item()
        item.delivery = self.create_delivery()
        item.delivery.address = self.create_address()
        self.assertEquals(item.sale.get_details_str(), (u'Delivery Address: '
                                                        u'Mainstreet 138, '
                                                        u'Cidade Araci'))

        item.delivery = None
        item.notes = u'Testing!!!'
        details.append(item.sale.get_details_str())
        self.assertEquals(details[0], (u'"Description" Notes: %s' % item.notes))
        service = self.create_service()
        item2 = self.create_sale_item(sale=item.sale)
        item2.sellable = service.sellable
        str = item2.sale.get_details_str()
        details.append((u'"%s" Estimated Fix Date: %s') % (
                       item2.get_description(),
                       item2.estimated_fix_date.strftime('%x')))
        self.assertEquals(str, u'\n'.join(sorted(details)))

    def test_get_salesperson_name(self):
        item = self.create_sale_item()
        self.assertEquals(item.sale.get_salesperson_name(), u'SalesPerson')

    def test_get_client_name(self):
        sale = self.create_sale()
        self.assertEquals(sale.get_client_name(), u'Not Specified')

        sale.client = self.create_client()
        self.assertEquals(sale.get_client_name(), u'Client')

    def test_nfe_coupon_info(self):
        sale = self.create_sale()
        self.assertIsNone(sale.nfe_coupon_info)

        sale.coupon_id = 982738
        self.assertEquals(sale.nfe_coupon_info.coo, 982738)

    def test_get_iss_total(self):
        item = self.create_sale_item()
        service = self.create_service()
        service.sellable = item.sellable
        iss = item.sale._get_iss_total(av_difference=10)
        self.assertEquals(iss, Decimal('19.80000'))

    def test_add_inpayments(self):
        sale = self.create_sale()
        expected = ('You must have at least one payment for each payment '
                    'group')
        with self.assertRaisesRegexp(ValueError, expected):
            sale._add_inpayments()

    def test_get_average_difference(self):
        sale = self.create_sale()
        expected = (u"Sale orders must have items, which means products or "
                    u"services")
        with self.assertRaisesRegexp(DatabaseInconsistency, expected):
            sale._get_average_difference()

        self.add_product(sale, quantity=0)

        expected = (u"Sale total quantity should never be zero")
        with self.assertRaisesRegexp(DatabaseInconsistency, expected):
            sale._get_average_difference()

    def test_get_iss_entry(self):
        sale = self.create_sale()
        fiscal = self.create_fiscal_book_entry(
            entry_type=FiscalBookEntry.TYPE_SERVICE)
        fiscal.payment_group = sale.group
        self.assertIs(sale._get_iss_entry(), fiscal)

    def test_create_fiscal_entries(self):
        sale = self.create_sale()
        sale.service_invoice_number = 82739
        service = self.create_service()
        sale.add_sellable(sellable=service.sellable)

        fiscal = self.create_fiscal_book_entry(
            entry_type=FiscalBookEntry.TYPE_SERVICE)
        fiscal.payment_group = sale.group

        sale._create_fiscal_entries()

        results = self.store.find(FiscalBookEntry, payment_group=sale.group)
        self.assertIn(fiscal, list(results))

    def test_recipient(self):
        # Without client
        sale = self.create_sale()
        self.assertEquals(sale.recipient, None)

        # With client
        client = self.create_client()
        sale2 = self.create_sale(client=client)
        self.assertEquals(sale2.recipient, client.person)

    def test_is_external(self):
        sale = self.create_sale()
        self.assertFalse(sale.is_external())

        callback = lambda sale: False
        SaleIsExternalEvent.connect(callback)
        self.assertFalse(sale.is_external())
        SaleIsExternalEvent.disconnect(callback)

        callback = lambda sale: True
        SaleIsExternalEvent.connect(callback)
        self.assertTrue(sale.is_external())
        SaleIsExternalEvent.disconnect(callback)


class TestSaleToken(DomainTest):
    def test_status_change(self):
        token = self.create_sale_token(code=u'token')
        token.open_token()
        self.assertEquals(token.status, SaleToken.STATUS_OCCUPIED)
        token.close_token()
        self.assertEquals(token.status, SaleToken.STATUS_AVAILABLE)


class TestSaleItem(DomainTest):
    def test__init__(self):
        with self.assertRaises(TypeError) as error:
            SaleItem()
        self.assertEquals(str(error.exception), 'You must provide a sellable '
                                                'argument')

    def test_return_to_stock(self):
        sale = self.create_sale()
        branch = sale.branch
        storable = self.create_storable(branch=branch, stock=10)

        sale_item = sale.add_sellable(storable.product.sellable, quantity=5)
        sale_item.reserve(5)

        self.assertEqual(storable.get_balance_for_branch(branch), 5)
        sale_item.return_to_stock(2)
        self.assertEqual(storable.get_balance_for_branch(branch), 7)

        # We cant return more than what was reserved
        with self.assertRaises(AssertionError):
            sale_item.return_to_stock(30)

    def test_reserve(self):
        sale = self.create_sale()
        branch = sale.branch
        storable = self.create_storable(branch=branch, stock=10)

        sale_item = sale.add_sellable(storable.product.sellable, quantity=5)
        # We cannot reserve 0
        with self.assertRaises(AssertionError):
            sale_item.reserve(0)

        self.assertEqual(storable.get_balance_for_branch(branch), 10)
        sale_item.reserve(3)
        self.assertEqual(storable.get_balance_for_branch(branch), 7)

        # We cant reserve more than what is on a sale
        with self.assertRaises(AssertionError):
            sale_item.reserve(3)

        # We should still be allowed to reserve without a stock
        product = self.create_product(storable=False)
        sale_item = sale.add_sellable(product.sellable, quantity=5)
        sale_item.reserve(3)

    def test_set_batches(self):
        sale_item = self.create_sale_item(product=True, quantity=10)
        batch1 = self.create_storable_batch(
            storable=sale_item.sellable.product_storable, batch_number=u'1')
        batch2 = self.create_storable_batch(
            storable=sale_item.sellable.product_storable, batch_number=u'2')
        batch3 = self.create_storable_batch(
            storable=sale_item.sellable.product_storable, batch_number=u'3')

        with self.assertRaisesRegexp(
                ValueError,
                ("The sum of batch quantities needs to be equal "
                 "or less than the item's original quantity")):
            sale_item.set_batches({batch1: 11})

        sale_item.set_batches({batch1: 3, batch2: 6, batch3: 1})
        self.assertEqual(
            set((i.batch, i.quantity) for i in sale_item.sale.get_items()),
            set([(batch1, 3), (batch2, 6), (batch3, 1)]))

        with self.assertRaisesRegexp(ValueError,
                                     "This item already has a batch"):
            sale_item.set_batches({})

    def test_set_batches_partially(self):
        sale_item = self.create_sale_item(product=True, quantity=10)
        batch1 = self.create_storable_batch(
            storable=sale_item.sellable.product_storable, batch_number=u'1')
        batch2 = self.create_storable_batch(
            storable=sale_item.sellable.product_storable, batch_number=u'2')

        sale_item.set_batches({batch1: 2, batch2: 3})
        self.assertEqual(
            set((i.batch, i.quantity) for i in sale_item.sale.get_items()),
            set([(None, 5), (batch1, 2), (batch2, 3)]))

    def test_set_batches_with_work_order_item(self):
        sale_item = self.create_sale_item(product=True, quantity=10)
        work_order_item = self.create_work_order_item(quantity=10)
        work_order_item.sale_item = sale_item
        work_order_item.sellable = sale_item.sellable
        work_order_item.order.branch = sale_item.sale.branch

        batch1 = self.create_storable_batch(
            storable=sale_item.sellable.product_storable, batch_number=u'1')
        batch2 = self.create_storable_batch(
            storable=sale_item.sellable.product_storable, batch_number=u'2')
        batch3 = self.create_storable_batch(
            storable=sale_item.sellable.product_storable, batch_number=u'3')

        sale_item.set_batches({batch1: 3, batch2: 6, batch3: 1})
        self.assertEqual(
            set((i.batch, i.quantity) for i in sale_item.sale.get_items()),
            set([(batch1, 3), (batch2, 6), (batch3, 1)]))

        self.assertEqual(work_order_item.order.order_items.count(), 3)
        for wo_item in work_order_item.order.order_items:
            self.assertEqual(wo_item.batch, wo_item.sale_item.batch)
            self.assertEqual(wo_item.quantity, wo_item.sale_item.quantity)

    def test_cancel_with_work_order_item(self):
        sale_item = self.create_sale_item(product=True, quantity=10)
        branch = sale_item.sale.branch
        sellable = sale_item.sellable
        # This quantity will be used to test all the cases above
        storable = self.create_storable(sellable.product,
                                        branch=branch, stock=10)
        work_order_item = self.create_work_order_item(quantity=10)
        work_order_item.sale_item = sale_item
        work_order_item.sellable = sellable
        work_order_item.order.branch = branch

        # Test the case where there's no storable
        item_without_storable = self.create_sale_item(quantity=10)
        item_without_storable.branch = branch
        work_item_without_storable = self.create_work_order_item(quantity=10)
        work_item_without_storable.sale_item = item_without_storable
        work_item_without_storable.sellable = item_without_storable.sellable
        item_without_storable.cancel(branch)

        # Sale item being cancelled with quantity_decreased on both items
        # equal to 0
        sale_item.quantity_decreased = 0
        work_order_item.quantity_decreased = 0
        sale_item.cancel(branch)
        self.assertEqual(sale_item.quantity_decreased, 0)
        self.assertEqual(work_order_item.quantity_decreased, 0)
        # 10 + 0 = 10
        self.assertEqual(storable.get_balance_for_branch(branch), 10)

        # Sale item being cancelled with an already decreased quantity on
        # sale_item
        sale_item.quantity_decreased = 5
        work_order_item.quantity_decreased = 0
        sale_item.cancel(branch)
        self.assertEqual(sale_item.quantity_decreased, 0)
        self.assertEqual(work_order_item.quantity_decreased, 0)
        # 10 + 5 = 15
        self.assertEqual(storable.get_balance_for_branch(branch), 15)

        # Sale item being cancelled with an already decreased quantity on
        # work_order_item
        sale_item.quantity_decreased = 5
        work_order_item.quantity_decreased = 0
        sale_item.cancel(branch)
        self.assertEqual(sale_item.quantity_decreased, 0)
        self.assertEqual(work_order_item.quantity_decreased, 0)
        # 15 + 5 = 20
        self.assertEqual(storable.get_balance_for_branch(branch), 20)

        # Sale item being cancelled with an already decreased quantity on
        # work_order_item and sale_item (both equal)
        sale_item.quantity_decreased = 5
        work_order_item.quantity_decreased = 5
        sale_item.cancel(branch)
        self.assertEqual(sale_item.quantity_decreased, 0)
        self.assertEqual(work_order_item.quantity_decreased, 0)
        # 20 + 5 = 25
        self.assertEqual(storable.get_balance_for_branch(branch), 25)

        # Sale item being cancelled with an already decreased quantity on
        # work_order_item and sale_item (both different. It should increase
        # based on the max decreased)
        sale_item.quantity_decreased = 2
        work_order_item.quantity_decreased = 5
        sale_item.cancel(branch)
        self.assertEqual(sale_item.quantity_decreased, 0)
        self.assertEqual(work_order_item.quantity_decreased, 0)
        # 25 + 5 = 30
        self.assertEqual(storable.get_balance_for_branch(branch), 30)

        # Sale item being cancelled with an already decreased quantity on
        # work_order_item and sale_item (both different. It should increase
        # based on the max decreased)
        sale_item.quantity_decreased = 5
        work_order_item.quantity_decreased = 2
        sale_item.cancel(branch)
        self.assertEqual(sale_item.quantity_decreased, 0)
        self.assertEqual(work_order_item.quantity_decreased, 0)
        # 30 + 5 = 35
        self.assertEqual(storable.get_balance_for_branch(branch), 35)

        # Sale item being cancelled with all items decreased
        sale_item.quantity_decreased = 10
        work_order_item.quantity_decreased = 10
        sale_item.cancel(branch)
        self.assertEqual(sale_item.quantity_decreased, 0)
        self.assertEqual(work_order_item.quantity_decreased, 0)
        # 35 + 10 = 45
        self.assertEqual(storable.get_balance_for_branch(branch), 45)

    def test_sell_with_work_order_item(self):
        sale_item = self.create_sale_item(product=True, quantity=10)
        branch = sale_item.sale.branch
        sellable = sale_item.sellable
        # This quantity will be used to test all the cases above
        storable = self.create_storable(sellable.product,
                                        branch=branch, stock=1000)
        work_order_item = self.create_work_order_item(quantity=10)
        work_order_item.sale_item = sale_item
        work_order_item.sellable = sellable
        work_order_item.order.branch = branch

        # Test the case where there's no storable
        item_without_storable = self.create_sale_item(quantity=10)
        item_without_storable.branch = branch
        work_item_without_storable = self.create_work_order_item(quantity=10)
        work_item_without_storable.sale_item = item_without_storable
        work_item_without_storable.sellable = item_without_storable.sellable
        item_without_storable.sell(branch)
        self.assertEqual(sale_item.quantity_decreased, 0)
        self.assertEqual(work_order_item.quantity_decreased, 0)

        # Sale item being sold with quantity_decreased on both items
        # equal to 0 (no one decreased nothing yet)
        sale_item.quantity_decreased = 0
        work_order_item.quantity_decreased = 0
        sale_item.sell(branch)
        self.assertEqual(sale_item.quantity_decreased, 10)
        self.assertEqual(work_order_item.quantity_decreased, 10)
        # 100 - 10 = 990
        self.assertEqual(storable.get_balance_for_branch(branch), 990)

        # Sale item being sold with an already decreased quantity on sale_item
        sale_item.quantity_decreased = 5
        work_order_item.quantity_decreased = 0
        sale_item.sell(branch)
        self.assertEqual(sale_item.quantity_decreased, 10)
        self.assertEqual(work_order_item.quantity_decreased, 10)
        # 990 - 5 = 985
        self.assertEqual(storable.get_balance_for_branch(branch), 985)

        # Sale item being sold with an already decreased quantity on
        # work_order_item
        sale_item.quantity_decreased = 0
        work_order_item.quantity_decreased = 5
        sale_item.sell(branch)
        self.assertEqual(sale_item.quantity_decreased, 10)
        self.assertEqual(work_order_item.quantity_decreased, 10)
        # 985 - 5 = 980
        self.assertEqual(storable.get_balance_for_branch(branch), 980)

        # Sale item being sold with an already decreased quantity on
        # work_order_item and sale_item (both equal)
        sale_item.quantity_decreased = 5
        work_order_item.quantity_decreased = 5
        sale_item.sell(branch)
        self.assertEqual(sale_item.quantity_decreased, 10)
        self.assertEqual(work_order_item.quantity_decreased, 10)
        # 980 - 5 = 975
        self.assertEqual(storable.get_balance_for_branch(branch), 975)

        # Sale item being sold with an already decreased quantity on
        # work_order_item and sale_item (both different. It should decrease
        # based on the max decreased)
        sale_item.quantity_decreased = 8
        work_order_item.quantity_decreased = 5
        sale_item.sell(branch)
        self.assertEqual(sale_item.quantity_decreased, 10)
        self.assertEqual(work_order_item.quantity_decreased, 10)
        # 975 - 2 = 9 973
        self.assertEqual(storable.get_balance_for_branch(branch), 973)

        # Sale item being sold with an already decreased quantity on
        # work_order_item and sale_item (both different. It should decrease
        # based on the max decreased)
        sale_item.quantity_decreased = 5
        work_order_item.quantity_decreased = 7
        sale_item.sell(branch)
        self.assertEqual(sale_item.quantity_decreased, 10)
        self.assertEqual(work_order_item.quantity_decreased, 10)
        # 973 - 3 = 9 970
        self.assertEqual(storable.get_balance_for_branch(branch), 970)

        # Sale item being sold with all quantity already decreased on both
        sale_item.quantity_decreased = 10
        work_order_item.quantity_decreased = 10
        sale_item.sell(branch)
        self.assertEqual(sale_item.quantity_decreased, 10)
        self.assertEqual(work_order_item.quantity_decreased, 10)
        # 970 - 0 = 970
        self.assertEqual(storable.get_balance_for_branch(branch), 970)

    @mock.patch('stoqlib.domain.sale.get_current_branch')
    def test_sell_branch(self, get_current_branch_):
        get_current_branch_.return_value = self.create_branch()
        item = self.create_sale_item()
        expected = (u"Stoq still doesn't support sales for branch companies "
                    u"different than the current one")
        with self.assertRaisesRegexp(SellError, expected):
            item.sell(branch=None)
        with self.assertRaisesRegexp(SellError, expected):
            item.sell(branch=item.sale.branch)
        get_current_branch_.assert_called_once_with(self.store)

    def test_sell_product(self):
        sale_item1 = self.create_sale_item(product=True)
        sale_item1.sellable.description = u'Product 666'
        storable1 = Storable(store=self.store,
                             product=sale_item1.sellable.product)

        sale_item2 = self.create_sale_item(product=True)
        sale_item2.sellable.description = u'Product 667'
        # Mimic "already decreased stock" for sale_item2
        sale_item2.quantity_decreased = sale_item2.quantity

        # First test with is_available returning False
        with mock.patch.object(Sellable, 'is_available', new=lambda s: False):
            with self.assertRaisesRegexp(
                    SellError,
                    "Product 666 is not available for sale. Try making it "
                    "available first and then try again."):
                sale_item1.sell(sale_item1.sale.branch)
            with self.assertRaisesRegexp(
                    SellError,
                    "Product 667 is not available for sale. Try making it "
                    "available first and then try again."):
                sale_item2.sell(sale_item2.sale.branch)

        # Now test with is_available returning True (the normal case)
        # sale_item1 will still raise SellError because of the lack of stock
        with self.assertRaisesRegexp(
                SellError,
                "Quantity to sell is greater than the available stock."):
            sale_item1.sell(sale_item1.sale.branch)
        # This won't raise SellError since it won't decrease stock
        sale_item2.sell(sale_item2.sale.branch)

        storable1.increase_stock(1, sale_item1.sale.branch,
                                 StockTransactionHistory.TYPE_INITIAL, None)
        # Now sale_item1 will really decrease stock
        sale_item1.sell(sale_item1.sale.branch)

    def test_sell_service(self):
        sale_item = self.create_sale_item(product=False)
        sale_item.sellable.description = u'Service 666'

        # closed services should raise SellError here
        sale_item.sellable.close()
        with self.assertRaisesRegexp(
                SellError,
                "Service 666 is not available for sale. Try making it "
                "available first and then try again."):
            sale_item.sell(branch=sale_item.sale.branch)

        # Setting the status to available should make it possible to sell
        sale_item.sellable.set_available()
        sale_item.sell(branch=sale_item.sale.branch)

    def test_get_total(self):
        sale = self.create_sale()
        product = self.create_product(price=10)
        sale_item = sale.add_sellable(product.sellable, quantity=5)
        sale_item.ipi_info.v_ipi = 30

        self.assertEqual(sale_item.get_total(), 80)

        sale_item.ipi_info = None
        self.assertEqual(sale_item.get_total(), 50)

    def test_get_quantity_unit_string(self):
        item = self.create_sale_item()
        item.sellable.unit = self.create_sellable_unit(description=u'Kg')
        str = u"%s %s" % (format_quantity(item.quantity),
                          item.sellable.unit_description)
        self.assertEquals(item.get_quantity_unit_string(), str)

    def test_get_description(self):
        sale = self.create_sale()
        product = self.create_product()
        sale_item = sale.add_sellable(product.sellable)
        self.assertEqual(sale_item.get_description(), u'Description')

    def test_parent(self):
        sale = self.create_sale()
        sale_item = self.create_sale_item(sale)
        self.assertEquals(sale_item.parent, sale)

    def test_nfe_cfop_code(self):
        item = self.create_sale_item()
        client = self.create_client()
        self.create_address(person=client.person)
        item.sale.client = client
        item.sale.coupon_id = 912839712

        # Test if branch address isn't the same of client
        self.assertEquals(item.nfe_cfop_code, u'6929')

        # Test if branch address is the same of client
        item.sale.branch.person = client.person
        self.assertEquals(item.nfe_cfop_code, u'5929')

        # Test without sale coupon
        item.sale.coupon_id = None
        cfop_code = item.nfe_cfop_code

        item.cfop = None
        self.assertEquals(item.nfe_cfop_code, cfop_code)

    def test_item_discount(self):
        item = self.create_sale_item()
        item.price = 100
        item.base_price = 150
        self.assertEquals(item.item_discount, 50)
        item.price = 150
        self.assertEquals(item.item_discount, 0)

    def test_sale_discount(self):
        sale = self.create_sale()

        # valid discount
        product = self.create_product(price=100)
        sale_item = sale.add_sellable(product.sellable, price=80)
        self.assertEqual(sale_item.sale_discount, 20)

        # no discount
        product = self.create_product(price=100)
        sale_item = sale.add_sellable(product.sellable, price=100)
        self.assertEqual(sale_item.sale_discount, 0)

    def test_get_sale_surcharge(self):
        sale = self.create_sale()

        # valid surcharge
        product = self.create_product(price=100)
        sale_item = sale.add_sellable(product.sellable, price=180)
        self.assertEqual(sale_item.get_sale_surcharge(), 80)

        # no surcharge
        product = self.create_product(price=100)
        sale_item = sale.add_sellable(product.sellable, price=100)
        self.assertEqual(sale_item.get_sale_surcharge(), 0)

        # discount insted of surcharge
        product = self.create_product(price=100)
        sale_item = sale.add_sellable(product.sellable, price=80)
        self.assertEqual(sale_item.get_sale_surcharge(), 0)

    def test_is_service(self):
        sale = self.create_sale()
        product = self.create_product(price=10)
        sale_item = sale.add_sellable(product.sellable, quantity=5)
        self.failIf(sale_item.is_service() is True)

        service = self.create_service()
        sale_item = sale.add_sellable(service.sellable, quantity=2)
        self.failIf(sale_item.is_service() is False)

    def test_batch(self):
        sale = self.create_sale()
        storable1 = self.create_storable(is_batch=False)
        storable2 = self.create_storable(is_batch=True)
        storable3 = self.create_storable(is_batch=True)
        batch = self.create_storable_batch(storable2)

        # This should not fail, since the storable does not have batches
        sale.add_sellable(storable1.product.sellable)

        # This *should fail*, since the storable does not require batches
        self.assertRaises(ValueError, sale.add_sellable,
                          storable1.product.sellable, batch=batch)

        # This should fail since the storable2 requires a batch, but we didnt
        # give any
        self.assertRaises(ValueError, sale.add_sellable,
                          storable2.product.sellable)

        # This should not fail
        sale.add_sellable(storable2.product.sellable, batch=batch)

        # Now this should fail since the batch is not related to the given
        # storable
        self.assertRaises(ValueError, sale.add_sellable,
                          storable3.product.sellable, batch=batch)


class TestDelivery(DomainTest):
    def test_status_str(self):
        delivery = self.create_delivery()
        self.assertEquals(delivery.status_str, u'Waiting')

    def test_address_str(self):
        delivery = self.create_delivery()
        delivery.address = self.create_address()
        self.assertEquals(delivery.address_str, u'Mainstreet 138, Cidade '
                                                u'Araci')

        delivery.address = None
        self.assertEquals(delivery.address_str, u'')

    def test_client_str(self):
        delivery = self.create_delivery()
        delivery.service_item = self.create_sale_item()
        delivery.service_item.sale.client = self.create_client()
        self.assertEquals(delivery.client_str, 'Client')

        delivery.service_item.sale.client = None
        self.assertEquals(delivery.client_str, u'')

    @mock.patch('stoqlib.domain.sale.DeliveryStatusChangedEvent.emit')
    def test_set_initial(self, emit):
        delivery = self.create_delivery()
        emit.return_value = None
        delivery.set_initial()
        emit.assert_called_once_with(delivery, delivery.STATUS_INITIAL)

    @mock.patch('stoqlib.domain.sale.DeliveryStatusChangedEvent.emit')
    def test_set_sent(self, emit):
        delivery = self.create_delivery()
        emit.return_value = None
        delivery.set_sent()
        emit.assert_called_once_with(delivery, delivery.STATUS_INITIAL)
        delivery.set_sent()
        emit.assert_called_with(delivery, delivery.STATUS_SENT)

    @mock.patch('stoqlib.domain.sale.DeliveryStatusChangedEvent.emit')
    def test_set_received(self, emit):
        delivery = self.create_delivery()
        emit.return_value = None
        delivery.set_sent()
        delivery.set_received()
        emit.assert_called_with(delivery, delivery.STATUS_SENT)

    def test_remove_item(self):
        delivery = self.create_delivery()
        item = self.create_sale_item()
        delivery.add_item(item)

        self.assertEquals(len(delivery.get_items()), 1)

        delivery.remove_item(item)
        self.assertEquals(len(delivery.get_items()), 0)


class TestSalePaymentMethodView(DomainTest):
    def test_with_one_payment_method_sales(self):
        # Let's create two sales: one with money and another with bill.
        sale_money = self.create_sale()
        self.add_product(sale_money)
        self.add_payments(sale_money, method_type=u'money')

        sale_bill = self.create_sale()
        self.add_product(sale_bill)
        self.add_payments(sale_bill, method_type=u'bill')

        # If we search for sales that have money payment...
        method = PaymentMethod.get_by_name(self.store, u'money')
        res = SalePaymentMethodView.find_by_payment_method(self.store, method)
        # Initial database already has a money payment
        self.assertEquals(res.count(), 2)
        # Only the first sale should be in the results.
        self.assertTrue(sale_money in [r.sale for r in res])
        self.assertFalse(sale_bill in [r.sale for r in res])

        # We don't have any sale with deposit payment method.
        method = PaymentMethod.get_by_name(self.store, u'deposit')
        res = SalePaymentMethodView.find_by_payment_method(self.store, method)
        self.assertEquals(res.count(), 0)

    def test_with_two_payment_method_sales(self):
        # Create sale with two payments with different methods: money and bill.
        sale_two_methods = self.create_sale()
        self.add_product(sale_two_methods)
        self.add_payments(sale_two_methods, method_type=u'money')
        self.add_payments(sale_two_methods, method_type=u'bill')

        # The sale should appear when searching for money payments...
        method = PaymentMethod.get_by_name(self.store, u'money')
        res = SalePaymentMethodView.find_by_payment_method(self.store, method)
        # Initial database already has a money payment
        self.assertEquals(res.count(), 2)
        self.assertTrue(sale_two_methods in [r.sale for r in res])

        # And bill payments...
        method = PaymentMethod.get_by_name(self.store, u'bill')
        res = SalePaymentMethodView.find_by_payment_method(self.store, method)
        # Initial database already has a bill payment
        self.assertEquals(res.count(), 2)
        self.assertTrue(sale_two_methods in [r.sale for r in res])

    def test_with_two_installments_sales(self):
        # A sale that has two installments of the same method should appear only
        # once in the results.
        sale_two_inst = self.create_sale()
        self.add_product(sale_two_inst)
        self.add_payments(sale_two_inst, method_type=u'deposit', installments=2)

        method = PaymentMethod.get_by_name(self.store, u'deposit')
        res = SalePaymentMethodView.find_by_payment_method(self.store, method)
        self.assertEquals(res.count(), 1)
        self.assertTrue(sale_two_inst in [r.sale for r in res])


class TestReturnedSaleView(DomainTest):
    def test_get_children_items(self):
        branch = self.create_branch()
        client = self.create_client()
        salesperson = self.create_sales_person()
        sale = self.create_sale(branch=branch, client=client,
                                salesperson=salesperson)
        package = self.create_product(description=u'Package', is_package=True)
        component = self.create_product(description=u'Component', stock=4,
                                        storable=True)
        p_component = self.create_product_component(product=package,
                                                    component=component,
                                                    component_quantity=3,
                                                    price=5)
        parent_item = sale.add_sellable(package.sellable, quantity=1, price=0)
        child_qty = parent_item.quantity * p_component.quantity
        child_price = parent_item.quantity * p_component.price
        sale.add_sellable(component.sellable, quantity=child_qty,
                          price=child_price,
                          parent=parent_item)
        self.add_payments(sale)
        sale.order()
        sale.confirm()

        r_sale = sale.create_sale_return_adapter()
        child_item = r_sale.returned_items.find(Ne(ReturnedSaleItem.parent_item_id,
                                                   None)).one()

        query = And(Eq(ReturnedSaleView.returned_item.parent_item_id, None),
                    Eq(ReturnedSaleView.client_id, client.id))
        view = self.store.find(ReturnedSaleView, query).one()
        for child in view.get_children_items():
            self.assertEquals(child.quantity, 3)
            self.assertEquals(child.returned_sale, r_sale)
            self.assertEquals(child.sale, sale)
            self.assertEquals(child.client, client)
            self.assertEquals(child.returned_item, child_item)


class TestReturnedSaleItemsView(DomainTest):
    def test_new_sale(self):
        branch = self.create_branch()
        client = self.create_client(name=u'Test')
        returned = self.create_returned_sale()
        sale_item = self.create_sale_item(sale=returned.sale)
        returned_item = ReturnedSaleItem(store=self.store,
                                         returned_sale_id=returned.id,
                                         sale_item=sale_item)
        returned_item_view = self.store.find(ReturnedSaleItemsView,
                                             id=returned_item.id).one()
        self.assertEquals(returned_item_view.new_sale, None)

        new_sale = self.create_sale(branch=branch, client=client)
        returned.new_sale_id = new_sale.id
        returned_item_view = self.store.find(ReturnedSaleItemsView,
                                             id=returned_item.id).one()
        self.assertEquals(returned_item_view.new_sale, returned.new_sale)

        found = returned_item_view.find_by_sale(store=self.store,
                                                sale=returned.sale).one()
        self.assertEquals(found.id, returned_item_view.id)


class TestSaleView(DomainTest):
    def test_post_search_callback(self):
        sale = self.create_sale()
        sale.identifier = 1138
        self.add_product(sale)
        self.add_payments(sale)

        sresults = self.store.find(SaleView, identifier=1138)
        postresults = SaleView.post_search_callback(sresults)
        self.assertEqual(postresults[0], ('count', 'sum'))
        self.assertEqual(self.store.execute(postresults[1]).get_one(),
                         (1L, Decimal("10")))

    def test_find_by_branch(self):
        sale = self.create_sale()
        views = SaleView.find_by_branch(store=self.store,
                                        branch=sale.branch)

        self.assertIn(sale, [view.sale for view in views])

        views = SaleView.find_by_branch(store=self.store, branch=None)
        self.assertIn(sale, [view.sale for view in views])

    def test_returned_sales(self):
        sale = self.create_sale()

        view = self.store.find(SaleView, id=sale.id).one()
        self.assertFalse(view.returned_sales.count())

        returned = self.create_returned_sale()

        view = self.store.find(SaleView, id=returned.sale.id).one()
        self.assertTrue(view.returned_sales.count())

    def test_subtotal(self):
        item = self.create_sale_item()

        view = self.store.find(SaleView, id=item.sale.id).one()
        self.assertEquals(view.subtotal, 100)

    def test_total(self):
        item = self.create_sale_item()
        item.ipi_info.v_ipi = 30

        view = self.store.find(SaleView, id=item.sale.id).one()
        self.assertEquals(view.total, Decimal(130))

        item.ipi_info = None
        view = self.store.find(SaleView, id=item.sale.id).one()
        self.assertEquals(view.total, Decimal(100))

    def test_get_salesperson_name(self):
        sale = self.create_sale()
        view = self.store.find(SaleView, id=sale.id).one()
        self.assertEquals(view.salesperson_name, u'SalesPerson')

    def test_open_date_as_string(self):
        sale = self.create_sale()
        view = self.store.find(SaleView, id=sale.id).one()
        self.assertEquals(view.open_date_as_string,
                          sale.open_date.strftime("%x"))

    def test_status_name(self):
        sale = self.create_sale()
        view = self.store.find(SaleView, id=sale.id).one()
        self.assertEquals(view.status_name, u'Opened')

    def test_get_first_sale_comment(self):
        sale = self.create_sale()
        self.create_sale_comment(sale=sale, comment=u'Foo bar')

        self.assertEquals(sale.get_first_sale_comment(), u'Foo bar')

    def test_get_first_sale_comment_without_comment(self):
        sale = self.create_sale()

        self.assertEquals(sale.get_first_sale_comment(), u'')

    def test_get_first_sale_comment_with_multiple_comments(self):
        sale = self.create_sale()
        self.create_sale_comment(sale=sale, comment=u'Foo bar')
        self.create_sale_comment(sale=sale, comment=u'Bar foo')

        self.assertEquals(sale.get_first_sale_comment(), u'Foo bar')


class TestSalesPersonSalesView(DomainTest):
    def test_find_by_date(self):
        sale = self.create_sale()

        date1 = localdate(2012, 1, 1)
        date2 = localdate(2012, 1, 3)

        sale.confirm_date = localdate(2012, 1, 2)
        sale.status = u'confirmed'

        date = date1, date2
        views = list(SalesPersonSalesView.find_by_date(store=self.store,
                                                       date=date))
        for view in views:
            if view.id == sale.salesperson.id:
                self.assertEquals(view.name, sale.salesperson.person.name)

        date = localdate(2012, 1, 2)
        view = SalesPersonSalesView.find_by_date(store=self.store,
                                                 date=date).one()

        self.assertEquals(view.name, sale.salesperson.person.name)

        views = SalesPersonSalesView.find_by_date(store=self.store, date=None)
        self.assertIn(sale.salesperson.id, [row.id for row in views])


class TestClientsWithSale(DomainTest):

    def test_total_amount(self):
        branch = get_current_branch(self.store)
        client = self.create_client()
        sellable = self.create_sellable()

        sale = self.create_sale(branch=branch, client=client)
        sale.add_sellable(sellable, quantity=2, price=Decimal('112.25'))
        self.add_payments(sale)
        sale.order()
        sale.confirm()
        sale.open_date = sale.confirm_date = localtoday()

        sale2 = self.create_sale(branch=branch, client=client)
        sale2.add_sellable(sellable, quantity=1, price=Decimal('225.50'))
        self.add_payments(sale2)
        sale2.order()
        sale2.confirm()
        sale2.open_date = sale2.confirm_date = localtoday()

        view = self.store.find(ClientsWithSaleView, id=sale.client.person_id).one()
        self.assertEquals(view.total_amount, 450)
