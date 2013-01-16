# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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
"""
This classes should be used when creating a migration script.

Since the domain classes evolve, python db patches should use the classes as
they were when the patch was created.

Here you will find the base Domain class to inherit from.

If the Domain or TransactionEntry classes change in the future, a new generation
of this file will be created, and new patches should inherit from those classes
instead.

One catch though, is that References should not be specified with strings, only
real properties. This is necessary because if the same class is created in
more than one patch, we will end up with one reference matching more than one
class.
"""

# pylint: disable=E1101
from storm.info import get_obj_info
from storm.references import Reference
from storm.store import AutoReload

from stoqlib.database.properties import DateTimeCol, IntCol, BoolCol
from stoqlib.database.orm import ORMObject
from stoqlib.database.expr import StatementTimestamp


class TransactionEntry(ORMObject):
    __storm_table__ = 'transaction_entry'

    id = IntCol(primary=True, default=AutoReload)

    te_time = DateTimeCol(allow_none=False)
    user_id = IntCol(default=None)
    station_id = IntCol(default=None)
    dirty = BoolCol(default=True)


class Domain(ORMObject):
    __storm_table__ = 'invalid'

    id = IntCol(primary=True, default=AutoReload)

    te_id = IntCol(default=None)
    te = Reference(te_id, 'TransactionEntry.id')

    def __init__(self, *args, **kwargs):
        self._listen_to_events()
        self._creating = True
        ORMObject.__init__(self, *args, **kwargs)
        self._creating = False

    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.id)

    def __storm_loaded__(self):
        self._listen_to_events()
        self._creating = False

    # Private

    def _listen_to_events(self):
        event = get_obj_info(self).event
        event.hook('added', self._on_object_added)
        event.hook('changed', self._on_object_changed)
        event.hook('removed', self._on_object_removed)

    def _on_object_changed(self, obj_info, variable, old_value, new_value,
                           fromdb):
        if new_value is not AutoReload and not fromdb:
            if self._creating:
                return
            store = obj_info.get("store")
            store.add_modified_object(self)

    def _on_object_added(self, obj_info):
        store = obj_info.get("store")

        self.te = TransactionEntry(store=store,
            time=StatementTimestamp(),
            user_id=None,
            station_id=None)

        store.add_created_object(self)

    def _on_object_removed(self, obj_info):
        store = obj_info.get("store")
        store.add_deleted_object(self)

    def on_create(self):
        pass

    def on_update(self):
        pass

    def on_delete(self):
        pass
