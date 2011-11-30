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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

from twisted.trial.unittest import SkipTest

from stoqlib.database.exceptions import ORMTestError
from stoqlib.database.orm import (orm_get_columns, orm_get_random,
                                  orm_get_unittest_value)
from stoqlib.database.tables import get_table_types
from stoqlib.domain.test.domaintest import DomainTest


class _Base(DomainTest):
    pass


def _create_domain_test():
    tables = get_table_types()
    tables_dict = {}

    for table in tables:
        tables_dict[table.__name__] = table

    def _test_domain(self, klass):
        kwargs = {}
        args = []
        for column, name in orm_get_columns(klass):
            try:
                value = orm_get_unittest_value(klass, self, tables_dict, name, column)
            except ORMTestError, e:
                raise SkipTest(e)

            kwargs[name] = value

            args.append((name, column))

        if 'id' in kwargs:
            del kwargs['id']
        obj = klass(connection=self.trans, **kwargs)

        for name, col in args:
            try:
                value = orm_get_random(col)
            except ValueError:
                continue
            if value is not None:
                setattr(obj, name, value)

    TODO = {
        'CommissionSource': '',
        'PurchaseItem': 'quantity_return cant be random',
        'PaymentMethod': 'missing account',
        'FiscalDayTax': 'invalid code',
        }

    namespace = dict(_test_domain=_test_domain)
    for table in tables:
        tname = table.__name__
        name = 'test' + tname
        func = lambda self, t=table: self._test_domain(t)
        func.__name__ = name
        if tname in TODO:
            continue
        namespace[name] = func

    return type('TestDomain', (_Base, ), namespace)

TestDomain = _create_domain_test()
