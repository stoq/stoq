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
## Author(s):     Henrique Romano <henrique@async.com.br>
##                Johan Dahlin <jdahlin@async.com.br>
##

from decimal import Decimal

from stoqdrivers.exceptions import DriverError

from stoqlib.database.runtime import get_current_station
from stoqlib.domain.devices import DeviceSettings
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib.drivers import (get_fiscal_printer_settings_by_station,
                                 CouponPrinter)

class TestDrivers(DomainTest):

    def test_virtual_printer_creation(self):
        station = get_current_station(self.trans)
        settings = get_fiscal_printer_settings_by_station(self.trans,
                                                          station)
        self.failUnless(settings is not None, ("You should have a valid "
                                               "printer at this point."))


class TestCouponPrinter(DomainTest):
    def setUp(self):
        DomainTest.setUp(self)
        settings = DeviceSettings(station=get_current_station(self.trans),
                                  device=DeviceSettings.DEVICE_SERIAL1,
                                  brand='virtual',
                                  model='Simple',
                                  type=DeviceSettings.FISCAL_PRINTER_DEVICE,
                                  connection=self.trans)
        self.printer = CouponPrinter(settings.get_interface(), settings)

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
