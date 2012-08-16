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

import os

import unittest

import stoqlib
from stoqlib.lib.process import Process


class TestPylint(unittest.TestCase):
    def setUp(self):
        unittest.TestCase.setUp(self)
        self.root = os.path.dirname(
            os.path.dirname(stoqlib.__file__)) + '/'

    def test_stoqlib_domain(self):
        args = ["pylint",
                "--rcfile=%s/tools/pylint.rcfile" % (self.root,),
                "--load-plugins", "tools/pylint_stoq",
                "-E",
                "stoqlib.domain"]
        p = Process(args)
        retval = p.wait()
        if retval:
            raise Exception("Pylint errors")
