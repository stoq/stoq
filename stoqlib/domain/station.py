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
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
##  Author(s):  Evandro Vale Miquelito      <evandro@async.com.br>
##              Johan Dahlin                <jdahlin@async.com.br>
##
""" Station, a branch station per computer """

import socket

from sqlobject import UnicodeCol, ForeignKey, BoolCol
from sqlobject.sqlbuilder import AND
from zope.interface import implements

from stoqlib.domain.base import Domain
from stoqlib.domain.columns import AutoIncCol
from stoqlib.domain.interfaces import IActive, IBranch
from stoqlib.exceptions import StoqlibError
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

class BranchStation(Domain):
    """Defines a computer which access Stoqlib database and lives in a
    certain branch company
    """
    implements(IActive)

    identifier = AutoIncCol('stoqlib_branch_station_seq')
    name = UnicodeCol()
    is_active = BoolCol(default=False)
    branch = ForeignKey("PersonAdaptToBranch")

    @classmethod
    def get_active_stations(cls, conn):
        """
        Returns the currently active branch stations.
        @param conn: a database connection
        """
        return cls.select(cls.q.is_active == True, connection=conn)

    @classmethod
    def create(cls, conn, branch=None):
        """
        Create a new station id for the current machine.
        Optionally a branch can be specified which will be set as the branch
        for created station.

        @param conn: a database connection
        @param branch: Branch
        @returns: the name of the created station
        @rtype: string
        """
        from stoqlib.domain.person import Person

        if not branch:
            branches = Person.iselect(IBranch, connection=conn)
            if branches.count() != 1:
                raise StoqlibError("More than one branch detected")
            branch = branches[0]

        name = socket.gethostname()

        stations = cls.select(
            AND(cls.q.name == name,
                cls.q.branchID == branch.id), connection=conn)
        if stations.count() != 0:
            raise StoqlibError(
                "There is already a station registered as `%s'." % name)

        return cls(name=name, is_active=True, branch=branch,
                   connection=conn)

    #
    # IActive implementation
    #

    def inactivate(self):
        assert self.is_active, ('This station is already inactive')
        self.is_active = False

    def activate(self):
        assert not self.is_active, ('This station is already active')
        self.is_active = True

    def get_status_str(self):
        if self.is_active:
            return _(u'Active')
        return _(u'Inactive')

    #
    # Accessors
    #

    def get_identifier_str(self):
        return u"%05d" % self.identifier

    def get_branch_name(self):
        """
        Returns the branch name
        """
        return self.branch.get_adapted().name

# XXX: Remove and use BranchStation.create() directly
def create_station(conn, branch=None):
    return BranchStation.create(conn, branch)
