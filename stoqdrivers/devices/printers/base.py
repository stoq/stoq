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
import os
import gettext

from zope.interface import providedBy
from kiwi.python import namedAny

from stoqdrivers.log import Logger
from stoqdrivers.configparser import StoqdriversConfig
from stoqdrivers.exceptions import CriticalError, ConfigError
from stoqdrivers.devices import printers
from stoqdrivers.devices.printers.interface import (ICouponPrinter,
                                                    IChequePrinter)
from stoqdrivers.utils import get_module_list

_ = lambda msg: gettext.dgettext("stoqdrivers", msg)

class BasePrinter(Logger):
    log_domain = "stoqdrivers"
    
    def __init__(self, brand=None, model=None, device=None, config_file=None):
        Logger.__init__(self)
        self.brand, self.model, self.device = brand, model, device
        self._load_configuration(config_file)

    def _load_configuration(self, config_file):
        if not self.model or not self.brand or not self.device:
            self.config = StoqdriversConfig(config_file)
            if not self.config.has_section("Printer"):
                raise ConfigError(_("There is no printer configured!"))
            self.brand = self.config.get_option("brand", "Printer")
            self.device = self.config.get_option("device", "Printer")
            self.model = self.config.get_option("model", "Printer")

        name = 'stoqdrivers.devices.printers.%s.%s' % (self.brand, self.model)
        try:
            module = __import__(name, None, None, 'stoqdevices')
        except ImportError, reason:
            raise CriticalError("Could not load driver %s %s: %s"
                                % (self.brand.capitalize(),
                                   self.model.upper(), reason))

        class_name = self.model

        driver_class = getattr(module, class_name, None)
        if not driver_class:
            raise CriticalError("Printer driver %s needs a class called %s"
                                % (name, class_name))

        self._driver = driver_class(device=self.device)

        self.debug(("Config data: brand=%s,device=%s,model=%s\n"
                    % (self.brand, self.device, self.model)))

        driver_interfaces = providedBy(self._driver)
        if not (ICouponPrinter in driver_interfaces):
            raise TypeError("The driver %s doesn't implements a known "
                            "interface" % self._driver)

def get_virtual_printer():
    from stoqdrivers.devices.printers.fiscal import FiscalPrinter
    return FiscalPrinter(brand='virtual', model='Simple')

def get_supported_printers():
    printers_dir = os.path.dirname(printers.__file__)
    result = {}

    for brand in os.listdir(printers_dir):
        brand_dir = os.path.join(printers_dir, brand)
        if ((not os.path.isdir(brand_dir)) or brand.startswith(".")
            or brand.startswith("virtual")):
            continue

        result[brand] = []
        for module_name in get_module_list(brand_dir):
            try:
                obj = namedAny("stoqdrivers.devices.printers.%s.%s.%s"
                               % (brand, module_name, module_name))
            except AttributeError:
                raise ImportError("Can't find class %s for module %s"
                                  % (module_name, module_name))
            if not (IChequePrinter.implementedBy(obj) or
                    ICouponPrinter.implementedBy(obj)):
                raise TypeError("The driver %s %s doesn't implements a "
                                "valid interface" % (brand, model_name))
            result[brand].append(obj)
    return result

