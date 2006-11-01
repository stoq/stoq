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
from stoqlib.lib.message import error

_ = stoqlib_gettext

log = Logger('stoqlib.database')

def database_exists(conn, dbname):
    """
    Given a database name, returns True if it exists, False otherwise
    @param conn: a database connection
    @param dbname: name of the database
    @returns: if the database exists
    """
    return conn.databaseExists(dbname)

def clean_database(dbname):
    """
    Cleans a database
    @param dbname: name of the database
    """
    settings = get_utility(IDatabaseSettings)
    conn = settings.get_default_connection()
    conn.dropDatabase(dbname, ifExists=True)
    conn.createDatabase(dbname)
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
    if model is None:
        trans.commit()
    else:
        rollback_and_begin(trans)

    return model


def execute_sql(filename):
    """
    Inserts Raw SQL commands into the database read from a file.
    @param filename: filename with SQL commands
    """
    settings = get_utility(IDatabaseSettings)
    cmd = ("psql -n -h %(address)s -p %(port)s %(dbname)s -q "
           "--variable ON_ERROR_STOP= -f \"%(schema)s\"")% dict(
        address=settings.address,
        port=settings.port,
        dbname=settings.dbname,
        schema=filename)

    log.debug('sql_prepare: executing %s' % cmd)
    proc = subprocess.Popen(cmd, shell=True,
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE)
    returncode = proc.wait()
    if returncode != 0:
        error('psql returned error code %d' % returncode)

