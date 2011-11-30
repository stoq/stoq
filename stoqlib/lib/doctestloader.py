# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2007 Async Open Source <http://www.async.com.br>
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
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import doctest
import glob
import os
import sys
import unittest

_doctest_flags = doctest.ELLIPSIS | doctest.REPORT_ONLY_FIRST_FAILURE


def create_doctest(pattern):

    def _test_one(self, filename):
        failures, tries = doctest.testfile(filename, verbose=False,
                                           module_relative=False,
                                           raise_on_error=False,
                                           optionflags=_doctest_flags)
        if failures:
            raise AssertionError('%d test(s) failed in doctest %s, see above' % (
                failures, os.path.basename(filename)))

    filename = sys._getframe(1).f_code.co_filename

    namespace = dict(_test_one=_test_one)
    doctest_pattern = os.path.join(os.path.dirname(filename), pattern)
    for filename in glob.glob(doctest_pattern):
        name = 'test_' + os.path.basename(filename[:-4])
        func = lambda self, f=filename: self._test_one(f)
        namespace[name] = func
        func.__name__ = name
    return type('DocTest', (unittest.TestCase, ), namespace)

# Monkeys of all countries, unite!
# This is done so we can use ellipsis in the tests.
try:
    from twisted.trial import runner
    from twisted.trial.runner import PyUnitTestCase, TestSuite

    class DocTestSuite(TestSuite):
        def __init__(self, testModule):
            TestSuite.__init__(self)
            suite = doctest.DocTestSuite(testModule,
                                         optionflags=_doctest_flags)
            for test in suite._tests:
                self.addTest(PyUnitTestCase(test))
    runner.DocTestSuite = DocTestSuite
except ImportError:
    pass
