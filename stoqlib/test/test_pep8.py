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
import unittest

import mock
import pep8

import stoqlib

ERRORS = [
    'E111', # indentation is not a multiple of four
    'E112', # expected an indented block
    'E113', # unexpected indentation
    'E201', # whitespace after '{'
    'E202', # whitespace before ')'
    'E203', # whitespace before ':'
    'E211', # whitespace before '('
    'E221', # multiple spaces before operator
    'E225', # missing whitespace around operator
    'E231', # E231 missing whitespace after ','/':'
    'E241', # multiple spaces after operator
    'E251', # no spaces around keyword / parameter equals
    # pep8 needs to be updated to allow the #: syntax that that
    # sphinx.ext.autodoc uses
    # 'E262', # inline comment should start with '# '
    'W291', # trailing whitespace
    'W292', # no newline at end of file
    'W293', # blank line contains whitespace
    'E301', # expected 1 blank line, found 0
    'E302', # expected 2 blank lines, found 1
    'E303', # too many blank lines
    'W391', # blank line at end of file
    'E401', # multiple imports on one line
    'W601', # in instead of dict.has_key
    'W602', # deprecated form of raising exception
    'W603', # '<>' is deprecated, use '!='"
    'W604', # backticks are deprecated, use 'repr()'
    'E701', # multiple statements on one line (colon)
    'E702', # multiple statements on one line (semicolon)
]


class TestPEP8(unittest.TestCase):
    def setUp(self):
        self.root = os.path.dirname(
                    os.path.dirname(stoqlib.__file__)) + '/'

    @mock.patch('pep8.message')
    def test_PEP8(self, message):
        pep8.process_options([
            '--repeat',
            '--select=%s' % (','.join(ERRORS), ), self.root])
        pep8.input_dir(os.path.join(self.root, 'stoq'))
        pep8.input_dir(os.path.join(self.root, 'stoqlib'))
        result = pep8.get_count()
        msgs = []
        for call in message.call_args_list:
            msgs.append(call[0][0][len(self.root):])
        if result:
            raise AssertionError(
                "ERROR: %d PEP8 errors:\n%s" % (result, '\n'.join(msgs)))
