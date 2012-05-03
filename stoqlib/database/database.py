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
""" Database access methods """

# FIXME: Refactor this to other files

import os
import platform
import socket
import sys
import time

from kiwi.component import get_utility
from kiwi.log import Logger

from stoqlib.database.exceptions import SQLError
from stoqlib.database.interfaces import IDatabaseSettings
from stoqlib.database.settings import DatabaseSettings

from stoqlib.lib.message import warning
from stoqlib.lib.process import Process, PIPE
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext
_system = platform.system()
log = Logger('stoqlib.db.database')


def drop_database(dbname, settings=None):
    """Drops a database.
    :param dbname: the name of the database to be dropped.
    :param settings: optionally provide seetings, so that you dont have to
        provide IDatabaseSettings before calling this function.
    """
    if not settings:
        settings = get_utility(IDatabaseSettings)
    conn = settings.get_default_connection()

    try:
        # Postgres is lovely, try again a few times
        # before showing an error
        for i in range(3):
            try:
                if conn.databaseExists(dbname):
                    conn.dropDatabase(dbname)
                log.info("Dropped database %s" % (dbname, ))
                break
            except Exception, e:
                time.sleep(1)
        else:
            if conn.databaseExists(dbname):
                raise e
    finally:
        conn.close()


# As of 2012-03-30:
# 604 is the number of entries that are created when you create an
# empty database
# 1174 when you create examples
_ENTRIES_DELETE_THRESHOLD = 1000


def database_exists_and_should_be_dropped(settings, dbname, force):
    """Return False if it is safe to drop the database
    """
    # We are forcing. No need to check
    if force:
        return False

    # We are trying to delete another database. This happens when restoring a
    # backup
    if dbname != settings.dbname:
        settings = DatabaseSettings(rdbms=settings.rdbms,
                        address=settings.address, port=settings.port,
                        dbname=dbname, username=settings.username,
                        password=settings.password)

    # There is no database. Safe to drop.
    if not settings.has_database():
        return False

    conn = settings.get_connection()

    # There is no transaction_entry table. Safe to drop.
    if not conn.tableExists('transaction_entry'):
        # FIXME: Check if there are any other tables, we don't want to
        #        delete other databases
        conn.close()
        return False

    # In demo mode, we can always remove the database
    demo_mode = conn.queryOne("""SELECT field_value FROM parameter_data
                                 WHERE field_name = 'DEMO_MODE'""")[0]
    if demo_mode == '1':
        conn.close()
        return False

    # Insignificant amount of data in the database. Safe to drop
    entries = conn.queryOne("SELECT COUNT(*) FROM transaction_entry")[0]
    if entries < _ENTRIES_DELETE_THRESHOLD:
        conn.close()
        return False

    conn.close()

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


def clean_database(dbname, settings=None, force=False):
    """Cleans a database. If the database does not exist, it will be created.
    :param dbname: name of the database.
    :param settings: optionally provide seetings, so that you dont have to
        provide IDatabaseSettings before calling this function.
    """
    log.info("Cleaning database %s" % (dbname, ))
    if not settings:
        settings = get_utility(IDatabaseSettings)

    if database_exists_and_should_be_dropped(settings, dbname, force):
        if force:
            raise SystemExit("Not dropping database")
        else:
            raise SystemExit("Cannot drop a database with existing "
                             "tables (use --force to really drop it)")

    try:
        drop_database(dbname, settings)
    except Exception, e:
        raise e

    conn = settings.get_default_connection()
    conn.createEmptyDatabase(dbname)
    conn.close()


#
# General routines
#


def execute_sql(filename, settings=None):
    """Inserts Raw SQL commands into the database read from a file.
    :param filename: filename with SQL commands
    :param settings: optionally provide seetings, so that you dont have to
        provide IDatabaseSettings before calling this function.
    :returns: return code, 0 if succeeded, positive integer for failure
    :rtype: int
    """
    if not settings:
        settings = get_utility(IDatabaseSettings)

    log.info("Executing SQL script %s" % filename)

    if settings.rdbms == 'postgres':
        # Okay, this might look crazy, but it's actually the only way
        # to execute many SQL statements in PostgreSQL and
        # 1) Stop immediatelly when an error occur
        # 2) Print the error message, the filename and the line number where
        #    the error occurred.
        # 3) Do not print anything on the output unless it's an warning or a
        #    an error
        args = ['psql']
        # -U needs to go in first or psql on windows get confused
        args.extend(settings.get_tool_args())
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

        args.append(settings.dbname)
        log.debug('executing %s' % (' '.join(args), ))
        proc = Process(args,
                       stdin=PIPE,
                       stdout=PIPE,
                       stderr=PIPE,
                       **kwargs)

        if read_from_pipe:
            # We don't want to see notices on the output, skip them,
            # this will make all reported line numbers offset by 1
            proc.stdin.write("SET SESSION client_min_messages TO 'warning';")

            data = open(filename).read()
            # Rename serial into bigserial, for 64-bit id columns
            data = data.replace('id serial', 'id bigserial')
        else:
            data = None
        stdout, stderr = proc.communicate(data)
        if read_from_pipe and stderr:
            raise SQLError(stderr[:-1])
        return proc.returncode
    else:
        raise NotImplementedError(settings.rdbms)


def start_shell(command=None, quiet=False, settings=None):
    """Runs a database shell using the current settings

    :param command: tell psql to execute the command string
    :param quiet: sets psql quiet option (-q)
    :param settings: optionally provide seetings, so that you dont have to
        provide IDatabaseSettings before calling this function.
    """
    if not settings:
        settings = get_utility(IDatabaseSettings)

    if settings.rdbms == 'postgres':
        args = ['psql']
        if command:
            args.extend(['-c', command])
        if quiet:
            args.append('-q')
        args.extend(settings.get_tool_args())
        args.append(settings.dbname)

        print 'Connecting to %s' % (
            settings.get_connection_uri(filter_password=True), )
        proc = Process(args)
        proc.wait()
    else:
        raise NotImplementedError(settings.rdbms)


def test_local_database():
    """Check and see if we postgres running locally"""
    if _system == 'Windows':
        # Windows uses local sockets, just try and see if a connection
        # can be established
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect(('127.0.0.1', 5432))
        except socket.error:
            return False
        return True
    else:
        # default location for unix socket files is /tmp,
        # ubuntu/debian patches that to /var/run/postgresl
        for pgdir in ['/tmp', '/var/run/postgresql']:
            if (not os.path.exists(pgdir) and
                not os.path.isdir(pgdir)):
                continue

            # Check for the default unix socket which
            # we will later use to create a database user
            fname = os.path.join(pgdir, '.s.PGSQL.5432')
            if os.path.exists(fname):
                return True
        return False


def test_connection(settings=None):
    """Test database connectivity for using command line tools
    :param settings: optionally provide seetings, so that you dont have to
        provide IDatabaseSettings before calling this function.
    :returns: True for success, False if connection fails
    :rtype: bool
    """
    if not settings:
        settings = get_utility(IDatabaseSettings)

    log.info("Testing database connectivity using command line tools")

    if settings.rdbms == 'postgres':
        args = ['psql', '-n', '-q',
                '--variable', 'ON_ERROR_STOP=',
                '-c', 'SELECT 1;']
        args.extend(settings.get_tool_args())
        args.append(settings.dbname)

        log.debug('executing %s' % (' '.join(args), ))
        proc = Process(args,
                       stdin=PIPE,
                       stdout=PIPE)

        retval = proc.wait()
        return retval == 0
    else:
        raise NotImplementedError(settings.rdbms)


def dump_database(filename, settings=None, schema_only=False,
                  gzip=False, format='custom'):
    """Dump the contents of the current database
    :param filename: filename to write the database dump to
    :param settings: optionally provide seetings, so that you dont have to
        provide IDatabaseSettings before calling this function.
    :param schema_only: If only the database schema will be dumped
    """
    if not settings:
        settings = get_utility(IDatabaseSettings)
    log.info("Dumping database to %s" % filename)

    if settings.rdbms == 'postgres':
        args = ['pg_dump',
                '--format=%s' % (format, ),
                '--encoding=UTF-8']
        if gzip:
            args.append('--compress=9')
        if schema_only:
            args.append('--schema-only')
        if filename is not None:
            args.extend(['-f', filename])
        args.extend(settings.get_tool_args())
        args.append(settings.dbname)

        log.debug('executing %s' % (' '.join(args), ))
        proc = Process(args)
        return proc.wait() == 0
    else:
        raise NotImplementedError(settings.rdbms)


def rename_database(src, dest, settings=None):
    """Renames a database.
    :param src: the name of the database we want to rename.
    :param dest: the new database name.
    :param settings: optionally provide seetings, so that you dont have to
        provide IDatabaseSettings before calling this function.
    """
    if not settings:
        settings = get_utility(IDatabaseSettings)

    log.info("Renaming %s database to %s" % (src, dest))

    settings.dbname = dest
    conn = settings.get_default_connection()
    conn.renameDatabase(src, dest)
    conn.close()


def restore_database(dump, settings=None, new_name=None, clean_first=True):
    """Restores the current database.
    :param dump: a database dump file to be used to restore the database.
    :param settings: optionally provide seetings, so that you dont have to
        provide IDatabaseSettings before calling this function.
    :param new_name: optional name for the new restored database.
    :param clean_first: if a clean_database will be performed before restoring.
    """
    if not settings:
        settings = get_utility(IDatabaseSettings)

    log.info("Restoring database %s using %s" % (settings.dbname, dump))

    if settings.rdbms == 'postgres':
        # This will create a new database
        if not new_name:
            new_name = "%s__backup_%s" % (settings.dbname,
                                         time.strftime("%Y%m%d_%H%M"))
        if clean_first:
            clean_database(new_name, settings)

        args = ['pg_restore', '-d', new_name]
        args.extend(settings.get_tool_args())
        args.append(dump)

        log.debug('executing %s' % (' '.join(args), ))

        proc = Process(args, stderr=PIPE)
        proc.wait()
        return new_name
    else:
        raise NotImplementedError(settings.rdbms)


def dump_table(table, filename=None, settings=None):
    """Dump the contents of a table.
    Note this does not include the schema itself, just the data.
    To get the data call stdout.read() on the returned object.
    :param table: table to write
    :param proc: a Process instance
    :param settings: optionally provide seetings, so that you dont have to
        provide IDatabaseSettings before calling this function.
    """
    if not settings:
        settings = get_utility(IDatabaseSettings)

    log.info("Dumping table to %s" % table)

    if settings.rdbms == 'postgres':
        args = ['pg_dump',
                '--format=custom',
                '--encoding=UTF-8',
                '--data-only',
                '--table=%s' % (table, )]
        if filename is not None:
            args.extend(['-f', filename])
        args.extend(settings.get_tool_args())
        args.append(settings.dbname)

        log.debug('executing %s' % (' '.join(args), ))
        return Process(args,
                       stdout=PIPE,
                       env=dict(LANG='C'))
    else:
        raise NotImplementedError(settings.rdbms)


def query_server_time(conn, settings=None):
    if not settings:
        settings = get_utility(IDatabaseSettings)
    conn = settings.get_default_connection()

    if settings.rdbms == 'postgres':
        return conn.queryAll("SELECT NOW();")[0][0]
    else:
        raise NotImplementedError


def check_version(conn, settings=None):
    if not settings:
        settings = get_utility(IDatabaseSettings)
    if settings.rdbms == 'postgres':
        version = conn.queryOne('SELECT VERSION();')[0]
        server_version = version.split(' ', 2)[1]
        assert server_version.count('.') == 2, version
        parts = server_version.split(".")[:2]
        try:
            svs = map(int, parts)
        except ValueError:
            log.info("Error getting server version: %s" % (server_version, ))
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
        #assert len(parts) == 3, parts
        if len(parts) != 3:
            log.info("Error getting psql version: %s" % (line, ))
            return

        client_version = parts[2]
        #assert client_version.count('.') == 2, line
        if client_version.count('.') != 2:
            log.info("Error getting pg version: %s" % (client_version, ))
            return

        cvs = map(int, client_version.split('.'))[:2]

        if svs != cvs:
            warning(_("Problem with PostgreSQL version"),
                    _("The version of the PostgreSQL database server (%s) and the "
                      "postgres client tools (%s) differ. I will let you use "
                      "Stoq, but you will always see this warning when "
                      "starting Stoq until you resolve the version "
                      "incompatibilty by upgrading the server or the client "
                      "tools." % (server_version,
                                  client_version)))
    else:
        raise NotImplementedError
