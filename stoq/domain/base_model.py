# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2004 Async Open Source <http://www.async.com.br>
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
stoq/domain/base_model.py:

   Base routines for domain modules.
"""

import datetime

from sqlobject import SQLObject
from sqlobject import DateTimeCol, ForeignKey
from sqlobject.styles import mixedToUnder
from sqlobject.inheritance import InheritableSQLObject
from twisted.python.components import Componentized, Interface, Adapter
from twisted.python.reflect import qual



#
# Base classes
#



class AbstractModel:

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
    # Auxiliar methods
    #

    

    def clone(self):
        # Get a persistent copy of an existent object. Remember that we can
        # not use copy because this approach will not activate SQLObject
        # methods which allow creating persitent objects. We also always
        # need a new id and _sys_data values for each copied object.
        if not isinstance(self, SQLObject):
            raise TypeError('Invalid type for parent class, got %s' %
                            type(self))
        klass = type(self)
        kwargs = {'connection' : self._connection}
        columns = self._columns

        if isinstance(self, InheritableSQLObject):
            # This is an InheritableSQLObject object and we also 
            # need to copy data from the parent.
            # XXX SQLObject should provide a get_parent method.
            columns += self._parent._columns
        for column in columns:
            if column.name == '_sys_data':
                continue
            kwargs[column.name] = getattr(self, column.name)
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
    # Inheritable objects methods
    #



    def set_original_references(self, _original, kwargs):
        assert isinstance(self, Adapter)
        if _original:
            kwargs['_originalID'] = getattr(_original, 'id', None)
            kwargs['_original'] = _original
        # HMMM!
        self.__dict__['_original'] = _original


class BaseDomain(SQLObject, AbstractModel):
    model_created = DateTimeCol(default=datetime.datetime.now())
    model_modified = DateTimeCol(default=datetime.datetime.now())
    # TODO add in the future a 'last_changed_by_user' attribute here
    class sqlmeta:
        cacheValues = False
        # FIXME Waiting for SQLObject bug fix. Select method doesn't work 
        # properly with parent tables for inherited tables. E.g:
        # list(AbstractSellable.select()) = list of AbstractSellable objects
        # instead child table objects.
        #lazyUpdate = True

class Domain(BaseDomain, Componentized):

    def __init__(self, *args, **kwargs):
        BaseDomain.__init__(self, *args, **kwargs)
        Componentized.__init__(self)

    @classmethod
    def getAdapterClass(cls, iface):
        iface_str = qual(iface)
        if not cls._facets.has_key(iface_str):
            raise TypeError(
                "%s doesn't have a facet for interface %s" %
                (cls.__name__, iface.__name__))
        return cls._facets[iface_str]

    def getComponent(self, iface, registry, default, connection=None):
        k = qual(iface)
        adapter = self._adapterCache.get(k)
        if adapter is not None:
            if connection:
                adapter._connection = connection
            return adapter
            
        adapterClass = self._facets.get(k)
        if adapterClass:
            results = adapterClass.select("original_id = %d" % self.id,
                                          connection=connection)
            
            assert not results.count() > 1 
            if results.count() == 1:
                adapter = results[0]
                self.setComponent(iface, adapter)
            
        return adapter

    @classmethod
    def registerFacet(cls, facet):
        """
        registers a facet for class cls.
        
        For each interface specificed in class a facet for the specified
        class will be registered. Unless it already exists in the facet,
        a foreign key with the name '_original' will be assigned.
        The assigned key will have the name of the class cls.
        """
        
        ifaces = getattr(facet, '__implements__', ())
        if not isinstance(ifaces, (tuple, list)):
            ifaces = (ifaces,)

        if not hasattr(cls, '_facets'):
            cls._facets = {}

        for iface in ifaces:
            if cls._facets.has_key(iface):
                raise TypeError(
                    '%s does already have a facet for interface %s' %
                    (cls.__name__, iface.__name__))
            cls._facets[qual(iface)] = facet

        if not hasattr(facet, '_original'):
            facet.sqlmeta.addColumn(ForeignKey(cls.__name__,
                                    name='_original',
                                    forceDBName=True))

    def addFacet(self, iface, *args, **kwargs):
        if not issubclass(iface, Interface):
            raise TypeError('iface must be a ConnInterface subclass')

        facets = self.__class__._facets

        k = qual(iface)
        
        funcName = 'facet_%s_add' % iface.__name__
        func = getattr(self, funcName, None)
        if func:
            adapter = func(*args, **kwargs)
        elif facets.has_key(k):
            adapterClass = facets[k]
            adapter = adapterClass(self, *args, **kwargs)
        else:
            adapter = None
            
        if adapter:
            self.setComponent(iface, adapter)

        return adapter 
            
    def removeFacet(self, iface, *args, **kwargs):
        if not issubclass(iface, Interface):
            raise TypeError('iface must be a ConnInterface subclass')

        if not self._facets.has_key(iface):
            raise TypeError('%s does not have a facet for interface %s' %
                            (self.__name__, iface.__name__))
        
        funcName = 'facet_%s_remove' % iface.__name__
        func = getattr(self, funcName, None)
        if func:
            func(*args, **kwargs)

        k = qual(iface)
        del self._facets[k]
        if self._adapterCache.has_key(k):
            self.unsetComponent(iface)



#
# Adapters
#



class ModelAdapter(BaseDomain, Adapter):
    def __init__(self, _original=None, *args, **kwargs):
        self.set_original_references(_original, kwargs)
        BaseDomain.__init__(self, *args, **kwargs)



#
# Inheritance 
#



class InheritableModel(InheritableSQLObject, AbstractModel):
    model_created = DateTimeCol(default=datetime.datetime.now())
    model_modified = DateTimeCol(default=datetime.datetime.now())
    class sqlmeta:
        cacheValues = False
        #lazyUpdate = True

class InheritableModelAdapter(InheritableModel, Adapter):

    def __init__(self, _original=None, *args, **kwargs):
        self.set_original_references(_original, kwargs)
        InheritableModel.__init__(self, *args, **kwargs)
