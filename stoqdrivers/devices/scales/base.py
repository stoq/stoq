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
Useful functions related to all scales supported by stoqdrivers
"""

import os

from kiwi.python import namedAny
from zope.interface import providedBy

from stoqdrivers.utils import get_module_list
from stoqdrivers.devices import scales
from stoqdrivers.devices.interfaces import IScale
from stoqdrivers.devices.base import BaseDevice
from stoqdrivers.enum import DeviceType

class BaseScale(BaseDevice):
    device_dirname = "scales"
    device_type = DeviceType.SCALE

    def check_interfaces(self):
        driver_interfaces = providedBy(self._driver)
        if not IScale in driver_interfaces:
            raise TypeError("This driver doesn't implements a valid "
                            "interface")

def get_supported_scales():
    scales_dir = os.path.dirname(scales.__file__)
    result = {}

    for brand in os.listdir(scales_dir):
        brand_dir = os.path.join(scales_dir, brand)
        if (not os.path.isdir(brand_dir)) or brand.startswith("."):
            continue
        result[brand] = []
        for module_name in get_module_list(brand_dir):
            try:
                obj = namedAny("stoqdrivers.devices.scales.%s.%s.%s"
                               % (brand, module_name, module_name))
            except AttributeError:
                raise ImportError("Can't find class %s for module %s"
                                  % (module_name, module_name))
            if not IScale.implementedBy(obj):
                raise TypeError("The driver %s %s doesn't implements a "
                                "valid interface"
                                % (brand, obj.model_name))
            result[brand].append(obj)
    return result
