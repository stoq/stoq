# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
""" This module tests stoq/database/database.py """

import unittest

from stoqlib.database.runtime import finish_transaction, rollback_and_begin


class FakeTransaction:
    def __init__(self):
        self.committed = False
        self.rollbacked = False
        self.begun = False

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rollbacked = True

    def begin(self):
        self.begun = True


class Model:
    pass


class DatabaseTest(unittest.TestCase):
    def testFinishTransaction(self):
        for item in (True, object(), Model()):
            trans = FakeTransaction()
            finish_transaction(trans, item)
            self.failUnless(trans.committed, "%s is not committed" % item)
            self.failIf(trans.begun, "%s is begun" % item)
            self.failIf(trans.rollbacked, "%s is rollbacked" % item)

        for item in (False, None):
            trans = FakeTransaction()
            finish_transaction(trans, item)
            self.failIf(trans.committed, "%s is committed" % item)
            self.failUnless(trans.begun, "%s is not begun" % item)
            self.failUnless(trans.rollbacked, "%s is not rollbacked" % item)

    def testRollBackAndBegin(self):
        trans = FakeTransaction()
        rollback_and_begin(trans)
        self.failUnless(trans.begun, "is not begun")
        self.failUnless(trans.rollbacked, "is not rollbacked")
