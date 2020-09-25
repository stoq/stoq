# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##

import datetime

from kiwi.currency import currency

from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.purchase import PurchaseOrder
from stoq.lib.gui.slaves.paymentconfirmslave import (PurchasePaymentConfirmSlave,
                                                     SalePaymentConfirmSlave)
from stoq.lib.gui.test.uitestutils import GUITest
from stoqlib.lib.dateutils import localtoday


class TestPurchasePaymentConfirmSlave(GUITest):
    def test_create(self):
        # We are creating a cost center, but it should not appear in the slave,
        # since payment is not a lonely payment.
        self.create_cost_center()
        self.create_cost_center(is_active=False)

        payment = self.create_payment()
        payment.identifier = 12345
        payment.method = self.get_payment_method(u'money')
        payment.description = u'payment description'

        order = self.create_purchase_order()
        self.create_purchase_order_item(order)
        order.identifier = 68395
        order.status = PurchaseOrder.ORDER_PENDING
        order.confirm(self.current_user)

        payment.group = order.group

        slave = PurchasePaymentConfirmSlave(self.store, [payment])

        self.assertSensitive(slave, ['source_account', 'destination_account'])
        self.check_editor(slave, 'editor-purchase-payment-confirm-create')


class TestSalePaymentConfirmSlave(GUITest):
    def test_create(self):
        # We are creating a cost center, but it should not appear in the slave,
        # since payment is not a lonely payment.
        self.create_cost_center()
        self.create_cost_center(is_active=False)

        payment = self.create_payment()
        payment.identifier = 12345
        payment.method = self.get_payment_method(u'money')
        payment.description = u'payment description'

        sale = self.create_sale()
        sale.identifier = 47384
        sale_item = self.create_sale_item(sale=sale)
        self.create_storable(sale_item.sellable.product,
                             get_current_branch(self.store), 10)

        payment.group = sale.group
        sale.order(self.current_user)

        slave = SalePaymentConfirmSlave(self.store, [payment])

        self.check_editor(slave, 'editor-sale-payment-confirm-create')

    def test_penalty_and_interest(self):
        sale = self.create_sale()
        sale_item = self.create_sale_item(sale=sale)
        self.create_storable(sale_item.sellable.product,
                             get_current_branch(self.store), 10)

        payment = self.create_payment(payment_type=Payment.TYPE_OUT, value=100,
                                      date=localtoday().date() - datetime.timedelta(5))

        sale.group = payment.group

        sale.order(self.current_user)

        payment.method.daily_interest = 1
        payment.method.penalty = 1

        slave = PurchasePaymentConfirmSlave(self.store, [payment])

        # Penalty and interest enabled
        self.assertEqual(slave.penalty.read(), currency('1'))
        self.assertEqual(slave.interest.read(), currency('5.05'))

        # Penalty disabled and interest enabled
        self.click(slave.pay_penalty)
        self.assertEqual(slave.penalty.read(), currency('0'))
        self.assertEqual(slave.interest.read(), currency('5'))

        # Penalty enabled and interest disabled
        self.click(slave.pay_penalty)
        self.click(slave.pay_interest)
        self.assertEqual(slave.penalty.read(), currency('1'))
        self.assertEqual(slave.interest.read(), currency('0'))

        # Penalty and interest disabled
        self.click(slave.pay_penalty)
        self.assertEqual(slave.penalty.read(), currency('0'))
        self.assertEqual(slave.interest.read(), currency('0'))

    def test_discount(self):
        sale = self.create_sale()
        sale_item = self.create_sale_item(sale=sale)
        payment = self.create_card_payment(payment_value=sale_item.price)
        payment.identifier = 12345

        payment.group = sale.group
        card_data = payment.card_data
        card_data.fee_value = 2
        card_data.fare = 4
        sale.order(self.current_user)

        slave = SalePaymentConfirmSlave(self.store, [payment])
        self.assertEqual(slave.discount.read(), 6)


class TestLonelyPaymentConfirmSlave(GUITest):
    def test_create(self):
        # We are creating a cost center, and it should appear in the slave,
        # since payment is a lonely payment.
        self.create_cost_center()
        self.create_cost_center(is_active=False)

        payment = self.create_payment()
        payment.identifier = 28567
        payment.method = self.get_payment_method(u'money')
        payment.description = u'payment description'
        slave = PurchasePaymentConfirmSlave(self.store, [payment])

        self.check_editor(slave, 'editor-lonely-payment-confirm-create')

    def test_penalty_and_interest(self):
        payment = self.create_payment(payment_type=Payment.TYPE_OUT, value=100,
                                      date=localtoday().date() - datetime.timedelta(5))

        payment.method.daily_interest = 1
        payment.method.penalty = 1

        slave = PurchasePaymentConfirmSlave(self.store, [payment])

        # Penalty and interest enabled
        self.assertEqual(slave.penalty.read(), currency('1'))
        self.assertEqual(slave.interest.read(), currency('5.05'))

        # Penalty disabled and interest enabled
        self.click(slave.pay_penalty)
        self.assertEqual(slave.penalty.read(), currency('0'))
        self.assertEqual(slave.interest.read(), currency('5'))

        # Penalty enabled and interest disabled
        self.click(slave.pay_penalty)
        self.click(slave.pay_interest)
        self.assertEqual(slave.penalty.read(), currency('1'))
        self.assertEqual(slave.interest.read(), currency('0'))

        # Penalty and interest disabled
        self.click(slave.pay_penalty)
        self.assertEqual(slave.penalty.read(), currency('0'))
        self.assertEqual(slave.interest.read(), currency('0'))
