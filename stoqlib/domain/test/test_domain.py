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

import datetime
import decimal

from kiwi.currency import currency
from storm import Undef
from storm.properties import PropertyColumn
from storm.references import Reference
from storm.variables import (BoolVariable, DateTimeVariable,
                             RawStrVariable, DecimalVariable,
                             IntVariable)

from stoqlib.domain.base import Domain
from stoqlib.database.properties import (AutoUnicodeVariable, StringCol, IntCol,
                                  QuantityVariable, PriceVariable)
from stoqlib.database.tables import get_table_types
from stoqlib.domain.test.domaintest import DomainTest


class ORMTestError(Exception):
    pass


def orm_get_columns(table):
    for name, v in table.__dict__.items():
        if not isinstance(v, (PropertyColumn, Reference)):
            continue
        yield getattr(table, name), name


def orm_get_random(column):
    if isinstance(column, Reference):
        return None

    variable = column.variable_factory.func

    if issubclass(variable, AutoUnicodeVariable):
        value = u''
    elif issubclass(variable, RawStrVariable):
        value = ''
    elif issubclass(variable, DateTimeVariable):
        value = datetime.datetime.now()
    elif issubclass(variable, IntVariable):
        value = None
    elif issubclass(variable, PriceVariable):
        value = currency(20)
    elif issubclass(variable, BoolVariable):
        value = False
    elif isinstance(variable, QuantityVariable):
        value = decimal.Decimal(1)
    elif issubclass(variable, DecimalVariable):
        value = decimal.Decimal(1)
    else:
        raise ValueError(column)

    return value


def orm_get_unittest_value(klass, test, tables_dict, name, column):
    value = None
    if isinstance(column, PropertyColumn):
        if column.variable_factory.keywords['value'] is not Undef:
            value = column.variable_factory.keywords['value']
        else:
            try:
                value = orm_get_random(column)
            except ValueError:
                raise ORMTestError("No default for %r" % (column, ))

    elif isinstance(column, Reference):
        if name in ('te_created', 'te_modified'):
            return None
        if isinstance(column._remote_key, str):
            cls = tables_dict[column._remote_key.split('.')[0]]
        else:
            cls = column._remote_key[0].cls
        value = test.create_by_type(cls)
        if value is None:
            raise ORMTestError("No example for %s" % cls)
    return value


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
                continue

            kwargs[name] = value

            args.append((name, column))

        # Sellable does not accept all arguments
        if klass.__name__ == 'Sellable':
            kwargs = {}

        # Payment needs a value argument
        if klass.__name__ == 'Payment':
            kwargs['value'] = 123

        if 'id' in kwargs:
            del kwargs['id']
        # ReturnedSaleItem needs this
        if 'sale_item' in kwargs and 'sellable' in kwargs:
            kwargs['sellable'] = kwargs['sale_item'].sellable

        try:
            obj = klass(store=self.store, **kwargs)
        except Exception as e:
            self.fail(e)

        if hasattr(klass, 'te_created_id') and not obj.te_created:
            self.fail('Object should have a te_created')

        if hasattr(klass, 'te_modified_id') and not obj.te_modified:
            self.fail('Object should have a te_modified')

        for name, col in args:
            try:
                value = orm_get_random(col)
            except ValueError:
                continue
            if value is not None:
                setattr(obj, name, value)

    namespace = dict(_test_domain=_test_domain)
    for table in tables:
        tname = table.__name__
        name = 'test' + tname
        func = lambda self, t=table: self._test_domain(t)
        func.__name__ = name
        namespace[name] = func

    return type('TestDomain', (DomainTest, ), namespace)

TestDomainGeneric = _create_domain_test()


class _ReferencedTestDomain(Domain):
    __storm_table__ = '_referenced_test_domain'


class _TestDomain(Domain):
    __storm_table__ = '_test_domain'

    test_var = StringCol(default='')
    test_reference_id = IntCol(default=None)
    test_reference = Reference(test_reference_id, _ReferencedTestDomain.id)


class TestDomain(DomainTest):
    def setUp(self):
        super(TestDomain, self).setUp()

        self.store.execute("""
            DROP TABLE IF EXISTS _test_domain;
            DROP TABLE IF EXISTS _referenced_domain;

            CREATE TABLE _referenced_domain (
                id serial NOT NULL PRIMARY KEY,
                te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
                te_modified_id bigint UNIQUE REFERENCES transaction_entry(id)
                );
            CREATE TABLE _test_domain (
                id serial NOT NULL PRIMARY KEY,
                test_var text,
                test_reference_id bigint REFERENCES _referenced_domain(id),
                te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
                te_modified_id bigint UNIQUE REFERENCES transaction_entry(id)
                );
            """)

        self.store.commit()

    def testCloneObject(self):
        # Create an object to test, clone() method.
        old_order = self.create_purchase_order()
        self.assertTrue(old_order.id)
        self.assertTrue(old_order.identifier)
        # Clone object.
        new_order = old_order.clone()
        self.assertTrue(new_order.id)
        self.assertTrue(new_order.identifier)
        # Id and identifier fields from old and new object must be different.
        self.assertNotEquals(old_order.id, new_order.id)
        self.assertNotEquals(old_order.identifier, new_order.identifier)
