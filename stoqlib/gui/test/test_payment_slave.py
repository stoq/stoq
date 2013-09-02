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
                                             CardMethodSlave)
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.gui.wizards.purchasewizard import PurchaseWizard
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
        sysparam(self.store).update_parameter(u'ALLOW_OUTDATED_OPERATIONS', u'1')
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
        sysparam(self.store).update_parameter(u'ALLOW_OUTDATED_OPERATIONS', u'0')
        wizard = PurchaseWizard(self.store)

        method = PaymentMethod.get_by_name(self.store, u'bill')
        order = self.create_purchase_order()

        today = localtoday().date()
        slave = BillMethodSlave(wizard, None, self.store, order, method,
                                Decimal(200), today)
        self.assertValid(slave, ['first_duedate'])

        slave.first_duedate.update(datetime.date(2012, 01, 01))
        self.assertInvalid(slave, ['first_duedate'])


class TestCheckPaymentSlaves(GUITest):
    def test_create(self):
        sysparam(self.store).update_parameter(u'MANDATORY_CHECK_NUMBER', u'True')

        wizard = PurchaseWizard(self.store)

        method = PaymentMethod.get_by_name(self.store, u'check')
        order = self.create_purchase_order()
        order.identifier = 12345
        slave = CheckMethodSlave(wizard, None, self.store, order, method,
                                 Decimal(200))
        self.check_slave(slave, 'slave-check-method')

    def test_check_payment_mandatory_check_number(self):
        sysparam(self.store).update_parameter(u'MANDATORY_CHECK_NUMBER', u'True')

        wizard = PurchaseWizard(self.store)

        method = PaymentMethod.get_by_name(self.store, u'check')
        order = self.create_purchase_order()
        order.identifier = 123456
        CheckMethodSlave(wizard, None, self.store, order, method, Decimal(200))

        self.assertNotSensitive(wizard, ['next_button'])

    def test_check_payment(self):
        sysparam(self.store).update_parameter(u'MANDATORY_CHECK_NUMBER', u'False')

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


if __name__ == '__main__':
    from stoqlib.api import api
    c = api.prepare_test()
    unittest.main()
