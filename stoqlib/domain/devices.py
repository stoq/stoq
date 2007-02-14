# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005,2006, 2007 Async Open Source <http://www.async.com.br>
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
## Author(s):   Henrique Romano <henrique@async.com.br>
##            Johan Dahlin    <jdahlin@async.com.br>
##
"""
stoq/domain/devices.py

   Domain classes related to stoqdrivers package.
"""

from sqlobject import UnicodeCol, IntCol, PickleCol, ForeignKey, BoolCol
from sqlobject.sqlbuilder import AND
from zope.interface import implements
from stoqdrivers.devices.interfaces import IDriverConstants
from stoqdrivers.devices.printers.fiscal import FiscalPrinter
from stoqdrivers.devices.printers.cheque import ChequePrinter
from stoqdrivers.devices.scales.scales import Scale
from stoqdrivers.devices.serialbase import VirtualPort, SerialPort

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.defaults import (get_all_methods_dict, METHOD_MONEY,
                                  METHOD_CHECK)
from stoqlib.domain.base import Domain
from stoqlib.domain.interfaces import IActive
from stoqlib.exceptions import DatabaseInconsistency

_ = stoqlib_gettext

class DeviceConstants(Domain):
    """ This class stores information about custom device constants.
    There is only an dictionary attribute, where keys and its values
    are in the following form:

    {
     CONSTANT_ID: value,
    }
    """
    implements(IDriverConstants)

    constants = PickleCol()

    def _check_identifier(self, identifier):
        if not identifier in self.constants:
            raise ValueError("The constant with ID %d "
                             "doesn't exists" % identifier)

    def set_constants(self, constants):
        self.constants = constants

    #
    # IDriverConstants implementation
    #

    def get_items(self):
        return self.constants.keys()

    def get_value(self, identifier):
        self._check_identifier(identifier)
        return self.constants[identifier]

class DeviceSettings(Domain):
    implements(IActive)

    type = IntCol()
    brand = UnicodeCol()
    model = UnicodeCol()
    device = IntCol()
    station = ForeignKey("BranchStation")
    constants = ForeignKey("DeviceConstants", default=None)
    # Here we are going to store Stoq specific constants for payment
    # methods. It's interesting to have a unique field for that and
    # and avoid value conflicts.
    pm_constants = ForeignKey("DeviceConstants", default=None)
    is_active = BoolCol(default=True)

    (DEVICE_SERIAL1,
     DEVICE_SERIAL2,
     DEVICE_PARALLEL) = range(1, 4)

    (SCALE_DEVICE,
     FISCAL_PRINTER_DEVICE,
     CHEQUE_PRINTER_DEVICE) = range(1, 4)

    device_descriptions = {DEVICE_SERIAL1: _('Serial port 1'),
                           DEVICE_SERIAL2: _('Serial port 2'),
                           DEVICE_PARALLEL: _('Parallel port')}

    port_names = {DEVICE_SERIAL1: '/dev/ttyS0',
                  DEVICE_SERIAL2: '/dev/ttyS1',
                  DEVICE_PARALLEL: '/dev/parport'}

    device_types = {SCALE_DEVICE: _('Scale'),
                    FISCAL_PRINTER_DEVICE: _('Fiscal Printer'),
                    CHEQUE_PRINTER_DEVICE: _('Cheque Printer')}

    def _create(self, id, **kw):
        # XXX: Bug #2630 will be responsible for this part.
#         if 'pm_constants' in kw:
#             raise DatabaseInconsistency("You should not specify a value "
#                                         "for pm_constants, since it will "
#                                         "be created internally")
        data = {}
        for payment_method in get_all_methods_dict():
            # We don't store these constants to reach compatibility with
            # stoqdrivers.
            if payment_method not in (METHOD_MONEY, METHOD_CHECK):
                data[payment_method] = None
        kw['pm_constants'] = DeviceConstants(constants=data,
                                             connection=self.get_connection())
        Domain._create(self, id, **kw)

    def _is_a_virtual_printer(self):
        return (self.is_a_printer() and self.brand == "virtual" and
                self.model == "Simple")

    def is_custom_pm_configured(self):
        """
        @returns: True if all the custom payment methods is properly configured,
        False otherwise.
        """
        if not self.pm_constants:
            return False
        for method in get_all_methods_dict():
            if method in (METHOD_MONEY, METHOD_CHECK):
                continue
            if self.pm_constants.get_value(method) is None:
                return False
        return True

    def get_printer_description(self):
        return "%s %s" % (self.brand.capitalize(), self.model)

    def get_device_description(self, device=None):
        return DeviceSettings.device_descriptions[device or self.device]

    # TODO: rename to get_device_name
    def get_port_name(self, device=None):
        return DeviceSettings.port_names[device or self.device]

    def get_device_type_name(self, type=None):
        return DeviceSettings.device_types[type or self.type]

    # XXX: Maybe stoqdrivers can implement a generic way to do this?
    def get_interface(self):
        """ Based on the column values instantiate the stoqdrivers interface
        for the device itself.
        """
        if self._is_a_virtual_printer():
            port = VirtualPort()
        else:
            port = SerialPort(device=self.get_port_name())

        if self.type == DeviceSettings.FISCAL_PRINTER_DEVICE:
            return FiscalPrinter(brand=self.brand, model=self.model, port=port)
        elif self.type == DeviceSettings.CHEQUE_PRINTER_DEVICE:
            return ChequePrinter(brand=self.brand, model=self.model, port=port)
        elif self.type == DeviceSettings.SCALE_DEVICE:
            return Scale(brand=self.brand, model=self.model,
                         device=self.get_port_name())
        raise DatabaseInconsistency("The device type referred by this "
                                    "record (%r) is invalid, given %r."
                                    % (self, self.type))

    def is_a_printer(self):
        return self.type in (DeviceSettings.FISCAL_PRINTER_DEVICE,
                             DeviceSettings.CHEQUE_PRINTER_DEVICE)

    def is_a_fiscal_printer(self):
        return self.type == DeviceSettings.FISCAL_PRINTER_DEVICE

    def is_valid(self):
        return (None not in (self.model, self.device, self.brand, self.station)
                and self.type in DeviceSettings.device_types)

    @classmethod
    def get_by_station_and_type(cls, conn, station, type):
        """
        Fetch all non-virtual settings for a specific station and type.

        @param conn: a database connection
        @param station: a BranchStation instance
        @param type: device type
        """
        return cls.select(
            AND(cls.q.stationID == station,
                cls.q.type == type,
                cls.q.brand != 'virtual'),
        connection=conn)

    @classmethod
    def get_virtual_printer_settings(cls, conn, station):
        """
        Fetch the virtual printer settings for a station. None will
        be return if the station lacks a setting.
        @param conn: a database connection
        @param station: a BranchStation instance
        """
        return cls.selectOneBy(
            station=station,
            brand="virtual",
            type=DeviceSettings.FISCAL_PRINTER_DEVICE,
            connection=conn)


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

