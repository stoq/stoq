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

__tests__ = 'stoqlib.lib.stringutils'

import unittest

from stoqlib.lib.stringutils import next_value_for, max_value_for


class TestStringUtils(unittest.TestCase):
    def test_next_value_for(self):
        # Trivial cases
        self.assertEqual(next_value_for(u''), u'1')
        self.assertEqual(next_value_for(u'1'), u'2')
        self.assertEqual(next_value_for(u'999'), u'1000')

        # Ending with digit cases
        self.assertEqual(next_value_for(u'A999'), u'A1000')
        self.assertEqual(next_value_for(u'A8'), u'A9')
        self.assertEqual(next_value_for(u'A9'), u'A10')
        self.assertEqual(next_value_for(u'A99'), u'A100')
        self.assertEqual(next_value_for(u'A199'), u'A200')
        self.assertEqual(next_value_for(u'999A1'), u'999A2')
        self.assertEqual(next_value_for(u'A009'), u'A010')
        self.assertEqual(next_value_for(u'AB0099'), u'AB0100')

        # Ending with alphanumeric cases
        self.assertEqual(next_value_for(u'999A'), u'999B')
        self.assertEqual(next_value_for(u'A999A'), u'A999B')
        self.assertEqual(next_value_for(u'A99AZ'), u'A99B0')
        self.assertEqual(next_value_for(u'A999Z'), u'A10000')
        self.assertEqual(next_value_for(u'A999-A'), u'A999-B')
        self.assertEqual(next_value_for(u'A999-Z'), u'A999-00')

        # Not handled cases
        self.assertEqual(next_value_for(u'A999-'), u'A999-0')

    def test_max_value_for(self):
        self.assertEqual(max_value_for([u'']), u'')
        self.assertEqual(max_value_for([u'1']), u'1')
        self.assertEqual(max_value_for([u'1', u'2']), u'2')
        self.assertEqual(max_value_for([u'9', u'10']), u'10')
        self.assertEqual(max_value_for([u'009', u'10']), u'010')
        self.assertEqual(max_value_for([u'a09', u'999']), u'a09')
