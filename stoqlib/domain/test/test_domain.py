# -*- coding: utf-8 -*-
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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s):   Johan Dahlin   <jdahlin@async.com.br>
##

import datetime
from decimal import Decimal

from kiwi.datatypes import currency
from sqlobject.col import (SOBoolCol, SODateTimeCol, SOForeignKey, SOIntCol,
                           SOStringCol, SOUnicodeCol)
from sqlobject.sqlbuilder import NoDefault
from twisted.trial.unittest import SkipTest

from stoqlib.database.columns import AbstractDecimalCol, SOPriceCol
from stoqlib.database.tables import get_table_types

from stoqlib.domain.test.domaintest import DomainTest

def _get_columns(table):
    columns = table.sqlmeta.columnList[:]

    parent = table.sqlmeta.parentClass
    while parent:
        columns.extend(_get_columns(parent))
        parent = parent.sqlmeta.parentClass

    return columns

class _Base(DomainTest):
    pass

def get_random(column):
    if isinstance(column, SOUnicodeCol):
        value = u''
    elif isinstance(column, SOStringCol):
        value = ''
    elif isinstance(column, SODateTimeCol):
        value = datetime.datetime.now()
    elif isinstance(column, SOIntCol):
        value = None
    elif isinstance(column, SOPriceCol):
        value = currency(20)
    elif isinstance(column, SOBoolCol):
        value = False
    elif isinstance(column, AbstractDecimalCol):
        value = Decimal(1)
    else:
        raise ValueError

    return value

def _create_domain_test():
    def _test_domain(self, klass):
        kwargs = {}
        args = []
        for column in _get_columns(klass):
            value = None
            if column.default is not NoDefault:
                value = column.default
            else:
                if isinstance(column, SOForeignKey):
                    if column.origName in ('te_created', 'te_modified'):
                        continue
                    value = self.create_by_type(column.foreignKey)
                    if value is None:
                        raise SkipTest("No example for %s" % column.foreignKey)
                else:
                    try:
                        value = get_random(column)
                    except ValueError:
                        raise SkipTest("No default for %r" % column)

            if not klass._inheritable and column.origName == 'childName':
                continue
            kwargs[column.origName] = value

            if not isinstance(column, SOForeignKey):
                args.append((column.origName, column))

        obj = klass(connection=self.trans, **kwargs)

        for name, col in args:
            getattr(obj, name)
            value = get_random(col)
            setattr(obj, name, value)

    TODO = {
        'ReceivingOrder': 'invalid invoice number',
        'ProductAdaptToSellable' : '',
        'ServiceAdaptToSellable' : '',
        'PurchaseOrderAdaptToPaymentGroup': '',
        }

    namespace = dict(_test_domain=_test_domain)
    for table in get_table_types():
        tname = table.__name__
        name = 'test' + tname
        func = lambda self, t=table: self._test_domain(t)
        func.__name__ = name
        if tname in TODO:
            func.todo = TODO[tname]
        namespace[name] = func

    return type('TestDomain', (_Base, ), namespace)

TestDomain = _create_domain_test()
