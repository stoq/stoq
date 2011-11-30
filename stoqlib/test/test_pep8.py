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

import pep8
from twisted.trial import unittest

import stoq

class TestPEP8(unittest.TestCase):
    def runPep8(self, path):
        result = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                if not filename.endswith('.py'):
                    continue
                filename = os.path.join(dirpath, filename)
                pep8.process_options([
                    '--repeat',
                    '--select=%s' % (','.join(ERRORS), ), filename])
                pep8.input_file(filename)
                result += pep8.get_count()

        if result:
            raise AssertionError("ERROR: %d PEP8 errors in %s" % (result, path, ))

ERRORS = [
    'E111', # indentation is not a multiple of four
    'E112', # expected an indented block
    'E113', # unexpected indentation
    'E201', # whitespace after '{'
    'E202', # whitespace before ')'
    'E203', # whitespace before ':'
    'E211', # whitespace before '('
    'E225', # missing whitespace around operator
    'E231', # E231 missing whitespace after ','/':'
    'E251', # no spaces around keyword / parameter equals
    'E262', # inline comment should start with '# '
    'W291', # trailing whitespace
    'W292', # no newline at end of file
    'W293', # blank line contains whitespace
    'W391', # blank line at end of file
    'E401', # multiple imports on one line
    'W601', # in instead of dict.has_key
    'W602', # deprecated form of raising exception
    'W603', # '<>' is deprecated, use '!='"
    'W604', # backticks are deprecated, use 'repr()'
    'E701', # multiple statements on one line (colon)
    'E702', # multiple statements on one line (semicolon)
]

root = os.path.dirname(os.path.dirname(stoq.__file__)) + '/'
for dirpath in ['stoq', 'stoqlib', 'plugins']:
    path = os.path.abspath(os.path.join(root, dirpath))
    name = 'test_%s_pep8' % (dirpath, )
    func = lambda self, path=path: self.runPep8(path)
    func.__name__ = name
    setattr(TestPEP8, name, func)
