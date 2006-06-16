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
## Author(s):   Johan Dahlin     <jdahlin@async.com.br>
##

from serial import Serial, EIGHTBITS, PARITY_NONE, STOPBITS_ONE
from zope.interface import providedBy
from zope.interface.exceptions import DoesNotImplement

from stoqdrivers.log import Logger
from stoqdrivers.devices.interfaces import IBytesRecorder

class SerialBase(Serial, Logger):
    log_domain = 'serial'

    # All commands will have this prefixed
    CMD_PREFIX = '\x1b'
    CMD_SUFFIX = ''

    # used by readline()
    EOL_DELIMIT = '\r'

    def __init__(self, device, baudrate=9600, bytesize=EIGHTBITS,
                 parity=PARITY_NONE, stopbits=STOPBITS_ONE):
        self._recorder = None
        Logger.__init__(self)
        self.info('opening device %s' % device)
        Serial.__init__(self, device, baudrate=baudrate,
                        bytesize=bytesize, parity=parity,
                        stopbits=stopbits)
        self.setDTR(True)
        self.flushInput()
        self.flushOutput()
        self.setTimeout(3)

    def readline(self):
        c = ''
        out = ''
        while True:
            c = self.read(1)
            if c == self.EOL_DELIMIT:
                self.debug('<<< %r' % out)
                if self._recorder is not None:
                    self._recorder.bytes_read(out)
                return out
            out +=  c

    def write(self, data):
        self.debug(">>> %r (%dbytes)" % (data, len(data)))
        if self._recorder is not None:
            self._recorder.bytes_written(data)
        Serial.write(self, data)

    def writeline(self, data):
        self.write(self.CMD_PREFIX + data + self.CMD_SUFFIX)
        return self.readline()

    def set_recorder(self, recorder):
        """ Define a recorder to log all the bytes read and written. The
        recorder must implements the IBytesRecorder interface.
        """
        if not IBytesRecorder in providedBy(recorder):
            raise DoesNotImplement("The recorder %r must implement the "
                                   "IBytesRecorder interface"% recorder)
        self._recorder = recorder
