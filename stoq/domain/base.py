# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s):       Evandro Vale Miquelito      <evandro@async.com.br>
##                  Johan Dahlin                <jdahlin@async.com.br>
##              
"""
stoq/domain/base.py:

   Base routines for domain modules.
"""

import datetime
import warnings

from kiwi.datatypes import currency
from kiwi.python import qual
from sqlobject import SQLObject
from sqlobject import DateTimeCol, ForeignKey, BoolCol
from sqlobject.converters import registerConverter
from sqlobject.styles import mixedToUnder
from sqlobject.inheritance import InheritableSQLObject
from stoqlib.exceptions import AdapterError
from stoqlib.database import Adapter
from zope.interface.adapter import AdapterRegistry
from zope.interface.declarations import implementedBy
from zope.interface.interface import Interface, InterfaceClass

from stoq.lib.runtime import get_connection

__connection__ = get_connection()

class MetaInterface(InterfaceClass):
    pass

class _Nothing:
    pass

class CannotAdapt(Exception):
    pass



#
# Abstract classes
#


class AbstractModel:
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
    # Classmethods
    #

    @classmethod
    def get_db_table_name(cls):
        assert issubclass(cls, SQLObject)
        className = cls.__name__
        return (className[0].lower() + mixedToUnder(className[1:]))

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
    # Auxiliar methods
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
            columns += self._parentClass.sqlmeta.columnList
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
        assert isinstance(self, Adapter)
        if _original:
            kwargs['_originalID'] = getattr(_original, 'id', None)
            kwargs['_original'] = _original
        # HMMM!
        self.__dict__['_original'] = _original


class Adaptable:
    def __init__(self):
        self._adapterCache = {}

    @classmethod
    def getAdapterClass(cls, iface):
        iface_str = qual(iface)
        if not iface_str in cls._facets:
            raise TypeError(
                "%s doesn't have a facet for interface %s" %
                (cls.__name__, iface.__name__))
        return cls._facets[iface_str]

    def _getComponent(self, iface, registry, connection=None):
        k = qual(iface)
        adapter = self._adapterCache.get(k)
        if adapter is not None:
            if connection:
                adapter._connection = connection
            return adapter
            
        adapterClass = self._facets.get(k)
        if adapterClass:
            query = adapterClass.q._originalID == self.id
            results = adapterClass.select(query,
                                          connection=connection)
            
            assert not results.count() > 1 
            if results.count() == 1:
                adapter = results[0]
                self._adapterCache[k] = adapter
        return adapter
        
    def addFacet(self, iface, *args, **kwargs):
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
            ifaces = list(implementedBy(facet))
            if len(ifaces) > 1:
                warnings.warn(
                    '%s has more than one iface, %s will be ignored' % (
                    qual(cls),
                    ', '.join(map(qual, ifaces[1:]))),
                    DeprecationWarning, stacklevel=2)
            del ifaces[1:]
            
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


class BaseDomain(SQLObject, AbstractModel):
    """An abstract mixin class for domain classes"""


#
# Interfaces
#


_NoImplementor = object()

class ConnMetaInterface(MetaInterface):
    """A special interface for Stoq domain classes. It allows us to make
    mandatory the connection argument
    """
    def __call__(self, adaptable, persist=None,
                 registry=None, connection=None):
        """
        Try to adapt `adaptable' to self; return `default' if it 
        was passed, otherwise raise L{CannotAdapt}.
        """
        if not isinstance(adaptable, (Domain, InheritableModel)):
            raise TypeError('Adaptable argument must be of type Domain '
                            'or InheritableModel, got %s instead' 
                            % type(adaptable))
        default = _Nothing
        registry = getRegistry()
        # should this be `implements' of some kind?
        if ((persist is None or persist) 
            and hasattr(adaptable, '_getComponent')):
            adapter = adaptable._getComponent(self, registry,
                                              connection=connection)
        else:
            adapter = registry.getAdapter(adaptable, self, _NoImplementor,
                                          persist=persist)
        if adapter is _NoImplementor:
            if hasattr(self, '__adapt__'):
                adapter = self.__adapt__.im_func(adaptable, default)
            else:
                adapter = default

        if adapter is _Nothing:
            raise CannotAdapt("%s cannot be adapted to %s." %
                              (adaptable, self))
        return adapter

ConnInterface = ConnMetaInterface('ConnInterface',
                                  __module__='stoq.domain.base')


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


class InheritableModel(InheritableSQLObject, AbstractModel, Adaptable):
    """Subclasses of InheritableModel are able to be base classes of other
    classes in a database level. Adapters are also allowed for these classes
    """
    def __init__(self, *args, **kwargs):
        InheritableSQLObject.__init__(self, *args, **kwargs)
        Adaptable.__init__(self)


#
# Adapters
#

class ModelAdapter(BaseDomain, Adapter):
        
    def __init__(self, _original=None, *args, **kwargs):
        self._set_original_references(_original, kwargs)
        BaseDomain.__init__(self, *args, **kwargs)


class InheritableModelAdapter(InheritableModel, Adapter):

    def __init__(self, _original=None, *args, **kwargs):
        self._set_original_references(_original, kwargs)
        InheritableModel.__init__(self, *args, **kwargs)




for klass in (InheritableModel, Domain, ModelAdapter):
    klass.sqlmeta.cacheValues = False
    klass.sqlmeta.addColumn(DateTimeCol(name='model_created',
                                        default=datetime.datetime.now))
    klass.sqlmeta.addColumn(DateTimeCol(name='model_modified',
                                        default=datetime.datetime.now))
    klass.sqlmeta.addColumn(BoolCol(name='_is_valid_model', default=True,
                                    forceDBName=True))
    # FIXME Waiting for SQLObject bug fix. Select method doesn't work 
    # properly with parent tables for inherited tables. E.g:
    # list(AbstractSellable.select()) = list of AbstractSellable 
    # objects instead child table objects.
    # lazyUpdate = True

def CurrencyConverter(value, db):
    return repr(float(value))
registerConverter(currency, CurrencyConverter)

_registry = AdapterRegistry()

def getRegistry():
    return _registry
