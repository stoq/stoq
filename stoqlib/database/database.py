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

from stoqlib.database.interfaces import IDatabaseSettings
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

log = Logger('stoqlib.db.database')

def clean_database(dbname):
    """
    Cleans a database
    @param dbname: name of the database
    """
    settings = get_utility(IDatabaseSettings)
    conn = settings.get_default_connection()
    try:
        conn.dropDatabase(dbname, ifExists=True)
        conn.createDatabase(dbname)
    finally:
        conn.close()

#
# General routines
#


def execute_sql(filename):
    """
    Inserts Raw SQL commands into the database read from a file.
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
    """
    Dump the contents of the current database
    @param filename: filename to write the database dump to
    """
    settings = get_utility(IDatabaseSettings)

    log.info("Dumping database to %s" % filename)

    if settings.rdbms == 'postgres':
        cmd = ("pg_dump -E UTF-8 -h %(address)s -U %(username)s "
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

def dump_table(table):
    """
    Dump the contents of a table.
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

