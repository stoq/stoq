# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005,2006 Async Open Source
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
##
""" Database access methods """

# FIXME: Refactor this to other files

import sys

from kiwi.log import Logger

from stoqlib.exceptions import SQLError
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

log = Logger('stoqlib.database')

def check_installed_database(conn):
    """Checks if Stoqlib database is properly installed"""
    from stoqlib.domain.system import SystemTable
    table_name = SystemTable.get_db_table_name()
    if not conn.tableExists(table_name):
        log.info('There is no table called %s' % table_name)
        return False

    return bool(SystemTable.select(connection=conn))

def database_exists(conn, dbname):
    """ Given a database name, returns True if it exists, False otherwise
    """
    results = conn.queryOne(
        "SELECT COUNT(*) FROM pg_database WHERE datname='%s'" % dbname)
    return results[0] == 1

def drop_database(conn, dbname):
    """ Try to drop the specified database, also check if the database
    exists before apply the drop command. """
    if not database_exists(conn, dbname):
        return
    pgconn = conn.getConnection()
    curs = pgconn.cursor()
    curs.execute('commit')
    log.info('Dropping SQL database: %s' % dbname)
    curs.execute('DROP DATABASE %s' % dbname)

def create_database_if_missing(conn, dbname):
    """
    Checks if there's a database present and creates a new one if it's not
    @param conn: a connection
    @param dbname: the name of the database
    @returns: True if a database was created, False otherwise
    """
    if database_exists(conn, dbname):
        return False

    # We need to close the current transaction, which is probably created
    # by SQLObject somehow, the only way to do that is to fetch the psycopg
    # connection, get the cursor and run the 'commit' statement
    pgconn = conn.getConnection()
    curs = pgconn.cursor()
    curs.execute('commit')

    log.info('Creating SQL database: %s' % dbname)
    curs.execute('CREATE DATABASE %s' % dbname)

    return True

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
        conn.close()
    return model


def run_sql_file(sql_file, conn):
    """This method takes a full sql_file name and run it in a given
    connection
    """
    file_data = open(sql_file).read()
    try:
        conn.query(file_data)
    except:
        type, value = sys.exc_info()[:2]
        raise SQLError("Bad sql script, got error %s, of type %s"
                       % (value, type))

def db_table_name(cls):
    """
    Returns a table name for a specific class, eg SystemTable -> system_table
    @param cls: a SQLObject class
    @returns: the table name
    @rtype: string
    """
    return cls.sqlmeta.table
