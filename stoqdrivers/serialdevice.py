# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Fiscal Printer
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
## Author(s):   Christian Reis              <kiko@async.com.br>
##              Evandro Vale Miquelito      <evandro@async.com.br>
##
"""
stoqdrivers/serialdevice.py:
    
    Base routines for serial devices
"""

import serial

from stoqdrivers.basedevice import BaseSerialDevice
from stoqdrivers.exceptions import CommError


class SerialDevice(BaseSerialDevice):
    """This class implements a SerialDevice using the pySerial package
    available at http://pyserial.sourceforge.net/. The reasons for using
    this instead of the original PosixSerial.py include :
       * Multi-plattform
       * Thread safe
       * Timeouts (properly) implemented
       * Readily available in Debian ;) """

    # Optional read/write timeout
    # Should be moved later to config file
    _read_timeout  = 3
    _write_timeout = 3

    def __init__(self, device, baudrate):
        try:
            # serial.Serial wants a integer
            self.port = serial.Serial(port=device,
                                      baudrate=baudrate, 
                                      timeout=self._read_timeout)
            self.port.setDTR(1)
            self.port.setWriteTimeout(self._write_timeout)
        except:
            raise CommError('Could not *open* serial port.')

    def read(self, n_bytes=1):
        try:
            return self.port.read(size=n_bytes)
        except:
            raise CommError('Could not *read* data from printer.')


    def write(self, data):
        try:
            self.port.write(data)
        except:
            raise CommError('Could not *send* data to printer.')

    def close(self):
        self.port.close()
