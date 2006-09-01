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
## Author(s):   Johan Dahlin      <jdahlin@async.com.br>
##
""" This module test all class in stoq/domain/station.py """

import datetime
import unittest

from stoqlib.lib.runtime import new_transaction
from stoqlib.domain.synchronization import BranchSynchronization
from stoqlib.domain.person import Person
from stoqlib.domain.interfaces import IBranch, ICompany

import tests.base
tests.base #pyflakes

def get_branch(conn):
    person = Person(name='John', connection=conn)
    person.addFacet(ICompany, connection=conn)
    return person.addFacet(IBranch, connection=conn, manager=person)

class TestBranchSynchronization(unittest.TestCase):
    def test_sync(self):
        conn = new_transaction()

        branch = get_branch(conn)
        results = BranchSynchronization.select(
            BranchSynchronization.q.branchID == branch.id, connection=conn)
        self.assertEqual(results.count(), 0)

        t1 = datetime.datetime.now()
        obj = BranchSynchronization.update(branch, "shop", t1, conn)

        results = BranchSynchronization.select(
            BranchSynchronization.q.branchID == branch.id, connection=conn)
        self.assertEqual(results.count(), 1)
        self.assertEqual(results[0], obj)
        # Bug in SQLObject, we lose the precision, so filter out the microseconds
        self.assertEqual(obj.timestamp.timetuple()[:-2], t1.timetuple()[:-2])
        self.assertEqual(obj.policy, "shop")
        self.assertEqual(obj.branch, branch)

        t2 = datetime.datetime.now()
        obj = BranchSynchronization.update(branch, "shop", t2, conn)
        results = BranchSynchronization.select(
            BranchSynchronization.q.branchID == branch.id, connection=conn)
        self.assertEqual(results.count(), 1)
        self.assertEqual(results[0], obj)
        self.assertEqual(obj.timestamp.timetuple()[:-2], t2.timetuple()[:-2])
        self.assertEqual(obj.policy, "shop")
        self.assertEqual(obj.branch, branch)
