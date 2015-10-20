# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2015 Async Open Source <http://www.async.com.br>
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

from storm.info import get_obj_info
from storm.references import Reference
from storm.store import AutoReload, PENDING_ADD, PENDING_REMOVE

from stoqlib.database.properties import DateTimeCol, IntCol, IdCol, BoolCol
from stoqlib.database.orm import ORMObject


(_OBJ_CREATED,
 _OBJ_DELETED,
 _OBJ_UPDATED) = range(3)


class TransactionEntry(ORMObject):
    __storm_table__ = 'transaction_entry'

    id = IntCol(primary=True, default=AutoReload)
    te_time = DateTimeCol(allow_none=False)
    dirty = BoolCol(default=True)


class Domain(ORMObject):
    __storm_table__ = 'invalid'

    repr_fields = []

    id = IdCol(primary=True, default=AutoReload)
    te_id = IntCol(default=AutoReload)
    te = Reference(te_id, TransactionEntry.id)

    def __init__(self, *args, **kwargs):
        self._listen_to_events()
        ORMObject.__init__(self, *args, **kwargs)

    def __repr__(self):
        parts = ['%r' % self.id]
        for field in self.repr_fields:
            parts.append('%s=%r' % (field, getattr(self, field)))

        desc = ' '.join(parts)
        return '<%s %s>' % (self.__class__.__name__, desc)

    def __storm_loaded__(self):
        self._listen_to_events()

    def __storm_pre_flush__(self):
        obj_info = get_obj_info(self)
        pending = obj_info.get("pending")
        stoq_pending = obj_info.get('stoq-status')
        store = obj_info.get("store")

        if pending is PENDING_ADD:
            obj_info['stoq-status'] = _OBJ_CREATED
        elif pending is PENDING_REMOVE:
            obj_info['stoq-status'] = _OBJ_DELETED
        else:
            # This is storm's approach to check if the obj has pending changes,
            # but only makes sense if the obj is not being created/deleted.
            if (store._get_changes_map(obj_info, True) and
                    stoq_pending not in [_OBJ_CREATED, _OBJ_DELETED]):
                obj_info['stoq-status'] = _OBJ_UPDATED

    #
    #   Private
    #

    def _listen_to_events(self):
        event = get_obj_info(self).event
        event.hook('before-removed', self._on_object_before_removed)
        event.hook('before-commited', self._on_object_before_commited)

    def _on_object_before_removed(self, obj_info):
        # If the obj was created and them removed, nothing needs to be done.
        # It never really got into the database.
        if obj_info.get('stoq-status') == _OBJ_CREATED:
            obj_info['stoq-status'] = None
        else:
            self.on_delete()

        # This is emited right before the object is removed from the store.
        # We must also remove the transaction entry, but the entry should be
        # deleted *after* the object is deleted, thats why we need to specify
        # the flush order.
        store = obj_info.get("store")
        store.remove(self.te)
        store.add_flush_order(self, self.te)

    def _on_object_before_commited(self, obj_info):
        # on_create/on_update hooks can modify the object and make it be
        # flushed again, so lets reset pending before calling them
        stoq_pending = obj_info.get('stoq-status')
        obj_info['stoq-status'] = None

        if stoq_pending == _OBJ_CREATED:
            self.on_create()
        elif stoq_pending == _OBJ_UPDATED:
            self.on_update()

    def on_create(self):
        pass

    def on_update(self):
        pass

    def on_delete(self):
        pass
