# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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

import datetime
from decimal import Decimal
import unittest

from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.gui.slaves.paymentslave import (BillMethodSlave, CheckMethodSlave,
                                             CardMethodSlave, MultipleMethodSlave,
                                             MoneyMethodSlave)
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.gui.wizards.purchasewizard import PurchaseWizard
from stoqlib.gui.wizards.salewizard import ConfirmSaleWizard
from stoqlib.lib.dateutils import localdate
from stoqlib.lib.dateutils import localtoday
from stoqlib.lib.parameters import sysparam


class TestBillPaymentSlaves(GUITest):
    def test_create(self):
        wizard = PurchaseWizard(self.store)

        method = PaymentMethod.get_by_name(self.store, u'bill')
        order = self.create_purchase_order()
        order.identifier = 12345
        slave = BillMethodSlave(wizard, None, self.store, order, method,
                                Decimal(200))
        self.check_slave(slave, 'slave-bill-method')

    def test_installments(self):
        sysparam.set_bool(self.store, 'ALLOW_OUTDATED_OPERATIONS', True)
        wizard = PurchaseWizard(self.store)

        method = PaymentMethod.get_by_name(self.store, u'bill')
        order = self.create_purchase_order()
        order.identifier = 12345

        slave = BillMethodSlave(wizard, None, self.store, order, method,
                                Decimal(200), localdate(2012, 01, 01).date())
        self.check_slave(slave, 'slave-bill-method-1-installments')

        slave.installments_number.update(2)
        self.check_slave(slave, 'slave-bill-method-2-installments')

    def test_outdated(self):
        sysparam.set_bool(self.store, 'ALLOW_OUTDATED_OPERATIONS', False)
        wizard = PurchaseWizard(self.store)

        method = PaymentMethod.get_by_name(self.store, u'bill')
        order = self.create_purchase_order()

        today = localtoday().date()
        slave = BillMethodSlave(wizard, None, self.store, order, method,
                                Decimal(200), today)
        self.assertValid(slave, ['first_duedate'])

        slave.first_duedate.update(datetime.date(2012, 01, 01))
        self.assertInvalid(slave, ['first_duedate'])


class TestMoneyMethodSlave(GUITest):
    def test_create_with_param_mandatory_check_number_true(self):
        with self.sysparam(MANDATORY_CHECK_NUMBER=True):
            wizard = PurchaseWizard(self.store)

            method = PaymentMethod.get_by_name(self.store, u'money')
            order = self.create_purchase_order()
            order.identifier = 12345
            slave = MoneyMethodSlave(wizard,
                                     None,
                                     self.store,
                                     order,
                                     method,
                                     Decimal(200))
            self.assertEquals(
                slave.bank_first_check_number.get_property('mandatory'), False)


class TestCheckPaymentSlaves(GUITest):
    def test_create(self):
        with self.sysparam(MANDATORY_CHECK_NUMBER=True):
            wizard = PurchaseWizard(self.store)

            method = PaymentMethod.get_by_name(self.store, u'check')
            order = self.create_purchase_order()
            order.identifier = 12345
            slave = CheckMethodSlave(wizard, None, self.store, order, method,
                                     Decimal(200))
            self.assertEquals(
                slave.bank_first_check_number.get_property('mandatory'), True)
            self.check_slave(slave, 'slave-check-method')

    def test_check_payment_mandatory_check_number(self):
        with self.sysparam(MANDATORY_CHECK_NUMBER=True):
            wizard = PurchaseWizard(self.store)

            method = PaymentMethod.get_by_name(self.store, u'check')
            order = self.create_purchase_order()
            order.identifier = 123456
            CheckMethodSlave(wizard, None, self.store, order, method, Decimal(200))

            self.assertNotSensitive(wizard, ['next_button'])

    def test_check_payment(self):
        with self.sysparam(MANDATORY_CHECK_NUMBER=False):
            wizard = PurchaseWizard(self.store)

            method = PaymentMethod.get_by_name(self.store, u'check')
            order = self.create_purchase_order()
            order.identifier = 1234567
            CheckMethodSlave(wizard, None, self.store, order, method, Decimal(200))

            self.assertSensitive(wizard, ['next_button'])


class TestCardPaymentSlaves(GUITest):
    def test_create(self):
        wizard = PurchaseWizard(self.store)

        method = PaymentMethod.get_by_name(self.store, u'card')
        order = self.create_purchase_order()
        slave = CardMethodSlave(wizard, None, self.store, order, method,
                                Decimal(200))
        self.check_slave(slave, 'slave-card-method')

    def test_installments(self):
        wizard = PurchaseWizard(self.store)

        method = PaymentMethod.get_by_name(self.store, u'card')
        order = self.create_purchase_order()
        slave = CardMethodSlave(wizard, None, self.store, order, method,
                                Decimal(200))

        # Select a option for multiple installments
        for radio in slave.types_box.get_children():
            if radio.get_label() == 'Credit Card Installments Store':
                radio.set_active(True)
                break
        else:
            raise AssertionError

        self.check_slave(slave, 'slave-card-installments-store')

    def test_on_auth_number_validate(self):
        sellable = self.create_sellable(price=100)
        sale = self.create_sale()
        sale.add_sellable(sellable)
        subtotal = sale.get_sale_subtotal()
        wizard = ConfirmSaleWizard(self.store, sale, subtotal)
        method = PaymentMethod.get_by_name(self.store, u'card')
        slave = CardMethodSlave(wizard, None, self.store, sale, method)
        slave.auth_number.update(1234567)
        self.assertEquals(unicode(slave.auth_number.emit("validate", 1234567)),
                          "Authorization number must have 6 digits or less.")
        self.assertNotSensitive(wizard, ['next_button'])
        slave.auth_number.update(123456)
        self.assertSensitive(wizard, ['next_button'])


class TestMultipleMethodSlave(GUITest):
    def _create_sale(self):
        client = self.create_client()
        client.credit_limit = 20
        sale = self.create_sale(client=client)
        sale.identifier = 1234
        sellable = self.create_sellable(price=10)
        sale.add_sellable(sellable)
        return sale

    def test_create(self):
        sale = self._create_sale()
        subtotal = sale.get_sale_subtotal()

        wizard = ConfirmSaleWizard(self.store, sale, subtotal)
        slave = MultipleMethodSlave(wizard, None, self.store, sale)
        self.check_slave(slave, 'slave-multiple-method')

    def test_on_method_toggled(self):
        sale = self._create_sale()
        subtotal = sale.get_sale_subtotal()

        wizard = ConfirmSaleWizard(self.store, sale, subtotal)
        slave = MultipleMethodSlave(wizard, None, self.store, sale)

        self.assertEquals(slave.value.read(), 10)
        self.assertEquals(unicode(slave.value.emit("validate", 0)),
                          u"You must provide a payment value.")
        self.assertNotSensitive(slave, ['add_button'])

        # Test with an invalid value.
        slave.value.set_text("Test")
        self.assertNotSensitive(slave, ['add_button'])
        for radio in slave.methods_box.get_children():
            if radio.get_label() == 'Check':
                radio.set_active(True)
                break
        # Check if value was updated.
        self.assertEquals(slave.value.read(), 10)
        self.assertSensitive(slave, ['add_button'])

        # Test with store credit.
        for radio in slave.methods_box.get_children():
            if radio.get_label() == 'Store Credit':
                radio.set_active(True)
                break
        self.assertEquals(slave.value.read(), 10)
        self.assertSensitive(slave, ['add_button'])
        self.assertEquals(unicode(slave.value.emit("validate", 30)),
                          u"Client does not have enough credit. Client store credit: 20.0.")
        self.assertNotSensitive(slave, ['add_button'])
        slave.value.update(10)
        self.assertSensitive(slave, ['add_button'])

        # Change the payment method.
        for radio in slave.methods_box.get_children():
            if radio.get_label() == 'Bill':
                radio.set_active(True)
                break
        self.assertEquals(slave.value.read(), 10)
        self.assertSensitive(slave, ['add_button'])

        # Change to money.
        slave.value.update(5)
        self.assertSensitive(slave, ['add_button'])
        for radio in slave.methods_box.get_children():
            if radio.get_label() == 'Money':
                radio.set_active(True)
                break
        # Check if the value typed was kept.
        self.assertEquals(slave.value.read(), 5)
        self.assertSensitive(slave, ['add_button'])


if __name__ == '__main__':
    from stoqlib.api import api
    c = api.prepare_test()
    unittest.main()
