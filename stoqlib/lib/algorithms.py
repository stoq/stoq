# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##


# http://en.wikipedia.org/wiki/Luhn algorithm
# Also known as mod 10
def luhn(value):
    if not isinstance(value, basestring):
        raise TypeError("value must be a string, not %s" % (
            value, ))
    total = 0
    try:
        values = map(int, reversed(value))
    except ValueError:
        return None
    for i, v in enumerate(values):
        if not i % 2:
            v *= 2
        if v > 10:
            v -= 9
        total += v
    return str(10 - total % 10)

if __name__ == '__main__':
    assert luhn('810907487') == '5'
