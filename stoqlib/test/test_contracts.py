# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import inspect

from twisted.trial import unittest
from zope.interface import implementedBy
from zope.interface.verify import verifyClass
from zope.interface.exceptions import Invalid

from stoqlib.lib.introspection import (get_all_adapters,
                                       get_interfaces_for_package)


def _create_adapter_test():
    # Create a dynamic test class which verifies that methods in all adapters
    # are defined in an interface.
    #
    # Exceptions:
    #    ORMObject create to_python/from_python
    #    Private methods, which has a name starting with _
    #    class methods
    #
    TODO = {
        }

    def _test_adapter(self, adapter):
        ifaces = implementedBy(adapter)
        if not ifaces:
            self.fail("%s does not provide any interfaces" % adapter)

        # Collect methods
        methods = []
        for name in adapter.__dict__.keys():
            if name.startswith('_'):
                continue
            value = getattr(adapter, name)
            if not inspect.ismethod(value):
                continue

            # Skip methods added by ORMObject
            if name in ('to_python', 'from_python'):
                continue

            # Skip classmethods
            if value.im_self is not None:
                # TODO: Only allow classmethods on base/abstract classes
                continue

            # Skip events
            if name in ['on_create', 'on_update', 'on_delete']:
                continue
            methods.append(name)

        # Remove methods which are part of an interface
        for iface in ifaces:
            for name, desc in iface.namesAndDescriptions():
                if not name in methods:
                    continue
                methods.remove(name)

        if methods:
            self.fail(
                "%s has public methods %s which are not part of an "
                "interface" % (adapter.__name__, ', '.join(methods)))
    namespace = dict(_test_adapter=_test_adapter)

    for klass in get_all_adapters():
        tname = klass.__name__
        name = 'test' + tname
        func = lambda self, adapter=klass: self._test_adapter(adapter)
        func.__name__ = name
        if tname in TODO:
            func.todo = TODO[tname]
        namespace[name] = func

    return type('TestAdapters', (unittest.TestCase, ), namespace)


def _create_iface_test():
    def _test_class(self, klass):
        for iface in implementedBy(klass):
            try:
                verifyClass(iface, klass)
            except Invalid, message:
                self.fail("%s(%s): %s" % (
                    klass.__name__, iface.__name__, message))

    TODO = {}
    namespace = dict(_test_class=_test_class)
    for iface in get_interfaces_for_package('stoqlib'):
        tname = iface.__name__
        name = 'test' + tname
        func = lambda self, f=iface: self._test_class(f)
        func.__name__ = name
        if tname in TODO:
            func.todo = TODO[tname]
        namespace[name] = func

    return type('TestIfaces', (unittest.TestCase, ), namespace)

TestAdapters = _create_adapter_test()
TestIfaces = _create_iface_test()
