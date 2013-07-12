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

from stoqdrivers.printers.cheque import ChequePrinter
from stoqdrivers.scales.scales import Scale
from stoqdrivers.serialbase import SerialPort
from storm.references import Reference, ReferenceSet
from zope.interface import implementer

from stoqlib.database.properties import PriceCol
from stoqlib.database.properties import (IntCol, BoolCol,
                                         DateTimeCol, UnicodeCol,
                                         IdCol)
from stoqlib.database.runtime import get_current_station
from stoqlib.domain.base import Domain
from stoqlib.domain.interfaces import IActive, IDescribable
from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


@implementer(IActive)
@implementer(IDescribable)
class DeviceSettings(Domain):

    __storm_table__ = 'device_settings'

    type = IntCol()
    brand = UnicodeCol()
    model = UnicodeCol()
    device_name = UnicodeCol()
    station_id = IdCol()
    station = Reference(station_id, 'BranchStation.id')
    is_active = BoolCol(default=True)

    (SCALE_DEVICE,
     _UNUSED,
     CHEQUE_PRINTER_DEVICE) = range(1, 4)

    device_types = {SCALE_DEVICE: _(u'Scale'),
                    CHEQUE_PRINTER_DEVICE: _(u'Cheque Printer')}

    #
    # Domain
    #

    def get_printer_description(self):
        return u"%s %s" % (self.brand.capitalize(), self.model)

    def get_device_type_name(self, type=None):
        return DeviceSettings.device_types[type or self.type]

    # XXX: Maybe stoqdrivers can implement a generic way to do this?
    def get_interface(self):
        """ Based on the column values instantiate the stoqdrivers interface
        for the device itself.
        """
        port = SerialPort(device=self.device_name)

        if self.type == DeviceSettings.CHEQUE_PRINTER_DEVICE:
            return ChequePrinter(brand=self.brand, model=self.model, port=port)
        elif self.type == DeviceSettings.SCALE_DEVICE:
            return Scale(brand=self.brand, model=self.model,
                         device=self.device_name)
        raise DatabaseInconsistency("The device type referred by this "
                                    "record (%r) is invalid, given %r."
                                    % (self, self.type))

    def is_a_printer(self):
        return self.type == DeviceSettings.CHEQUE_PRINTER_DEVICE

    def is_valid(self):
        return (all((self.model, self.device_name, self.brand, self.station))
                and self.type in DeviceSettings.device_types)

    @classmethod
    def get_by_station_and_type(cls, store, station, type):
        """Fetch all settings for a specific station and type.

        :param store: a store
        :param station: a BranchStation instance
        :param type: device type
        """
        return store.find(cls, station=station, type=type)

    @classmethod
    def get_scale_settings(cls, store):
        """
        Get the scale device settings for the current station
        :param store: a store
        :returns: a :class:`DeviceSettings` object or None if there is none
        """
        station = get_current_station(store)
        return store.find(cls, station=station,
                          type=cls.SCALE_DEVICE).one()

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

    #
    # IDescribable implementation
    #

    def get_description(self):
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
