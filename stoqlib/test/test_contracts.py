# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2012 Async Open Source <http://www.async.com.br>
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

from twisted.trial import unittest
from zope.interface import implementedBy
from zope.interface.verify import verifyClass
from zope.interface.exceptions import Invalid

from stoqlib.lib.introspection import get_interfaces_for_package


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

TestIfaces = _create_iface_test()
