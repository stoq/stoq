# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005 Async Open Source
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
##
""" Runtime routines for applications"""

import sys
from datetime import datetime

from kiwi.component import get_utility
from sqlobject import connectionForURI
from sqlobject.dbconnection import Transaction

from stoqlib.lib.interfaces import (ICurrentBranch, ICurrentBranchStation,
                                    ICurrentUser)

_connection = None
_verbose = False


#
# Working with connections and transactions
#

class StoqlibTransaction(Transaction):

    def __init__(self, *args, **kwargs):
        self._change_data = []
        Transaction.__init__(self, *args, **kwargs)

    def update_change_data(self, new_obj):
        obj_ids = [id(obj) for obj in self._change_data]
        if id(new_obj) not in obj_ids:
            self._change_data.append(new_obj)

    def commit(self, *args, **kwargs):
        # XXX: we may be missing a utility at this point, because
        #      things might be committed during startup, before
        #      a user is logged in (and a utility is provided)
        #      Migration and parameter updates
        try:
            current_user = get_current_user(get_connection())
        except NotImplementedError:
            current_user = None

        for obj in self._change_data:
            if obj.sqlmeta._obsolete:
                continue
            obj.model_modified = datetime.now()
            if current_user is not None:
                obj.last_user_id = current_user.id
        Transaction.commit(self, *args, **kwargs)
        self._change_data = []

    def rollback(self, *args, **kwargs):
        self._change_data = []
        Transaction.rollback(self, *args, **kwargs)

    def close(self):
        self._connection.close()
        self._obsolete = True


def initialize_connection():
    # Avoiding circular imports
    from stoqlib.database import get_registered_db_settings
    global _connection
    assert not _connection, (
        'The connection for this application was already set.')

    db_settings = get_registered_db_settings()
    assert db_settings, ('You need to register db settings before calling '
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

def set_verbose(verbose_value):
    global _verbose
    _verbose = verbose_value


def print_immediately(message, break_line=True):
    if break_line:
        print message
    else:
        print message,
    sys.stdout.flush()


def print_msg(message, break_line=True):
    global _verbose
    if not _verbose:
        return
    print_immediately(message, break_line)

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

