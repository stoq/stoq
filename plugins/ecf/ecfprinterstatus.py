# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##

import os
import platform

# pyserial bug
try:
    import fcntl
    fcntl.O_NONBLOCK = os.O_NONBLOCK
except ImportError:
    pass

import glib
import gobject
from kiwi.utils import gsignal
from stoqdrivers.serialbase import SerialPort


class ECFAsyncPrinterStatus(gobject.GObject):
    """
    @ivar printer:
    """
    gsignal('reply', str)
    gsignal('timeout')

    def __init__(self, device_name, printer_class, baudrate=9600, delay=5):
        """
        @param device_name:
        @param printer_class:
        @param delay:
        """
        gobject.GObject.__init__(self)
        self._reply = ''
        self._device_name = device_name
        self._delay = delay
        self._port = self._create_port(baudrate)
        self.printer = printer_class(self._port)

        if platform.system() != 'Windows':
            self._timeout_id = glib.timeout_add(self._delay * 1000, self._on_timeout)
            glib.io_add_watch(self._port, glib.IO_OUT, self._fd_watch_out)
            glib.io_add_watch(self._port, glib.IO_IN, self._fd_watch_in)
        else:
            self._timeout_id = glib.timeout_add(400, self._check_windows)

    def _check_windows(self):
        try:
            self._reply = self.printer.get_serial()
        finally:
            # Since we are trying to comminicate with a printer without being
            # sure of the parameters the user set, something wrong might occour.
            # What ever happens, we should remove the timeout and emit a reply.
            self._remove_timeout()
            self.emit('reply', self._reply)

    def _create_port(self, baudrate):
        port = SerialPort(device=self._device_name, baudrate=baudrate)
        port.writeTimeout = 5
        if platform.system() != 'Windows':
            port.nonblocking()
        return port

    def _remove_timeout(self):
        if self._timeout_id != -1:
            glib.source_remove(self._timeout_id)
            self._timeout_id = -1

    def _fd_watch_out(self, port, condition):
        value = self.printer.query_status()
        if value is None:
            self._remove_timeout()
            self.emit('reply', self._reply)
            return False
        os.write(port.fileno(), value)
        return False

    def _fd_watch_in(self, port, condition):
        c = port.read()
        self._reply += c
        if self.printer.status_reply_complete(self._reply):
            # We need to remove the timeout before emitting the reply,
            # so we can show dialogs inside the reply callback.
            self._remove_timeout()
            self.emit('reply', self._reply)
            return False
        return True

    def _on_timeout(self):
        self._remove_timeout()
        self.emit('timeout')
        return False

    def stop(self):
        self._remove_timeout()

    def get_device_name(self):
        return self._device_name

    def get_driver(self):
        return self.printer

    def get_port(self):
        return self._port
