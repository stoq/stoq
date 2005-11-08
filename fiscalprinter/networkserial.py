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
fiscalprinter/networkserial.py:
    
    Network serial routines
"""

import socket

from fiscalprinter.basedevice import BaseSerialDevice
from fiscalprinter.exceptions import CommError


class NetworkSerialDevice(BaseSerialDevice):
    """This class is designed to work with the 'ser2net' package, from
    http://ser2net.sourceforge.net.

    You should use this device when the serial port is not on the same
    machine the application is running on (think of thin clients, more
    specifically LTSP terminals).
    """

    def __init__(self, host, port):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect(host, port)            
        except:
           raise CommError("Could not communicate with printer."
                           "Please check if you have network "
                           "connectivity and if the printer is "
                           "attached to the remote computer.")

    def read(self, count=1):
        try:
            return self.socket.recv(count)
        except:
            raise CommError("Could not read data from network printer.")

    def write(self, data):
        try:
            self.socket.send(data)
        except:
            raise CommError("Could not send data to network printer.")

    def close(self):
        self.socket.close()
