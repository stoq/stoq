# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2007 Async Open Source <http://www.async.com.br>
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

from stoqlib.database.orm import DateTimeCol, IntCol
from stoqlib.database.orm import ORMObject
from stoqlib.domain.base import AbstractModel


class SystemTable(ORMObject, AbstractModel):
    """Stores information about database schema migration

    I{update}: the date when the database schema was updated
    I{patchlevel}: the version of the schema installed
    """

    updated = DateTimeCol()
    patchlevel = IntCol()
    generation = IntCol()

    @classmethod
    def is_available(cls, conn):
        """Checks if Stoqlib database is properly installed
        @param conn: a database connection
        """
        table_name = cls.sqlmeta.table
        if not conn.tableExists(table_name):
            return False

        return bool(cls.select(connection=conn))

