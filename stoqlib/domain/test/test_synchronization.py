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
""" This module test all class in stoq/domain/station.py """

import datetime

from stoqlib.domain.synchronization import BranchSynchronization

from stoqlib.domain.test.domaintest import DomainTest


class TestBranchSynchronization(DomainTest):
    def setUp(self):
        DomainTest.setUp(self)
        self.branch = self.create_branch()

    def test_sync(self):
        results = BranchSynchronization.select(
            BranchSynchronization.q.branchID == self.branch.id,
            connection=self.trans)
        self.assertEqual(results.count(), 0)

        t1 = datetime.datetime.now()
        obj = BranchSynchronization(branch=self.branch,
                                    policy="shop",
                                    sync_time=t1,
                                    connection=self.trans)

        results = BranchSynchronization.select(
            BranchSynchronization.q.branchID == self.branch.id,
            connection=self.trans)
        self.assertEqual(results.count(), 1)
        self.assertEqual(results[0], obj)
        self.assertEqual(obj.sync_time, t1)
        self.assertEqual(obj.policy, "shop")
        self.assertEqual(obj.branch, self.branch)

        t2 = datetime.datetime.now()
        obj.sync_time = t2

        results = BranchSynchronization.select(
            BranchSynchronization.q.branchID == self.branch.id,
            connection=self.trans)
        self.assertEqual(results.count(), 1)
        self.assertEqual(results[0], obj)
        self.assertEqual(obj.sync_time, t2)
        self.assertEqual(obj.policy, "shop")
        self.assertEqual(obj.branch, self.branch)
