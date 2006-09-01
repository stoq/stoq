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

import os
import pwd
import sys
import socket

from kiwi.log import Logger
from sqlobject import connectionForURI
from sqlobject.styles import mixedToUnder
from zope.interface import implements

from stoqlib.domain.tables import get_table_types, get_sequence_names
from stoqlib.exceptions import ConfigError, DatabaseError, SQLError
from stoqlib.exceptions import StoqlibError
from stoqlib.lib.interfaces import IDatabaseSettings
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.runtime import new_transaction

_ = stoqlib_gettext

DEFAULT_RDBMS = 'postgres'

log = Logger('stoqlib.database')

# Exported exceptions
try:
    import psycopg2 as psycopg
    log.info('Using psycopg2')
    # pyflakes
    psycopg
except ImportError:
    import psycopg
    log.info('Using psycopg')

PostgreSQLError = psycopg.Error
IntegrityError = psycopg.IntegrityError
ProgrammingError = psycopg.ProgrammingError
OperationalError = psycopg.OperationalError

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

    def _get_connection_uri_internal(self, dbname):
        # Here we construct a uri for database access like:
        # 'postgresql://username@localhost/dbname'
        if self.rdbms != DEFAULT_RDBMS:
            raise ConfigError("Unsupported database type: %s" % self.rdbms)

        authority = '%s:%s@%s:%s' % (
            self.username, self.password, self.address, self.port)
        if dbname is None:
            # template1 is a special database which is always present in 7.4
            # and later which we current depend on. When we upgrade the
            # dependency to 8.1 we can switch this to `postgres'
            dbname = 'template1'

        return '%s://%s/%s' % (self.rdbms, authority, dbname)

    def _get_connection_internal(self, dbname):
        conn_uri = self._get_connection_uri_internal(dbname)
        log.info('connecting to %s' % conn_uri)
        try:
            conn = connectionForURI(conn_uri)
            conn.makeConnection()
        except OperationalError, e:
            log.info('OperationalError: %s' % e)
            if 'does not exist' in e.args[0]:
                return None
            elif 'password authentication failed for user' in e.args[0]:
                raise DatabaseError(
                    _("Password authentication failed"),
                    _("The provided password for user %s was not correct") % self.username)
            elif 'no password supplied' in e.args[0]:
                raise DatabaseError(
                    _("Invalid authentication mechanism"),
                    _("Trust was selected but the database does "
                      "only support password authentication."))
            raise
        except Exception, e:
            value = sys.exc_info()[1]
            raise DatabaseError(
                _("Could not connect to %s database. The error message is "
                  "'%s'. Please fix the connection settings you have set "
                  "and try again." % (DEFAULT_RDBMS, value)))
        return conn

    # Public API

    def get_connection_uri(self):
        """
        Returns a uri representing the current database settings.
        It's used by SQLObject to connect to a database.
        @returns: a string like postgresql://username@localhost/dbname
        """
        return self._get_connection_uri_internal(self.dbname)

    def get_connection(self):
        """
        Returns a connection to the configured database
        @returns: a database connection
        """
        return self._get_connection_internal(self.dbname)

    def get_default_connection(self):
        """
        Returns a connection to the default database, note that this
        different from the configred.
        This method is mainly here to able to create other databases,
        which will need a connection, Be careful when using this method.
        @returns: a database connection
        """
        return self._get_connection_internal(None)

    # FIXME: Remove/Rethink these two
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

    log.info('Creating SQL batabase: %s' % dbname)
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
    conn = new_transaction()

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
