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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Station, a branch station per computer """

from zope.interface import implements

from stoqlib.database.orm import UnicodeCol, ForeignKey, BoolCol
from stoqlib.domain.base import Domain
from stoqlib.domain.event import Event
from stoqlib.domain.interfaces import IActive, IBranch
from stoqlib.exceptions import StoqlibError
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class BranchStation(Domain):
    """Defines a computer which access Stoqlib database and lives in a
    certain branch company
    """
    implements(IActive)

    name = UnicodeCol(unique=True)
    is_active = BoolCol(default=False)
    branch = ForeignKey("PersonAdaptToBranch")

    # Public

    @classmethod
    def get_active_stations(cls, conn):
        """Returns the currently active branch stations.
        @param conn: a database connection
        @returns: a sequence of currently active stations
        """
        return cls.selectBy(is_active=True, connection=conn)

    @classmethod
    def create(cls, conn, branch, name):
        """Create a new station id for the current machine.
        Optionally a branch can be specified which will be set as the branch
        for created station.

        @param conn: a database connection
        @param branch: the branch
        @param name: name of the station
        @returns: a BranchStation instance
        """

        if cls.get_station(conn, branch, name):
            raise StoqlibError(
                _("There is already a station registered as `%s'.") % name)
        return cls(name=name, is_active=True, branch=branch,
                   connection=conn)

    def check_station_exists(self, name):
        """Returns True if we already have a station with the given name
        """
        # FIXME: We should allow computers with the same on different
        # branches.
        return self.check_unique_value_exists('name', name)

    @classmethod
    def get_station(cls, conn, branch, name):
        """Fetches a station from a branch

        @param conn: a database connection
        @param branch: the branch
        @param name: name of the station
        """

        if IBranch(branch, None) is None:
            raise TypeError("%r must implemented IBranch" % (branch, ))
        return cls.selectOneBy(name=name, branch=branch, connection=conn)

    # Events

    def on_create(self):
        # Should be done after_create()
        return
        Event.log(Event.TYPE_SYSTEM,
                  _("Created computer '%s' for branch '%s'") % (
                       self.name, self.branch.person.name))

    #
    # IActive implementation
    #

    def inactivate(self):
        assert self.is_active, ('This station is already inactive')
        self.is_active = False

    def activate(self):
        assert not self.is_active, ('This station is already active')
        self.is_active = True

    def get_status_string(self):
        if self.is_active:
            return _(u'Active')
        return _(u'Inactive')

    #
    # Accessors
    #

    def get_branch_name(self):
        """Returns the branch name
        """
        return self.branch.get_description()
