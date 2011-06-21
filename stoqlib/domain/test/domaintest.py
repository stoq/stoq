# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2007 Async Open Source <http://www.async.com.br>
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
""" Base module to be used by all domain test modules"""

from stoqlib.database.runtime import new_transaction
from stoqlib.domain.exampledata import ExampleCreator

try:
    from twisted.trial import unittest
    unittest # pyflakes
except:
    import unittest


class DomainTest(unittest.TestCase, ExampleCreator):
    def __init__(self, test):
        unittest.TestCase.__init__(self, test)
        ExampleCreator.__init__(self)

    def setUp(self):
        self.trans = new_transaction()
        self.set_transaction(self.trans)

    def tearDown(self):
        self.trans.rollback()
        self.clear()


# Ensure that the database settings and etc are available for all
# the domain tests
import tests.base
tests.base # pyflakes
