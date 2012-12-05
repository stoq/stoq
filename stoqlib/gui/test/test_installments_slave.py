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
from stoqlib.gui.slaves.installmentslave import PurchaseInstallmentConfirmationSlave
from stoqlib.gui.uitestutils import GUITest


class TestPurchaseInstallmentConfirmationSlave(GUITest):
    def test_create(self):
        payment = self.create_payment()
        payment.identifier = 12345
        payment.method = self.get_payment_method('money')
        payment.description = 'payment description'
        slave = PurchaseInstallmentConfirmationSlave(self.trans, [payment])

        self.assertSensitive(slave, ['account'])
        self.check_slave(slave,
                         'test-purchase-installment-confirmation-slave-create')


class TestSaleInstallmentConfirmationSlave(GUITest):
    def test_penalty_and_interest(self):
        sale = self.create_sale()
        sale_item = self.create_sale_item(sale=sale)
        storable = self.create_storable(product=sale_item.sellable.product)
        storable.increase_stock(10, get_current_branch(self.trans))

        payment = self.create_payment(payment_type=Payment.TYPE_OUT,
                            date=datetime.date.today() - datetime.timedelta(5))

        sale.group = payment.group

        sale.order()

        payment.method.daily_interest = 1
        payment.method.penalty = 1

        slave = PurchaseInstallmentConfirmationSlave(self.trans, [payment])

        # Penalty and interest enabled
        self.assertEquals(slave.penalty.read(), currency('0.1'))
        self.assertEquals(slave.interest.read(), currency('0.51'))

        # Penalty disabled and interest enabled
        self.click(slave.pay_penalty)
        self.assertEquals(slave.penalty.read(), currency('0'))
        self.assertEquals(slave.interest.read(), currency('0.5'))

        # Penalty enabled and interest disabled
        self.click(slave.pay_penalty)
        self.click(slave.pay_interest)
        self.assertEquals(slave.penalty.read(), currency('0.1'))
        self.assertEquals(slave.interest.read(), currency('0'))

        # Penalty and interest disabled
        self.click(slave.pay_penalty)
        self.assertEquals(slave.penalty.read(), currency('0'))
        self.assertEquals(slave.interest.read(), currency('0'))


class TestLonelyInstallmentConfirmationSlave(GUITest):
    def test_penalty_and_interest(self):
        payment = self.create_payment(payment_type=Payment.TYPE_OUT,
                            date=datetime.date.today() - datetime.timedelta(5))

        payment.method.daily_interest = 1
        payment.method.penalty = 1

        slave = PurchaseInstallmentConfirmationSlave(self.trans, [payment])

        # Penalty and interest enabled
        self.assertEquals(slave.penalty.read(), currency('0.1'))
        self.assertEquals(slave.interest.read(), currency('0.51'))

        # Penalty disabled and interest enabled
        self.click(slave.pay_penalty)
        self.assertEquals(slave.penalty.read(), currency('0'))
        self.assertEquals(slave.interest.read(), currency('0.5'))

        # Penalty enabled and interest disabled
        self.click(slave.pay_penalty)
        self.click(slave.pay_interest)
        self.assertEquals(slave.penalty.read(), currency('0.1'))
        self.assertEquals(slave.interest.read(), currency('0'))

        # Penalty and interest disabled
        self.click(slave.pay_penalty)
        self.assertEquals(slave.penalty.read(), currency('0'))
        self.assertEquals(slave.interest.read(), currency('0'))
