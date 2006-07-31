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

import socket
import unittest

from stoqlib.lib.runtime import new_transaction
from stoqlib.domain.station import BranchStation, create_station
from stoqlib.domain.person import Person
from stoqlib.domain.interfaces import IBranch, ICompany
from stoqlib.exceptions import StoqlibError

import tests.base
tests.base #pyflakes

class TestStation(unittest.TestCase):
    def setUp(self):
        self.conn = new_transaction()

    def _create_extra_branch(self):
        conn = self.conn
        person = Person(name='Dummy', connection=conn)
        person.addFacet(ICompany, fancy_name='Dummy shop', connection=conn)
        return person.addFacet(IBranch, connection=conn)

    def test_create_simple(self):
        self.assertEqual(create_station(self.conn), socket.gethostname())
        self.assertRaises(StoqlibError, create_station, self.conn)

    def test_create_branch(self):
        conn = self.conn
        branch = self._create_extra_branch()

        results = BranchStation.select(
            BranchStation.q.branchID == branch.id,
            connection=conn)
        self.assertEquals(results.count(), 0)
        create_station(conn, branch=branch)

        results = BranchStation.select(
            BranchStation.q.branchID == branch.id,
            connection=conn)
        self.assertEquals(results.count(), 1)
        self.assertEquals(results[0].name, socket.gethostname())
        self.assertEquals(results[0].branch, branch)

    def test_create_error(self):
        branch = self._create_extra_branch()
        self.assertRaises(StoqlibError, create_station, self.conn)
