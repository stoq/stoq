# -*- Mode: Python; coding: utf-8 -*-
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

"""Database Interfaces: Connection, Settings etc
"""

# pylint: disable=E0102,E0211,E0213

from zope.interface import Attribute
from zope.interface.interface import Interface


class ICurrentBranch(Interface):
    """This is a mainly a marker for the current branch of type
    :class:`stoqlib.domain.person.Branch`
    It's mainly used by get_current_branch()
    """


class ICurrentBranchStation(Interface):
    """This is a mainly a marker for the current branch station.
    It's mainly used by get_current_station()
    """


class ICurrentUser(Interface):
    """This is a mainly a marker for the current user.
    It's mainly used by get_current_user()
    """

    username = Attribute('Username')
    pw_hash = Attribute('A hash of the user password')
    profile = Attribute('A profile represents a colection of information '
                        'which represents what this user can do in the '
                        'system')


class ISearchFilter(Interface):

    def get_state():
        """
        Gets the state.
        :rtype: :class:`QueryState`
        """

# pylint: enable=E0102,E0211,E0213
