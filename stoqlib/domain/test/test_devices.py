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

from stoqdrivers.serialbase import VirtualPort
from stoqlib.domain.devices import DeviceSettings, _
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.exceptions import DatabaseInconsistency


class TestDeviceSettings(DomainTest):
    def test_properties(self):
        station = self.create_station()
        device = DeviceSettings(store=self.store, brand=u'Brand', model=u'XX',
                                type=DeviceSettings.CHEQUE_PRINTER_DEVICE,
                                station=station)

        self.assertEquals(device.description, u'Brand XX')
        self.assertEquals(device.station_name, u'station')
        self.assertEquals(device.device_type_name, u'Cheque Printer')

    @mock.patch('stoqlib.domain.devices.SerialPort')
    @mock.patch('stoqlib.domain.devices.ChequePrinter')
    @mock.patch('stoqlib.domain.devices.Scale')
    def test_get_interface(self, Scale, ChequePrinter, SerialPort):
        port = SerialPort()
        SerialPort.return_value = port
        device = DeviceSettings(store=self.store,
                                device_name=u'/dev/ttyS0',
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
        device.type = None
        with self.assertRaises(DatabaseInconsistency) as error:
            device.get_interface()
        expected = "The device type referred by this record" \
                   " (%r) is invalid, given None." % device
        self.assertEquals(str(error.exception), expected)

    @mock.patch('stoqlib.domain.devices.NonFiscalPrinter')
    def test_get_interface_usb(self, NonFiscalPrinter):
        device = DeviceSettings(store=self.store,
                                device_name=u'usb:0xa:0x1',
                                type=DeviceSettings.NON_FISCAL_PRINTER_DEVICE)

        obj = object()
        NonFiscalPrinter.return_value = obj
        self.assertIs(device.get_interface(), obj)
        NonFiscalPrinter.assert_called_with(brand=None, model=None, port=None,
                                            product_id=1, vendor_id=10,
                                            interface='usb')

    def test_get_interface_virtual(self):
        device = DeviceSettings(store=self.store, brand=u'virtual',
                                model=u'Simple', device_name=u'/dev/null',
                                type=DeviceSettings.NON_FISCAL_PRINTER_DEVICE)
        interface = device.get_interface()
        self.assertIsInstance(interface._port, VirtualPort)

    def test_get_by_station_and_type(self):
        station = self.create_station()
        type = DeviceSettings.SCALE_DEVICE
        device = DeviceSettings(store=self.store, station=station,
                                type=type)
        results = device.get_by_station_and_type(store=self.store,
                                                 station=station,
                                                 type=type)
        self.assertEquals(results, device)

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
