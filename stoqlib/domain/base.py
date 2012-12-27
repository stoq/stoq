# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2012 Async Open Source <http://www.async.com.br>
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
The base :class:`Domain` class for Stoq.

"""

from storm.store import Store
from storm.info import get_cls_info

# pylint: disable=E1101
from stoqlib.database.orm import AutoReload, IntCol, Reference
from stoqlib.database.orm import ORMObject, const, AND, ILIKE
from stoqlib.database.runtime import (StoqlibStore,
                                      get_current_user, get_current_station)
from stoqlib.domain.system import TransactionEntry


class Domain(ORMObject):
    """The base domain for Stoq.

    This builds on top of :class:`stoqlib.database.orm.ORMObject` and adds:

    * created and modified |transactionentry|, a log which is mainly used
      by database synchonization, it allows us to find out what has been
      modified and created within a specific time frame.
    * create/update/modify hooks, which some domain objects implement to
      fire of events that can be used to find out when a specific
      domain event is triggered, eg a |sale| is created, a |product| is
      modified. etc.
    * cloning of domains, when you want to create a new similar domain
    * function to check if an value of a column is unique within a domain.

    Not all domain objects need to subclass Domain, some, such as
    :class:`stoqlib.domain.system.SystemTable` inherit from ORMObject.
    """

    # FIXME: this is only used by pylint
    __storm_table__ = 'invalid-not-used'

    id = IntCol(primary=True, default=AutoReload)

    te_created_id = IntCol(default=None)

    #: a |transactionentry| for when the domain object was created
    te_created = Reference(te_created_id, 'TransactionEntry.id')

    te_modified_id = IntCol(default=None)

    #: a |transactionentry| for when the domain object last modified
    te_modified = Reference(te_modified_id, 'TransactionEntry.id')

    def __init__(self, *args, **kwargs):
        ORMObject.__init__(self, *args, **kwargs)

    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.id)

    #
    # ORMObject
    #

    def on_object_changed(self):
        if self._creating:
            return
        store = self._store

        if isinstance(store, StoqlibStore):
            store.add_modified_object(self)

    def on_object_added(self):
        store = Store.of(self)
        store.block_implicit_flushes()
        user = get_current_user(store)
        station = get_current_station(store)
        store.unblock_implicit_flushes()

        for attr, entry_type in [('te_created', TransactionEntry.CREATED),
                                 ('te_modified', TransactionEntry.MODIFIED)]:
            entry = TransactionEntry(
                te_time=const.NOW(),
                user_id=user and user.id,
                station_id=station and station.id,
                type=entry_type,
                store=store)
            setattr(self, attr, entry)

        store.add_created_object(self)

    def on_object_removed(self):
        self._store.add_deleted_object(self)

    #
    # Public API
    #

    @classmethod
    def delete(cls, id, store=None):
        obj = cls.get(id, store=store)
        Store.of(obj).remove(obj)

    def on_create(self):
        """Called when *self* is about to be created on the database

        This hook can be overridden on child classes for improved functionality.

        A trick you may want to use: Use :meth:`ORMObject.get_store` to get the
        :class:`store <stoqlib.database.runtime.StoqlibStore>` in which
        *self* lives and do your modifications in it.
        """

    def on_update(self):
        """Called when *self* is about to be updated on the database

        This hook can be overridden on child classes for improved
        functionality.

        A trick you may want to use: Use :meth:`ORMObject.get_store` to get the
        :class:`store <stoqlib.database.runtime.StoqlibStore>` in which
        *self* lives and do your modifications in it.
        """

    def on_delete(self):
        """Called when *self* is about to be updated on the database

        This hook can be overridden on child classes for improved
        functionality.

        A trick you may want to use: Use :meth:`ORMObject.get_store` to get the
        :class:`store <stoqlib.database.runtime.StoqlibStore>` in which
        *self* lives and do your modifications in it.

        Do not try to modify *self*, as it was marked as obsolete by
        :class:`stoqlib.database.orm.ORMObject` and it will result in errors.
        """

    def clone(self):
        """Get a persistent copy of an existent object. Remember that we can
        not use copy because this approach will not activate ORMObject
        methods which allow creating persitent objects. We also always
        need a new id for each copied object.

        :returns: the copy of ourselves
        """

        kwargs = {}
        for column in get_cls_info(self.__class__).columns:
            # FIXME: Make sure this is cloning correctly
            name = column.name
            if name in ['id', 'identifier',
                        'te_created_id',
                        'te_modified_id']:
                continue
            if name.endswith('_id'):
                name = name[:-3]
            kwargs[name] = getattr(self, name)

        klass = type(self)
        return klass(store=self._store, **kwargs)

    def check_unique_value_exists(self, attribute, value,
                                  case_sensitive=True):
        """Returns ``True`` if we already have the given attribute
        and value in the database, but ignoring myself.

        :param attribute: the attribute that should be unique
        :param value: value that we will check if exists in the database
        :param case_sensitive: If the checking should be case sensitive or
          not.
        """

        return self.check_unique_tuple_exists({attribute: value},
                                              case_sensitive)

    def check_unique_tuple_exists(self, values, case_sensitive=True):
        """Returns ``True`` if we already have the given attributes and values
        in the database, but ignoring myself.

        :param values: dictionary of attributes:values that we will check if
          exists in the database.
        :param case_sensitive: If the checking should be case sensitive or
          not.
        """

        if all([value in ['', None] for value in values.values()]):
            return False

        clauses = []
        for attr, value, in values.items():
            if not isinstance(value, unicode) or case_sensitive:
                clauses.append(attr == value)
            else:
                clauses.append(ILIKE(attr, value))
        # Remove myself from the results.
        if hasattr(self, 'id'):
            clauses.append(self.q.id != self.id)
        query = AND(*clauses)

        return self.select(query, store=self.store).count() > 0

    # FIXME: this a bad name API wise, should be
    #        last_modified_user or so, if it's needed at all.
    @property
    def user(self):
        """The |loginuser| who last modified this object"""
        return self.te_modified.user
