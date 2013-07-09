# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU Lesser General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
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
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import unittest

from stoqlib.lib.colorutils import get_random_color, _TANGO_PALETTE


class TestColorUtils(unittest.TestCase):
    def test_get_random_color(self):
        for i in xrange(100):
            self.assertIn(get_random_color(), _TANGO_PALETTE)

        used_colors = set()
        for i in xrange(len(_TANGO_PALETTE)):
            color = get_random_color(ignore=used_colors)
            self.assertNotIn(color, used_colors)
            self.assertIn(color, _TANGO_PALETTE)
            used_colors.add(color)

        # One last time, since all colors were used
        get_random_color(ignore=used_colors)
