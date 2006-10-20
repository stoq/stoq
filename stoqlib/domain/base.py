# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005,2006 Async Open Source <http://www.async.com.br>
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
""" Base routines for domain modules """

import datetime

from kiwi.component import get_utility
from sqlobject import SQLObject
from sqlobject import ForeignKey, BoolCol
from sqlobject.inheritance import InheritableSQLObject
from sqlobject.dbconnection import DBAPI, Transaction
from sqlobject.converters import sqlrepr
from sqlobject.sqlbuilder import SQLExpression, AND
from zope.interface.interface import adapter_hooks

from stoqlib.domain.transaction import TransactionEntry
from stoqlib.lib.component import Adapter, Adaptable
from stoqlib.lib.interfaces import IDatabaseSettings
from stoqlib.database.runtime import (StoqlibTransaction, get_current_user,
                                      get_current_station)


DATABASE_ENCODING = 'UTF-8'

#
# SQLObject provides for our adapter infrastructure
#

class SQLObjectAdapter(Adapter):
    def __init__(self, _original, kwargs):
        Adapter.__init__(self, _original)

        if _original:
            kwargs['_originalID'] = getattr(_original, 'id', None)
            kwargs['_original'] = _original
        # HMMM!
        self.__dict__['_original'] = _original

class AdaptableSQLObject(Adaptable):
    @classmethod
    def registerFacet(cls, facet, *ifaces):
        super(AdaptableSQLObject, cls).registerFacet(facet, *ifaces)

        if not hasattr(facet, '_original'):
            facet.sqlmeta.addColumn(ForeignKey(cls.__name__,
                                    name='_original',
                                    forceDBName=True))


def _adaptable_sqlobject_adapter_hook(iface, obj):
    """
    A zope.interface hook used to fetch an adapter when calling
    iface(adaptable).
    It fetches the facet type and does a select in the database to
    see if the object is present.

    @param iface: the interface to adapt to
    @param obj: object we want to adapt
    """

    # We're only interested in Adaptable subclasses which defines
    # the getFacetType method
    if not isinstance(obj, AdaptableSQLObject):
        return

    try:
        facetType = obj.getFacetType(iface)
    except LookupError:
        # zope.interface will handle this and raise TypeError,
        # see InterfaceClass.__call__ in zope/interface/interface.py
        return None

    # FIXME: Use selectOneBy
    if facetType:
        results = facetType.selectBy(
            _originalID=obj.id, connection=obj.get_connection())

    if results.count() == 1:
        return results[0]

adapter_hooks.append(_adaptable_sqlobject_adapter_hook)

#
# Abstract classes
#


class AbstractModel(object):
    """Generic methods for any domain classes."""

    # For pylint
    _is_valid_model = False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __eq__(self, other):
        if type(self) is not type(other):
            return False
        return self.id == other.id

    #
    # Overwriting some SQLObject methods
    #

    def _create(self, *args, **kwargs):
        conn = kwargs.get('connection', self._connection)
        user = get_current_user(conn)
        station = get_current_station(conn)

        timestamp = datetime.datetime.now()
        for entry, entry_type in [('te_created', TransactionEntry.CREATED),
                                  ('te_modified', TransactionEntry.MODIFIED)]:
            kwargs[entry] = TransactionEntry(
                timestamp=timestamp,
                user_id=user and user.id,
                station_id=station and station.id,
                type=entry_type,
                connection=conn)
        super(AbstractModel, self)._create(*args, **kwargs)

    def _init(self, *args, **kwargs):
        # _init is called when an object is created OR fetched from the
        # database.
        # We're overriding here because we want to keep track of all objects
        # inside a transaction
        super(AbstractModel, self)._init(*args, **kwargs)

        conn = self.get_connection()
        if isinstance(conn, StoqlibTransaction):
            conn.add_object(self)

    @classmethod
    def select(cls, clause=None, connection=None, **kwargs):
        cls._check_connection(connection)
        if clause and not isinstance(clause, SQLExpression):
            raise TypeError("Stoqlib doesn't support non sqlbuilder queries")
        query = cls.q._is_valid_model == True
        if clause:
            # This make queries in stoqlib applications consistent
            clause = AND(query, clause)
        else:
            clause = query
        clause_repr = sqlrepr(clause, get_utility(IDatabaseSettings).rdbms)
        if isinstance(clause_repr, unicode):
            clause = clause_repr.encode(DATABASE_ENCODING)
        return super(AbstractModel, cls).select(clause=clause,
                                                connection=connection,
                                                **kwargs)

    @classmethod
    def selectBy(cls, connection=None, **kw):
        # This make queries in stoqlib applications consistent
        kw['_is_valid_model'] = True
        cls._check_connection(connection)
        for field_name, search_str in kw.items():
            if not isinstance(search_str, unicode):
                continue
            kw[field_name] = search_str.encode(DATABASE_ENCODING)
        return super(AbstractModel, cls).selectBy(connection=connection,
                                                  **kw)

    @classmethod
    def selectOne(cls, clause=None, clauseTables=None, lazyColumns=False,
                  connection=None):
        cls._check_connection(connection)
        if clause and not isinstance(clause, SQLExpression):
            raise TypeError("Stoqlib doesn't support non sqlbuilder queries")
        query = cls.q._is_valid_model == True
        if clause:
            # This make queries in stoqlib applications consistent
            clause = AND(query, clause)
        else:
            clause = query
        clause_repr = sqlrepr(clause, get_utility(IDatabaseSettings).rdbms)
        if isinstance(clause_repr, unicode):
            clause = clause_repr.encode(DATABASE_ENCODING)
        return super(AbstractModel, cls).selectOne(
            clause=clause,
            clauseTables=clauseTables,
            lazyColumns=lazyColumns,
            connection=connection)

    @classmethod
    def selectOneBy(cls, clause=None, connection=None, **kw):
        kw['_is_valid_model'] = True
        cls._check_connection(connection)
        for field_name, search_str in kw.items():
            if not isinstance(search_str, unicode):
                continue
            kw[field_name] = search_str.encode(DATABASE_ENCODING)
        return super(AbstractModel, cls).selectOneBy(connection=connection,
                                                     **kw)


    #
    # Classmethods
    #

    @classmethod
    def _check_connection(cls, connection):
        if connection is None and issubclass(cls, InheritableSQLObject):
            # For an uncertain reason SQLObject doesn't send child
            # connection to its parent. the interesting thing is that
            # the connection is actually properly set on the instances
            return
        if connection is None:
            raise ValueError("You must provide a valid connection "
                             "argument for class %s" % cls)
        if not isinstance(connection, (Transaction, DBAPI)):
            raise TypeError("The argument connection must be of type "
                            "Transaction, or DBAPI got %r instead"
                            % connection)

    #
    # Useful methods to deal with transaction isolation problems. See
    # domain/base docstring for further informations
    #

    def set_valid(self):
        if self._is_valid_model:
            raise ValueError('This model is already valid.')
        self._is_valid_model = True

    def set_invalid(self):
        if not self._is_valid_model:
            raise ValueError('This model is already invalid.')
        self._is_valid_model = False

    def get_valid(self):
        return self._is_valid_model

    #
    # General methods
    #

    def clone(self):
        """Get a persistent copy of an existent object. Remember that we can
        not use copy because this approach will not activate SQLObject
        methods which allow creating persitent objects. We also always
        need a new id for each copied object.
        """
        columns = self.sqlmeta.columnList

        if isinstance(self, InheritableSQLObject):
            # This is an InheritableSQLObject object and we also
            # need to copy data from the parent.
            # XXX SQLObject should provide a get_parent method.
            columns += self.sqlmeta.parentClass.sqlmeta.columnList

        kwargs = {}
        for column in columns:
            if column.origName == 'childName':
                continue
            kwargs[column.origName] = getattr(self, column.origName)

        klass = type(self)
        return klass(connection=self._connection, **kwargs)

    def get_connection(self):
        return self._connection

class BaseDomain(AbstractModel, SQLObject):
    """An abstract mixin class for domain classes"""



#
# Base classes
#


class Domain(BaseDomain, AdaptableSQLObject):
    """If you want to be able to extend a certain class with adapters or
    even just have a simple class without sublasses, this is the right
    choice.
    """
    def __init__(self, *args, **kwargs):
        BaseDomain.__init__(self, *args, **kwargs)
        AdaptableSQLObject.__init__(self)

    @classmethod
    def iselect(cls, iface, *args, **kwargs):
        """
        Like select, but search on the adapter implementing the interface iface
        associated with the domain class cls.

        @param iface: interface
        @returns: a SQLObject search result
        """
        adapter = cls.getAdapterClass(iface)
        return adapter.select(*args, **kwargs)

    @classmethod
    def iselectBy(cls, iface, *args, **kwargs):
        """
        Like selectBy, but search on the adapter implementing the interface iface
        associated with the domain class cls.

        @param iface: interface
        @returns: a SQLObject search result
        """
        adapter = cls.getAdapterClass(iface)
        return adapter.selectBy(*args, **kwargs)

    @classmethod
    def iselectOne(cls, iface, *args, **kwargs):
        """
        Like selectOne, but search on the adapter implementing the interface iface
        associated with the domain class cls.

        @param iface: interface
        @returns: None, object or raises SQLObjectMoreThanOneResultError
        """
        adapter = cls.getAdapterClass(iface)
        return adapter.selectOne(*args, **kwargs)

    @classmethod
    def iselectOneBy(cls, iface, *args, **kwargs):
        """
        Like selectOneBy, but search on the adapter implementing the interface iface
        associated with the domain class cls.

        @param iface: interface
        @returns: None, object or raises SQLObjectMoreThanOneResultError
        """
        adapter = cls.getAdapterClass(iface)
        return adapter.selectOneBy(*args, **kwargs)

    @classmethod
    def iget(cls, iface, object_id, **kwargs):
        """
        Like get, but gets on the adapter implementing the interface iface
        associated with the domain class cls.

        @param iface: interface
        @param object_id: id of object
        @returns: the SQLObject
        """
        adapter = cls.getAdapterClass(iface)
        return adapter.get(object_id, **kwargs)


class InheritableModel(AbstractModel, InheritableSQLObject, AdaptableSQLObject):
    """Subclasses of InheritableModel are able to be base classes of other
    classes in a database level. Adapters are also allowed for these classes
    """
    def __init__(self, *args, **kwargs):
        AbstractModel.__init__(self)
        InheritableSQLObject.__init__(self, *args, **kwargs)
        AdaptableSQLObject.__init__(self)


class BaseSQLView:
    """A base marker class for SQL Views"""


#
# Adapters
#


class ModelAdapter(BaseDomain, SQLObjectAdapter):

    def __init__(self, _original=None, *args, **kwargs):
        SQLObjectAdapter.__init__(self, _original, kwargs) # Modifies kwargs
        BaseDomain.__init__(self, *args, **kwargs)


class InheritableModelAdapter(AbstractModel, InheritableSQLObject, SQLObjectAdapter):

    def __init__(self, _original=None, *args, **kwargs):
        AbstractModel.__init__(self)
        SQLObjectAdapter.__init__(self, _original, kwargs) # Modifies kwargs
        InheritableSQLObject.__init__(self, *args, **kwargs)

for klass in (InheritableModel, Domain, ModelAdapter, InheritableModelAdapter):
    sqlmeta = klass.sqlmeta
    sqlmeta.cacheValues = False
    sqlmeta.addColumn(ForeignKey('TransactionEntry', name='te_created',
                                 default=None))
    sqlmeta.addColumn(ForeignKey('TransactionEntry', name='te_modified',
                                 default=None))
    sqlmeta.addColumn(BoolCol(name='_is_valid_model', default=True,
                              forceDBName=True))

