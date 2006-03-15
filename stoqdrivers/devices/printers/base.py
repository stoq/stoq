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

from zope.interface import providedBy, implements
from kiwi.python import namedAny

from stoqdrivers.devices import printers
from stoqdrivers.devices.printers.interface import (ICouponPrinter,
                                                    IDriverConstants,
                                                    IChequePrinter)
from stoqdrivers.devices.base import BaseDevice
from stoqdrivers.utils import get_module_list
from stoqdrivers.constants import PRINTER_DEVICE

_ = lambda msg: gettext.dgettext("stoqdrivers", msg)

class BaseDriverConstants:
    implements(IDriverConstants)

    # Must be defined on subclasses
    _constants = None

    @classmethod
    def get_constant_value(cls, name):
        try:
            return cls._constants[name]
        except KeyError:
            raise ValueError("The constant value isn't valid")

class BasePrinter(BaseDevice):
    device_dirname = "printers"
    device_type = PRINTER_DEVICE

    def check_interfaces(self):
        driver_interfaces = providedBy(self._driver)
        if (not ICouponPrinter in driver_interfaces
            and not IChequePrinter in driver_interfaces):
            raise TypeError("The driver `%r' doesn't implements a valid "
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
            result[brand].append(obj)
    return result

def get_supported_printers_by_iface(interface):
    """ Returns all the printers that supports the interface.  The result
    format is the same for get_supported_printers."""
    if not interface in (ICouponPrinter, IChequePrinter):
        raise TypeError("Interface specified (`%r') is not a valid "
                        "printer interface" % interface)
    all_printers_supported = get_supported_printers()
    result = {}
    for model, driver_list in all_printers_supported.items():
        drivers = []
        for driver in driver_list:
            if interface.implementedBy(driver):
                drivers.append(driver)
        if drivers:
            result[model] = drivers
    return result
