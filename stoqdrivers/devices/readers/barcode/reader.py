# -*- Mode: Python; coding: iso-8859-1 -*-
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
## Author(s):   Henrique Romano  <henrique@async.com.br>
##
"""
Barcode reader interface implementation.
"""

from zope.interface import providedBy

from stoqdrivers.constants import BARCODE_READER_DEVICE
from stoqdrivers.devices.interfaces import IBarcodeReader
from stoqdrivers.devices.base import BaseDevice

class BarcodeReader(BaseDevice):
    device_dirname = "readers.barcode"
    device_type = BARCODE_READER_DEVICE

    def check_interfaces(self):
        if not IBarcodeReader in providedBy(self._driver):
            raise TypeError("The driver `%r' doesn't implements a valid "
                            "interface" % self._driver)

    def get_code(self):
        return self._driver.get_code()

