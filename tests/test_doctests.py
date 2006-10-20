# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s):   Johan Dahlin  <jdahlin@async.com.br>
##

import doctest
import os
import sys
import unittest

# So we can use database connections in doctests.
import tests.base
tests.base # pyflakes

flags = doctest.ELLIPSIS | doctest.REPORT_ONLY_FIRST_FAILURE

def _test_one(self, filename):
    failures, tries = doctest.testfile(filename, verbose=False,
                                       module_relative=False,
                                       raise_on_error=False,
                                       optionflags=flags)
    if failures:
        raise AssertionError('%d test(s) failed in doctest %s, see above' % (
            failures, os.path.basename(filename)))

test_dir = os.path.dirname(__file__)
doctest_dir = os.path.join(test_dir, 'doctests')
namespace = {}
namespace['_test_one'] = _test_one
for filename in os.listdir(doctest_dir):
    if not filename.endswith('.txt'):
        continue
    full = os.path.join(doctest_dir, filename)
    name = 'test_' + filename[:-4]
    namespace[name] = lambda self, f=full: self._test_one(f)

# FIXME: Trials coverage does not like this test; figure out why
if not '--coverage' in sys.argv:
    DocTest = type('DocTest', (unittest.TestCase,), namespace)
