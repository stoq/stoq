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
##
""" Database access methods """

import os
import pwd
import sys
import socket

from kiwi.argcheck import argcheck
from sqlobject import connectionForURI

from stoqlib.exceptions import ConfigError
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.runtime import new_transaction, print_msg
from stoqlib.domain.tables import get_table_types

_ = stoqlib_gettext

_db_settings = None

DEFAULT_RDBMS = 'postgres'


# This class will be moved to it's proper place after bug 2253
class Adapter:
    pass

class DatabaseSettings:
    def __init__(self, rdbms=DEFAULT_RDBMS, address='localhost', port=5432,
                 dbname='stoq', username=None, password=''):
        self.rdbms = rdbms
        self.address = address
        self.port = port
        self.dbname = dbname
        if not username:
            username = pwd.getpwuid(os.getuid())[0]
        self.username = username
        self.password = password

    def get_connection_uri(self):
        return get_connection_uri(self.address, self.port, self.dbname,
                                  self.rdbms, self.username,
                                  self.password)

    def check_database_address(self):
        try:
            socket.gethostbyaddr(self.address)
        except socket.gaierror:
            return False
        return True

    def check_database_connection(self):
        """Checks the database connection according to the stored
        database settings.
        @return: a tuple with two itens where the first one is the check
                 ok status (True or False) and the second one is the error
                 message. The error message is None if the status is ok.
        """
        conn_uri = self.get_connection_uri()
        return check_database_connection(conn_uri)


def get_connection_uri(address, port, dbname, rdbms=DEFAULT_RDBMS,
                       username=None, password=''):
    if not username:
        username = pwd.getpwuid(os.getuid())[0]

    # Here we construct a uri for database access like:
    # 'postgresql://username@localhost/dbname'
    if rdbms == DEFAULT_RDBMS:
        authority = '%s:%s@%s:%s' % (username, password, address, port)
        path = '/' + dbname
    else:
        raise ConfigError("Unsupported database type: %s" % rdbms)
    return '%s://%s%s' % (rdbms, authority, path)


def check_database_connection(conn_uri):
    """Checks the database connection according to the stored
    database settings.
    @return: a tuple with two itens where the first one is the check
             ok status (True or False) and the second one is the error
             message. The error message is None if the status is ok.
    """
    try:
        conn = connectionForURI(conn_uri)
        conn.makeConnection()
    except:
        type, value, trace = sys.exc_info()
        msg = _("Could not connect to %s database. The error message is "
                "'%s'. Please fix the connection settings you have set "
                "and try again." % (DEFAULT_RDBMS, value))
        return False, msg
    return True, None


#
# General routines
#


def rollback_and_begin(conn):
    conn.rollback()
    conn.begin()

def finish_transaction(conn, model=None, keep_transaction=False):
    if model:
        conn.commit()
    else:
        rollback_and_begin(conn)
    if not keep_transaction:
        # XXX Waiting for SQLObject improvements. We need there a
        # simple method do this in a simple way.
        conn._connection.close()
    return model


def setup_tables(delete_only=False, list_tables=False, verbose=False):
    from stoqlib.lib.parameters import ParameterData
    if not list_tables and verbose:
        print_msg('Setting up tables... ', break_line=False)
    else:
        print_msg('Setting up tables... ')

    conn = new_transaction()
    # We need that since DecimalCol attributes fetch some data from this
    # table. If we are trying to initialize an existent database this table
    # can already exist and DecimalCols will get wrong data from it
    if conn.tableExists(ParameterData.get_db_table_name()):
        ParameterData.clearTable(connection=conn)
    conn.commit()
    table_types = get_table_types()
    for table in table_types:
        if conn.tableExists(table.get_db_table_name()):
            table.dropTable(ifExists=True, cascade=True, connection=conn)
            if list_tables:
                print_msg('<removed>:  %s' % table)
            conn.commit()
        if delete_only:
            continue
        table.createTable(connection=conn)
        if list_tables:
            print_msg('<created>:  %s' % table)
    conn.commit()
    if delete_only:
        return

    # Import here since we must create properly the domain schema before
    # importing them in the migration module
    from stoqlib.lib.migration import add_system_table_reference
    add_system_table_reference(conn, check_new_db=True)
    finish_transaction(conn, 1)
    print_msg('done')


@argcheck(DatabaseSettings)
def register_db_settings(db_settings):
    global _db_settings
    _db_settings = db_settings


def get_registered_db_settings():
    global _db_settings
    return _db_settings

