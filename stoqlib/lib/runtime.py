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

from sqlobject import connectionForURI
from kiwi.argcheck import argcheck

_connection = None
_current_user = None
_verbose = False
_test_mode = False
_app_names = None
_database_settings = None


#
# Working with connections and transactions
#

def initialize_connection():
    # Avoiding circular imports
    from stoqlib.database import get_registered_db_settings
    global _connection
    msg = 'The connection for this application was already set.'
    assert not _connection, msg

    db_settings = get_registered_db_settings()
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
    _transaction = get_connection().transaction()
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


def get_current_user():
    global _current_user
    return _current_user


def set_current_user(user):
    global _current_user
    assert user
    # Here we store a PersonAdaptToUser object.
    _current_user = user


@argcheck(list)
def register_application_names(app_names):
    global _app_names
    _app_names = app_names

def get_application_names():
    global _app_names
    return _app_names
