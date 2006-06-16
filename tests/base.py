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
from stoqdrivers.devices.interfaces import IBytesRecorder

# The directory where tests data will be stored
RECORDER_DATA_DIR = "data"

class TestBytesRecorder:
    implements(IBytesRecorder)

    def __init__(self, filename):
        self._fd = open(filename, "w")

    def bytes_written(self, bytes):
        self._fd.write("< %r\n" % bytes)

    def bytes_read(self, bytes):
        self._fd.write("> %r\n" % bytes)

class BaseTest(unittest.TestCase):
    def __init__(self, test_name):
        self._test_name = test_name
        unittest.TestCase.__init__(self, test_name)

    def setUp(self):
        self._device = self.device_class()
        filename = self._get_recorder_filename()
        if not os.path.exists(filename):
            self._device.get_driver().set_recorder(TestBytesRecorder(filename))

    def _get_recorder_filename(self):
        device_name = self._device.get_model_name().replace(" ", "_")
        return os.path.join(os.path.dirname(stoqdrivers.__file__), "..", "tests",
                            RECORDER_DATA_DIR,
                            "%s-%s.txt" % (device_name,
                                           self._test_name.replace(" ", "_")))
