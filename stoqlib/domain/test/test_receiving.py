# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007-2013 Async Open Source <http://www.async.com.br>
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

""" This module test all class in stoqlib/domain/receiving.py """

from decimal import Decimal

from kiwi.currency import currency
import mock

from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.product import ProductStockItem, Storable
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.domain.receiving import ReceivingOrder, ReceivingInvoice
from stoqlib.lib.dateutils import localdate

__tests__ = 'stoqlib/domain/receiving.py'


class TestReceivingOrder(DomainTest):

    def test_constructor(self):
        cfop = self.create_cfop_data()
        branch = self.create_branch()

        # When we don't provide a CFOP, the constructor should use the default
        # one
        order = ReceivingOrder(self.store, branch=branch, station=self.current_station)
        self.assertNotEqual(order.cfop, None)
        self.assertNotEqual(order.cfop, cfop)

        order = ReceivingOrder(self.store, cfop=cfop, branch=branch, station=self.current_station)
        self.assertEqual(order.cfop, cfop)

    def test_get_total(self):
        order = self.create_receiving_order()
        purchase = order.purchase_orders.find()[0]
        self.create_receiving_order_item(order)
        self.assertEqual(order.total, currency(1000))
        purchase.discount_value = 10
        self.assertEqual(order.total, currency(990))
        purchase.surcharge_value = 10
        self.assertEqual(order.total, currency(1000))

    def test_confirm(self):
        order = self.create_receiving_order()
        order.quantity = 8
        order_item = self.create_receiving_order_item(order)
        order_item.quantity_received = 10
        with self.assertRaises(ValueError):
            order.confirm(self.current_user)
        order_item.quantity_received = 8
        with self.assertRaises(ValueError):
            order.confirm(self.current_user)

        storable = order_item.sellable.product_storable
        stock_item = storable.get_stock_item(branch=order.branch, batch=None)
        purchase = order.purchase_orders.find()[0]
        for item in purchase.get_items():
            item.quantity_received = 0
        purchase.status = purchase.ORDER_PENDING
        self.assertEqual(stock_item.quantity, 8)
        purchase.confirm(self.current_user)
        order.confirm(self.current_user)
        installment_count = order.payments.count()
        for pay in order.payments:
            self.assertEqual(pay.value,
                             order.total / installment_count)
            self.assertEqual(pay.value,
                             order.total / installment_count)
        self.assertEqual(order.receiving_invoice.invoice_total, order.total)
        self.assertEqual(stock_item.quantity, 16)

    def test_order_receive_sell(self):
        product = self.create_product()
        storable = Storable(product=product, store=self.store)
        self.assertFalse(self.store.find(ProductStockItem, storable=storable).one())
        purchase_order = self.create_purchase_order()
        purchase_item = purchase_order.add_item(product.sellable, 1)
        purchase_order.status = purchase_order.ORDER_PENDING
        method = PaymentMethod.get_by_name(self.store, u'money')
        method.create_payment(purchase_order.branch, purchase_order.station, Payment.TYPE_OUT,
                              purchase_order.group, purchase_order.purchase_total)
        purchase_order.confirm(self.current_user)

        receiving_order = self.create_receiving_order(purchase_order)
        receiving_order.branch = self.current_branch
        self.create_receiving_order_item(
            receiving_order=receiving_order,
            sellable=product.sellable,
            purchase_item=purchase_item,
            quantity=1)
        self.assertFalse(self.store.find(ProductStockItem, storable=storable).one())
        receiving_order.confirm(self.current_user)
        product_stock_item = self.store.find(ProductStockItem,
                                             storable=storable).one()
        self.assertTrue(product_stock_item)
        self.assertEqual(product_stock_item.quantity, 1)

        sale = self.create_sale()
        sale.add_sellable(product.sellable)
        sale.order(self.current_user)
        method = PaymentMethod.get_by_name(self.store, u'check')
        method.create_payment(sale.branch, sale.station, Payment.TYPE_IN, sale.group, Decimal(100))
        sale.confirm(self.current_user)
        self.assertEqual(product_stock_item.quantity, 0)

    def test_update_payment_values(self):
        order = self.create_receiving_order()
        receiving_invoice = order.receiving_invoice
        purchase = order.purchase_orders.find()[0]
        purchase_item = self.create_purchase_order_item(order=purchase)
        self.add_payments(purchase, installments=2)
        self.create_receiving_order_item(order, purchase_item=purchase_item)
        self.assertEqual(order.total, currency(1000))

        for item in purchase.get_items():
            item.quantity_received = 0
        purchase.status = purchase.ORDER_PENDING
        purchase.confirm(self.current_user)

        installment_count = order.payments.count()
        payment_dict = {}
        for pay in order.payments:
            self.assertEqual(pay.value,
                             receiving_invoice.total / installment_count)
            payment_dict[pay] = pay.value

        receiving_invoice.discount_value = 20
        receiving_invoice.surcharge_value = 100
        receiving_invoice.freight_total = 10
        receiving_invoice.secure_value = 15
        receiving_invoice.expense_value = 5
        order.update_payments()

        for pay in order.payments:
            self.assertEqual(pay.value, receiving_invoice.total / installment_count)
            self.assertFalse(pay.value <= payment_dict[pay])

    def test_update_payment_values_with_freight_payment(self):
        order = self.create_receiving_order()
        receiving_invoice = order.receiving_invoice
        purchase = order.purchase_orders.find()[0]
        purchase_item = self.create_purchase_order_item(order=purchase)
        self.add_payments(purchase, installments=2)
        # Cover the case of the receiving having more than one purchase
        purchase2 = self.create_purchase_order()
        order.add_purchase(purchase2)
        self.create_receiving_order_item(order, purchase_item=purchase_item)
        self.assertEqual(order.total, currency(1000))

        for item in purchase.get_items():
            item.quantity_received = 0
        purchase.status = purchase.ORDER_PENDING
        purchase.confirm(self.current_user)

        installment_count = order.payments.count()
        payment_dict = {}
        for pay in order.payments:
            self.assertEqual(pay.value,
                             receiving_invoice.total / installment_count)
            payment_dict[pay] = pay.value

        receiving_invoice.discount_value = 20
        receiving_invoice.surcharge_value = 100
        receiving_invoice.freight_total = 10
        receiving_invoice.secure_value = 15
        receiving_invoice.expense_value = 5
        order.update_payments(create_freight_payment=True)

        for pay in order.payments:
            if pay not in payment_dict.keys():
                self.assertEqual(pay.value, receiving_invoice.freight_total)
            else:
                self.assertFalse(pay.value <= payment_dict[pay])

    def test_get_percentage_value(self):
        sellable = self.create_sellable()
        sellable.cost = Decimal('35')
        receiving_order = self.create_receiving_order()
        invoice = receiving_order.receiving_invoice
        ro = invoice._get_percentage_value(None)
        self.assertEqual(currency(0), ro)

        self.create_receiving_order_item(receiving_order, quantity=1,
                                         sellable=sellable)
        self.assertEqual(invoice._get_percentage_value(5), Decimal('1.75'))

    def test_add_purchase_item(self):
        receiving_order = self.create_receiving_order()
        purchase = receiving_order.purchase_orders.find()[0]
        item = self.create_purchase_order_item()

        receiving_order = self.create_receiving_order()
        item = self.create_purchase_order_item(purchase)

        with self.assertRaisesRegex(ValueError, "The quantity must be higher "
                                                "than 0 and lower than the "
                                                "purchase item's quantity"):
            receiving_order.add_purchase_item(item, quantity=0)

        receiving_order = self.create_receiving_order()
        purchase = receiving_order.purchase_orders.find()[0]
        item = self.create_purchase_order_item(purchase)
        item.quantity_received = 2
        with self.assertRaisesRegex(ValueError, "The quantity must be lower "
                                                "than the item's pending "
                                                "quantity"):
            receiving_order.add_purchase_item(item, quantity=8)

        storable = Storable(store=self.store, product=item.sellable.product)
        storable.is_batch = True
        p = receiving_order.add_purchase_item(item, batch_number=u'12')
        self.assertEqual(p.batch.batch_number, u'12')

    def test_update_payments(self):
        receiving_order = self.create_receiving_order()
        purchase = receiving_order.purchase_orders.find()[0]
        group = purchase.group

        receiving_order.receiving_invoice.freight_total = 50
        receiving_order.update_payments(create_freight_payment=True)
        receiving_invoice = receiving_order.receiving_invoice
        difference = (receiving_invoice.total - receiving_invoice.products_total)
        difference -= receiving_invoice.freight_total
        self.assertEqual(difference, Decimal('0'))
        self.assertEqual(group.get_pending_payments().count(), 1)

        receiving_order = self.create_receiving_order()
        receiving_order.receiving_invoice.create_freight_payment()
        receiving_order.receiving_invoice.freight_total = 50
        receiving_order.update_payments()
        self.assertEqual(group.get_pending_payments().count(), 1)

    def test_remove_items(self):
        receiving_order = self.create_receiving_order()
        purchase = receiving_order.purchase_orders.find()[0]
        item = self.create_purchase_order_item(purchase)
        receiving_order.add_purchase_item(item, quantity=2)

        receiving_order.remove_items()
        self.assertEqual(receiving_order.get_items().count(), 0)

    def test_remove_item(self):
        receiving_order = self.create_receiving_order()
        purchase = receiving_order.purchase_orders.find()[0]
        item = self.create_purchase_order_item(purchase)
        removed = receiving_order.add_purchase_item(item, quantity=2)

        receiving_order.remove_item(removed)
        self.assertEqual(receiving_order.get_items().count(), 0)

    def test_get_cfop_code(self):
        order = self.create_receiving_order()
        order.cfop.code = u'1.234'
        self.assertEqual(order.cfop_code, '1.234')

    def test_get_branch_name(self):
        branch = self.create_branch()
        branch.person.company.fancy_name = u'foo'
        order = self.create_receiving_order(branch=branch)
        self.assertEqual(order.branch_name, u'foo')

    def test_get_responsible_name(self):
        order = self.create_receiving_order()
        order.responsible = self.create_user()
        order.responsible.person.name = u'user'
        self.assertEqual(order.responsible_name, u'user')

    def test_get_receival_date_str(self):
        order = self.create_receiving_order()
        order.receival_date = localdate(2010, 1, 1)
        self.assertEqual(order.receival_date_str, u'01/01/2010')

    def test_total_quantity(self):
        receiving_order = self.create_receiving_order()
        self.create_receiving_order_item(receiving_order, quantity=3)
        self.create_receiving_order_item(receiving_order, quantity=4)
        self.assertEqual(receiving_order.total_quantity, Decimal('7'))

    def test_get_freight_type(self):
        receiving = self.create_receiving_order()
        receiving.receiving_invoice = None
        self.assertEqual(receiving.freight_type, None)
        invoice = self.create_receiving_invoice()
        invoice.freight_type = invoice.FREIGHT_FOB_PAYMENT
        receiving.receiving_invoice = invoice
        self.assertEqual(receiving.freight_type, invoice.FREIGHT_FOB_PAYMENT)


class TestReceivingOrderItem(DomainTest):

    def test_get_remaining_quantity(self):
        order_item = self.create_receiving_order_item()
        self.assertEqual(order_item.get_remaining_quantity(), 8)
        self.assertNotEqual(order_item.get_remaining_quantity(), 4)
        self.assertNotEqual(order_item.get_remaining_quantity(), 5)
        self.assertNotEqual(order_item.get_remaining_quantity(), 18)
        self.assertNotEqual(order_item.get_remaining_quantity(), 0)

        order_item.purchase_item.quantity_received = 7
        self.assertEqual(order_item.get_remaining_quantity(), 1)
        self.assertNotEqual(order_item.get_remaining_quantity(), 5)
        self.assertNotEqual(order_item.get_remaining_quantity(), 8)

        order_item.purchase_item.quantity_received = 8
        self.assertEqual(order_item.get_remaining_quantity(), 0)
        self.assertNotEqual(order_item.get_remaining_quantity(), 1)
        self.assertNotEqual(order_item.get_remaining_quantity(), 8)

    def test_get_total(self):
        order_item = self.create_receiving_order_item()
        self.assertEqual(order_item.get_total(), currency(1000))

    def test_get_quantity_unit_string(self):
        order_item = self.create_receiving_order_item()

        self.assertEqual(order_item.get_quantity_unit_string(), u'8.000')

        unit = self.create_sellable_unit(u'XX')
        order_item.sellable.unit = unit
        self.assertEqual(order_item.get_quantity_unit_string(), u'8.000 XX')

    def test_get_unit_description(self):
        order_item = self.create_receiving_order_item()
        self.assertEqual(order_item.unit_description, u'')

        order_item.sellable.unit = self.create_sellable_unit(u'XX')
        self.assertEqual(order_item.unit_description, u'XX')


class TestReceivingInvoice(DomainTest):
    def test_get_transporter_name(self):
        receiving_order = self.create_receiving_order()
        invoice = receiving_order.receiving_invoice

        # Without transporter, the transporter name should be empty
        invoice.transporter = None
        name = invoice.transporter_name
        self.assertEqual(name, u'')

        # Now there is a transporter...
        transporter = self.create_transporter(u'Juca')
        invoice.transporter = transporter
        name = invoice.transporter_name
        self.assertEqual(name, u'Juca')

    def test_supplier_name(self):
        receiving_order = self.create_receiving_order()
        invoice = receiving_order.receiving_invoice

        # Without supplier, the supplier name should be empty
        invoice.supplier = None
        name = invoice.supplier_name
        self.assertEqual(name, '')

        # With a supplier 'test'
        transporter = self.create_supplier(u'test')
        invoice.supplier = transporter
        name = invoice.supplier_name
        self.assertEqual(name, u'test')

    def test_guess_freight_type(self):
        order = self.create_receiving_order()
        invoice = order.receiving_invoice
        purchase = order.purchase_orders.find()[0]
        purchase.freight_type = PurchaseOrder.FREIGHT_FOB
        self.assertEqual(invoice.guess_freight_type(), invoice.FREIGHT_FOB_PAYMENT)

        with mock.patch(
                'stoqlib.domain.purchase.PurchaseOrder.is_paid') as is_paid:
            is_paid.return_value = False
            self.assertEqual(invoice.guess_freight_type(), invoice.FREIGHT_FOB_INSTALLMENTS)

        purchase.freight_type = PurchaseOrder.FREIGHT_CIF
        purchase.expected_freight = True
        self.assertEqual(invoice.guess_freight_type(), invoice.FREIGHT_CIF_INVOICE)

        purchase.expected_freight = False
        self.assertEqual(invoice.guess_freight_type(), invoice.FREIGHT_CIF_UNKNOWN)

    def test_receiving_with_cif_freight(self):
        purchase = self.create_purchase_order()
        purchase.freight_type = PurchaseOrder.FREIGHT_CIF

        order = self.create_receiving_order(purchase_order=purchase)
        self.assertEqual(order.receiving_invoice.guess_freight_type(),
                         ReceivingInvoice.FREIGHT_CIF_UNKNOWN)

        purchase.expected_freight = 10
        order = self.create_receiving_order(purchase_order=purchase)
        self.assertEqual(order.receiving_invoice.guess_freight_type(),
                         ReceivingInvoice.FREIGHT_CIF_INVOICE)

    def test_discount_percentage_setter(self):
        sellable = self.create_sellable()
        sellable.cost = Decimal('190')
        receiving_order = self.create_receiving_order()
        self.create_receiving_order_item(receiving_order, quantity=1,
                                         sellable=sellable)

        invoice = receiving_order.receiving_invoice
        invoice.discount_percentage = Decimal('10')
        self.assertEqual(invoice.discount_value, Decimal('19'))

    def test_discount_percentage_getter(self):
        sellable = self.create_sellable()
        sellable.cost = Decimal('220')

        receiving_order = self.create_receiving_order()
        invoice = receiving_order.receiving_invoice
        invoice.discount_value = None
        p = invoice.discount_percentage
        self.assertEqual(p, currency(0))

        receiving_order = self.create_receiving_order()
        invoice = receiving_order.receiving_invoice
        invoice.discount_value = 22
        with self.assertRaises(AssertionError):
            self.unused = invoice.discount_percentage

        self.create_receiving_order_item(receiving_order, quantity=1,
                                         sellable=sellable)
        self.assertEqual(invoice.discount_percentage, 10)

    def test_set_surcharge_by_percentage(self):
        sellable = self.create_sellable()
        sellable.cost = Decimal('200')
        receiving_order = self.create_receiving_order()
        self.create_receiving_order_item(receiving_order, quantity=1,
                                         sellable=sellable)

        invoice = receiving_order.receiving_invoice
        invoice.surcharge_percentage = Decimal('10')
        self.assertEqual(invoice.surcharge_value, Decimal('20'))

    def test_get_surcharge_by_percentage(self):
        sellable = self.create_sellable()
        sellable.cost = Decimal('210')

        receiving_order = self.create_receiving_order()
        invoice = receiving_order.receiving_invoice
        invoice.surcharge_value = None
        p = invoice.surcharge_percentage
        self.assertEqual(p, currency(0))

        receiving_order = self.create_receiving_order()
        invoice = receiving_order.receiving_invoice
        invoice.surcharge_value = 42
        with self.assertRaises(AssertionError):
            self.x = invoice.surcharge_percentage

        self.create_receiving_order_item(receiving_order, quantity=2,
                                         sellable=sellable)
        self.assertEqual(invoice.surcharge_percentage, 10)

    def test_get_total(self):
        order = self.create_receiving_order()
        purchase = order.purchase_orders.find()[0]
        self.create_receiving_order_item(order)
        invoice = order.receiving_invoice
        self.assertEqual(invoice.total, currency(1000))

        invoice.discount_value = 10
        self.assertEqual(invoice.total, currency(990))
        purchase.discount_value = 5
        self.assertEqual(invoice.total, currency(985))
        purchase.surcharge_value = 8
        invoice.surcharge_value = 15
        self.assertEqual(invoice.total, currency(1008))
        invoice.ipi_total = 10
        self.assertEqual(invoice.total, currency(1018))
        invoice.freight_total = 6
        self.assertEqual(invoice.total, currency(1024))
        invoice.secure_value = 6
        self.assertEqual(invoice.total, currency(1030))
        invoice.expense_value = 12
        self.assertEqual(invoice.total, currency(1042))
        invoice.icms_st_total = 10
        self.assertEqual(invoice.total, currency(1052))

        purchase.status = purchase.ORDER_PENDING
        purchase.confirm(self.current_user)
        invoice.confirm(self.current_user)
        self.assertEqual(invoice.invoice_total, invoice.total)

    def test_get_total_for_payment(self):
        order = self.create_receiving_order()
        self.create_receiving_order_item(order)
        invoice = order.receiving_invoice
        self.assertEqual(invoice.total_for_payment, currency(1000))
        invoice.freight_total = 10
        invoice.freight_type = invoice.FREIGHT_FOB_INSTALLMENTS
        self.assertEqual(invoice.total_for_payment, currency(1010))
        invoice.freight_type = invoice.FREIGHT_FOB_PAYMENT
        self.assertEqual(invoice.total_for_payment, currency(1000))

    def test_create_freight_payment(self):
        receiving_invoice = self.create_receiving_invoice()
        transporter = self.create_transporter(u'teste')
        receiving_invoice.transporter = transporter
        receiving_invoice.group = self.create_payment_group()

        receiving_invoice.identifier = 125
        payment = receiving_invoice.create_freight_payment()
        self.assertNotEqual(receiving_invoice.group, payment.group)
        self.assertEqual(payment.group.recipient, receiving_invoice.transporter.person)
        self.assertEqual(payment.description, u'Freight for receiving 00125')

        receiving_invoice.transporter = None
        payment = receiving_invoice.create_freight_payment()
        self.assertNotEqual(receiving_invoice.group, payment.group)
        self.assertEqual(payment.group.recipient, receiving_invoice.supplier.person)

        receiving_invoice = self.create_receiving_invoice()
        receiving_invoice.group = self.create_payment_group()
        payment = receiving_invoice.create_freight_payment(group=receiving_invoice.group)
        self.assertEqual(receiving_invoice.group, payment.group)
