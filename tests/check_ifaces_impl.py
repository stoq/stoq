#!/usr/bin/env python
# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Stoqdrivers
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
## Author(s):   Henrique Romano        <henrique@async.com.br>
##
""" This is a simple module to check if all the drivers implements properly
its interfaces. """
from zope.interface.verify import verifyClass
from zope.interface.exceptions import Invalid

from stoqdrivers.interfaces import (ICouponPrinter,
                                    IChequePrinter,
                                    IScale)
from stoqdrivers.printers.base import get_supported_printers_by_iface
from stoqdrivers.scales.base import get_supported_scales

def _check_drivers(iface, brand, drivers):
    print "\t- Checking %s devices:" % brand
    for driver in drivers:
        print "\t\t- %s\n" % driver.model_name,
        try:
            verifyClass(iface, driver)
        except Invalid, e:
            print "ERROR: ", e

def _check_printers(iface):
    printers_dict = get_supported_printers_by_iface(iface)
    for brand, drivers in printers_dict.items():
        _check_drivers(iface, brand, drivers)

def check_coupon_printers():
    print "Checking Coupon Printers..."
    _check_printers(ICouponPrinter)

def check_cheque_printers():
    print "Checking Cheque Printers..."
    _check_printers(IChequePrinter)

def check_scales():
    print "Checking Scales..."
    for brand, drivers in get_supported_scales().items():
        _check_drivers(IScale, brand, drivers)

if __name__ == "__main__":
    check_coupon_printers()
    check_cheque_printers()
    check_scales()

