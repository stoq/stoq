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

"""Component infrastructure for Stoqlib

Stoqlib uses the adapter pattern U{http://en.wikipedia.org/wiki/Adapter_pattern}
to solve a specific set of problems, most noticeable roles for Persons.

First we need an object that we can adapt into something else.
It needs to be a subclass of AdaptableORMObject:

    >>> from stoqlib.lib.component import Adaptable
    >>> class Bike(Adaptable):
    ...     pass

We have no facets, yet so getFacetTypes() will return an empty list:

    >>> Bike.getFacetTypes()
    []

Let's define an interface for something we can adapt

    >>> from zope.interface.interface import Interface
    >>> class ISuspension(Interface):
    ...    def lockout():
    ...        pass
    ...    def is_locked():
    ...        pass

To be able to adapt our object into the interface we need to create an
adapter which needs to be a subclass of Adapter

    >>> from stoqlib.lib.component import Adapter
    >>> class BikeAdaptToSuspension(Adapter):
    ...     def __init__(self, original):
    ...         Adapter.__init__(self, original)
    ...         self.locked = False
    ...     def lockout(self):
    ...         self.locked = True
    ...     def is_locked(self):
    ...         return self.locked

We need to register the adapter, to attach the adapter to the
adaptable object, which will return the

    >>> Bike.registerFacet(BikeAdaptToSuspension, ISuspension)

If we try to register the same facet twice we'll receive an exception:

    >>> Bike.registerFacet(BikeAdaptToSuspension, ISuspension)
    Traceback (most recent call last):
        ...
    TypeError: Bike does already have a facet for interface ISuspension

Now, if you want to listen the adapter types for a specific interface you
can call getFacetTypes():

    >>> Bike.getFacetTypes() # doctest:+ELLIPSIS
    [<class '...BikeAdaptToSuspension'>]

    >>> bike = Bike()
    >>> ISuspension(bike) # doctest:+ELLIPSIS
    Traceback (most recent call last):
        ...
    TypeError: ('Could not adapt', ...)

TypeError should never be caught in user code, so if we want to check
if a certain object implements an adapter or not we should pass in a
default object as the second argument to the interface "casting":

    >>> ISuspension(bike, False)
    False

To attach an adapter to an object, we use addFacet, which will return
the adapted object, which will return the adapter.

    >>> bike.addFacet(ISuspension) # doctest:+ELLIPSIS
    <...BikeAdaptToSuspension object at ...>

Call addFacet with the same interface again raises a

    >>> bike.addFacet(ISuspension)
    Traceback (most recent call last):
        ...
    AdapterError: Bike already has a facet for interface ISuspension

We can now adapt the object:

    >>> suspension = ISuspension(bike)
    >>> suspension # doctest:+ELLIPSIS
    <...BikeAdaptToSuspension object at ...>

And we can call methods on the object, which are part of the interface:

    >>> suspension.is_locked()
    False
    >>> suspension.lockout()
    >>> suspension.is_locked()
    True

To fetch the adaptable/adapted object call get_adapted():

    >>> suspension.get_adapted() # doctest:+ELLIPSIS
    <...Bike object at ...>

"""

from kiwi.python import qual, namedAny
from zope.interface.interface import InterfaceClass, adapter_hooks

from stoqlib.exceptions import AdapterError

#
# Adaptors
#


class Adapter(object):
    """Adapter base class, all adapters must subclass this.
    """
    def __init__(self, adaptable):
        """Creates a new Adapted for I{adaptable}
        @param adaptable: the adapted object
        """
        self._adaptable = adaptable

    def __ne__(self, other):
        return not self.__eq__(other)

    def __eq__(self, other):
        if type(self) is not type(other):
            return False
        return self._adaptable.id == other._adaptable.id

    def __conform__(self, iface):
        return iface(self.get_adapted(), None)

    def get_adapted(self):
        """Get the adapted object
        @returns: the adapted object
        """
        return self._adaptable


class Adaptable(object):
    """Adapter base class, everything you want to adapt must subclass this.
    """

    #
    # Class methods
    #

    @classmethod
    def getFacetType(cls, iface):
        """Fetches a facet type associated with an interface, or raise
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
        """Returns facet classes for this object
        @returns: a list of facet classes
        """

        facets = getattr(cls, '_facets', {})

        return facets.values()

    @classmethod
    def registerFacet(cls, facet, *ifaces):
        """Registers a facet for class cls.

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
        """Adds a facet implementing iface for the current object
        @param iface: interface of the facet to add
        @returns: the facet
        """

        if isinstance(self, Adapter):
            raise TypeError("An adapter can not be adapted to another "
                            "object.")
        if not isinstance(iface, InterfaceClass):
            raise TypeError('iface must be an Interface')

        if not hasattr(self, '_adapterCache'):
            self._adapterCache = {}

        k = qual(iface)
        if k in self._adapterCache:
            raise AdapterError('%s already has a facet for interface %s' %
                               (self.__class__.__name__, iface.__name__))

        facets = self.__class__._facets

        funcName = 'facet_%s_add' % iface.__name__
        func = getattr(self, funcName, None)

        if func:
            adapter = func(*args, **kwargs)
        elif k in facets:
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
        """Removes a facet from the current object

        @param iface: interface of the facet to remove
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
        """Gets a list of facets assoicated with the current object.
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

# This is a simple in memory register of all adapters, which
# depends on the state of the object itself [_adapterCache], it's
# also a cache which can be used by persisted adapters so we don't
# need to refetch.


def _adapter_hook(iface, obj):
    # Twisted's IPathImportMapper occasionally sends in None
    # which breaks isinstance, work-around. Johan 2008-09-29
    try:
        is_adaptable = isinstance(obj, Adaptable)
    except TypeError:
        is_adaptable = False

    if is_adaptable and hasattr(obj, '_adapterCache'):
        return obj._adapterCache.get(qual(iface))
adapter_hooks.append(_adapter_hook)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
