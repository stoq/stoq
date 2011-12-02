# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2007 Async Open Source <http://www.async.com.br>
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
""" Base routines for domain modules """

# pylint: disable=E1101
from zope.interface.interface import adapter_hooks

from stoqlib.database.orm import orm_name, ForeignKey, IntCol
from stoqlib.database.orm import ORMObject, const, AND, ILIKE
from stoqlib.database.runtime import (StoqlibTransaction,
                                      get_current_user, get_current_station)
from stoqlib.domain.system import TransactionEntry
from stoqlib.lib.component import Adapter, Adaptable


DATABASE_ENCODING = 'UTF-8'

#
# Persistent ORMObject adapters
#


class ORMObjectAdapter(Adapter):
    def __init__(self, adaptable, kwargs):
        Adapter.__init__(self, adaptable)

        if adaptable:
            kwargs['original'] = adaptable

        self.__dict__['original'] = adaptable

    def get_adapted(self):
        return self.original


class AdaptableORMObject(Adaptable):
    @classmethod
    def registerFacet(cls, facet, *ifaces):
        super(AdaptableORMObject, cls).registerFacet(facet, *ifaces)

        if not issubclass(facet, ORMObject):
            return

        # This might not be the best location to do this, but it has
        # a nice lazy property to it. The alternative would be to
        # attach it to all domain objects during startup, or just
        # load the schema definition from postgres dynamically.
        if not hasattr(facet, 'original'):
            facet.sqlmeta.addColumn(ForeignKey(cls.__name__,
                                    name='original',
                                    forceDBName=True))


def _adaptable_orm_adapter_hook(iface, obj):
    """A zope.interface hook used to fetch an adapter when calling
    iface(adaptable).
    It fetches the facet type and does a select in the database to
    see if the object is present.

    @param iface: the interface to adapt to
    @param obj: object we want to adapt
    """

    # We're only interested in Adaptable subclasses which defines
    # the getFacetType method
    if not isinstance(obj, AdaptableORMObject):
        return

    try:
        facetType = obj.getFacetType(iface)
    except LookupError:
        # zope.interface will handle this and raise TypeError,
        # see InterfaceClass.__call__ in zope/interface/interface.py
        return None

    if not facetType:
        return

    # Persistant Adapters
    if issubclass(facetType, ORMObjectAdapter):
        # FIXME: Use selectOneBy
        results = facetType.selectBy(
            originalID=obj.id, connection=obj.get_connection())

        if results.count() == 1:
            return results[0]
    # Non-Persistant Adapters
    else:
        return facetType(obj)

adapter_hooks.append(_adaptable_orm_adapter_hook)

#
# Abstract classes
#


class AbstractModel(object):
    """Generic methods for any domain classes."""

    def __ne__(self, other):
        return not self.__eq__(other)

    def __eq__(self, other):
        if type(self) is not type(other):
            return False
        return self.id == other.id

    #
    # Overwriting some ORMObject methods
    #

    def _create(self, *args, **kwargs):
        # Don't flush right now. The object being created is not complete
        # yet!
        conn = self._connection
        conn.block_implicit_flushes()
        user = get_current_user(conn)
        station = get_current_station(conn)
        conn.unblock_implicit_flushes()

        for entry, entry_type in [('te_created', TransactionEntry.CREATED),
                                  ('te_modified', TransactionEntry.MODIFIED)]:
            kwargs[entry] = TransactionEntry(
                te_time=const.NOW(),
                user_id=user and user.id,
                station_id=station and station.id,
                type=entry_type,
                connection=conn)
        super(AbstractModel, self)._create(*args, **kwargs)
        conn.add_created_object(self)

    def destroySelf(self):
        super(AbstractModel, self).destroySelf()

        if isinstance(self._connection, StoqlibTransaction):
            self._connection.add_deleted_object(self)

    def _SO_setValue(self, name, value, from_, to):
        super(AbstractModel, self)._SO_setValue(name, value, from_, to)

        if not self.sqlmeta._creating:
            connection = self._connection
            if isinstance(connection, StoqlibTransaction):
                connection.add_modified_object(self)

    #
    # General methods
    #

    def on_create(self):
        """Called when C{self} is about to be created on the database

        This hook can be overridden on child classes for improved
        functionality.
        @note: A trick you may want to use: Use C{self.get_connection}
            to get the L{stoqlib.runtime.StoqlibTransaction} in which
            C{self} lives and do your modifications in it.
        """
        pass

    def on_update(self):
        """Called when C{self} is about to be updated on the database

        This hook can be overridden on child classes for improved
        functionality.
        @note: A trick you may want to use: Use C{self.get_connection}
            to get the L{stoqlib.runtime.StoqlibTransaction} in which
            C{self} lives and do your modifications in it.
        """
        pass

    def on_delete(self):
        """Called when C{self} is about to be deleted on the database

        This hook can be overridden on child classes for improved
        functionality.
        @note: A trick you may want to use: Use C{self.get_connection}
            to get the L{stoqlib.runtime.StoqlibTransaction} in which
            C{self} lives.
        @attention: Do not try to modify C{self}, as it was marked as
            obsolet by L{stoqlib.database.orm.ORMObject} and it will
            result in errors.
        """
        pass

    def clone(self):
        """Get a persistent copy of an existent object. Remember that we can
        not use copy because this approach will not activate ORMObject
        methods which allow creating persitent objects. We also always
        need a new id for each copied object.
        """
        columns = self.sqlmeta.columnList

        kwargs = {}
        for column in columns:
            if column.origName == 'childName':
                continue
            kwargs[column.origName] = getattr(self, column.origName)

        klass = type(self)
        return klass(connection=self._connection, **kwargs)

    def get_connection(self):
        return self._connection


class _BaseDomain(AbstractModel, ORMObject):
    """An abstract mixin class for domain classes"""

    def check_unique_value_exists(self, attribute, value,
                                  case_sensitive=True):
        """Returns True if we already have the given attribute
        and value in the database, but ignoring myself.

        @param attribute: the attribute that should be unique
        @param value: value that we will check if exists in the database
        @param case_sensitive: If the checking should be case sensitive or
            not.
        """
        if not value:
            return False

        if case_sensitive:
            query = getattr(self.q, attribute) == value
        else:
            query = ILIKE(getattr(self.q, attribute), value)

        # Remove ourself from the results.
        if hasattr(self, 'id'):
            query = AND(query, self.q.id != self.id)
        return self.select(query, connection=self.get_connection()).count() > 0

#
# Base classes
#


class Domain(_BaseDomain, AdaptableORMObject):
    """If you want to be able to extend a certain class with adapters or
    even just have a simple class without sublasses, this is the right
    choice.
    """
    def __init__(self, *args, **kwargs):
        _BaseDomain.__init__(self, *args, **kwargs)
        AdaptableORMObject.__init__(self)

    def _create(self, id, **kw):
        if not isinstance(self._connection, StoqlibTransaction):
            raise TypeError(
                "creating a %s instance needs a StoqlibTransaction, not %s"
                % (self.__class__.__name__,
                   self._connection.__class__.__name__))
        _BaseDomain._create(self, id, **kw)

    if orm_name == 'storm':
        def __repr__(self):
            return '<%s %r %s>' \
                   % (self.__class__.__name__,
                      self.id,
                      ''
                      )

    @property
    def user(self):
        return self.te_modified.user

    @classmethod
    def iselect(cls, iface, *args, **kwargs):
        """Like select, but search on the adapter implementing the interface iface
        associated with the domain class cls.

        @param iface: interface
        @returns: a ORMObject search result
        """
        adapter = cls.getAdapterClass(iface)
        return adapter.select(*args, **kwargs)

    @classmethod
    def iselectBy(cls, iface, *args, **kwargs):
        """Like selectBy, but search on the adapter implementing the interface iface
        associated with the domain class cls.

        @param iface: interface
        @returns: a ORMObject search result
        """
        adapter = cls.getAdapterClass(iface)
        return adapter.selectBy(*args, **kwargs)

    @classmethod
    def iselectOne(cls, iface, *args, **kwargs):
        """Like selectOne, but search on the adapter implementing the interface iface
        associated with the domain class cls.

        @param iface: interface
        @returns: None, object or raises ORMObjectMoreThanOneResultError
        """
        adapter = cls.getAdapterClass(iface)
        return adapter.selectOne(*args, **kwargs)

    @classmethod
    def iselectOneBy(cls, iface, *args, **kwargs):
        """Like selectOneBy, but search on the adapter implementing the interface iface
        associated with the domain class cls.

        @param iface: interface
        @returns: None, object or raises ORMObjectMoreThanOneResultError
        """
        adapter = cls.getAdapterClass(iface)
        return adapter.selectOneBy(*args, **kwargs)

    @classmethod
    def iget(cls, iface, object_id, **kwargs):
        """Like get, but gets on the adapter implementing the interface iface
        associated with the domain class cls.

        @param iface: interface
        @param object_id: id of object
        @returns: the ORMObject
        """
        adapter = cls.getAdapterClass(iface)
        return adapter.get(object_id, **kwargs)


class BaseSQLView:
    """A base marker class for SQL Views"""


#
# Adapters
#


class ModelAdapter(_BaseDomain, ORMObjectAdapter):

    if orm_name == 'storm':
        originalID = IntCol('original_id')

    def __init__(self, original=None, *args, **kwargs):
        ORMObjectAdapter.__init__(self, original, kwargs) # Modifies kwargs
        _BaseDomain.__init__(self, *args, **kwargs)


for klass in (Domain, ModelAdapter):
    sqlmeta = klass.sqlmeta
    sqlmeta.addColumn(ForeignKey('TransactionEntry', name='te_created',
                                 default=None))
    sqlmeta.addColumn(ForeignKey('TransactionEntry', name='te_modified',
                                 default=None))
