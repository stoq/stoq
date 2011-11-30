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
import platform

try:
    import gudev
    gudev # pyflakes
except ImportError:
    gudev = None

try:
    import dbus
    dbus # pyflakes
except ImportError:
    dbus = None

if dbus:
    class _HALDevice(object):
        def __init__(self, bus, udi):
            self._device = dbus.Interface(
                bus.get_object('org.freedesktop.Hal', udi),
                'org.freedesktop.Hal.Device')

        def get(self, property):
            return self._device.GetProperty(property)

    class _HALManager(object):
        def __init__(self):
            self._bus = dbus.SystemBus()
            hal_obj = self._bus.get_object('org.freedesktop.Hal', '/org/freedesktop/Hal/Manager')
            self._hal = dbus.Interface(hal_obj, 'org.freedesktop.Hal.Manager')

        def find_device(self, capability):
            for udi in self._hal.FindDeviceByCapability(capability):
                yield _HALDevice(self._bus, udi)


class SerialDevice(object):
    """An object representing a serial device
    @ivar device_name: the device name, /dev/ttyXXX
    """
    def __init__(self, device_name):
        """
        Create a new SerialDevice object.
        @param device_name: name of the device
        """
        self.device_name = device_name


class DeviceManager(object):
    """DeviceManager is responsible for interacting with hardware devices.
    It optionally uses HAL to probe the system

    """
    def __init__(self):
        self._hal_manager = None
        if dbus:
            try:
                self._hal_manager = _HALManager()
            except dbus.DBusException:
                pass

    def _get_default_devices(self):
        if platform.system() == "Windows":
            return [SerialDevice("COM1"),
                    SerialDevice("COM2"),
                    SerialDevice("COM3"),
                    SerialDevice("COM4")]
        else:
            return [SerialDevice('/dev/ttyS0'),
                    SerialDevice('/dev/ttyS1')]

    def _get_hal_devices(self):
        devices = []
        for device in self._hal_manager.find_device(capability='serial'):
            devices.append(SerialDevice(device.get('serial.device')))
        return devices

    def _get_gudev_devices(self):
        client = gudev.Client(["tty", 'usb-serial'])
        devices = []

        # usb serial devices
        for dev in client.query_by_subsystem("usb-serial"):
            devices.append(SerialDevice('/dev/' + dev.get_name()))

        # serial tty devices
        for dev in client.query_by_subsystem("tty"):
            parent = dev.get_parent()
            if parent is None:
                continue
            if parent.get_driver() != 'serial':
                continue
            devices.append(SerialDevice('/dev/' + dev.get_name()))
        return devices

    def get_serial_devices(self):
        """Get a list of serial devices available on the system
        @returns: a list of L{SerialDevice}
        """
        if gudev:
            devices = self._get_gudev_devices()
        elif self._hal_manager:
            devices = self._get_hal_devices()
        else:
            devices = self._get_default_devices()
        return sorted(devices, key=operator.attrgetter('device_name'))
