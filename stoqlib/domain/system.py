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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
""" Routines for system data management"""

# pylint: enable=E1101

from storm.store import AutoReload

from stoqlib.database.orm import ORMObject
from stoqlib.database.properties import DateTimeCol, IntCol, BoolCol


class SystemTable(ORMObject):
    """Stores information about database schema migration

    I{update}: the date when the database schema was updated
    I{patchlevel}: the version of the schema installed
    """
    __storm_table__ = 'system_table'

    id = IntCol(primary=True, default=AutoReload)
    updated = DateTimeCol()
    patchlevel = IntCol()
    generation = IntCol()

    @classmethod
    def is_available(cls, store):
        """Checks if Stoqlib database is properly installed
        :param store: a store
        """
        if not store.table_exists(u'system_table'):
            return False

        return bool(store.find(cls))


class TransactionEntry(ORMObject):
    """
    A TransactionEntry keeps track of state associated with a database
    transaction. It's main use case is to know information about the system when
    a domain object is created or modified.

    Such information will be used by stoq when syncing databases
    """
    __storm_table__ = 'transaction_entry'

    id = IntCol(primary=True, default=AutoReload)

    #: last time this object was modified
    te_time = DateTimeCol(allow_none=False)

    #: It this object was modified since the last time it was synced
    #: After the object is synced, this property will be set to ``False``, so
    #: that when the next sync begins, only the objects that are **dirty** will be
    #: processed
    dirty = BoolCol(default=True)
