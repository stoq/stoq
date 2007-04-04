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

log = Logger('stoqlib.database')

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


def rollback_and_begin(conn):
    conn.rollback()
    conn.begin()


def finish_transaction(trans, model):
    """
    Encapsulated method for committing/aborting changes in models.
    @param trans: a transaction
    @param model: abort if None else commit
    """

    # Allow false and None
    if model:
        trans.commit()
    else:
        rollback_and_begin(trans)

    return model


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
               "--variable ON_ERROR_STOP= -f \"%(schema)s\"")% dict(
            address=settings.address,
            username=settings.username,
            port=settings.port,
            dbname=settings.dbname,
            schema='-')

        log.debug('sql_prepare: executing %s' % cmd)
        proc = subprocess.Popen(cmd, shell=True,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE)

        # We don't want to see notices on the output, skip them,
        # this will make all reported line numbers offset by 1
        proc.stdin.write("SET SESSION client_min_messages TO 'warning';");

        data = open(filename).read()
        # Rename serial into bigserial, for 64-bit id columns
        data = data.replace('serial', 'bigserial')
        proc.stdin.write(data)
        proc.stdin.close()

        return proc.wait()
    else:
        raise NotImplementedError(settings.rdbms)
