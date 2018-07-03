# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2018 Async Open Source <http://www.async.com.br>
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
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##

import mock

from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib.devicemanager import DeviceManager


class TestDeviceManager(DomainTest):
    """A class for testing the functions on lib/payment.py
    """

    def test_singleton(self):
        instance1 = DeviceManager.get_instance()
        instance2 = DeviceManager.get_instance()
        self.assertEqual(instance1, instance2)

    @mock.patch('serial.tools.list_ports.comports')
    def test_get_serial_devices(self, comports):
        class MockDevice:
            device = '/dev/ttyS0'
        comports.return_value = [MockDevice()]
        devices = DeviceManager.get_serial_devices()

        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0].device_name, '/dev/ttyS0')

    def test_printer_empty(self):
        printer = DeviceManager.get_instance().printer
        self.assertIsNone(printer)

    def test_scale_empty(self):
        scale = DeviceManager.get_instance().scale
        self.assertIsNone(scale)
