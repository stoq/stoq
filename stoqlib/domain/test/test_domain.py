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

from nose.exc import SkipTest

from stoqlib.domain.base import Domain
from stoqlib.database.orm import (StringCol, ForeignKey, ORMTestError,
                                  orm_get_columns, orm_get_random,
                                  orm_get_unittest_value)
from stoqlib.database.tables import get_table_types
from stoqlib.domain.test.domaintest import DomainTest


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
        # ReturnedSaleItem needs this
        if 'sale_item' in kwargs and 'sellable' in kwargs:
            kwargs['sellable'] = kwargs['sale_item'].sellable

        try:
            obj = klass(connection=self.trans, **kwargs)
        except Exception as e:
            self.fail(e)

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
    pass


class _BaseTestDomain(Domain):
    test_var = StringCol(default='')
    test_reference = ForeignKey('_ReferencedTestDomain', default=None)


class _TestDomain(_BaseTestDomain):
    pass


class TestDomain(DomainTest):
    def setUp(self):
        super(TestDomain, self).setUp()

        self.trans.query("""
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

        self.trans.commit()

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

    def testSelectBy(self):
        # FIXME: This is only testing for the where clause for
        # ForeignKey defined on a parent class. Do some real
        # testing for selectBy in the future
        _TestDomain.selectOneBy(connection=self.trans,
                                test_var='XXX')
        _TestDomain.selectOneBy(connection=self.trans,
                                test_reference=None)
