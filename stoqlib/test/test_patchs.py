# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
"""Test patchs for Stoq"""

import os

import stoqlib
import unittest
from stoqlib.lib.osutils import list_recursively

_ROOT = os.path.dirname(os.path.dirname(stoqlib.__file__))


class TestPatchs(unittest.TestCase):

    def test_duplicated(self):
        path = os.path.join(_ROOT, 'data')
        sql_patchs = set([os.path.basename(fname)[:-4] for fname in
                          list_recursively(path, '*.sql')])
        py_patchs = set([os.path.basename(fname)[:-3] for fname in
                         list_recursively(path, '*.py')])
        identical_patchs = sql_patchs & py_patchs

        if identical_patchs:
            raise AssertionError("The patchs [%s] are duplicated" %
                                 (','.join(identical_patchs,)))
