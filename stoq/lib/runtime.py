# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2004 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
"""
lib/runtime.py:

    Runtime methods for Stoq applications.
"""

import sqlobject
from stoq.lib.configparser import StoqConfigParser

_connection = None
_current_user = None



#
# Work with connections and transactions
#



def initialize_connection():
    global _connection
    msg = 'The connection for this application was already set.'
    assert not _connection, msg

    domain = 'stoq'
    config = StoqConfigParser(domain, extra_sections=['Database'])

    address = config.get_database_address()
    rdbms = config.get_rdbms_name()
    dbname = config.get_dbname()
    dbusername = config.get_dbusername()

    # Here we define a full address for database access like:
    # 'postgresql://username@localhost/dbname'
    conn = sqlobject.connectionForURI('%s://%s@%s/%s' % (rdbms, 
                                      dbusername, address, dbname))
    # Stoq applications always use transactions explicitly
    conn.autoCommit = False
    _connection = conn


def get_connection():
    # There is no sense to have more than one database connection for an 
    # Stoq application. That's why we always reuse the same _connection
    # variable.
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



def get_current_user():
    global _current_user
    return _current_user


def set_current_user(user):
    global _current_user
    assert user
    # He we store a PersonAdaptToUser object.
    _current_user = user
