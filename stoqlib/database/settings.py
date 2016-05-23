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
import logging
import os
import platform
import re
import socket
import sys
import time
import urllib

from storm.database import create_database
from storm.uri import URI

from stoqlib.database.exceptions import OperationalError, SQLError
from stoqlib.exceptions import ConfigError, DatabaseError
from stoqlib.lib.message import warning
from stoqlib.lib.osutils import get_username
from stoqlib.lib.process import Process, PIPE
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext
_system = platform.system()
log = logging.getLogger(__name__)
DEFAULT_RDBMS = 'postgres'
# As of 2012-03-30:
# 604 is the number of entries that are created when you create an
# empty database
# 1174 when you create examples
_ENTRIES_DELETE_THRESHOLD = 1000
# List of PostgreSQL extensions that we need to be available on the
# server.
_REQUIRED_EXTENSIONS = [
    'pg_trgm',  # gist_trgm_ops index type
    'uuid-ossp',   # uuid data-type
]

#: We only allow alpha-numeric and underscores in database names
DB_NAME_RE = re.compile('^[a-zA-Z0-9_]+$')


def _fix_storm():  # pragma nocover
    # FIXME: This is a workaround for this bug: https://bugs.launchpad.net/storm/+bug/1170063
    # We are monkey-patching storm using the patch proposed there.
    # Remove when the bug is fixed.
    import psycopg2
    # psycopg2 version comes as '2.5.3 (dt dec mx pq3 ext)' (both in debian and
    # ubuntu). If that's not the case somehow, we will simply abort.
    try:
        psycopg2_version = psycopg2.__version__[:5]
        psycopg2_version = tuple(psycopg2_version.split('.'))
    except Exception:
        return

    # We only need to apply this if psycopg2 version is >= 2.5
    if psycopg2_version < (2, 5):
        return

    from storm.exceptions import (Error, Warning, InternalError,
                                  ProgrammingError, IntegrityError, DataError,
                                  NotSupportedError, InterfaceError,
                                  # Make pyflakes happy
                                  DatabaseError as _DatabaseError,
                                  OperationalError as _OperationalError)

    def install_exceptions(module):
        for exception in (Error, Warning, _DatabaseError, InternalError,
                          _OperationalError, ProgrammingError, IntegrityError,
                          DataError, NotSupportedError, InterfaceError):
            module_exception = getattr(module, exception.__name__, None)
            if module_exception is not None:
                try:
                    module_exception.__bases__ += (exception,)
                except TypeError:
                    # Since PsycoPG >= 2.5 psycopg2.Error is built-in
                    tmp_exception = module_exception

                    class PsycoPG25Error(tmp_exception):
                        """We can not patch built-in types
                        """

                    setattr(module, module_exception.__name__, PsycoPG25Error)
                    module_exception = getattr(module, exception.__name__)
                    module_exception.__bases__ += (exception,)

    import storm.exceptions
    storm.exceptions.install_exceptions = install_exceptions

_fix_storm()


def validate_database_name(dbname):
    """Verifies that a database name does not contain any invalid characters.

    :param dbname: name of a database
    :returns: ``True`` if it's valid, ``False`` otherwise
    """
    return bool(re.match(DB_NAME_RE, dbname))


def _database_exists(store, dbname):
    q = 'SELECT COUNT(*) FROM pg_database WHERE datname = %s'
    res = store.execute(q, (unicode(dbname), ))
    value = res.get_one()[0]
    return value


def _database_drop(store, dbname, ifExists=False):
    if not validate_database_name(dbname):
        raise ValueError(
            "Database names can only contain alpha numeric and underscores")

    if ifExists and not _database_exists(store, dbname):
        return False

    database = store.get_database()
    raw_conn = database.raw_connect()
    cur = raw_conn.cursor()
    cur.execute('COMMIT')
    cur.execute('DROP DATABASE %s' % (dbname, ))
    cur.close()
    del cur, raw_conn, database
    return True


def _extension_exists(cur, extension):
    q = """SELECT count(*)
             FROM pg_available_extensions
            WHERE name = %s"""
    cur.execute(q, (extension, ))
    return cur.fetchone()[0] == 1


def _create_empty_database(store, dbname, ifNotExists=False):
    if not validate_database_name(dbname):
        raise ValueError(
            "Database names can only contain alpha numeric and underscores")

    if ifNotExists and _database_exists(store, dbname):
        return False

    database = store.get_database()
    raw_conn = database.raw_connect()
    cur = raw_conn.cursor()
    cur.execute('COMMIT')
    cur.execute('CREATE DATABASE %s' % (dbname, ))
    check_extensions(cursor=cur)
    cur.close()
    del cur, raw_conn, database
    return True


def check_extensions(cursor=None, store=None):
    """
    Check if all required extensions can be installed.

    :param cursor: a cursor or ``None``
    :param store: a store or ``None``
    """
    if cursor is None:
        database = store.get_database()
        raw_conn = database.raw_connect()
        cursor = raw_conn.cursor()

    for extension in _REQUIRED_EXTENSIONS:
        if not _extension_exists(cursor, extension):
            raise ValueError("Database server is missing %s extension." % (
                extension))


def test_local_database():
    """Check and see if we postgres running locally

    :returns: (hostname, port)
    """
    ports = [5432, 5433, 5434]

    if _system == 'Windows':
        # Windows uses local sockets, just try and see if a connection
        # can be established
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        for port in ports:
            pair = ('127.0.0.1', port)
            try:
                s.connect(pair)
            except socket.error:
                pass
            else:
                return pair
    else:
        # default location for unix socket files is /tmp,
        # ubuntu/debian patches that to /var/run/postgresl
        for pgdir in ['/tmp', '/var/run/postgresql']:
            if (not os.path.exists(pgdir) and
                not os.path.isdir(pgdir)):
                continue

            for port in ports:
                # Check for the default unix socket which
                # we will later use to create a database user
                fname = os.path.join(pgdir, '.s.PGSQL.%d' % (port, ))
                if os.path.exists(fname):
                    return (pgdir, port)

        return None


def get_database_version(store):
    """Gets the database version as a tuple

    :param store: a store
    :returns: the version as a 3 item tuple
    """
    version_num = store.execute('SHOW server_version_num;').get_one()[0]
    version_num = '0' * (6 - len(version_num)) + version_num
    return tuple(map(
        int, [version_num[i:i + 2] for i in range(0, len(version_num), 2)]))


class DatabaseSettings(object):
    """DatabaseSettings contains all the information required to connect to
    a database, such as hostname, username and password.

    It also provides helpers on top of ORMObject to return a database
    connection using the settings inside the object.
    """

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

    def _log_connect(self, uri):
        log_uri = uri.copy()
        if log_uri.password:
            log_uri.password = '*****'
        log.info("Connecting to %s" % (log_uri, ))

    def _build_dsn(self, dbname, filter_password=False):
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

        return '%s://%s/%s' % (self.rdbms, authority, dbname)

    def _create_uri(self, dbname=None):
        # postgres is a special database which is always present,
        # it was added in 8.1 which is thus our requirement'
        dbname = dbname or 'postgres'

        # Do not output the password in the logs
        if not self.first:
            log.info('connecting to %s' % self._build_dsn(
                dbname, filter_password=True))
            self.first = False

        dsn = self._build_dsn(dbname, filter_password=False)
        uri = URI(dsn)
        uri.options['isolation'] = 'read-committed'

        if uri.host == "":
            pair = test_local_database()
            if pair is None:
                raise DatabaseError(
                    _("Could not find a database server on this computer"))
            uri.host = pair[0]
            uri.port = int(pair[1])

        return uri

    def _get_store_internal(self, dbname):
        from stoqlib.database.runtime import StoqlibStore
        uri = self._create_uri(dbname)
        try:
            self._log_connect(uri)
            store = StoqlibStore(create_database(uri))
        except OperationalError as e:
            log.info('OperationalError: %s' % e)
            raise DatabaseError(e.args[0])
        except Exception as e:
            value = sys.exc_info()[1]
            raise DatabaseError(
                _("Could not connect to %s database. The error message is "
                  "'%s'. Please fix the connection settings you have set "
                  "and try again.") % (DEFAULT_RDBMS, value))
        return store

    # Public API

    def get_store_uri(self, filter_password=False):
        """Returns a uri representing the current database settings.
        It's used by the orm to connect to a database.
        :param filter_password: if the password should be filtered out
        :returns: a string like postgresql://username@localhost/dbname
        """
        return self._build_dsn(self.dbname, filter_password=filter_password)

    def get_store_dsn(self):
        """Get a dsn that can be used to connect to the database

        Unlike :meth:`.get_store_uri`, this is supported by all PostgreSQL
        versions when used by `psycopg2.connect`.

        :returns: a string like "dbname=stoq host=localhost port=5432"
        """
        from storm.databases.postgres import make_dsn
        return make_dsn(self._create_uri(self.dbname))

    def create_store(self):
        """Creates a store using the provided default settings.
        store.close() needs to be called when usage of this store is
        completed.

        :returns: the new store
        """
        return self._get_store_internal(self.dbname)

    def create_super_store(self):
        """Creates a store to the default database, note that this
        different from the configred.
        This method is mainly here to able to create other databases,
        which will need a connection, Be careful when using this method.

        :returns: a store
        """
        return self._get_store_internal(None)

    def copy(self):
        return DatabaseSettings(address=self.address,
                                dbname=self.dbname,
                                rdbms=self.rdbms,
                                port=self.port,
                                username=self.username,
                                password=self.password)

    # FIXME: Remove/Rethink
    def check_database_address(self):
        if not self.address:
            return True

        try:
            socket.getaddrinfo(self.address, None)
        except (socket.gaierror, socket.error):
            return False
        return True

    def has_database(self):
        """Checks if the database specified in the settings exists
        :returns: if the database exists
        """
        try:
            super_store = self.create_super_store()
        except OperationalError as e:
            msg = e.args[0]
            details = None
            if ';' in msg:
                msg, details = msg.split(';')
            msg = msg.replace('\n', '').strip()
            details = details.replace('\n', '').strip()
            raise DatabaseError('Database Error:\n%s' % msg, details)
        retval = _database_exists(super_store, self.dbname)
        super_store.close()
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
            # This is for stoqdbadmin (not psql). -w takes a password
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

    def drop_database(self, dbname):
        """Drops a database.

        :param dbname: the name of the database to be dropped.
        """
        super_store = self.create_super_store()

        try:
            # Postgres is lovely, try again a few times
            # before showing an error
            for i in range(3):
                try:
                    if _database_exists(super_store, dbname):
                        _database_drop(super_store, dbname)
                    log.info("Dropped database %s" % (dbname, ))
                    break
                except Exception as e:
                    # time.sleep(1)
                    raise
            else:
                if _database_exists(super_store, dbname):
                    raise e
        finally:
            super_store.close()

    def database_exists(self, dbname):
        super_store = self.create_super_store()
        exists = _database_exists(super_store, dbname)
        super_store.close()
        return exists

    def database_exists_and_should_be_dropped(self, dbname, force):
        """Return ``False`` if it is safe to drop the database
        """
        # We are forcing. No need to check
        if force:
            return False

        # We are trying to delete another database. This happens when restoring a
        # backup
        db_settings_ = self
        if dbname != db_settings_.dbname:
            db_settings_ = db_settings_.copy()
            db_settings_.dbname = dbname

        # There is no database. Safe to drop.
        if not db_settings_.has_database():
            return False

        store = db_settings_.create_store()

        # There is no transaction_entry table. Safe to drop.
        if not store.table_exists('transaction_entry'):
            # FIXME: Check if there are any other tables, we don't want to
            #        delete other databases
            store.close()
            return False

        # In demo mode, we can always remove the database
        result = store.execute(
            """SELECT field_value FROM parameter_data
               WHERE field_name = 'DEMO_MODE'""")
        demo_mode = result.get_one()
        result.close()
        if demo_mode == '1':
            store.close()
            return False

        # Insignificant amount of data in the database. Safe to drop
        result = store.execute("SELECT COUNT(*) FROM transaction_entry")
        entries = result.get_one()
        result.close()
        store.close()
        if entries < _ENTRIES_DELETE_THRESHOLD:
            return False

        # Right now: 1) Not forcing, 2) Database exists, 3) There are tables, 4)
        # There is is a significant amount of data.
        # Ask if the user really wants to drop.
        if not os.isatty(sys.__stdin__.fileno()):
            return False

        text = raw_input(
            "Database %s has existing tables, "
            "do you really want to delete it?\n[yes/no] " % (dbname, ))
        if text == 'yes':
            return False

        return True

    def clean_database(self, dbname, force=False):
        """Cleans a database. If the database does not exist, it will be created.

        :param dbname: name of the database.
        """
        log.info("Cleaning database %s" % (dbname, ))
        if self.database_exists_and_should_be_dropped(dbname, force):
            if force:
                raise SystemExit("Not dropping database")
            else:
                raise SystemExit("Cannot drop a database with existing "
                                 "tables (use --force to really drop it)")

        self.drop_database(dbname)
        super_store = self.create_super_store()
        _create_empty_database(super_store, dbname)
        super_store.close()

    def execute_sql(self, filename, lock_database=False):
        """Inserts raw SQL commands into the database read from a file.

        :param filename: filename with SQL commands
        :param lock_database: If the existing tables in the database should be
          locked
        :returns: return code, ``0`` if succeeded, positive integer for failure
        """
        log.info("Executing SQL script %s database locked=%s" % (filename,
                                                                 lock_database))

        if self.rdbms == 'postgres':
            # Okay, this might look crazy, but it's actually the only way
            # to execute many SQL statements in PostgreSQL and
            # 1) Stop immediatelly when an error occur
            # 2) Print the error message, the filename and the line number where
            #    the error occurred.
            # 3) Do not print anything on the output unless it's an warning or a
            #    an error
            args = ['psql']
            # -U needs to go in first or psql on windows get confused
            args.extend(self.get_tool_args())
            args.extend(['-n', '-q'])

            kwargs = {}
            if _system == 'Windows':
                # Hide the console window
                # For some reason XP doesn't like interacting with
                # proceses via pipes
                read_from_pipe = False
            else:
                read_from_pipe = True

            # We have two different execution modes,
            # 1) open stdin (-) and write the data via a pipe,
            #    this allows us to also disable noticies and info messages,
            #    so that only warnings are printed, we also fail if a warning
            #    or error is printed
            # 2) Pass in the file normally to psql, no error reporting included
            if read_from_pipe:
                args.extend(['-f', '-'])
                args.extend(['--variable', 'ON_ERROR_STOP='])
            else:
                args.extend(['-f', filename])

            args.append(self.dbname)
            log.debug('executing %s' % (' '.join(args), ))
            proc = Process(args,
                           stdin=PIPE,
                           stdout=PIPE,
                           stderr=PIPE,
                           **kwargs)

            proc.stdin.write('BEGIN TRANSACTION;')
            if lock_database:
                store = self.create_store()
                lock_query = store.get_lock_database_query()
                proc.stdin.write(lock_query)
                store.close()

            if read_from_pipe:
                # We don't want to see notices on the output, skip them,
                # this will make all reported line numbers offset by 1
                proc.stdin.write("SET SESSION client_min_messages TO 'warning';")

                data = open(filename).read()
                # Rename serial into bigserial, for 64-bit id columns
                data = data.replace('id serial', 'id bigserial')
                data += '\nCOMMIT;'
            else:
                data = None
            stdout, stderr = proc.communicate(data)
            if read_from_pipe and stderr:
                raise SQLError(stderr[:-1])
            return proc.returncode
        else:
            raise NotImplementedError(self.rdbms)

    def start_shell(self, command=None, quiet=False):
        """Runs a database shell

        :param command: tell psql to execute the command string
        :param quiet: sets psql quiet option (``-q``)
        """

        if self.rdbms == 'postgres':
            args = ['psql']
            if command:
                args.extend(['-c', command])
            if quiet:
                args.append('-q')
            args.extend(self.get_tool_args())
            args.append(self.dbname)

            print('Connecting to %s' % (
                self.get_store_dsn(filter_password=True), ))
            proc = Process(args)
            proc.wait()
        else:
            raise NotImplementedError(self.rdbms)

    def test_connection(self):
        """Test for database connectivity using command line tools

        :returns: `True` if the database connection succeeded.
        """
        log.info("Testing database connectivity using command line tools")

        if self.rdbms == 'postgres':
            # -w avoids password prompts, which causes this to hang.
            args = ['psql', '-n', '-q', '-w',
                    '--variable', 'ON_ERROR_STOP=',
                    '-c', 'SELECT 1;']
            args.extend(self.get_tool_args())
            args.append(self.dbname)

            log.debug('executing %s' % (' '.join(args), ))
            proc = Process(args,
                           stdin=PIPE,
                           stdout=PIPE)

            retval = proc.wait()
            return retval == 0
        else:
            raise NotImplementedError(self.rdbms)

    def dump_database(self, filename, schema_only=False,
                      gzip=False, format='custom'):
        """Dump the contents of the current database

        :param filename: filename to write the database dump to
        :param schema_only: If only the database schema will be dumped
        :param gzip: if the dump should be compressed using gzip -9
        :param format: database dump format, defaults to ``custom``
        """
        log.info("Dumping database to %s" % filename)

        if self.rdbms == 'postgres':
            args = ['pg_dump',
                    '--format=%s' % (format, ),
                    '--encoding=UTF-8']
            if gzip:
                args.append('--compress=9')
            if schema_only:
                args.append('--schema-only')
            if filename is not None:
                args.extend(['-f', filename])
            args.extend(self.get_tool_args())
            args.append(self.dbname)

            log.debug('executing %s' % (' '.join(args), ))
            proc = Process(args)
            return proc.wait() == 0
        else:
            raise NotImplementedError(self.rdbms)

    def restore_database(self, dump, new_name=None, clean_first=True):
        """Restores the current database.

        :param dump: a database dump file to be used to restore the database.
        :param new_name: optional name for the new restored database.
        :param clean_first: if a clean_database will be performed before restoring.
        """
        log.info("Restoring database %s using %s" % (self.dbname, dump))

        if self.rdbms == 'postgres':
            # This will create a new database
            if not new_name:
                new_name = "%s__backup_%s" % (self.dbname,
                                              time.strftime("%Y%m%d_%H%M"))
            if clean_first:
                self.clean_database(new_name)

            args = ['pg_restore', '-d', new_name]
            args.extend(self.get_tool_args())
            args.append(dump)

            log.debug('executing %s' % (' '.join(args), ))

            proc = Process(args, stderr=PIPE)
            proc.wait()
            return new_name
        else:
            raise NotImplementedError(self.rdbms)

    def dump_table(self, table, filename=None):
        """Dump the contents of a table.
        Note this does not include the schema itself, just the data.
        To get the data call `.read()` on the returned object.

        :param table: table to write
        :param proc: a Process instance
        """
        log.info("Dumping table to %s" % table)

        if self.rdbms == 'postgres':
            args = ['pg_dump',
                    '--format=custom',
                    '--encoding=UTF-8',
                    '--data-only',
                    '--table=%s' % (table, )]
            if filename is not None:
                args.extend(['-f', filename])
            args.extend(self.get_tool_args())
            args.append(self.dbname)

            log.debug('executing %s' % (' '.join(args), ))
            return Process(args,
                           stdout=PIPE,
                           env=dict(LANG='C'))
        else:
            raise NotImplementedError(self.rdbms)

    def check_version(self, store):
        """Verify that the database version is recent enough to be supported
        by stoq. Emits a warning if the version isn't recent enough, suitable
        for usage by an installer.

        :param store: a store
        """
        if self.rdbms == 'postgres':
            try:
                svs = get_database_version(store)
            except DatabaseError as e:
                log.info(str(e))
                return

            # Client version
            kwargs = {}
            args = ['psql']
            if _system == 'Windows':
                # FIXME: figure out why this isn't working
                return
            else:
                args.append('--version')
            p = Process(args, stdout=PIPE, **kwargs)
            stdout = p.communicate()[0]
            line = stdout.split('\n', 1)[0]
            if line.endswith('\r'):
                line = line[:-1]

            parts = line.split(' ')
            # assert len(parts) == 3, parts
            if len(parts) != 3:
                log.info("Error getting psql version: %s" % (line, ))
                return

            client_version = parts[2]
            # assert client_version.count('.') == 2, line
            if client_version.count('.') != 2:
                log.info("Error getting pg version: %s" % (client_version, ))
                return

            cvs = tuple(map(int, client_version.split('.'))[:3])

            if svs != cvs:
                server_version = '.'.join(map(str, svs))
                warning(_(u"Problem with PostgreSQL version"),
                        _(u"The version of the PostgreSQL database server (%s) and the "
                          "postgres client tools (%s) differ. I will let you use "
                          "Stoq, but you will always see this warning when "
                          "starting Stoq until you resolve the version "
                          "incompatibilty by upgrading the server or the client "
                          "tools.") % (server_version, client_version))
        else:
            raise NotImplementedError(self.rdbms)


db_settings = DatabaseSettings()
