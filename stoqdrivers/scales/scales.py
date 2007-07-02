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
## Author(s):   Henrique Romano  <henrique@async.com.br>
##
"""
Base class implementation for all the scales drivers.
"""

from stoqdrivers.scales.base import BaseScale

#
# Scale interface
#

class Scale(BaseScale):
    def read_data(self):
        return self._driver.read_data()

def test():
    scale = Scale()

    print "Waiting for scale reply... "
    data = scale.read_data()
    print "...ok"
    print "Weight: %.02f" % data.weight
    print "Price per Kg: %.02f" % data.price_per_kg
    print "Total price: %.02f" % data.total_price

if __name__ == "__main__":
    test()
