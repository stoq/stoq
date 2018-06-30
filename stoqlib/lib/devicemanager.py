# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

"""Device handling, probing hardware
"""

import operator

from stoqlib.lib.translation import locale_sorted


class SerialDevice(object):
    """An object representing a serial device
    :attribute device_name: the device name, /dev/ttyXXX
    """

    def __init__(self, device_name):
        """
        Create a new SerialDevice object.
        :param device_name: name of the device
        """
        self.device_name = device_name


class DeviceManager(object):
    """DeviceManager is responsible for interacting with hardware devices.
    """

    _instance = None

    def __init__(self):
        assert not DeviceManager._instance
        DeviceManager._instance = self

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            return cls()

        return cls._instance

    @classmethod
    def get_serial_devices(cls):
        """Get a list of serial devices available on the system
        :returns: a list of :class:`SerialDevice`
        """
        from serial.tools.list_ports import comports
        ports = [SerialDevice(p.device) for p in comports()]
        return locale_sorted(ports, key=operator.attrgetter('device_name'))
