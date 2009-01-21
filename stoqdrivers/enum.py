# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Stoqdrivers
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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
## Author(s):   Johan Dahlin                <jdahlin@async.com.br>
##
"""
StoqDrivers enums
"""

from kiwi.python import enum

class PaymentMethodType(enum):
    """
    Enum for Payment Methods
    """
    (MONEY,
     CHECK,
     BILL,
     CREDIT_CARD,
     DEBIT_CARD,
     FINANCIAL,
     GIFT_CERTIFICATE,
     CUSTOM,
     MULTIPLE) = range(9)

class UnitType(enum):
    """
    Enum for units
    """
    (WEIGHT,
     METERS,
     LITERS,
     EMPTY,
     CUSTOM) = range(20, 25)

class TaxType(enum):
    """
    Enum for taxes
    """
    (ICMS,
     SUBSTITUTION,
     EXEMPTION,
     NONE,
     SERVICE,
     CUSTOM) = range(40, 46)

class DeviceType(enum):
    """
    Enum for device types
    """

    (PRINTER,
     SCALE,
     BARCODE_READER) = range(3)

