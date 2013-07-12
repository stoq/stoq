# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2007 Async Open Source <http://www.async.com.br>
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

from nose.exc import SkipTest
from stoqdrivers.enum import PaymentMethodType, TaxType
from stoqlib.domain.sellable import SellableTaxConstant
from stoqlib.exceptions import DeviceError

from ecf.ecfdomain import DeviceConstant
from ecf.test.ecftest import ECFTest


class TestDeviceConstant(ECFTest):
    def test_get_custom_tax_constant(self):
        constant = DeviceConstant.get_custom_tax_constant(
            self.ecf_printer, 0, self.store)
        self.assertEquals(constant, None)

        constant = DeviceConstant.get_custom_tax_constant(
            self.ecf_printer, 18, self.store)
        self.assertNotEquals(constant, None)
        self.assertEquals(constant.constant_type, DeviceConstant.TYPE_TAX)
        self.assertEquals(constant.constant_enum, TaxType.CUSTOM)
        self.assertEquals(constant.constant_value, 18)
        self.assertEquals(constant.device_value, u'T1')

    def test_get_tax_constant(self):
        constant = DeviceConstant.get_tax_constant(
            self.ecf_printer, -1, self.store)
        self.assertEquals(constant, None)

        constant = DeviceConstant.get_tax_constant(
            self.ecf_printer, TaxType.NONE, self.store)
        self.assertNotEquals(constant, None)
        self.assertEquals(constant.constant_type, DeviceConstant.TYPE_TAX)
        self.assertEquals(constant.constant_enum, TaxType.NONE)
        self.assertEquals(constant.constant_value, None)
        self.assertEquals(constant.device_value, u'TN')


class TestECFPrinter(ECFTest):
    def test_get_constants_by_type(self):
        for constant_type in [DeviceConstant.TYPE_UNIT,
                              DeviceConstant.TYPE_TAX,
                              DeviceConstant.TYPE_PAYMENT]:
            self.assertEqual(
                list(self.ecf_printer.get_constants_by_type(constant_type)),
                [c for c in self.ecf_printer.constants if
                 c.constant_type == constant_type])

    def test_get_tax_constant_for_device(self):
        sellable = self.create_sellable()
        constant = self.ecf_printer.get_tax_constant_for_device(sellable)
        self.assertEquals(constant.constant_type, DeviceConstant.TYPE_TAX)
        self.assertEquals(constant.constant_enum, TaxType.NONE)
        self.assertEquals(constant.constant_value, None)
        self.assertEquals(constant.device_value, u"TN")

    def test_get_tax_constant_for_device_invalid_tax_value(self):
        sellable = self.create_sellable()
        sellable.tax_constant = SellableTaxConstant(
            store=self.store,
            description=u'',
            tax_value=decimal.Decimal('3.1415'),
            tax_type=int(TaxType.CUSTOM))
        self.assertRaises(
            DeviceError, self.ecf_printer.get_tax_constant_for_device, sellable)

    def test_get_payment_constant(self):
        if True:
            raise SkipTest(
                "Need to configure money payment method on fiscal printer")
        constant = self.ecf_printer.get_payment_constant(self.create_payment())
        self.assertEquals(constant.constant_type, DeviceConstant.TYPE_PAYMENT)
        self.assertEquals(constant.constant_enum, PaymentMethodType.MONEY)
        self.assertEquals(constant.device_value, u"M")
