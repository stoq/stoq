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

import subprocess

from kiwi.component import get_utility
from kiwi.log import Logger

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.interfaces import IDatabaseSettings
from stoqlib.lib.message import error

_ = stoqlib_gettext

log = Logger('stoqlib.database')

def check_installed_database(conn):
    """
    Checks if Stoqlib database is properly installed
    @param conn: a database connection
    """
    from stoqlib.domain.system import SystemTable
    table_name = SystemTable.sqlmeta.table
    if not conn.tableExists(table_name):
        log.info('There is no table called %s' % table_name)
        return False

    return bool(SystemTable.select(connection=conn))

def database_exists(conn, dbname):
    """
    Given a database name, returns True if it exists, False otherwise
    @param conn: a database connection
    @param dbname: name of the database
    @returns: if the database exists
    """
    results = conn.queryOne(
        "SELECT COUNT(*) FROM pg_database WHERE datname='%s'" % dbname)
    return results[0] == 1

def drop_database(conn, dbname):
    """
    Drop the specified database
    @param conn: a database connection
    @param dbname: name of the database
    """
    pgconn = conn.getConnection()
    curs = pgconn.cursor()
    curs.execute('commit')

    log.info('Dropping SQL database: %s' % dbname)
    curs.execute('DROP DATABASE %s' % dbname)

def create_database(conn, dbname):
    """
    Create the specified database
    @param conn: a database connection
    @param dbname: name of the database
    """

    # We need to close the current transaction, which is probably created
    # by SQLObject somehow, the only way to do that is to fetch the psycopg
    # connection, get the cursor and run the 'commit' statement
    pgconn = conn.getConnection()
    curs = pgconn.cursor()
    curs.execute('commit')

    log.info('Creating SQL database: %s' % dbname)
    curs.execute('CREATE DATABASE %s' % dbname)

def create_database_if_missing(conn, dbname):
    """
    Checks if there's a database present and creates a new one if it's not
    @param conn: a connection
    @param dbname: the name of the database
    @returns: True if a database was created, False otherwise
    """
    if database_exists(conn, dbname):
        return False

    create_database(conn, dbname)

    return True

def clean_database(dbname):
    """
    Cleans a database
    @param dbname: name of the database
    """

    settings = get_utility(IDatabaseSettings)
    conn = settings.get_default_connection()
    if database_exists(conn, dbname):
        drop_database(conn, dbname)

    create_database(conn, dbname)
    conn.close()

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


def execute_sql(filename):
    """
    Inserts Raw SQL commands into the database read from a file.
    @param filename: filename with SQL commands
    """
    settings = get_utility(IDatabaseSettings)
    cmd = ("psql -n -h %(address)s -p %(port)s %(dbname)s -q "
           "--variable ON_ERROR_STOP= -f \"%(schema)s\"")% dict(
        address=settings.address,
        port=settings.port,
        dbname=settings.dbname,
        schema=filename)

    log.debug('sql_prepare: executing %s' % cmd)
    proc = subprocess.Popen(cmd, shell=True,
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE)
    returncode = proc.wait()
    if returncode != 0:
        error('psql returned error code %d' % returncode)

