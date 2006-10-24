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
##              Henrique Romano   <henrique@async.com.br>
##
""" This module test all class in stoq/domain/station.py """

from stoqlib.database.exceptions import IntegrityError
from stoqlib.domain.station import BranchStation
from stoqlib.exceptions import StoqlibError
from stoqlib.lib.translation import stoqlib_gettext as _

from tests.base import DomainTest

class TestStation(DomainTest):
    name = 'test-station'

    def setUp(self):
        DomainTest.setUp(self)
        self.branch = self.create_branch()

    def test_create(self):
        results = BranchStation.selectBy(branch=self.branch,
                                         connection=self.trans)
        self.assertEquals(results.count(), 0)

        station = BranchStation.create(self.trans, self.branch, name=self.name)

        results = BranchStation.selectBy(branch=self.branch,
                                         connection=self.trans)
        self.assertEquals(results.count(), 1)
        self.assertEquals(results[0].name, self.name)
        self.assertEquals(results[0].branch, self.branch)

    def test_create_error(self):
        BranchStation.create(self.trans, self.branch, self.name)
        self.assertRaises(StoqlibError,
                          BranchStation.create, self.trans, self.branch,
                          self.name)

    def test_get_station(self):
        name = 'test-station'
        station = BranchStation.create(self.trans, self.branch, name)

        self.failUnless(isinstance(station, BranchStation),
                        ("A valid branch station should be created, "
                         "got %r instead" % station))
        self.assertRaises(IntegrityError,
                          BranchStation, name=station.name, branch=self.branch,
                          is_active=True, connection=self.trans)

    def test_get_active_stations(self):
        # Test BranchStation.get_active_stations as well inactivate and
        # activate methods
        station = BranchStation.create(self.trans, branch=self.branch,
                                       name=self.name)
        self.failUnless(
            station in BranchStation.get_active_stations(self.trans),
            "The new station %r should be active" % station)
        station.inactivate()
        self.failUnless(
            station not in BranchStation.get_active_stations(self.trans),
            "The station %r should not be active" % station)
        station.activate()
        self.failUnless(
            station in BranchStation.get_active_stations(self.trans),
            "The new station %r should be active" % station)

    def test_get_status_str(self):
        station = BranchStation.create(self.trans, branch=self.branch,
                                       name=self.name)
        station.inactivate()
        self.assertEqual(station.get_status_string(), _(u'Inactive'))

        station.activate()
        self.assertEqual(station.get_status_string(), _(u'Active'))

    def test_get_branch_name(self):
        station = BranchStation.create(self.trans, branch=self.branch,
                                       name=self.name)
        self.assertEqual(station.get_branch_name(), 'Dummy')
