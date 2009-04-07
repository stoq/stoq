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

import os
import subprocess
import time

from kiwi.component import get_utility
from kiwi.log import Logger

from stoqlib.database.interfaces import IDatabaseSettings
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

log = Logger('stoqlib.db.database')


def drop_database(dbname):
    """Drops a database.
    @param dbname: the name of the database to be dropped.
    """
    log.info("Droping database %s" % (dbname,))
    settings = get_utility(IDatabaseSettings)
    conn = settings.get_default_connection()

    try:
        # Postgres is lovely, try again a few times
        # before showing an error
        for i in range(3):
            try:
                conn.dropDatabase(dbname, ifExists=True)
                break
            except Exception, e:
                time.sleep(1)
        else:
            if conn.databaseExists(dbname):
                raise e
    finally:
        conn.close()


def clean_database(dbname):
    """Cleans a database. If the database does not exist, it will be created.
    @param dbname: name of the database.
    """
    log.info("Cleaning database %s" % (dbname,))

    try:
        drop_database(dbname)
    except Exception, e:
        raise e

    settings = get_utility(IDatabaseSettings)
    if settings.dbname == dbname:
        conn = settings.get_default_connection()
    else:
        conn = settings.get_connection()

    conn.createDatabase(dbname)
    conn.close()


#
# General routines
#


def execute_sql(filename):
    """Inserts Raw SQL commands into the database read from a file.
    @param filename: filename with SQL commands
    @returns: return code, 0 if succeeded, positive integer for failure
    @rtype: int
    """
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
        cmd = ("psql -n -h %(address)s -U %(username)s "
               "-p %(port)s %(dbname)s -q "
               "--variable ON_ERROR_STOP= -f \"%(schema)s\"") % dict(
            address=settings.address,
            username=settings.username,
            port=settings.port,
            dbname=settings.dbname,
            schema='-')

        log.debug('executing %s' % cmd)
        proc = subprocess.Popen(cmd, shell=True,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE)

        # We don't want to see notices on the output, skip them,
        # this will make all reported line numbers offset by 1
        proc.stdin.write("SET SESSION client_min_messages TO 'warning';");

        data = open(filename).read()
        # Rename serial into bigserial, for 64-bit id columns
        data = data.replace('id serial', 'id bigserial')
        proc.stdin.write(data)
        proc.stdin.close()

        return proc.wait()
    else:
        raise NotImplementedError(settings.rdbms)

def dump_database(filename):
    """Dump the contents of the current database
    @param filename: filename to write the database dump to
    """
    settings = get_utility(IDatabaseSettings)

    log.info("Dumping database to %s" % filename)

    if settings.rdbms == 'postgres':
        cmd = ("pg_dump -Fc -E UTF-8 -h %(address)s -U %(username)s "
               "-p %(port)s %(dbname)s") % dict(
            address=settings.address,
            username=settings.username,
            port=settings.port,
            dbname=settings.dbname,
            )
        if filename:
            cmd += ' -f ' + filename

        log.debug('executing %s' % cmd)
        proc = subprocess.Popen(cmd, shell=True)
        return proc.wait()
    else:
        raise NotImplementedError(settings.rdbms)


def rename_database(src, dest):
    """Renames a database.
    @param src: the name of the database we want to rename.
    @param dest: the new database name.
    """
    settings = get_utility(IDatabaseSettings)

    log.info("Renaming %s database to %s" % (src, dest))

    settings.dbname = dest
    conn = settings.get_default_connection()
    conn.renameDatabase(src, dest)
    conn.close()


def restore_database(dump):
    """Restores the current database.
    @param dump: a database dump file to be used to restore the database.
    """
    settings = get_utility(IDatabaseSettings)

    log.info("Restoring database %s using %s" % (settings.dbname, dump))

    if settings.rdbms == 'postgres':
        # This will create a new database
        newname = settings.dbname + '__backup'
        clean_database(newname)

        cmd = ("pg_restore -h %(address)s -U %(username)s "
               "-p %(port)s -d %(dbname)s %(dump)s") % dict(
            address=settings.address,
            username=settings.username,
            port=settings.port,
            dbname=newname,
            dump=dump,)

        # We will recover the created database
        log.debug('executing %s' % cmd)
        # Let's ignore the output of pg_restore ...
        devnull = open(os.devnull, 'w')
        proc = subprocess.Popen(cmd, shell=True, stderr=devnull)
        retcode = proc.wait()

        drop_database(settings.dbname)
        rename_database(newname, settings.dbname)
        return retcode
    else:
        raise NotImplementedError(settings.rdbms)


def dump_table(table):
    """Dump the contents of a table.
    Note this does not include the schema itself, just the data.
    To get the data call stdout.read() on the returned object.
    @param table: table to write
    @param proc: a subprocess.Popen instance
    """
    settings = get_utility(IDatabaseSettings)

    log.info("Dumping table to %s" % table)

    if settings.rdbms == 'postgres':
        cmd = ("pg_dump -E UTF-8 -h %(address)s -U %(username)s "
               "-p %(port)s %(dbname)s -t %(table)s -a -d") % dict(
            address=settings.address,
            username=settings.username,
            port=settings.port,
            dbname=settings.dbname,
            table=table)
        log.info('executing %s' % cmd)
        return subprocess.Popen(cmd, shell=True,
                                stdout=subprocess.PIPE,
                                env=dict(LANG='C'))
    else:
        raise NotImplementedError(settings.rdbms)

