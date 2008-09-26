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

"""Settings required to access the database, hostname, username etc
"""
import os
import pwd
import sys
import socket

from kiwi.log import Logger
from zope.interface import implements

from stoqlib.database.exceptions import OperationalError
from stoqlib.database.interfaces import IDatabaseSettings
from stoqlib.database.orm import connectionForURI
from stoqlib.exceptions import ConfigError, DatabaseError
from stoqlib.lib.translation import stoqlib_gettext

DEFAULT_RDBMS = 'postgres'

_ = stoqlib_gettext

log = Logger('stoqlib.db.settings')

class DatabaseSettings(object):
    """DatabaseSettings contains all the information required to connect to
    a database, such as hostname, username and password.

    It also provides helpers on top of ORMObject to return a database
    connection using the settings inside the object.
    """

    implements(IDatabaseSettings)

    def __init__(self, rdbms=DEFAULT_RDBMS, address=None, port=5432,
                 dbname='stoq', username=None, password=''):

        self.rdbms = rdbms
        if address is None:
            address = os.environ.get('PGHOST', 'localhost')
        self.address = address
        self.port = port
        self.dbname = dbname
        if not username:
            username = pwd.getpwuid(os.getuid())[0]
        self.username = username
        self.password = password

    def _build_uri(self, dbname, filter_password=False):
        # Here we construct a uri for database access like:
        # 'postgresql://username@localhost/dbname'
        if self.rdbms != DEFAULT_RDBMS:
            raise ConfigError("Unsupported database type: %s" % self.rdbms)

        if filter_password:
            password = '*****'
        else:
            password = self.password

        authority = '%s:%s@%s:%s' % (
            self.username, password, self.address, self.port)
        if dbname is None:
            # postgres is a special database which is always present,
            # it was added in 8.1 which is thus our requirement'
            dbname = 'postgres'

        return '%s://%s/%s' % (self.rdbms, authority, dbname)

    def _get_connection_internal(self, dbname):
        conn_uri = self._build_uri(dbname)

        # Do not output the password in the logs
        log.info('connecting to %s' % self._build_uri(
            dbname, filter_password=True))

        try:
            conn = connectionForURI(conn_uri)
            conn.makeConnection()
        # FIXME: Remove and display the messages to the user.
        except OperationalError, e:
            log.info('OperationalError: %s' % e)
            if 'password authentication failed for user' in e.args[0]:
                raise DatabaseError(
                    _("Password authentication failed"),
                    _("The provided password for user %s was not correct") %
                    self.username)
            elif 'no password supplied' in e.args[0]:
                raise DatabaseError(
                    _("Invalid authentication mechanism"),
                    _("Trust was selected but the database does "
                      "only support password authentication."))

            # Raise the exception otherwise to avoid swallowing unexpected
            # exceptions.
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
        """Returns a uri representing the current database settings.
        It's used by the orm to connect to a database.
        @returns: a string like postgresql://username@localhost/dbname
        """
        return self._build_uri(self.dbname)

    def get_connection(self):
        """Returns a connection to the configured database
        @returns: a database connection
        """
        return self._get_connection_internal(self.dbname)

    def get_default_connection(self):
        """Returns a connection to the default database, note that this
        different from the configred.
        This method is mainly here to able to create other databases,
        which will need a connection, Be careful when using this method.
        @returns: a database connection
        """
        return self._get_connection_internal(None)

    # FIXME: Remove/Rethink
    def check_database_address(self):
        try:
            socket.getaddrinfo(self.address, None)
        except socket.gaierror:
            return False
        return True

    def has_database(self):
        """Checks if the database specified in the settings exists
        @return: if the database exists
        """
        try:
            conn = self.get_default_connection()
        except OperationalError, e:
            msg = e.args[0]
            details = None
            if ';' in msg:
                msg, details = msg.split(';')
            msg = msg.replace('\n', '').strip()
            details = details.replace('\n', '').strip()
            raise DatabaseError('Database Error:\n%s' % msg, details)
        retval = conn.databaseExists(self.dbname)
        conn.close()
        return retval
