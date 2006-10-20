# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
## Author(s):       Johan Dahlin                <jdahlin@async.com.br>
##

"""Component infrastructure for Stoqlib"""

from kiwi.python import qual, namedAny
from zope.interface.interface import InterfaceClass

from stoqlib.exceptions import AdapterError

# FIXME: Remove these two, see #2819
class MetaInterface(InterfaceClass):
    pass

class NoneMetaInterface(MetaInterface):
    """
    Meta class for NoneInterface
    It's identical to a normal zope.interface.Interface type except
    that the default second argument is None
    """
    def __call__(self, adaptable, alternate=None):
        return MetaInterface.__call__(self, adaptable, alternate)

NoneInterface = NoneMetaInterface('NoneInterface',
                                  __module__='stoqlib.lib.component')

#
# Adaptors
#

class Adapter(object):
    def __init__(self, adaptable):
        self._adaptable = adaptable

    def __ne__(self, other):
        return not self.__eq__(other)

    def __eq__(self, other):
        if type(self) is not type(other):
            return False
        return self._adaptable.id == other._adaptable.id

    def get_adapted(self):
        return self._adaptable

class Adaptable(object):

    def __init__(self):
        self._adapterCache = {}

    #
    # Class methods
    #

    @classmethod
    def getFacetType(cls, iface):
        """
        Fetches a facet type associated with an interface, or raise
        LookupError if the facet type cannot be found.

        @param iface: interface name for the facet to grab
        @returns: the facet type for the interface
        """

        facets = getattr(cls, '_facets', [])

        iface_str = qual(iface)
        if not iface_str in facets:
            raise LookupError(
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

        facets = getattr(cls, '_facets', {})

        return facets.values()

    @classmethod
    def registerFacet(cls, facet, *ifaces):
        """
        Registers a facet for class cls.

        The 'facet' argument is an adapter class which will be registered
        using its interfaces specified in __implements__ argument.

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
            if not isinstance(iface, InterfaceClass):
                raise TypeError('iface must be an Interface')

            if qual(iface) in cls._facets.keys():
                raise TypeError(
                    '%s does already have a facet for interface %s' %
                    (cls.__name__, iface.__name__))
            cls._facets[qual(iface)] = facet

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
        if not isinstance(iface, InterfaceClass):
            raise TypeError('iface must be an Interface')

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
        if not isinstance(iface, InterfaceClass):
            raise TypeError('iface must be an Interface')

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

            facet = iface(self, None)
            # Filter out facets which are not set
            if facet is None:
                continue
            facets.append(facet)
        return facets
