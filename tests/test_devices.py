# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
##

from stoqlib.domain.devices import DeviceSettings
from stoqlib.database.runtime import get_current_station
from stoqlib.lib.defaults import get_all_methods_dict, METHOD_CARD

from tests.base import DomainTest

class TestDevice(DomainTest):
    _table = DeviceSettings

    def test_is_a_fiscal_printer(self):
        station = get_current_station(self.trans)
        settings = DeviceSettings(station=station,
                                  device=DeviceSettings.DEVICE_SERIAL1,
                                  brand='virtual',
                                  model='Simple',
                                  type=DeviceSettings.FISCAL_PRINTER_DEVICE,
                                  connection=self.trans)
        self.failUnless(settings.is_a_fiscal_printer())
        settings = DeviceSettings(station=station,
                                  device=DeviceSettings.DEVICE_SERIAL1,
                                  brand='virtual',
                                  model='Simple',
                                  type=DeviceSettings.CHEQUE_PRINTER_DEVICE,
                                  connection=self.trans)
        self.failUnless(not settings.is_a_fiscal_printer())

    def test_is_custom_pm_configured(self):
        station = get_current_station(self.trans)
        settings = DeviceSettings(station=station,
                                  device=DeviceSettings.DEVICE_SERIAL1,
                                  brand='virtual',
                                  model='Simple',
                                  type=DeviceSettings.FISCAL_PRINTER_DEVICE,
                                  connection=self.trans)
        pm_constants = settings.pm_constants
        self.failUnless(pm_constants is not None, ("pm_constants should be "
                                                   "valid a this point."))
        new_constants = {}
        for method in get_all_methods_dict():
            new_constants[method] = '00'
        pm_constants.set_constants(new_constants)
        self.failUnless(settings.is_custom_pm_configured(),
                        "pm constants should be valid now")
        new_constants[METHOD_CARD] = None
        pm_constants.set_constants(new_constants)
        self.failUnless(not settings.is_custom_pm_configured())
