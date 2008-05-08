# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008 Async Open Source <http://www.async.com.br>
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
## Author(s):   George Y. Kussumoto <george@async.com.br>
##              Johan Dahlin  <jdahlin@async.com.br>
##

import re

from twisted.trial import unittest

from kiwi.environ import environ
from kiwi.dist import listfiles


def _get_gladefiles():
    #FIXME: environ should provide this ?
    for path in environ.get_resource_paths('glade'):
        if re.search('stoqlib', path, 1):
            return listfiles(path, '*.glade')


class TestGladeFiles(unittest.TestCase):

    def testGladeFileDomain(self):
        matcher = re.compile('^<glade-interface domain="stoqlib"', re.M)
        for gladefile in _get_gladefiles():
            contents = open(gladefile).read()
            match = re.search(matcher, contents)
            # The test is ok, but when it fails the error message does
            # help in anything!
            self.failIf(match is None)
