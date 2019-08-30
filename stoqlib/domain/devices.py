# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2007 Async Open Source <http://www.async.com.br>
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
"""
Domain classes related to stoqdrivers package.
"""

# pylint: enable=E1101

import collections
import os
import platform
from serial.serialutil import SerialException

from stoqdrivers.printers.cheque import ChequePrinter
from stoqdrivers.printers.nonfiscal import NonFiscalPrinter
from stoqdrivers.scales.scales import Scale
from stoqdrivers.serialbase import SerialPort, VirtualPort
from storm.expr import And, Eq
from storm.references import Reference, ReferenceSet
from zope.interface import implementer

from stoqlib.database.properties import PriceCol
from stoqlib.database.properties import (IntCol, BoolCol,
                                         DateTimeCol, UnicodeCol,
                                         IdCol)
from stoqlib.domain.base import Domain
from stoqlib.domain.interfaces import IActive
from stoqlib.domain.station import BranchStation
from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

MAX_TTY_SEEKING = 3


@implementer(IActive)
class DeviceSettings(Domain):

    __storm_table__ = 'device_settings'

    #: The type of this device (printer or scale)
    type = IntCol()

    #: The brand (maker) of this device
    brand = UnicodeCol()

    #: The model of the device
    model = UnicodeCol()

    #: The device name on the computer (either /dev/ttySX or COMX - Linux/Windows)
    device_name = UnicodeCol()

    #: The baudrate of the device
    baudrate = IntCol(default=9600)

    #: If this device has a inverted drawer logic (When this device is a printer, and the printer
    # has a drawer connected)
    drawer_inverted = BoolCol(default=False)

    station_id = IdCol()
    #: The station this device is connected to.
    station = Reference(station_id, 'BranchStation.id')

    #: Is this device is active or not
    is_active = BoolCol(default=True)

    (SCALE_DEVICE,
     NON_FISCAL_PRINTER_DEVICE,
     CHEQUE_PRINTER_DEVICE) = range(1, 4)

    device_types = collections.OrderedDict([
        (SCALE_DEVICE, _(u'Scale')),
        (NON_FISCAL_PRINTER_DEVICE, _(u'Non Fiscal Printer')),
        (CHEQUE_PRINTER_DEVICE, _(u'Cheque Printer')),
    ])

    #
    # Domain
    #

    @property
    def station_name(self):
        return self.station.name

    @property
    def device_type_name(self):
        return self.describe_device_type(self.type)

    def get_printer_description(self):
        return u"%s %s" % (self.brand.capitalize(), self.model)

    def describe_device_type(self, type):
        return DeviceSettings.device_types[type]

    def _get_serial_port(self):
        try:
            return SerialPort(device=self.device_name, baudrate=self.baudrate)
        except SerialException:
            # Linux may rename the serial-usb port in which the device is connected
            # inadvertedly.
            # XXX: If there are 2 or more ttyUSB devices connected, this may not work.
            if platform.system() != 'Linux' or os.path.exists(self.device_name):
                raise

            for i in range(MAX_TTY_SEEKING):
                temp_device_name = self.device_name[:-1] + str(i)
                if os.path.exists(temp_device_name):
                    return SerialPort(device=temp_device_name, baudrate=self.baudrate)

            raise

    # XXX: Maybe stoqdrivers can implement a generic way to do this?
    def get_interface(self):
        """ Based on the column values instantiate the stoqdrivers interface
        for the device itself.
        """
        if self.device_name == '/dev/null':
            interface = 'serial'
            port = VirtualPort()
            product_id = vendor_id = None
        elif self.device_name.startswith('usb:'):
            # USB device
            interface, vendor_id, product_id = self.device_name.split(':')
            vendor_id = int(vendor_id, 16)
            product_id = int(product_id, 16)
            port = None
        else:
            # Serial device
            interface = 'serial'
            port = self._get_serial_port()
            product_id = vendor_id = None

        if self.type == DeviceSettings.CHEQUE_PRINTER_DEVICE:
            return ChequePrinter(brand=self.brand, model=self.model, port=port)
        elif self.type == DeviceSettings.NON_FISCAL_PRINTER_DEVICE:
            return NonFiscalPrinter(brand=self.brand, model=self.model,
                                    port=port, interface=interface,
                                    product_id=product_id, vendor_id=vendor_id)
        elif self.type == DeviceSettings.SCALE_DEVICE:
            return Scale(brand=self.brand, model=self.model,
                         device=self.device_name, port=port)

        raise DatabaseInconsistency("The device type referred by this "
                                    "record (%r) is invalid, given %r."
                                    % (self, self.type))

    def is_valid(self):
        return (all((self.model, self.device_name, self.brand, self.station))
                and self.type in DeviceSettings.device_types)

    @classmethod
    def get_by_station_and_type(cls, store, station, type, exclude=None):
        """Fetch the settings for a specific station and type.

        Note that one station can have only one active device of a given type.

        :param store: a store
        :param station: a BranchStation instance
        :param type: device type
        :param exclude: a device to exclude from search
        """
        except_id = exclude and exclude.id
        return store.find(cls, And(cls.station == station, cls.type == type,
                                   Eq(cls.is_active, True), cls.id != except_id)).one()

    @classmethod
    def get_scale_settings(cls, store, station: BranchStation):
        """
        Get the scale device settings for the current station
        :param store: a store
        :returns: a :class:`DeviceSettings` object or None if there is none
        """
        return cls.get_by_station_and_type(store, station, cls.SCALE_DEVICE)

    #
    # IActive implementation
    #

    def inactivate(self):
        self.is_active = False

    def activate(self):
        self.is_active = True

    def get_status_string(self):
        if self.is_active:
            return _(u'Active')
        return _(u'Inactive')

    @property
    def description(self):
        return self.get_printer_description()


class FiscalDayTax(Domain):
    """This represents the information that needs to be used to
    generate a Sintegra file of type 60M.
    """

    __storm_table__ = 'fiscal_day_tax'

    fiscal_day_history_id = IdCol()
    fiscal_day_history = Reference(fiscal_day_history_id, 'FiscalDayHistory.id')

    #: four bytes, either the percental of the tax, 1800 for 18% or one of:
    #:
    #: * ``I``: Isento
    #: * ``F``: Substitucao
    #: * ``N``: Nao tributado
    #: * ``ISS``: ISS
    #: * ``CANC``: Cancelled
    #: * ``DESC``: Discount
    code = UnicodeCol()

    value = PriceCol()
    type = UnicodeCol()


class FiscalDayHistory(Domain):
    """This represents the information that needs to be used to
    generate a Sintegra file of type 60A.
    """

    __storm_table__ = 'fiscal_day_history'

    emission_date = DateTimeCol()
    station_id = IdCol()
    station = Reference(station_id, 'BranchStation.id')
    serial = UnicodeCol()
    serial_id = IntCol()
    coupon_start = IntCol()
    coupon_end = IntCol()
    cro = IntCol()
    crz = IntCol()
    period_total = PriceCol()
    total = PriceCol()
    taxes = ReferenceSet('id', 'FiscalDayTax.fiscal_day_history_id')
    reduction_date = DateTimeCol()
