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
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" This module test all class in stoq/domain/purchase.py """

__tests__ = 'stoqlib/domain/purchase.py'

from decimal import Decimal, InvalidOperation

from kiwi.currency import currency

from stoqlib.database.runtime import get_current_user
from stoqlib.domain.account import AccountTransaction
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.purchase import PurchaseOrder, QuoteGroup, PurchaseItem, \
    PurchaseOrderView, _
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.exceptions import StoqlibError, DatabaseInconsistency
from stoqlib.lib.dateutils import localnow, localdate
from stoqlib.lib.formatters import format_quantity


class TestPurchaseItem(DomainTest):
    def test_constructor_without_sellable(self):
        order = self.create_purchase_order()

        # If we dont pass a Sellable, the constructor should raise an TypeError:
        # 'You must provide a sellable argument'
        with self.assertRaises(TypeError):
            PurchaseItem(store=self.store, order=order)

    def test_constructor_without_order(self):
        sellable = self.create_sellable()

        # If we dont pass a Order, the constructor should raise an TypeError:
        # 'You must provide a order argument'
        with self.assertRaises(TypeError):
            PurchaseItem(store=self.store, sellable=sellable)

    def test_constructor_cost(self):
        order = self.create_purchase_order()
        sellable = self.create_sellable()
        sellable.cost = 97

        # If we dont pass a cost, the constructor should get from the sellable
        item = PurchaseItem(store=self.store, sellable=sellable, order=order)
        self.assertEquals(item.cost, 97)

        # Now the cost of the sellable should be ignored.
        item = PurchaseItem(store=self.store, sellable=sellable, order=order,
                            cost=58)
        self.assertEquals(item.cost, 58)

    def test_get_total_sold(self):
        item = self.create_purchase_order_item()
        solded = 5
        item.quantity_sold = solded
        total_sold = item.get_total_sold()
        self.assertEquals(total_sold, currency(solded * item.cost))

    def test_get_received_total(self):
        item = self.create_purchase_order_item()
        received = 3
        item.quantity_received = received
        total_received = item.get_received_total()
        self.assertEquals(total_received, currency(received * item.cost))

    def test_get_pending_quantity(self):
        # Default value of item.quantity is 8
        item = self.create_purchase_order_item()
        pending = item.get_pending_quantity()

        # Check in case of received quantity is 0
        self.assertEquals(pending, Decimal(8))

        # Check in case of received quantity is 8, because in this case we dont
        # have any pending products to delivery
        item.quantity_received = 6
        pending = item.get_pending_quantity()
        self.assertEquals(pending, Decimal(2))

        item.quantity_received = 8
        pending = item.get_pending_quantity()
        self.assertEquals(pending, Decimal(0))

    def test_get_quantity_as_string(self):
        item = self.create_purchase_order_item()
        item.sellable.unit = self.create_sellable_unit(description=u'XX')
        str = u"%s XX" % (format_quantity(item.quantity),)
        str_quantity = item.get_quantity_as_string()
        self.assertEquals(str, str_quantity)

    def test_get_quantity_received_as_string(self):
        item = self.create_purchase_order_item()
        item.quantity_received = 8
        item.sellable.unit = self.create_sellable_unit(description=u'XX')
        str = u"%s XX" % (format_quantity(item.quantity_received),)
        str_received = item.get_quantity_received_as_string()
        self.assertEquals(str, str_received)

    def test_get_ordered_quantity(self):
        item = self.create_purchase_order_item()
        ordered = item.get_ordered_quantity(store=self.store,
                                            sellable=item.sellable)
        self.assertEquals(ordered, Decimal(0))
        item.order.status = item.order.ORDER_PENDING
        item.order.confirm()
        ordered = item.get_ordered_quantity(store=self.store,
                                            sellable=item.sellable)
        self.assertEquals(ordered, Decimal(8))

    def test_get_component_quantity(self):
        product = self.create_product(description=u'Package', is_package=True)
        component = self.create_product(description=u'Component')
        self.create_product_component(product=product, component=component)
        purchase_item = self.create_purchase_order_item(sellable=product.sellable)
        child_item = self.create_purchase_order_item(sellable=component.sellable,
                                                     parent_item=purchase_item)
        self.assertEquals(child_item.get_component_quantity(purchase_item), 1)


class TestPurchaseOrder(DomainTest):

    def test_confirm_order(self):
        order = self.create_purchase_order()
        self.assertRaises(ValueError, order.confirm)
        order.status = PurchaseOrder.ORDER_PENDING

        order.confirm()

    def test_close(self):
        order = self.create_purchase_order()
        self.assertRaises(ValueError, order.close)
        order.status = PurchaseOrder.ORDER_PENDING
        self.add_payments(order)
        order.confirm()

        payments = list(order.payments)
        self.failUnless(len(payments) > 0)

        for payment in payments:
            self.assertEqual(payment.status, Payment.STATUS_PENDING)

        order.close()
        self.assertEqual(order.status, PurchaseOrder.ORDER_CLOSED)

    def test_can_close(self):
        item = self.create_purchase_order_item()
        result = item.order.can_close()
        self.assertEquals(result, False)
        item.order.status = item.order.ORDER_CONFIRMED
        result = item.order.can_close()
        self.assertEquals(result, False)
        item.quantity_received = 8
        result = item.order.can_close()
        self.assertEquals(result, True)

    def test_close_consigned(self):
        order = self.create_purchase_order()
        order.consigned = True
        order.status = PurchaseOrder.ORDER_PENDING
        order.set_consigned()
        self.failIf(order.can_close())

    def test_set_consigned(self):
        order = self.create_purchase_order()
        order.status = PurchaseOrder.ORDER_PENDING
        order.set_consigned()
        current = get_current_user(store=self.store)
        self.assertEquals(current, order.responsible)
        self.assertEquals(order.status, order.ORDER_CONSIGNED)
        order.status = PurchaseOrder.ORDER_CONFIRMED
        with self.assertRaises(ValueError):
            order.set_consigned()

    def test_cancel_not_paid(self):
        order = self.create_purchase_order()
        self.assertRaises(ValueError, order.close)
        order.status = PurchaseOrder.ORDER_PENDING
        self.add_payments(order)
        order.confirm()

        payments = list(order.payments)
        self.failUnless(len(payments) > 0)

        for payment in payments:
            self.assertEqual(payment.status, Payment.STATUS_PENDING)

        order.cancel()
        self.assertEqual(order.status, PurchaseOrder.ORDER_CANCELLED)

        for payment in payments:
            self.assertEqual(payment.status, Payment.STATUS_CANCELLED)

    def test_receive_item_with_not_items(self):
        order = self.create_purchase_order()
        self.create_purchase_order_item(order=order)
        item2 = self.create_purchase_order_item()
        with self.assertRaises(StoqlibError):
            order.receive_item(item=item2, quantity_to_receive=2)

    def test_receive_item_with_quantity_to_receive_greater_than_quantity(self):
        order = self.create_purchase_order()
        item = self.create_purchase_order_item(order=order)
        item.quantity = 5
        with self.assertRaises(StoqlibError):
            order.receive_item(item=item, quantity_to_receive=20)

    def test_increase_quantity_received_with_not_qty(self):
        order = self.create_purchase_order()
        item = self.create_purchase_order_item()
        with self.assertRaises(ValueError):
            order.increase_quantity_received(purchase_item=item,
                                             quantity_received=3)

    def test_update_products_cost(self):
        order = self.create_purchase_order()
        supplier = self.create_supplier()
        order.supplier = supplier
        #We have an order and a supplier for it
        item = self.create_purchase_order_item(order=order, cost=100)
        #The order now has an item with cost 100
        item.sellable.cost = 200
        #The sellable cost is different from the item cost

        product_supplier = self.create_product_supplier_info(supplier=supplier,
                                                             product=item.sellable.product)
        product_supplier.base_cost = 150
        #The base cost for the product of this order's supplier
        #is also different from the item cost

        order.update_products_cost()
        #Now the sellable cost and the supplier's product cost
        #should be qual to the order's item cost

        self.assertEqual(item.sellable.cost, 100)
        self.assertEqual(product_supplier.base_cost, 100)

    def test_get_branch_name(self):
        branch = self.create_branch(name=u'Test')
        order = self.create_purchase_order(branch=branch)
        name = order.branch_name
        self.assertEquals(name, u'Test shop')

    def test_get_responsible_name(self):
        current_user = get_current_user(self.store)
        name = current_user.person.name
        order = self.create_purchase_order()
        value = order.responsible_name
        self.assertEquals(name, value)

    def test_get_freight_type_name(self):
        order = self.create_purchase_order()
        order.freight_type = 9
        with self.assertRaises(DatabaseInconsistency):
            order.freight_type_name  # pylint: disable=W0104

    def test_get_transporter_name_with_transporter(self):
        order = self.create_purchase_order()
        transporter = self.create_transporter(name=u'Transporter')
        order.transporter = transporter
        transporter_name = order.transporter_name
        self.assertEquals(transporter_name, u'Transporter')

    def test_get_purchase_total_with_negative_total(self):
        item = self.create_purchase_order_item()
        item.order.discount_percentage = 101
        with self.assertRaises(ValueError):
            item.order.purchase_total  # pylint: disable=W0104

    def test_get_remaining_total(self):
        item = self.create_purchase_order_item()
        item.quantity_received = 4
        result = item.order.get_remaining_total()
        self.assertEquals(result, currency(500))

    def test_get_partially_received_items(self):
        item = self.create_purchase_order_item()
        result = item.order.get_partially_received_items().one()
        self.assertEquals(result, None)
        item.quantity_received = 8
        result = item.order.get_partially_received_items().one()
        self.assertNotEquals(result, None)

    def test_get_open_date_as_string(self):
        order = self.create_purchase_order()
        now = localnow().strftime("%x")
        open_date = order.get_open_date_as_string()
        self.assertEquals(open_date, now)

    def test_get_quote_deadline_as_string(self):
        order = self.create_purchase_order()
        order.quote_deadline = localnow()
        quote_deadline = order.get_quote_deadline_as_string()
        self.assertEquals(quote_deadline, localnow().strftime("%x"))

    def test_get_receiving_orders(self):
        order = self.create_purchase_order()
        count = order.get_receiving_orders().count()
        self.assertEquals(count, 0)
        self.create_receiving_order(purchase_order=order)
        count = order.get_receiving_orders().count()
        self.assertEquals(count, 1)

    def test_get_data_for_labels(self):
        order = self.create_purchase_order()
        items = list(order.get_data_for_labels())
        self.assertEqual(items, [])
        purchase_item = self.create_purchase_order_item(order=order)
        purchase_item.sellable.description = u'Test'
        items = order.get_data_for_labels()
        settable = items.next()
        self.assertEquals(settable.description, u'Test')

    def test_remove_item(self):
        purchase_order = self.create_purchase_order()
        self.create_purchase_order_item(order=purchase_order)

        items = purchase_order.get_items()

        purchase_order.remove_item(items.one())

        items = purchase_order.get_items()

        self.assertFalse(items)

        # If we pass an item who the order doesn't is the current purchase,
        # order returns an error
        item = self.create_purchase_order_item()
        item.order = None
        with self.assertRaises(ValueError):
            purchase_order.remove_item(item)

        with self.sysparam(SYNCHRONIZED_MODE=True):
            item = self.create_purchase_order_item()
            order = item.order

            before_remove = self.store.find(PurchaseItem).count()
            order.remove_item(item)
            after_remove = self.store.find(PurchaseItem).count()

            # The item should still be on the database
            self.assertEqual(before_remove, after_remove)

            # But not related to the loan
            self.assertEquals(self.store.find(PurchaseItem, order=order).count(), 0)

    def test_discount_percentage_getter(self):
        order = self.create_purchase_order()
        self.create_purchase_order_item(order=order)
        percent = Decimal(50)
        order.discount_percentage = percent
        self.assertEquals(order.discount_percentage, percent)

    def test_discount_percentage_setter(self):
        item = self.create_purchase_order_item()
        discount = item.order.discount_percentage
        self.assertEquals(discount, 0)
        percent = Decimal(39)
        item.order.discount_percentage = percent
        discount = item.order.discount_percentage
        self.assertEquals(discount, percent)

    def test_surcharge_percentage_getter(self):
        item = self.create_purchase_order_item()
        surcharge = Decimal(39)
        item.order.surcharge_percentage = surcharge
        surcharge_str = currency(item.order._get_percentage_value(surcharge))
        self.assertEquals(item.order.surcharge_value, surcharge_str)

    def test_surcharge_percentage_setter(self):
        item = self.create_purchase_order_item()
        surcharge_str = item.order.surcharge_percentage
        self.assertEquals(surcharge_str, currency(0))
        surcharge = Decimal(39)
        item.order.surcharge_percentage = surcharge
        surcharge_str = item.order.surcharge_percentage
        self.assertEquals(surcharge_str, currency(surcharge))

    def test_get_percentage_value(self):
        item = self.create_purchase_order_item()
        percent = None
        val = item.order._get_percentage_value(percent)
        self.assertEquals(val, currency(0))
        percent = Decimal(15)
        val = item.order._get_percentage_value(percent)
        result = (item.order.purchase_subtotal * (percent / 100))
        self.assertEquals(val, result)
        percent = u'test'
        with self.assertRaises(InvalidOperation):
            item.order._get_percentage_value(percent)

    def test_translate_status(self):
        order = self.create_purchase_order()
        with self.assertRaises(DatabaseInconsistency):
            order.translate_status(u'test inconsistency')

    def test_cancel_paid(self):
        order = self.create_purchase_order()
        self.assertRaises(ValueError, order.close)
        order.status = PurchaseOrder.ORDER_PENDING
        order.add_item(self.create_sellable(), 1)
        self.add_payments(order, method_type=u'money')
        order.confirm()

        payments = list(order.payments)
        payments_before_cancel = len(payments)
        self.failUnless(payments_before_cancel > 0)

        for payment in payments:
            payment.pay()
            self.assertEqual(payment.status, Payment.STATUS_PAID)

        total_paid = order.group.get_total_paid()

        order.cancel()
        self.assertEqual(order.status, PurchaseOrder.ORDER_CANCELLED)

        payments = list(order.payments)
        payments_after_cancel = len(payments)
        self.assertEqual(payments_after_cancel, payments_before_cancel + 1)

        for payment in payments:
            # Ok, paid payments of cancelled purchases remain paid...
            self.assertEqual(payment.status, Payment.STATUS_PAID)

            # ... but there is one payback.
            if payment.is_inpayment():
                self.assertEqual(payment.value, total_paid)

    def test_can_cancel_partial(self):
        order = self.create_purchase_order()
        self.assertEqual(order.can_cancel(), True)
        sellable = self.create_sellable()
        purchase_item = order.add_item(sellable, 2)
        order.receive_item(purchase_item, 1)
        self.assertEqual(order.can_cancel(), False)

    def test_can_cancel(self):
        order = self.create_purchase_order()
        self.assertEqual(order.can_cancel(), True)
        order.cancel()
        self.assertEqual(order.can_cancel(), False)
        sellable = self.create_sellable()
        order.add_item(sellable, 2)

    def test_confirm_supplier(self):
        order = self.create_purchase_order()
        self.assertRaises(ValueError, order.confirm)
        order.status = PurchaseOrder.ORDER_PENDING

        order.supplier = self.create_supplier()
        order.confirm()
        self.assertEquals(order.group.recipient, order.supplier.person)

    def test_is_paid(self):
        order = self.create_purchase_order()
        order.status = PurchaseOrder.ORDER_PENDING
        order.add_item(self.create_sellable(), 1)
        self.add_payments(order)
        order.confirm()

        self.assertEqual(order.is_paid(), False)

        for payment in order.payments:
            payment.pay()

        self.assertEqual(order.is_paid(), True)

    def test_account_transaction_check(self):
        order = self.create_purchase_order()
        order.status = PurchaseOrder.ORDER_PENDING
        order.add_item(self.create_sellable(), 1)
        payment = self.add_payments(order, method_type=u'check')[0]
        account = self.create_account()
        payment.method.destination_account = account
        self.assertTrue(account.transactions.is_empty())
        order.confirm()

        for payment in order.payments:
            payment.pay()

        self.assertFalse(account.transactions.is_empty())
        self.assertEquals(account.transactions.count(), order.payments.count())

        transaction = account.transactions[0]
        self.assertEquals(transaction.payment, payment)
        self.assertEquals(transaction.value, payment.value)
        operation_type = AccountTransaction.TYPE_OUT
        self.assertEquals(transaction.operation_type, operation_type)

    def test_account_transaction_money(self):
        order = self.create_purchase_order()
        order.status = PurchaseOrder.ORDER_PENDING
        order.add_item(self.create_sellable(), 1)
        payment = self.add_payments(order, method_type=u'money')[0]
        account = self.create_account()
        payment.method.destination_account = account
        self.assertTrue(account.transactions.is_empty())
        order.confirm()

        for payment in order.payments:
            payment.pay()

        self.assertFalse(account.transactions.is_empty())

    def test_payments(self):
        order = self.create_purchase_order()
        order.add_item(self.create_sellable(), 2)

        check_payment = self.add_payments(order, method_type=u'check')[0]
        self.assertEqual(order.payments.count(), 1)
        self.assertTrue(check_payment in order.payments)
        self.assertEqual(order.group.payments.count(), 1)
        self.assertTrue(check_payment in order.group.payments)

        check_payment.cancel()
        # Cancelled payments should not appear on order, just on group
        self.assertEqual(order.payments.count(), 0)
        self.assertFalse(check_payment in order.payments)
        self.assertEqual(order.group.payments.count(), 1)
        self.assertTrue(check_payment in order.group.payments)

        money_payment = self.add_payments(order, method_type=u'money')[0]
        self.assertEqual(order.payments.count(), 1)
        self.assertTrue(money_payment in order.payments)
        self.assertEqual(order.group.payments.count(), 2)
        self.assertTrue(money_payment in order.group.payments)

    def test_has_batch_item(self):
        order = self.create_purchase_order()
        order.add_item(self.create_sellable(), 3)
        self.assertFalse(order.has_batch_item())

        sellable = self.create_sellable()
        self.create_storable(product=sellable.product, is_batch=True)

        order = self.create_purchase_order()
        order.add_item(sellable, 2)
        self.assertTrue(order.has_batch_item())

        order = self.create_purchase_order()
        order.add_item(self.create_sellable(), 3)
        order.add_item(sellable, 2)
        self.assertTrue(order.has_batch_item())


class TestQuotation(DomainTest):
    def test_get_description(self):
        quotation = self.create_quotation()
        quotation.purchase.supplier.person.name = u'Test'
        str = u"Group %s - %s" % (quotation.group.identifier, u'Test')
        quotation_description = quotation.get_description()
        self.assertEquals(quotation_description, str)


class TestQuoteGroup(DomainTest):
    def test_cancel(self):
        order = self.create_purchase_order()
        quote = QuoteGroup(store=self.store, branch=order.branch)
        order.status = PurchaseOrder.ORDER_QUOTING
        quote.add_item(order)

        self.assertEqual(order.status, PurchaseOrder.ORDER_QUOTING)
        order.cancel()
        self.assertEqual(order.status, PurchaseOrder.ORDER_CANCELLED)

        quote.add_item(item=order)
        quote.cancel()

    def test_close(self):
        order = self.create_purchase_order()
        quote = QuoteGroup(store=self.store, branch=order.branch)
        order.status = PurchaseOrder.ORDER_QUOTING
        quote.add_item(order)

        self.assertEqual(order.status, PurchaseOrder.ORDER_QUOTING)
        quotations = quote.get_items()
        self.assertEqual(quotations.count(), 1)

        self.assertFalse(quotations[0].is_closed())
        quotations[0].close()
        self.assertTrue(quotations[0].is_closed())

        self.assertEqual(order.status, PurchaseOrder.ORDER_CANCELLED)

    def test_get_description(self):
        quote = self.create_quote_group()
        description = quote.get_description()
        str = _(u"quote number %s") % quote.identifier
        self.assertEquals(description, str)

    def test_remove_item(self):
        order = self.create_purchase_order()
        self.create_purchase_order_item(order=order)
        self.create_purchase_order_item(order=order)
        quote = self.create_quote_group(branch=order.branch)
        order.status = PurchaseOrder.ORDER_QUOTING
        quote.add_item(order)

        items = quote.get_items()
        item = items.one()
        self.assertEquals(item.purchase, order)

        quote.remove_item(item)
        items = quote.get_items()
        self.assertFalse(items)

        # If the group of the item do not is the current, return an ValueError
        order.group = self.create_payment_group()
        with self.assertRaises(ValueError):
            quote.remove_item(order)


class TestPurchaseOrderView(DomainTest):
    def test_post_search_callback(self):
        branch = self.create_branch(name=u'Test')
        order = self.create_purchase_order(branch=branch)

        self.create_purchase_order_item(order=order)
        self.create_purchase_order_item(order=order)

        sresults = self.store.find(PurchaseOrderView)
        postresults = PurchaseOrderView.post_search_callback(sresults)
        self.assertEqual(postresults[0], ('count', 'sum'))
        self.assertEqual(self.store.execute(postresults[1]).get_one(),
                         (2L, Decimal('9930.000')))

    def test_get_sub_total(self):
        order = self.create_purchase_order()
        self.create_purchase_order_item(order=order)
        results = self.store.find(PurchaseOrderView, id=order.id).one()
        self.assertEquals(results.subtotal, Decimal(1000))

    def test_get_branch_name(self):
        branch = self.create_branch(name=u'Test')
        order = self.create_purchase_order(branch=branch)
        self.create_purchase_order_item(order=order)
        result = self.store.find(PurchaseOrderView, id=order.id).one()
        self.assertEquals(result.branch_name, u'Test shop')

    def test_get_transporter_name(self):
        order = self.create_purchase_order()
        self.create_purchase_order_item(order=order)
        transporter = self.create_transporter(name=u'Transporter')
        order.transporter = transporter
        result = self.store.find(PurchaseOrderView, id=order.id).one()
        self.assertEquals(result.transporter_name, u'Transporter')

    def test_get_open_date_as_string(self):
        item = self.create_purchase_order_item()
        result = self.store.find(PurchaseOrderView, id=item.order.id).one()
        self.assertEquals(result.get_open_date_as_string(), localnow().strftime("%x"))

    def test_find_confirmed(self):
        item = self.create_purchase_order_item()
        item.order.status = item.order.ORDER_CONFIRMED
        item.order.expected_receival_date = localdate(2013, 07, 15)
        due_date = localdate(2013, 07, 14), localdate(2013, 07, 16)
        result = self.store.find(PurchaseOrderView, id=item.order.id).one()
        found = result.find_confirmed(store=self.store, due_date=due_date).count()
        self.assertEquals(found, 1)

        due_date = localdate(2013, 07, 15)
        found = result.find_confirmed(store=self.store,
                                      due_date=due_date).count()
        self.assertEquals(found, 1)
        due_date = localdate(2025, 07, 15)
        found = result.find_confirmed(store=self.store,
                                      due_date=due_date).count()
        self.assertEquals(found, 0)
