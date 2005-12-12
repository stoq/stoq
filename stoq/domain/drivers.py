# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
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
## Author(s):   Henrique Romano <henrique@async.com.br>
##
"""
stoq/domain/drivers.py

   Domain classes related to stoqdrivers package.
"""

import gettext

from sqlobject import StringCol, IntCol

from stoq.domain.base import Domain

_ = gettext.gettext

class PrinterSettings(Domain):
    brand = StringCol(default=None)
    model = StringCol(default=None)
    device = IntCol(default=None)
    host = StringCol(default=None)

    (DEVICE_SERIAL1,
     DEVICE_SERIAL2,
     DEVICE_PARALLEL) = range(1, 4)

    device_descriptions = {DEVICE_SERIAL1: _('Serial port 1'),
                           DEVICE_SERIAL2: _('Serial port 2'),
                           DEVICE_PARALLEL: _('Parallel port')}

    device_names = {DEVICE_SERIAL1: '/dev/ttyS0',
                    DEVICE_SERIAL2: '/dev/ttyS1',
                    DEVICE_PARALLEL: '/dev/parport'}

    def get_printer_description(self):
        return "%s %s" % (self.brand.capitalize(), self.model)

    def get_device_description(self, device=None):
        return PrinterSettings.device_descriptions[device or self.device]

    def get_device_name(self, device=None):
        return PrinterSettings.device_names[device or self.device]
