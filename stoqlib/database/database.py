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
from sqlobject.styles import mixedToUnder

from stoqlib.database.exceptions import ProgrammingError
from stoqlib.database.runtime import new_transaction
from stoqlib.database.tables import get_table_types, get_sequence_names
from stoqlib.exceptions import StoqlibError, SQLError
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

    entries = SystemTable.select(connection=conn).count()
    log.info('Found %d SystemTable entries' % entries)
    return entries > 0

def create_database_if_missing(conn, dbname):
    """
    Checks if there's a database present and creates a new one if it's not
    @param conn: a connection
    @param dbname: the name of the database
    @returns: True if a database was created, False otherwise
    """

    results = conn.queryOne(
        "SELECT COUNT(*) FROM pg_database WHERE datname='%s'" % dbname)

    # If it's already present, quit
    if results[0] == 1:
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
        type, value, trace = sys.exc_info()
        raise SQLError("Bad sql script, got error %s, of type %s"
                       % (value, type))

# FIXME: Move into SQLObject itself
def createSequence(conn, sequence):
    conn.query('CREATE SEQUENCE "%s"' % sequence)

def dropSequence(conn, sequence):
    conn.query('DROP SEQUENCE "%s"' % sequence)

def sequenceExists(conn, sequence):
    return conn.tableExists(sequence)

def setup_tables(delete_only=False):
    trans = new_transaction()

    log.info('Dropping tables')
    table_types = get_table_types()
    for table in table_types:
        table_name = db_table_name(table)
        if trans.tableExists(table_name):
            trans.dropTable(table_name, cascade=True)

    log.info('Dropping sequences')
    for seq_name in get_sequence_names():
        if sequenceExists(trans, seq_name):
            dropSequence(trans, seq_name)

    if not delete_only:
        log.info('Creating tables')
        for table in table_types:
            table_name = db_table_name(table)
            if delete_only:
                continue
            try:
                table.createTable(connection=trans)
            except ProgrammingError, e:
                raise StoqlibError(
                    "An error occurred when creating %s table:\n"
                    "=========\n"
                    "%s\n" % (table_name, e))

        log.info('Creating sequences')
        for seq_name in get_sequence_names():
            createSequence(trans, seq_name)

    trans.commit()
    finish_transaction(trans, 1)

def db_table_name(cls):
    """
    Returns a table name for a specific class, eg SystemTable -> system_table
    @param cls: a SQLObject class
    @returns: the table name
    @rtype: string
    """
    className = cls.__name__
    return (className[0].lower() + mixedToUnder(className[1:]))
