# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Stoqdrivers
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s):   Henrique Romano             <henrique@async.com.br>
##              Johan Dahlin                <jdahlin@async.com.br>
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
from stoqdrivers.constants import TAX_NONE

# The directory where tests data will be stored
RECORDER_DATA_DIR = "data"

class LogSerialPort:
    """ A decorator for the SerialPort object expected by the driver to test,
    responsible for log all the bytes read/written.
    """
    implements(ISerialPort)

    def __init__(self, port):
        self._port = port
        self._bytes = []
        self._last = None
        self._buffer = ''

    def setDTR(self):
        return self._port.setDTR()

    def getDSR(self):
        return self._port.getDSR()

    def set_options(self, *args, **kwargs):
        self._port.set_options(*args, **kwargs)

    def read(self, n_bytes=1):
        data = self._port.read(n_bytes)
        self._buffer += data
        self._last = 'R'
        return data

    def write(self, bytes):
        if self._last == 'R':
            self._bytes.append(('R', self._buffer))
            self._buffer = ''

        self._bytes.append(('W', bytes))
        self._port.write(bytes)
        self._last = 'R'

    def save(self, filename):
        if self._buffer:
            self._bytes.append(('R', self._buffer))
        fd = open(filename, "w")
        for type, line in self._bytes:
            fd.write("%s %s\n" % (type, repr(line)[1:-1]))
        fd.close()

class PlaybackPort:
    implements(ISerialPort)

    def __init__(self, datafile):
        self._input = []
        self._output = ''
        self._load_data(datafile)

    def set_options(self, *args, **kwargs):
        pass

    def setDTR(self):
        pass

    def getDSR(self):
        return True

    def write(self, bytes):
        n_bytes = len(bytes)
        data = "".join([self._input.pop(0) for i in xrange(n_bytes)])
        if bytes != data:
            msg = ("Written data differs from the expected:\n"
                   "WROTE: %r\nEXPECTED: %r\n" % (data, bytes))
            raise ValueError(msg)

    def read(self, n_bytes=1):
        data = self._output[:n_bytes]
        if not data:
            return None
        self._output = self._output[n_bytes:]
        return data

    def _load_data(self, datafile):
        fd = open(datafile, "r")
        for n, line in enumerate(fd.readlines()):
            data = line[2:-1]
            data = data.replace('\\n', '\n')
            data = data.replace('\\r', '\r')
            data = data.replace('\\t', '\t')
            data = data.split('\\x')
            if len(data) == 1:
                data = data[0]
            else:
                n = ''
                for p in data:
                    if len(p) <= 1:
                        n += p
                    else:
                        n += p[:2].decode('hex') + p[2:]
                data = n

            if line.startswith("W"):
                self._input.extend(data)
            elif line.startswith("R"):
                self._output += data
            else:
                raise TypeError("Unrecognized entry type at %s:%d: %r"
                                % (datafile, n + 1, line[0]))
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
        filename = self._get_recorder_filename()
        if not os.path.exists(filename):
            self._device = self.device_class(brand=self.brand,
                                             model=self.model)
            # Decorate the port used by device
            self._port = LogSerialPort(self._device.get_port())
            self._device.set_port(self._port)
        else:
            self._port = PlaybackPort(filename)
            self._device = self.device_class(brand=self.brand,
                                             model=self.model,
                                             port=self._port)
        constant = self._device.get_constants()
        self._taxnone = constant.get_tax_constant(TAX_NONE)

    def _get_recorder_filename(self):
        testdir = os.path.join(os.path.dirname(stoqdrivers.__file__),
                               "..", "tests")
        test_name = self._test_name
        if test_name.startswith('test_'):
            test_name = test_name[5:]
        test_name = test_name.replace('_', '-')

        filename = "%s-%s-%s.txt" % (self.brand, self.model, test_name)
        return os.path.join(testdir, RECORDER_DATA_DIR, filename)
