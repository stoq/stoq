# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

from stoqdrivers.scales.scales import Scale

from stoqlib.database.runtime import get_current_station
from stoqlib.domain.devices import DeviceSettings
from stoqlib.lib.message import warning
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

_scale = None

#
# Private
#


def _get_scale(store):
    """ Returns a Scale instance pre-configured for the current
    workstation.
    """
    global _scale
    if _scale:
        return _scale
    settings = DeviceSettings.get_scale_settings(store)
    if settings and settings.is_active:
        _scale = Scale(brand=settings.brand,
                       model=settings.model,
                       device=settings.device_name)
    else:
        warning(_(u"There is no scale configured"),
                _(u"There is no scale configured for this station "
                  "(\"%s\") or the scale is not enabled currently"
                  % get_current_station(store).name))
    return _scale


def read_scale_info(store):
    """ Read informations from the scale configured for this station.
    """
    scale = _get_scale(store)
    return scale.read_data()
