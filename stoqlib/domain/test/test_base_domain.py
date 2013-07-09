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
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

from storm.exceptions import NotOneError

from stoqlib.database.runtime import new_store
from stoqlib.database.properties import IntCol, UnicodeCol
from stoqlib.domain.base import Domain

from stoqlib.domain.test.domaintest import DomainTest


class Ding(Domain):
    __storm_table__ = 'ding'
    int_field = IntCol(default=0)
    str_field = UnicodeCol(default=u'')


RECREATE_SQL = """
DROP TABLE IF EXISTS ding;
CREATE TABLE ding (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id),
    int_field integer default 0,
    str_field text default ''
    );
"""
store = new_store()
store.execute(RECREATE_SQL)
store.commit()


class TestSelect(DomainTest):
    def test_select_one(self):
        self.assertEquals(self.store.find(Ding).one(), None)
        ding1 = Ding(store=self.store)
        self.assertEquals(self.store.find(Ding).one(), ding1)
        Ding(store=self.store)
        self.assertRaises(NotOneError, self.store.find(Ding).one)

    def test_select_one_by(self):
        Ding(store=self.store)

        self.assertEquals(
            None, self.store.find(Ding, int_field=1).one())
        ding1 = Ding(store=self.store, int_field=1)
        self.assertEquals(
            ding1, self.store.find(Ding, int_field=1).one())
        Ding(store=self.store, int_field=1)
        self.assertRaises(NotOneError, self.store.find(Ding, int_field=1).one)

    def test_find_distinct_values(self):
        # One empty, 2 duplicates and an extra one
        for value in [u'', u'xxx', u'xxx', u'yyy']:
            Ding(store=self.store, str_field=value)

        r1 = list(sorted(Ding.find_distinct_values(
            self.store, Ding.str_field, exclude_empty=True)))
        r2 = list(sorted(Ding.find_distinct_values(
            self.store, Ding.str_field, exclude_empty=False)))

        self.assertEqual(r1, [u'xxx', u'yyy'])
        self.assertEqual(r2, [u'', u'xxx', u'yyy'])

    def test_check_unique_value_exists(self):
        ding_1 = Ding(store=self.store, str_field=u'Ding_1')
        Ding(store=self.store, str_field=u'Ding_2')

        self.assertFalse(ding_1.check_unique_value_exists(
            Ding.str_field, u'Ding_0'))
        self.assertFalse(ding_1.check_unique_value_exists(
            Ding.str_field, u'Ding_0', case_sensitive=False))

        self.assertFalse(ding_1.check_unique_value_exists(
            Ding.str_field, u'Ding_1'))
        self.assertFalse(ding_1.check_unique_value_exists(
            Ding.str_field, u'Ding_1', case_sensitive=False))

        self.assertTrue(ding_1.check_unique_value_exists(
            Ding.str_field, u'Ding_2'))
        self.assertFalse(ding_1.check_unique_value_exists(
            Ding.str_field, u'ding_2'))
        self.assertTrue(ding_1.check_unique_value_exists(
            Ding.str_field, u'Ding_2', case_sensitive=False))
        self.assertTrue(ding_1.check_unique_value_exists(
            Ding.str_field, u'ding_2', case_sensitive=False))

    def test_check_unique_tuple_exists(self):
        ding_1 = Ding(store=self.store, str_field=u'Ding_1', int_field=1)
        Ding(store=self.store, str_field=u'Ding_2', int_field=2)

        self.assertFalse(ding_1.check_unique_tuple_exists(
            {Ding.str_field: u'Ding_0', Ding.int_field: 0}))
        self.assertFalse(ding_1.check_unique_tuple_exists(
            {Ding.str_field: u'Ding_0', Ding.int_field: 1}))
        self.assertFalse(ding_1.check_unique_tuple_exists(
            {Ding.str_field: u'Ding_1', Ding.int_field: 1}))
        self.assertTrue(ding_1.check_unique_tuple_exists(
            {Ding.str_field: u'Ding_2', Ding.int_field: 2}))

        self.assertTrue(ding_1.check_unique_tuple_exists(
            {Ding.str_field: u'ding_2', Ding.int_field: 2},
            case_sensitive=False))
        self.assertTrue(ding_1.check_unique_tuple_exists(
            {Ding.str_field: u'Ding_2', Ding.int_field: 2},
            case_sensitive=False))

        self.assertFalse(ding_1.check_unique_tuple_exists({}))
        self.assertFalse(ding_1.check_unique_tuple_exists(
            {Ding.str_field: u'', Ding.int_field: 0}))
        self.assertFalse(ding_1.check_unique_tuple_exists(
            {Ding.str_field: None, Ding.int_field: None}))
