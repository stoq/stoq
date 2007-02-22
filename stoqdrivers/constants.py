# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Stoqdrivers
## Copyright (C) 2005,2006 Async Open Source <http://www.async.com.br>
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
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##              Henrique Romano             <henrique@async.com.br>
##
"""
StoqDrivers constants
"""

from stoqdrivers.translation import stoqdrivers_gettext

_ = lambda msg: stoqdrivers_gettext(msg)

#
# Special note regarding the constant values: it is *VERY IMPORTANT* each
# constant have an unique value. When adding new constants, add this at
# the end of the tuple, *never* at middle or top, this can break user's
# application.
#
(
    # Constants for product unit labels
    UNIT_WEIGHT,
    UNIT_METERS,
    UNIT_LITERS,
    UNIT_EMPTY,
    UNIT_CUSTOM,
    # Constants for product tax
    TAX_IOF,
    TAX_ICMS,
    TAX_SUBSTITUTION,
    TAX_EXEMPTION,
    TAX_NONE,
    # Constants for Payment Method
    MONEY_PM,
    CHEQUE_PM,
    # Constants for device types
    PRINTER_DEVICE,
    SCALE_DEVICE,
    # Custom payment method
    CUSTOM_PM,
    BARCODE_READER_DEVICE,
) = range(16)

# TODO: Improve these descriptions
_constant_descriptions = {
    UNIT_WEIGHT: _(u"Weight unit"),
    UNIT_METERS: _(u"Meters unit"),
    UNIT_LITERS: _(u"Liters unit"),
    UNIT_EMPTY: _(u"Empty unit"),
    TAX_IOF: _(u"IOF tax"),
    TAX_ICMS: _(u"ICMS tax"),
    TAX_SUBSTITUTION: _(u"Substitution tax"),
    TAX_EXEMPTION: _(u"Exemption tax"),
    TAX_NONE: _(u"No tax"),
    MONEY_PM: _(u"Money Payment Method"),
    CHEQUE_PM: _(u"Cheque Payment Method"),
    }

def describe_constant(constant_id):
    """ Given the constant identifier, return a short string describing it """
    global _constant_descriptions
    if not constant_id in _constant_descriptions:
        raise ValueError("The constant by id %r doesn't exists or there "
                         "is no description for it." % constant_id)
    return _constant_descriptions[constant_id]

