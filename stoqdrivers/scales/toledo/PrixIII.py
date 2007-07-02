# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Stoqdrivers
## Copyright (C) 2005 Async Open Source <http://www.async.com.br>
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
Implementation of Toled Prix III driver.
"""

from serial import EIGHTBITS, STOPBITS_ONE, PARITY_EVEN
from zope.interface import implements

from stoqdrivers.exceptions import InvalidReply
from stoqdrivers.interfaces import IScale, IScaleInfo
from stoqdrivers.serialbase import SerialBase

STX = 0x02
ETX = 0x03

PRICE_PRECISION = 2
QUANTITY_PRECISION = 3

class Package:
    """ This class implements a parser for the 4a protocol of Toledo Prix III
    """
    implements(IScaleInfo)

    SIZE = 25

    def __init__(self, raw_data):
        self.code = None
        self.price_per_kg = None
        self.total_price = None
        self.weight = None
        self._parse(raw_data)

    def _parse(self, data):
        if not data:
            return
        elif ord(data[0]) != STX or len(data) != Package.SIZE:
            raise InvalidReply("Received inconsistent data")
        self.code = int(data[1:7])
        self.price_per_kg = float(data[12:18]) / (10 ** PRICE_PRECISION)
        self.weight = float(data[7:12]) / (10 ** QUANTITY_PRECISION)
        self.total_price = float(data[18:24]) / (10 ** PRICE_PRECISION)

class PrixIII(SerialBase):
    CMD_PREFIX = "\x05"
    EOL_DELIMIT = chr(ETX)

    implements(IScale)

    model_name = "Toledo Prix III"

    def __init__(self, device):
        SerialBase.__init__(self, device, baudrate=9600, bytesize=EIGHTBITS,
                            stopbits=STOPBITS_ONE, parity=PARITY_EVEN)
        self._package = None

    def _get_package(self):
        reply = self.writeline('')
        # The sum is just because readline (called internally by writeline)
        # remove the EOL_DELIMIT from the package received and we need send
        # to Package's constructor the whole data.
        return Package(reply + PrixIII.EOL_DELIMIT)

    #
    # IScale implementation
    #

    def read_data(self):
        return self._get_package()

if __name__ == "__main__":
    r = PrixIII('/dev/ttyS0')
    print "*** PRESS THE 'PRINT' BUTTON ON THE SCALE TO READ THE DATA ***"
    data = r.read_data()

    print "WEIGHT:", data.weight
    print "PRICE BY KG:", data.price_per_kg
    print "TOTAL PRICE:", data.total_price
    print "CODE:", data.code
