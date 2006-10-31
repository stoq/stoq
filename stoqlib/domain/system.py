# -*- coding: utf-8 -*-
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
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s):       Evandro Vale Miquelito      <evandro@async.com.br>
##                  Johan Dahlin                <jdahlin@async.com.br>
##
##
""" Routines for system data management"""

import datetime

from sqlobject import SQLObject
from sqlobject import DateTimeCol, IntCol

from stoqlib import db_version
from stoqlib.domain.base import AbstractModel

class SystemTable(SQLObject, AbstractModel):
    """Stores information about database schema migration

    I{update_date}: the date when the database schema was updated
    I{version}: the version of the schema installed
    """

    update_date = DateTimeCol()
    version = IntCol()

    @classmethod
    def update(cls, trans, check_new_db=False, version=None):
        """Add a new entry on SystemTable with the current schema version"""
        result = cls.select(connection=trans)
        if result and check_new_db:
            raise ValueError(
                'SystemTable should be empty at this point got %d results' %
                result.count())
        elif not result and not check_new_db:
            raise ValueError(
                'SystemTable should have at least one item at this point, '
                'got nothing')

        return cls(version=version or db_version,
                   update_date=datetime.datetime.now(),
                   connection=trans)

    @classmethod
    def is_available(cls, conn):
        """
        Checks if Stoqlib database is properly installed
        @param conn: a database connection
        """
        table_name = cls.sqlmeta.table
        if not conn.tableExists(table_name):
            return False

        return bool(cls.select(connection=conn))

