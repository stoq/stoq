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

from stoqdrivers.devices.printers.interface import (ICouponPrinter,
                                                    IChequePrinter)
from stoqdrivers.devices.printers.base import get_supported_printers_by_iface

# TODO: Check for other devices types? (Scales?)

def check():
    for iface in (ICouponPrinter, IChequePrinter):
        printers = get_supported_printers_by_iface(iface)
        print "\n\nChecking drivers that implements %s..." % iface.__name__
        for brand in printers:
            print "\n\tChecking %s printers:" % brand
            for model in printers[brand]:
                print "\t\t%s" % model.model_name,
                try:
                    verifyClass(iface, model)
                except Invalid, e:
                    print "ERROR:", e
                else:
                    print "OK"

if __name__ == "__main__":
    check()

