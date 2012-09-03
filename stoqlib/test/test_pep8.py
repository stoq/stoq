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

import os
import subprocess
import unittest
import sys

import stoqlib

ERRORS = [
    'E261', # inline comment should have two spaces before
    # pep8 needs to be updated to allow the #: syntax that that
    # sphinx.ext.autodoc uses
    'E262', # inline comment should start with '# '
    'E501', # line too long
]


class TestPEP8(unittest.TestCase):
    def setUp(self):
        self.root = os.path.dirname(
                    os.path.dirname(stoqlib.__file__)) + '/'

    def test_PEP8(self):
        cmd = [sys.executable,
               os.path.join(self.root, 'tools', 'pep8.py'),
               '--count',
               '--repeat',
               '--ignore=%s' % (','.join(ERRORS), ),
               'stoq', 'stoqlib']

        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        stdout = p.communicate()[0]
        result = p.returncode
        if result:
            raise AssertionError(
                "ERROR: %d PEP8 errors:\n%s" % (result, stdout))
