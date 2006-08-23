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

from kiwi.log import Logger
from psycopg import ProgrammingError
from sqlobject import connectionForURI
from sqlobject.styles import mixedToUnder
from zope.interface import implements

from stoqlib.domain.tables import get_table_types, get_sequence_names
from stoqlib.exceptions import ConfigError, SQLError, StoqlibError
from stoqlib.lib.interfaces import IDatabaseSettings
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.runtime import new_transaction, set_verbose

_ = stoqlib_gettext

DEFAULT_RDBMS = 'postgres'

log = Logger('stoqlib.database')

class DatabaseSettings:
    implements(IDatabaseSettings)
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
        return build_connection_uri(self.address, self.port, self.dbname,
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


def build_connection_uri(address, port, dbname, rdbms=DEFAULT_RDBMS,
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

def setup_tables(delete_only=False, verbose=False):
    from stoqlib.domain.parameter import ParameterData
    set_verbose(verbose)
    conn = new_transaction()
    # We need that since DecimalCol attributes fetch some data from this
    # table. If we are trying to initialize an existent database this table
    # can already exist and DecimalCols will get wrong data from it
    if conn.tableExists(ParameterData.get_db_table_name()):
        ParameterData.clearTable(connection=conn)
    conn.commit()

    log.info('Dropping tables')
    table_types = get_table_types()
    for table in table_types:
        table_name = db_table_name(table)
        if conn.tableExists(table_name):
            conn.dropTable(table_name, cascade=True)

    log.info('Dropping sequences')
    for seq_name in get_sequence_names():
        if sequenceExists(conn, seq_name):
            dropSequence(conn, seq_name)

    if not delete_only:
        log.info('Creating tables')
        for table in table_types:
            table_name = db_table_name(table)
            if delete_only:
                continue
            try:
                table.createTable(connection=conn)
            except ProgrammingError, e:
                raise StoqlibError(
                    "An error occurred when creating %s table:\n"
                    "=========\n"
                    "%s\n" % (table_name, e))

        log.info('Creating sequences')
        for seq_name in get_sequence_names():
            createSequence(conn, seq_name)

    conn.commit()
    finish_transaction(conn, 1)

def db_table_name(cls):
    """
    Returns a table name for a specific class, eg SystemTable -> system_table
    @param cls: a SQLObject class
    @returns: the table name
    @rtype: string
    """
    className = cls.__name__
    return (className[0].lower() + mixedToUnder(className[1:]))
