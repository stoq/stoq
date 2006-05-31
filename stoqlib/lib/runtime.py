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

from sqlobject import connectionForURI
from sqlobject.dbconnection import Transaction
from kiwi.argcheck import argcheck

from stoqlib.exceptions import StoqlibError

_connection = None
_current_user = None
_current_branch_identifier = None
_current_station_identifier = None
_verbose = False
_test_mode = False
_app_names = None
_database_settings = None


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
        current_user = get_current_user(get_connection())
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
    from stoqlib.domain.person import Person
    from stoqlib.domain.interfaces import IUser
    global _current_user
    if _current_user is None:
        return
    return Person.iget(IUser, _current_user.id, connection=conn)


def set_current_user(user):
    """Sets a PersonAdaptToUser instance which represents the current
    logged user on the system
    """
    global _current_user
    assert user
    _current_user = user

@argcheck(list)
def register_application_names(app_names):
    global _app_names
    _app_names = app_names

def get_application_names():
    global _app_names
    return _app_names


#
# Managing Stations and Branch Companies
#


def _get_data_by_identifier(identifier, table, conn):
    if not identifier > 0:
        raise StoqlibError("You should have a valid registered identifier "
                           "at this point")

    items = table.selectBy(identifier=identifier, connection=conn)
    qty = items.count()
    if qty != 1:
        raise StoqlibError("You should have only one item for the "
                           "registered identifier %d, got %d"
                           % (identifier, qty))
    return items[0]


@argcheck(int)
def register_current_branch_identifier(identifier):
    """Register the current branch company which is using the system by its
    identifier attribute value
    """
    global _current_branch_identifier
    _current_branch_identifier = identifier


def get_current_branch(conn):
    """Returns the current branch company logged in the stoqlib applications
    """
    from stoqlib.domain.person import PersonAdaptToBranch
    global _current_branch_identifier
    return _get_data_by_identifier(_current_branch_identifier,
                                   PersonAdaptToBranch, conn)


@argcheck(int)
def register_current_station_identifier(identifier):
    """Register the current branch company which is using the system by its
    identifier attribute value
    """
    global _current_station_identifier
    _current_station_identifier = identifier


def get_current_station(conn):
    """Returns the current station (computer) where the stoqlib applications
    are running on
    """
    from stoqlib.domain.person import BranchStation
    global _current_station_identifier
    return _get_data_by_identifier(_current_station_identifier,
                                   BranchStation, conn)
