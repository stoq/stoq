# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011 Async Open Source <http://www.async.com.br>
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
"""Test pyflakes on stoq, stoqlib and plugins directories

Useful to early find syntax errors and other common problems.
"""

import sys
import os.path

from twisted.trial import unittest
try:
    from pyflakes.scripts import pyflakes
    pyflakes # pyflakes (ironique ah?)
except ImportError:
    pyflakes = None


class TestPyflakes(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestPyflakes, self).__init__(*args, **kwargs)

    def _test_path(self, path_name):
        # Skip test if user doesn't have pyflakes installed.
        if not pyflakes:
            raise unittest.SkipTest("Pyflakes not installed")

        test_path = None
        for path in sys.path:
            if path.endswith('stoq'):
                test_path = path
                break
        self.assertTrue(test_path)

        path = os.path.join(test_path, path_name)
        retval = pyflakes.main([path])
        self.assertEqual(retval, 0)


for subpath in ('stoq', 'stoqlib', 'plugins'):
    # subpath has to be passed as a kw, or it will always be plugins (the
    # last subpath variable on for).
    func = lambda self, subpath=subpath: self._test_path(subpath)
    name = 'test_%s_pyflakes' % (subpath,)
    func.__name__ = name
    setattr(TestPyflakes, name, func)
