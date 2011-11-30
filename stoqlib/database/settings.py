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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##

"""Settings required to access the database, hostname, username etc
"""
import os
import urllib
import sys
import socket

from kiwi.log import Logger
from zope.interface import implements

from stoqlib.database.exceptions import OperationalError
from stoqlib.database.interfaces import IDatabaseSettings
from stoqlib.database.orm import connectionForURI
from stoqlib.exceptions import ConfigError, DatabaseError
from stoqlib.lib.osutils import get_username
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

    def __init__(self, rdbms=None, address=None, port=None,
                 dbname=None, username=None, password=''):
        if not rdbms:
            rdbms = 'postgres'
        if rdbms == 'postgres':
            if not address:
                address = os.environ.get('PGHOST', '')
            if not dbname:
                dbname = os.environ.get('PGDATABASE', 'stoq')
            if not username:
                username = os.environ.get('PGUSER', get_username())
            if not port:
                port = os.environ.get('PGPORT', 5432)
        self.rdbms = rdbms
        self.address = address
        self.port = port
        self.dbname = dbname
        self.username = username
        self.password = password
        self.first = True

    def __repr__(self):
        return '<DatabaseSettings rdbms=%s address=%s port=%d dbname=%s username=%s' % (
            self.rdbms, self.address, self.port, self.dbname, self.username)

    def _build_uri(self, dbname, filter_password=False):
        # Here we construct a uri for database access like:
        # 'postgresql://username@localhost/dbname'
        if self.rdbms != DEFAULT_RDBMS:
            raise ConfigError("Unsupported database type: %s" % self.rdbms)

        if self.password:
            password = ":"
            if filter_password:
                password += '*****'
            else:
                password += urllib.quote_plus(self.password)
        else:
            password = ""
        authority = '%s%s@%s:%s' % (
            self.username, password, self.address, self.port)
        if dbname is None:
            # postgres is a special database which is always present,
            # it was added in 8.1 which is thus our requirement'
            dbname = 'postgres'

        return '%s://%s/%s' % (self.rdbms, authority, dbname)

    def _get_connection_internal(self, dbname):
        conn_uri = self._build_uri(dbname)

        # Do not output the password in the logs
        if not self.first:
            log.info('connecting to %s' % self._build_uri(
                dbname, filter_password=True))
            self.first = False

        try:
            conn = connectionForURI(conn_uri)
            conn.makeConnection()
        except OperationalError, e:
            log.info('OperationalError: %s' % e)
            raise DatabaseError(e.args[0])
        except Exception, e:
            value = sys.exc_info()[1]
            raise DatabaseError(
                _("Could not connect to %s database. The error message is "
                  "'%s'. Please fix the connection settings you have set "
                  "and try again." % (DEFAULT_RDBMS, value)))
        return conn

    # Public API

    def get_connection_uri(self, filter_password=False):
        """Returns a uri representing the current database settings.
        It's used by the orm to connect to a database.
        @param filter_password: if the password should be filtered out
        @returns: a string like postgresql://username@localhost/dbname
        """
        return self._build_uri(self.dbname, filter_password=filter_password)

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
        if not self.address:
            return True

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

    def get_command_line_arguments(self):
        """Get a list of command line arguments suitable
        to send into stoqdbadmin"""
        args = []
        # Keep in sync with stoq/lib/options.py
        args.extend(['-d', self.dbname])
        if self.address:
            args.extend(['-H', self.address])
        args.extend(['-p', str(self.port)])
        args.extend(['-u', self.username])
        if self.password:
            args.extend(['-w', self.password])
        return args

    def get_tool_args(self):
        """Return a list of arguments suitable for sending in
        to the command line tool of a database such as psql"""
        args = []
        if self.rdbms == 'postgres':
            # Postgres on windows wants -U first
            args.extend(['-U', self.username])
            # Password goes via ~/.pgpass
            if self.address:
                args.extend(['-h', self.address])
            args.extend(['-p', str(self.port)])
        else:
            raise NotImplementedError(self.rdbms)
        return args
