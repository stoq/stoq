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
## Author(s):   Henrique Romano  <henrique@async.com.br>
##              Johan Dahlin  <jdahlin@async.com.br>
##

import glob
import inspect

from kiwi.dist import listpackages
from kiwi.python import namedAny
from twisted.trial import unittest
from zope.interface import implementedBy
from zope.interface.interface import InterfaceClass
from zope.interface.verify import verifyClass
from zope.interface.exceptions import Invalid

def _test_class(self, klass):
    for iface in implementedBy(klass):
        try:
            verifyClass(iface, klass)
        except Invalid, message:
            self.fail("%s(%s): %s" % (
                klass.__name__, iface.__name__, message))

namespace = {}
namespace['_test_class'] = _test_class
TODO = {
    # IPayment.add_payment
    "AbstractPaymentGroup": "requires too many arguments",
    "PurchaseOrderAdaptToPaymentGroup": "requires too many arguments",
    "ReceivingOrderAdaptToPaymentGroup": "requires too many arguments",
    "SaleAdaptToPaymentGroup": "requires too many arguments",
    "TillAdaptToPaymentGroup": "requires too many arguments",
    "VirtualPort": "doesn't allow enough arguments",
    }

def get_all_classes():
    classes = []
    for package in listpackages('stoqlib'):
        package = package.replace('.', '/')
        for filename in glob.glob(package + '/*.py'):
            modulename = filename[:-3].replace('/', '.')
            module = namedAny(modulename)
            for name, klass in inspect.getmembers(module, inspect.isclass):
                classes.append(klass)
    return classes

for klass in get_all_classes():
    if not implementedBy(klass):
        continue
    if not klass.__module__.startswith('stoqlib.'):
        continue
    if issubclass(klass, InterfaceClass):
        continue
    tname = klass.__name__
    name = 'test_' + tname
    func = lambda self, f=klass: self._test_class(f)
    func.__name__ = name
    if tname in TODO:
        func.todo = TODO[tname]
    namespace[name] = func

TestInterfacesImplementation = type('TestInterfacesImplementation',
                                    (unittest.TestCase, ),
                                    namespace)
