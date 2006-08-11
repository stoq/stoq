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
from kiwi.python import qual, namedAny
from sqlobject import SQLObject
from sqlobject import ForeignKey, BoolCol
from sqlobject.inheritance import InheritableSQLObject
from sqlobject.dbconnection import DBAPI, Transaction
from sqlobject.converters import sqlrepr
from sqlobject.sqlbuilder import SQLExpression, AND

from zope.interface.interface import Interface

from stoqlib.database import db_table_name
from stoqlib.domain.transaction import TransactionEntry
from stoqlib.lib.component import Adapter, ConnMetaInterface
from stoqlib.lib.interfaces import IDatabaseSettings
from stoqlib.lib.runtime import (StoqlibTransaction, get_current_user,
                                 get_current_station)
from stoqlib.exceptions import (AdapterError, DatabaseInconsistency,
                                StoqlibError)


DATABASE_ENCODING = 'UTF-8'


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
        if not isinstance(self, Adapter):
            return self.id == other.id
        return self.get_adapted_id() == other.get_adapted_id()

    #
    # Overwriting some SQLObject methods
    #

    def _create(self, *args, **kwargs):
        conn = kwargs.get('connection', self._connection)
        try:
            user_id = get_current_user(conn).id
        except NotImplementedError:
            user_id = None

        try:
            station_id = get_current_station(conn).id
        except NotImplementedError:
            station_id = None

        timestamp = datetime.datetime.now()
        for entry in ['te_created', 'te_modified']:
            kwargs[entry] = TransactionEntry(
                timestamp=timestamp,
                user_id=user_id,
                station_id=station_id,
                connection=conn)
        super(AbstractModel, self)._create(*args, **kwargs)

    def _SO_setValue(self, *args, **kwargs):
        conn = self.get_connection()
        if not isinstance(conn, StoqlibTransaction):
            raise StoqlibError("Only StoqlibTransactions can edit data")

        conn.add_object(self)

        cls = self.__class__
        if issubclass(cls, InheritableSQLObject):
            InheritableSQLObject._SO_setValue(self, *args, **kwargs)
        elif issubclass(cls, SQLObject):
            SQLObject._SO_setValue(self, *args, **kwargs)
        else:
            raise StoqlibError("Invalid domain class type, it should be "
                               "a subclass of SQLObject or "
                               "InheritableSQLObject, got %s" % cls)

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

    #
    # Classmethods
    #

    @classmethod
    def get_db_table_name(cls):
        assert issubclass(cls, SQLObject)
        return db_table_name(cls)

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
        if not isinstance(self, SQLObject):
            raise TypeError('Invalid type for parent class, got %s' %
                            type(self))
        klass = type(self)
        kwargs = {'connection': self._connection}
        columns = self.sqlmeta.columnList

        if issubclass(klass, InheritableSQLObject):
            # This is an InheritableSQLObject object and we also
            # need to copy data from the parent.
            # XXX SQLObject should provide a get_parent method.
            columns += self.sqlmeta.parentClass.sqlmeta.columnList
        for column in columns:
            if column.origName == 'childName':
                continue
            kwargs[column.origName] = getattr(self, column.origName)
        return klass(**kwargs)

    def get_adapted(self):
        assert isinstance(self, Adapter)
        return self._original

    def get_connection(self):
        return self._connection

    def get_adapted_id(self):
        assert isinstance(self, Adapter)
        return self._original.id

    #
    # Inheritable object methods
    #

    def _set_original_references(self, _original, kwargs):
        if not isinstance(self, Adapter):
            raise TypeError("Invalid Adapter class, it should be inherited "
                            "from adapter, got %r"  % self)
        if _original:
            kwargs['_originalID'] = getattr(_original, 'id', None)
            kwargs['_original'] = _original
        # HMMM!
        self.__dict__['_original'] = _original


class Adaptable:
    def __init__(self):
        self._adapterCache = {}

    #
    # Private
    #

    def _getComponent(self, iface, registry):
        k = qual(iface)
        adapter = self._adapterCache.get(k)
        if adapter is not None:
            return adapter

        adapterClass = self._facets.get(k)
        if adapterClass:
            results = adapterClass.selectBy(_originalID=self.id,
                                            connection=self._connection)

            if results.count() > 1:
               raise DatabaseInconsistency("You should never have more then "
                                           "one adapter with the same "
                                           "original_id.")
            if results.count() == 1:
                adapter = results[0]
                self._adapterCache[k] = adapter
        return adapter

    #
    # Class methods
    #

    @classmethod
    def getFacetType(cls, iface):
        """
        Fetches a facet associated with an interface

        @param iface: interface name for the facet to grab
        @returns: the facet type for the interface
        """

        facets = getattr(cls, '_facets', [])

        iface_str = qual(iface)
        if not iface_str in facets:
            # XXX: LookupError
            raise TypeError(
                "%s doesn't have a facet for interface %s" %
                (cls.__name__, iface.__name__))

        return facets[iface_str]

    # XXX: Deprecate/Remove this
    getAdapterClass = getFacetType

    @classmethod
    def getFacetTypes(cls):
        """
        Returns facet classes for this object
        @returns: a list of facet classes
        """

        facets = getattr(cls, '_facets', [])

        return facets.values()

    @classmethod
    def registerFacet(cls, facet, *ifaces):
        """
        Registers a facet for class cls.

        The 'facet' argument is an adapter class which will be registered
        using its interfaces specified in __implements__ argument.
        Unless it already exists in the facet, a foreign key with the name
        '_original' will be assigned.

        Notes: the assigned key will have the name of the class cls.

        @param cls:
        @param facet:
        @param ifaces: optional list of interfaces to attach
        """
        if not hasattr(cls, '_facets'):
            cls._facets = {}

        if not ifaces:
            raise ValueError("It is not possible to register a facet "
                             "without specifing an interface")

        for iface in ifaces:
            if qual(iface) in cls._facets.keys():
                raise TypeError(
                    '%s does already have a facet for interface %s' %
                    (cls.__name__, iface.__name__))
            cls._facets[qual(iface)] = facet

        if not hasattr(facet, '_original'):
            facet.sqlmeta.addColumn(ForeignKey(cls.__name__,
                                    name='_original',
                                    forceDBName=True))

    #
    # Public API
    #

    def addFacet(self, iface, *args, **kwargs):
        """
        Adds a facet implementing iface for the current object
        @param iface: interface of the facet to add
        @returns: the facet
        """

        if isinstance(self, Adapter):
            raise TypeError("An adapter can not be adapted to another "
                            "object.")
        if not isinstance(iface, ConnMetaInterface):
            raise TypeError('iface must be a ConnInterface subclass')

        k = qual(iface)
        if k in self._adapterCache:
            raise AdapterError('%s already  have a facet for interface %s' %
                               (self.__class__.__name__, iface.__name__))

        facets = self.__class__._facets

        funcName = 'facet_%s_add' % iface.__name__
        func = getattr(self, funcName, None)

        if func:
            adapter = func(*args, **kwargs)
        elif facets.has_key(k):
            adapterClass = facets[k]
            adapter = adapterClass(self, *args, **kwargs)
        else:
            raise AdapterError("The object type %s doesn't implement an "
                               "adapter for interface %s" % (type(self),
                               iface))
        if adapter:
            self._adapterCache[k] = adapter

        return adapter

    def removeFacet(self, iface, *args, **kwargs):
        """
        @param iface:
        """
        if not issubclass(iface, Interface):
            raise TypeError('iface must be a ConnInterface subclass')

        facets = self.__class__._facets
        if not iface in facets:
            raise AdapterError('%s does not have a facet for interface %s' %
                               (self.__class__.__name__, iface.__name__))

        funcName = 'facet_%s_remove' % iface.__name__
        func = getattr(self, funcName, None)
        if func:
            func(*args, **kwargs)

        k = qual(iface)
        del facets[k]
        if k in self._adapterCache:
            del self._adapterCache[k]

    def getFacets(self):
        """
        Gets a list of facets assoicated with the current object.
        @returns: a list of facets
        """
        facet_types = getattr(self, '_facets', [])

        facets = []
        for iface_name in facet_types:
            iface = namedAny(iface_name)

            facet = iface(self)
            # Filter out facets which are not set
            if facet is None:
                continue
            facets.append(facet)
        return facets

class BaseDomain(AbstractModel, SQLObject):
    """An abstract mixin class for domain classes"""



#
# Base classes
#


class Domain(BaseDomain, Adaptable):
    """If you want to be able to extend a certain class with adapters or
    even just have a simple class without sublasses, this is the right
    choice.
    """
    def __init__(self, *args, **kwargs):
        BaseDomain.__init__(self, *args, **kwargs)
        Adaptable.__init__(self)

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


class InheritableModel(AbstractModel, InheritableSQLObject, Adaptable):
    """Subclasses of InheritableModel are able to be base classes of other
    classes in a database level. Adapters are also allowed for these classes
    """
    def __init__(self, *args, **kwargs):
        InheritableSQLObject.__init__(self, *args, **kwargs)
        Adaptable.__init__(self)


class BaseSQLView:
    """A base marker class for SQL Views"""


#
# Adapters
#


class ModelAdapter(BaseDomain, Adapter):

    def __init__(self, _original=None, *args, **kwargs):
        self._set_original_references(_original, kwargs)
        BaseDomain.__init__(self, *args, **kwargs)


class InheritableModelAdapter(AbstractModel, InheritableSQLObject, Adapter):

    def __init__(self, _original=None, *args, **kwargs):
        self._set_original_references(_original, kwargs)
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

