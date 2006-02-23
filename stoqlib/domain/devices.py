# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005,2006 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s):   Henrique Romano <henrique@async.com.br>
##
"""
stoq/domain/devices.py

   Domain classes related to stoqdrivers package.
"""

from sqlobject import UnicodeCol, IntCol

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.domain.base import Domain

_ = stoqlib_gettext

class DeviceSettings(Domain):
    type = IntCol()
    brand = UnicodeCol()
    model = UnicodeCol()
    device = IntCol()
    host = UnicodeCol()

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

    def get_printer_description(self):
        return "%s %s" % (self.brand.capitalize(), self.model)

    def get_device_description(self, device=None):
        return DeviceSettings.device_descriptions[device or self.device]

    def get_port_name(self, device=None):
        return DeviceSettings.port_names[device or self.device]

    def get_device_type_name(self, type=None):
        return DeviceSettings.device_types[type or self.type]
