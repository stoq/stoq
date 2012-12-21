# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2008 Async Open Source <http://www.async.com.br>
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

from stoqdrivers.enum import PaymentMethodType
from stoqdrivers.exceptions import DriverError
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.test.domaintest import DomainTest
from stoqdrivers.exceptions import CouponOpenError


class TestCouponPrinter(DomainTest):
    def setUp(self):
        DomainTest.setUp(self)
        self.printer = self.create_coupon_printer()

    def testCloseTill(self):
        self.printer.close_till(Decimal(0))
        self.assertRaises(DriverError, self.printer.close_till, 0)

    def testEmitCoupon(self):
        sale = self.create_sale()
        self.printer.emit_coupon(sale)

    def testAddCash(self):
        self.printer.add_cash(Decimal(100))

    def testRemoveCash(self):
        self.printer.remove_cash(Decimal(100))

    def testCancel(self):
        self.printer.cancel()

    def testSummarize(self):
        self.printer.summarize()


class TestFiscalCoupon(DomainTest):
    def setUp(self):
        DomainTest.setUp(self)
        self.printer = self.create_coupon_printer()
        self.sale = self.create_sale()
        self.coupon = self.printer.create_coupon(self.sale)

    def testAddItemProduct(self):
        product = self.create_product()
        sellable = product.sellable
        item = self.sale.add_sellable(sellable)

        self.assertRaises(CouponOpenError, self.coupon.add_item, item)

        self.coupon.open()
        self.coupon.add_item(item)

    def testAddItemService(self):
        service = self.create_service()
        sellable = service.sellable
        item = self.sale.add_sellable(sellable)

        self.coupon.open()
        self.coupon.add_item(item)


class _TestFiscalCouponPayments:
    def setUp(self):
        DomainTest.setUp(self)
        self.printer = self.create_coupon_printer()
        self.sale = self.create_sale()
        self.coupon = self.printer.create_coupon(self.sale)

    def _open_and_add(self, product):
        sellable = product.sellable
        item = self.sale.add_sellable(sellable)

        self.coupon.open()
        self.coupon.add_item(item)
        self.coupon.totalize()

    def _add_sale_payments(self, sale, constant, method_type):
        method = PaymentMethod.get_by_name(self.trans, method_type)
        method.create_inpayment(sale.group, sale.get_total_sale_amount())
        self.sale.set_valid()

    def testSetupPayment(self):
        product = self.create_product()
        self._open_and_add(product)
        self._add_sale_payments(self.sale, self.constant, self.method)
        self.coupon.setup_payments()


class TestFiscalCouponPaymentsBill(DomainTest, _TestFiscalCouponPayments):
    setUp = _TestFiscalCouponPayments.setUp
    method = 'bill'
    constant = PaymentMethodType.BILL


class TestFiscalCouponPaymentsCheck(DomainTest, _TestFiscalCouponPayments):
    setUp = _TestFiscalCouponPayments.setUp
    method = 'check'
    constant = PaymentMethodType.CHECK


class TestFiscalCouponPaymentsMoney(DomainTest, _TestFiscalCouponPayments):
    setUp = _TestFiscalCouponPayments.setUp
    method = 'money'
    constant = PaymentMethodType.MONEY
