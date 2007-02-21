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
from sqlobject.sqlbuilder import sqlIdentifier

from stoqlib.database.interfaces import (
    IDatabaseSettings, IConnection, ITransaction, ICurrentBranch,
    ICurrentBranchStation, ICurrentUser)
from stoqlib.exceptions import StoqlibError
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
        self._modified_object_sets = [set()]
        self._savepoints = []
        Transaction.__init__(self, *args, **kwargs)

    def add_object(self, obj):
        objset = self._modified_object_sets[-1]
        objset.add(obj)

    def commit(self, close=False):
        user = get_current_user(self)
        station = get_current_station(self)

        for objset in self._modified_object_sets:
            for obj in objset:
                # FIXME: Figure out when this is needed
                if obj.sqlmeta._obsolete:
                    continue

                obj.te_modified.te_time = datetime.datetime.now()
                if user is not None:
                    obj.te_modified.user_id = user.id
                if station is not None:
                    obj.te_modified.station_id = station.id
        self._modified_object_sets = [set()]

        Transaction.commit(self, close=close)

    def rollback(self, name=None):
        if name:
            self.rollback_to_savepoint(name)
        else:
            # FIXME: SQLObject is busted, this is called from __del__
            if Transaction is not None:
                Transaction.rollback(self)
            self._modified_object_sets = [set()]

    def close(self):
        self._connection.close()
        self._obsolete = True

    def get(self, obj):
        if not isinstance(obj, (SQLObject, InheritableSQLObject)):
            raise TypeError("obj must be a SQLObject")

        table = type(obj)
        return table.get(obj.id, connection=self)

    def savepoint(self, name):
        if not sqlIdentifier(name):
            raise ValueError("Invalid savepoint name: %r" % name)
        self.query('SAVEPOINT %s' % name)
        self._modified_object_sets.append(set())
        if not name in self._savepoints:
            self._savepoints.append(name)

    def rollback_to_savepoint(self, name):
        if not sqlIdentifier(name):
            raise ValueError("Invalid savepoint name: %r" % name)
        if not name in self._savepoints:
            raise ValueError("Unknown savepoint: %r" % name)

        self.query('ROLLBACK TO SAVEPOINT %s' % name)
        self._modified_object_sets.pop()
        self._savepoints.remove(name)

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
    station = BranchStation.selectOneBy(name=station_name, connection=conn)
    if station is None:
        error(_("The computer <u>%s</u> is not registered in Stoq") %
              station_name,
              _("To solve this, open the administrator application "
                "and register this computer."))

    if not station.is_active:
        error(_("The computer <u>%s</u> is not active in Stoq") %
              station_name,
              _("To solve this, open the administrator application "
                "and re-activate this computer."))

    provide_utility(ICurrentBranchStation, station)
    provide_utility(ICurrentBranch, station.branch)

def get_current_user(conn):
    """
    Fetch the user which is currently logged into the system or None
    None means that there are no utilities available which in turn
    should only happens during startup, for example when creating
    a new database or running the migration script,
    at that point no users are logged in

    @returns: currently logged in user or None
    @rtype: an object implementing IUser
    """
    user = get_utility(ICurrentUser, None)
    if user is not None:
        return user.get(user.id, connection=conn)

def get_current_branch(conn):
    """
    Fetches the current branch company.

    @returns: the current branch
    @rtype: an object implementing IBranch
    """

    branch = get_utility(ICurrentBranch, None)
    if branch is not None:
        return branch.get(branch.id, connection=conn)

def get_current_station(conn):
    """
    Fetches the current station (computer) which we are running on
    @param: current station
    @rtype: BranchStation
    """
    station = get_utility(ICurrentBranchStation, None)
    if station is not None:
        return station.get(station.id, connection=conn)

