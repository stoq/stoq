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
## Author(s): Henrique Romano             <henrique@async.com.br>
##
"""
stoqdrivers/devices/printers/base.py:

    Generic base class implementation for all printers
"""

from zope.interface import providedBy

from stoqdrivers.log import Logger
from stoqdrivers.configparser import StoqdriversConfig
from stoqdrivers.exceptions import CriticalError, ConfigError
from stoqdrivers.devices.printers.interface import ICouponPrinter

class BasePrinter(Logger):
    def __init__(self, config_file=None):
        Logger.__init__(self)
        self._load_configuration(config_file)

    def _load_configuration(self, config_file):
        self.config = StoqdriversConfig(config_file)

        if not self.config.has_section("Printer"):
            raise ConfigError("There is no printer configured!")

        self.brand = self.config.get_option("brand", "Printer")
        self.baudrate = int(self.config.get_option("baudrate", "Printer"))
        self.model = self.config.get_option("model", "Printer")
        self.device = self.config.get_option("device", "Printer")

        self.debug(("Config data: brand=%s,device=%s,model=%s,baudrate=%s\n"
                    % (self.brand, self.device, self.model, self.baudrate)))

        name = 'stoqdrivers.devices.printers.%s.%s' % (self.brand, self.model)
        try:
            module = __import__(name, None, None, 'stoqdevices')
        except ImportError, reason:
            raise CriticalError(("Could not load driver %s %s: %s"
                                 % (self.brand.capitalize(),
                                    self.model.upper(), reason)))

        class_name = self.model + 'Printer'

        driver_class = getattr(module, class_name, None)
        if not driver_class:
            raise CriticalError(("Printer driver %s needs a class called %s"
                                 % (name, class_name)))

        self._driver = driver_class(device=self.device,
                                    baudrate=self.baudrate)

        driver_interfaces = providedBy(self._driver)
        if not (ICouponPrinter in driver_interfaces):
            raise TypeError("The driver %s doesn't implements a known "
                            "interface")
