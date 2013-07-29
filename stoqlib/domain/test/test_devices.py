# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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
import mock
from stoqlib.domain.devices import DeviceSettings, _

from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.exceptions import DatabaseInconsistency


class TestDeviceSettings(DomainTest):
    def test_get_description(self):
        device = DeviceSettings(store=self.store, brand=u'Brand', model=u'XX',
                                type=DeviceSettings.CHEQUE_PRINTER_DEVICE)
        str = device.get_description()
        self.assertEquals(str, u'Brand XX')

    @mock.patch('stoqlib.domain.devices.SerialPort')
    @mock.patch('stoqlib.domain.devices.ChequePrinter')
    @mock.patch('stoqlib.domain.devices.Scale')
    def test_get_interface(self, Scale, ChequePrinter, SerialPort):
        port = SerialPort()
        SerialPort.return_value = port
        device = DeviceSettings(store=self.store,
                                type=DeviceSettings.CHEQUE_PRINTER_DEVICE)

        obj = object()
        ChequePrinter.return_value = obj
        self.assertIs(device.get_interface(), obj)
        ChequePrinter.assert_called_with(brand=device.brand,
                                         model=device.model,
                                         port=port)
        obj = object()
        device.type = DeviceSettings.SCALE_DEVICE
        Scale.return_value = obj
        self.assertIs(device.get_interface(), obj)
        ChequePrinter.assert_called_with(brand=device.brand,
                                         model=device.model,
                                         port=port)
        device.type = DeviceSettings._UNUSED
        with self.assertRaises(DatabaseInconsistency) as error:
            device.get_interface()
        expected = "The device type referred by this record" \
                   " (%r) is invalid, given 2." % device
        self.assertEquals(str(error.exception), expected)

    def test_is_a_printer(self):
        device = DeviceSettings(store=self.store,
                                type=DeviceSettings.CHEQUE_PRINTER_DEVICE)
        self.assertEquals(device.is_a_printer(), True)
        device.type = DeviceSettings.SCALE_DEVICE
        self.assertEquals(device.is_a_printer(), False)

    def test_get_by_station_and_type(self):
        station = self.create_station()
        type = DeviceSettings.SCALE_DEVICE
        device = DeviceSettings(store=self.store, station=station,
                                type=type)
        results = device.get_by_station_and_type(store=self.store,
                                                 station=station,
                                                 type=type)
        self.assertEquals(results.count(), 1)

    def test_inactivate(self):
        device = DeviceSettings(store=self.store)
        self.assertTrue(device.is_active)
        device.inactivate()
        self.assertFalse(device.is_active)

    def test_activate(self):
        device = DeviceSettings(store=self.store, is_active=False)
        self.assertFalse(device.is_active)
        device.activate()
        self.assertTrue(device.is_active)

    def test_get_status_string(self):
        device = DeviceSettings(store=self.store)
        self.assertEquals(device.get_status_string(), _(u'Active'))
        device.inactivate()
        self.assertEquals(device.get_status_string(), _(u'Inactive'))

    def test_get_scale_settings(self):
        device = DeviceSettings(store=self.store,
                                type=DeviceSettings.SCALE_DEVICE)
        self.assertIsNone(device.get_scale_settings(store=self.store))
