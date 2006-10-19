# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU Lesser General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
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
##
## Author(s):       Evandro Vale Miquelito      <evandro@async.com.br>
##                  Johan Dahlin                <jdahlin@async.com.br>
##
""" Runtime routines for applications"""

import datetime
import sys

from kiwi.component import get_utility, provide_utility, implements
from kiwi.log import Logger
from sqlobject.dbconnection import Transaction
from sqlobject.inheritance import InheritableSQLObject
from sqlobject.main import SQLObject

from stoqlib.exceptions import StoqlibError
from stoqlib.lib.interfaces import (ICurrentBranch, ICurrentBranchStation,
                                    ICurrentUser, IDatabaseSettings,
                                    IConnection, ITransaction)
from stoqlib.lib.message import error
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext
log = Logger('stoqlib.runtime')

#
# Working with connections and transactions
#

class StoqlibTransaction(Transaction):
    implements(ITransaction)

    def __init__(self, *args, **kwargs):
        self._objects = set()
        Transaction.__init__(self, *args, **kwargs)

    def add_object(self, obj):
        self._objects.add(obj)

    def commit(self, close=False):
        # None means that there are no utilities available which in turn
        # should only happens during startup, for example when
        # we're creating a new database or running the migration script,
        # at that point no users are logged in
        user = get_current_user(self)
        station = get_current_station(self)

        for obj in self._objects:
            # FIXME: Figure out when this is needed
            if obj.sqlmeta._obsolete:
                continue

            obj.te_modified.timestamp = datetime.datetime.now()
            if user is not None:
                obj.te_modified.user_id = user.id
            if station is not None: 
                obj.te_modified.station_id = station.id
        self._objects.clear()

        Transaction.commit(self, close=close)

    def rollback(self):
        self._objects.clear()

        # FIXME: SQLObject is busted, this is called from __del__
        if Transaction is not None:
            Transaction.rollback(self)

    def close(self):
        self._connection.close()
        self._obsolete = True

    def get(self, obj):
        if not isinstance(obj, (SQLObject, InheritableSQLObject)):
            raise TypeError("obj must be a SQLObject")

        table = type(obj)
        return table.get(obj.id, connection=self)

def get_connection():
    """
    This function returns a connection to the current database.
    Notice that connections are considered read-only inside Stoqlib
    applications. Only transactions can modify objects and should be
    created using new_transaction().
    This function depends on the IDatabaseSettings utility which must be
    provided before it can be used.

    @returns: a database connection
    """
    conn = get_utility(IConnection, None)
    if conn is None:
        try:
            settings = get_utility(IDatabaseSettings)
        except NotImplementedError:
            raise StoqlibError(
                'You need to provide a IDatabaseSettings utility before '
                'calling get_connection')
        conn = settings.get_connection()
        assert conn is not None

        # Stoq applications always use transactions explicitly
        conn.autoCommit = False

        provide_utility(IConnection, conn)
    return conn

def new_transaction():
    log.debug('Creating a new transaction in %s()'
              % sys._getframe(1).f_code.co_name)
    _transaction = StoqlibTransaction(get_connection())
    assert _transaction is not None
    return _transaction

#
# User methods
#

def set_current_branch_station(conn, station_name):
    """
    Registers the current station and the branch of the station
    as the current branch for the system
    @param conn: a database connection
    @param station_name: name of the station to register
    """
    from stoqlib.domain.station import BranchStation
    stations = BranchStation.select(
        BranchStation.q.name == station_name, connection=conn)
    if not stations:
        error(_("The computer <u>%s</u> is not registered in Stoq") %
              station_name,
              _("To solve this, open the administrator application "
                "and register this computer."))
    station = stations[0]

    if not station.is_active:
        error(_("The computer <u>%s</u> is not active in Stoq") %
              station_name,
              _("To solve this, open the administrator application "
                "and re-activate this computer."))

    provide_utility(ICurrentBranchStation, station)
    provide_utility(ICurrentBranch, station.branch)

def get_current_user(conn):
    """Returns a PersonAdaptToUser instance which represents the current
    logged user on the system
    """
    user = get_utility(ICurrentUser, None)
    if user is not None:
        return user.get(user.id, connection=conn)

def get_current_branch(conn):
    """Returns the current branch company logged in the stoqlib applications
    """

    branch = get_utility(ICurrentBranch, None)
    if branch is not None:
        return branch.get(branch.id, connection=conn)

def get_current_station(conn):
    """Returns the current station (computer) where the stoqlib applications
    are running on
    """
    station = get_utility(ICurrentBranchStation, None)
    if station is not None:
        return station.get(station.id, connection=conn)

