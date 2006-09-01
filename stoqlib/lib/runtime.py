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
import sets

from kiwi.component import get_utility
from sqlobject import connectionForURI
from sqlobject.dbconnection import Transaction

from stoqlib.exceptions import StoqlibError
from stoqlib.lib.interfaces import (ICurrentBranch, ICurrentBranchStation,
                                    ICurrentUser, IDatabaseSettings)

_connection = None


#
# Working with connections and transactions
#

class StoqlibTransaction(Transaction):

    def __init__(self, *args, **kwargs):
        self._objects = sets.Set()
        Transaction.__init__(self, *args, **kwargs)

    def add_object(self, obj):
        self._objects.add(obj)

    def commit(self, close=False):
        # NotImplementedError means that there are no utility for ICurrentUser,
        # which in turn only happens during startup, for example when
        # we're creating a new database or running the migration script,
        # at that point no users are logged in
        try:
            user_id = get_current_user(self).id
        except NotImplementedError:
            user_id = None

        try:
            station_id = get_current_station(self).id
        except NotImplementedError:
            station_id = None

        for obj in self._objects:
            # FIXME: Figure out when this is needed
            if obj.sqlmeta._obsolete:
                continue
            obj.te_modified.timestamp = datetime.datetime.now()
            obj.te_modified.user_id = user_id
            obj.te_modified.station_id = station_id
        self._objects.clear()

        Transaction.commit(self, close=close)

    def rollback(self):
        self._objects.clear()
        Transaction.rollback(self)

    def close(self):
        self._connection.close()
        self._obsolete = True

def initialize_connection():
    # Avoiding circular imports
    global _connection
    assert not _connection, (
        'The connection for this application was already set.')

    try:
        db_settings = get_utility(IDatabaseSettings)
    except NotImplementedError, e:
        raise StoqlibError('You need to register db settings before calling '
                           'initialize_connection')
    # TODO if port is invalid there will be an error here
    conn = connectionForURI(db_settings.get_connection_uri())

    # Stoq applications always use transactions explicitly
    conn.autoCommit = False
    _connection = conn


def get_connection():
    """This function return the main connection with the database. If users
    would like to get another connection they should use new_transaction
    instead
    """
    global _connection
    if not _connection:
        initialize_connection()
    return _connection


def new_transaction():
    _transaction = StoqlibTransaction(get_connection())
    assert _transaction is not None
    return _transaction

#
# User methods
#

def get_current_user(conn):
    """Returns a PersonAdaptToUser instance which represents the current
    logged user on the system
    """
    user = get_utility(ICurrentUser)
    return user.get(user.id, connection=conn)

def get_current_branch(conn):
    """Returns the current branch company logged in the stoqlib applications
    """

    branch = get_utility(ICurrentBranch)
    return branch.get(branch.id, connection=conn)

def get_current_station(conn):
    """Returns the current station (computer) where the stoqlib applications
    are running on
    """
    station = get_utility(ICurrentBranchStation)
    return station.get(station.id, connection=conn)

