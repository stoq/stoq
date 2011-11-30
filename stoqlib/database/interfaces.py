# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

"""Database Interfaces: Connection, Settings etc
"""

from zope.interface import Attribute
from zope.interface.interface import Interface


class IDatabaseSettings(Interface):
    """This is an interface to describe all important database settings
    """

    rdbms = Attribute('name identifying the database type')
    dbname = Attribute('name identifying the database name')
    address = Attribute('database address')
    port = Attribute('database port')

    def get_connection_uri():
        """
        Gets a ORM connection URI.
        @returns: a ORM connection URI.
        """


class IConnection(Interface):
    """This is an interface that describes a database connection
    """

    def close():
        """Drops the connection to the database"""


class ITransaction(IConnection):
    """This is an interface that describes a database transaction.
    It extends the IConnection interface.
    """

    def commit(close=False):
        """Commits the objects to the database.
        Sends all the modifications of the current objects to the database,
        @param close: Optional, if True also closes the database
        """

    def rollback(name=None):
        """Undos all the changes made within the current transaction
        @param name: If supplied limit changes to the last savepoint
        """

    def get(object):
        """Fetches an object within the transaction
        @param obj: a ORMObject
        @returns: a reference to the same object within the transaction
        """

    def add_created_object(object):
        """Adds a created C{object} to the transaction.

        @param object: an L{stoqlib.database.orm.ORMObject} subclass
        """

    def add_deleted_object(object):
        """Adds a deleted C{object} to the transaction.

        @param object: an L{stoqlib.database.orm.ORMObject} subclass
        """

    def add_modified_object(object):
        """Adds a modified object to the transaction.
        It's used to update TransactionEntry to keep a log of all modified object
        @param object: An ORMObject subclass which should be marked as modified
        """

    def savepoint(name):
        """Creates a new savepoint
        @param name: name of savepoint
        """

    def rollback_to_savepoint(name):
        """Rollback to a savepoint
        @param name: name of the savepoint
        """


class ICurrentBranch(Interface):
    """This is a mainly a marker for the current branch which is expected
    to implement L{stoqlib.domain.interfaces.IBranch}
    It's mainly used by get_current_branch()
    """


class ICurrentBranchStation(Interface):
    """This is a mainly a marker for the current branch station.
    It's mainly used by get_current_station()
    """


class ICurrentUser(Interface):
    """This is a mainly a marker for the current user.
    It's mainly used by get_current_user()
    """

    username = Attribute('Username')
    password = Attribute('Password')
    profile = Attribute('A profile represents a colection of information '
                        'which represents what this user can do in the '
                        'system')
