# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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
""" Test case for stoqlib/domain/station.py module.  """

from stoqlib.domain.station import BranchStation
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.exceptions import StoqlibError

__tests__ = 'stoqlib/domain/station.py'


class TestBranchStation(DomainTest):
    def test_check_station_exists(self):
        station = self.create_station()
        self.assertFalse(station.check_station_exists(u'foo'))

        BranchStation(name=u'foo', store=self.store)
        self.assertTrue(station.check_station_exists(u'foo'))

    def test_get_active_stations(self):
        active = self.store.find(BranchStation, is_active=True).order_by(
            BranchStation.name)
        self.assertEquals(set(BranchStation.get_active_stations(self.store)),
                          set(active))

    def test_create(self):
        branch = self.create_branch()
        BranchStation.create(self.store, branch, u'foo')
        with self.assertRaisesRegexp(
            StoqlibError, u"There is already a station registered as `foo'."):
            BranchStation.create(self.store, branch, u'foo')

    def test_get_station(self):
        with self.assertRaisesRegexp(
            TypeError, ur"BranchStation.get_station\(\) requires a Branch"):
            BranchStation.get_station(self.store, None, None)

    def test_activate(self):
        station = self.create_station()
        station.activate()
        with self.assertRaises(AssertionError):
            station.activate()
        station.inactivate()
        with self.assertRaises(AssertionError):
            station.inactivate()

    def test_get_status_string(self):
        station = self.create_station()
        self.assertEquals(station.get_status_string(), u'Inactive')
        station.activate()
        self.assertEquals(station.get_status_string(), u'Active')

    def test_get_branch_name(self):
        branch = self.create_branch()
        branch.person.company.fancy_name = u'foo'
        station = self.create_station(branch=branch)
        self.assertEquals(station.get_branch_name(), u'foo')
