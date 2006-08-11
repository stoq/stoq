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

from zope.interface import providedBy
from zope.interface.adapter import AdapterRegistry
from zope.interface.interface import InterfaceClass

#
# Interface implementation
#


_NoImplementor = object()

class MetaInterface(InterfaceClass):
    pass

class _Nothing:
    pass

class ConnMetaInterface(MetaInterface):
    """A special interface for Stoq domain classes. It allows us to make
    mandatory the connection argument
    """
    def __call__(self, adaptable, persist=None, registry=None):
        """
        Try to adapt `adaptable' to self; return `default' if it
        was passed, otherwise raise L{CannotAdapt}.
        """
        if isinstance(adaptable, Adapter):
            raise TypeError('Adaptable argument can not be of type Adapter '
                            'got %s instead' % type(adaptable))
        default = _Nothing
        registry = getRegistry()
        # should this be `implements' of some kind?
        if ((persist is None or persist)
            and hasattr(adaptable, '_getComponent')):
            adapter = adaptable._getComponent(self, registry)
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

    def providedBy(self, adapter):
        """
        @param adapter:
        @returns: If the adapter object implements the given interface
        """
        if not isinstance(adapter, Adapter):
            raise TypeError('adapter argument must be of type Adapter,'
                            'got %s instead'
                            % type(adapter))
        return self in providedBy(adapter)

ConnInterface = ConnMetaInterface('ConnInterface',
                                  __module__='stoq.domain.base')

#
# Adaptors
#

class CannotAdapt(Exception):
    pass

class Adapter:
    pass


_registry = AdapterRegistry()

def getRegistry():
    return _registry
