# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Stoqdrivers
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s):   Henrique Romano             <henrique@async.com.br>
##
"""
stoqdrivers/tests/base.py:

    Base classes for Stoqdrivers tests
"""
import os
import unittest

from zope.interface import implements

import stoqdrivers
from stoqdrivers.devices.interfaces import ISerialPort
from stoqdrivers.devices.serialbase import SerialPort

# The directory where tests data will be stored
RECORDER_DATA_DIR = "data"
# The port where the device to test is connected
DEVICE_PORT = "/dev/ttyS0"

class LogSerialPort:
    """ A decorator for the SerialPort object expected by the driver to test,
    responsible for log all the bytes read/written.
    """
    implements(ISerialPort)

    def __init__(self, device):
        self._port = SerialPort(device)
        self._bytes_read = []
        self._bytes_written = []

    def set_options(self, *args, **kwargs):
        self._port.set_options(*args, **kwargs)

    def read(self, n_bytes):
        data = self._port.read(n_bytes)
        self._bytes_read.append(data)
        return data

    def write(self, bytes):
        self._bytes_written.append(bytes)
        self._port.write(bytes)

    def save(self, filename):
        fd = open(filename, "w")
        for d in self._bytes_written:
            fd.write("< %r\n" % d)
        for d in self._bytes_read:
            fd.write("> %r\n" % d)
        fd.close()

class BaseTest(unittest.TestCase):
    def __init__(self, test_name):
        self._test_name = test_name
        unittest.TestCase.__init__(self, test_name)

    def tearDown(self):
        filename = self._get_recorder_filename()
        if not os.path.exists(filename):
            self._port.save(filename)

    def setUp(self):
        self._port = LogSerialPort(DEVICE_PORT)
        self._device = self.device_class(port=self._port)

    def _get_recorder_filename(self):
        device_name = self._device.get_model_name().replace(" ", "_")
        return os.path.join(os.path.dirname(stoqdrivers.__file__), "..", "tests",
                            RECORDER_DATA_DIR,
                            "%s-%s.txt" % (device_name,
                                           self._test_name.replace(" ", "_")))
