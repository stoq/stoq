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

from stoqdrivers.enum import PaymentMethodType, TaxType

from stoqlib.database.exceptions import IntegrityError
from stoqlib.domain.sellable import SellableTaxConstant
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.exceptions import DeviceError
from stoqlib.lib.translation import stoqlib_gettext

from ecf.ecfdomain import ECFPrinter, DeviceConstant

_ = stoqlib_gettext


class TestDeviceConstant(DomainTest):
    def testGetConstantDescription(self):
        constant = self.create_device_constant()
        self.assertEqual(constant.get_constant_type_description(), _(u"Tax"))

    def testGetCustomTaxConstant(self):
        settings = self.create_ecf_printer()
        constant = DeviceConstant.get_custom_tax_constant(
            settings, 0, self.trans)
        self.assertEquals(constant, None)

        constant = DeviceConstant.get_custom_tax_constant(
            settings, 18, self.trans)
        self.assertNotEquals(constant, None)
        self.assertEquals(constant.constant_type, DeviceConstant.TYPE_TAX)
        self.assertEquals(constant.constant_enum, TaxType.CUSTOM)
        self.assertEquals(constant.constant_value, 18)
        self.assertEquals(constant.device_value, 'T1')

    def testGetTaxConstant(self):
        settings = self.create_ecf_printer()
        constant = DeviceConstant.get_tax_constant(
            settings, -1, self.trans)
        self.assertEquals(constant, None)

        constant = DeviceConstant.get_tax_constant(
            settings, TaxType.NONE, self.trans)
        self.assertNotEquals(constant, None)
        self.assertEquals(constant.constant_type, DeviceConstant.TYPE_TAX)
        self.assertEquals(constant.constant_enum, TaxType.NONE)
        self.assertEquals(constant.constant_value, None)
        self.assertEquals(constant.device_value, 'TN')


class TestECFPrinter(DomainTest):

    def create_ecf_printer(self):
        return

    def testIsAFiscalPrinter(self):
        settings = self.create_ecf_printer()
        settings.type = ECFPrinter.FISCAL_PRINTER_DEVICE
        self.failUnless(settings.is_a_fiscal_printer())
        settings = self.create_ecf_printer()
        settings.type = ECFPrinter.CHEQUE_PRINTER_DEVICE
        self.failIf(settings.is_a_fiscal_printer())

    def testGetConstantsByType(self):
        settings = self.create_ecf_printer()
        settings.create_fiscal_printer_constants()

        for constant_type in [DeviceConstant.TYPE_UNIT,
                              DeviceConstant.TYPE_TAX,
                              DeviceConstant.TYPE_PAYMENT]:
            self.assertEqual(
                list(settings.get_constants_by_type(constant_type)),
                [c for c in settings.constants
                       if c.constant_type == constant_type])

    def testGetTaxConstantForDevice(self):
        settings = self.create_ecf_printer()
        settings.create_fiscal_printer_constants()
        sellable = self.create_sellable()
        constant = settings.get_tax_constant_for_device(sellable)
        self.assertEquals(constant.constant_type, DeviceConstant.TYPE_TAX)
        self.assertEquals(constant.constant_enum, TaxType.NONE)
        self.assertEquals(constant.constant_value, None)
        self.assertEquals(constant.device_value, "TN")

    def testGetTaxConstantForDeviceInvalidTaxValue(self):
        settings = self.create_ecf_printer()
        settings.create_fiscal_printer_constants()
        sellable = self.create_sellable()
        sellable.tax_constant = SellableTaxConstant(
            connection=self.trans,
            description='',
            tax_value=3.1415,
            tax_type=int(TaxType.CUSTOM))
        self.assertRaises(DeviceError,
                          settings.get_tax_constant_for_device, sellable)

    def testGetTaxConstantForDeviceInvalidTaxType(self):
        settings = self.create_ecf_printer()
        settings.create_fiscal_printer_constants()
        sellable = self.create_sellable()
        try:
            sellable.tax_constant = SellableTaxConstant(
                connection=self.trans,
                description='',
                tax_value=18,
                tax_type=999)
        except IntegrityError:
            pass
        else:
            raise AssertionError

    def testGetPaymentConstant(self):
        settings = self.create_ecf_printer()
        settings.create_fiscal_printer_constants()
        constant = settings.get_payment_constant(PaymentMethodType.MONEY)
        self.assertEquals(constant.constant_type, DeviceConstant.TYPE_PAYMENT)
        self.assertEquals(constant.constant_enum, PaymentMethodType.MONEY)
        self.assertEquals(constant.device_value, "M")
