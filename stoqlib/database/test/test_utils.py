# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2016 Stoq Tecnologia <http://stoq.link>
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

__tests__ = 'stoqlib/database/utils.py'

from unittest import mock

import psycopg2

from stoqlib.database.properties import BoolCol, IntCol
from stoqlib.database.utils import (
    _select_rows_ids_in_batch,
    _update_rows_batch,
    add_default_to_column,
)
from stoqlib.domain.base import Domain
from stoqlib.domain.test.domaintest import DomainTest


class TestTable(Domain):
    __storm_table__ = 'test_table'

    is_high = BoolCol()
    power_level = IntCol()


class TestUtils(DomainTest):

    @classmethod
    def setUpClass(cls):
        DomainTest.setUpClass()
        RECREATE_SQL = """
        DROP TABLE IF EXISTS test_table;

        CREATE TABLE test_table (
            id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
            te_id bigint UNIQUE REFERENCES transaction_entry(id),
            is_high BOOLEAN DEFAULT NULL,
            power_level INTEGER DEFAULT NULL
        );
        """
        cls.store.execute(RECREATE_SQL)
        cls.store.commit()

    def test_select_rows_ids_in_batch(self):
        TestTable(is_high=True)

        rows = _select_rows_ids_in_batch(self.store, TestTable, 'is_high', limit=5)
        self.assertEquals(len(rows), 0)

        for _ in range(10):
            TestTable(self.store)

        rows = _select_rows_ids_in_batch(self.store, TestTable, 'is_high', limit=5)
        self.assertEquals(len(rows), 5)

        rows = _select_rows_ids_in_batch(self.store, TestTable, 'is_high', limit=11)
        self.assertEquals(len(rows), 10)

    def test_update_rows_batch_one_run(self):
        for _ in range(10):
            TestTable(self.store)

        _update_rows_batch(self.store, TestTable, 'power_level', default=9001, limit=10)

        rs = self.store.find(TestTable, TestTable.power_level == 9001)
        self.assertEquals(rs.count(), 10)

    def test_update_rows_batch_multiple_runs(self):
        for _ in range(10):
            TestTable(self.store)

        _update_rows_batch(self.store, TestTable, 'power_level', default=9001, limit=3)

        rs = self.store.find(TestTable, TestTable.power_level == 9001)
        self.assertEquals(rs.count(), 10)

    def test_update_rows_batch_without_rows(self):
        with mock.patch.object(self.store, "find") as mock_find:
            _update_rows_batch(self.store, TestTable, 'power_level', default=8001, limit=10)

        mock_find.assert_called_once_with(TestTable, power_level=None)

    def test_add_default_column_boolean(self):
        for _ in range(10):
            TestTable(self.store)

        add_default_to_column(
            self.store,
            TestTable,
            column_name='is_high',
            default=True,
        )

        rs = self.store.find(TestTable, TestTable.is_high == 1)
        self.assertEquals(rs.count(), 10)

        TestTable(self.store)
        rs = self.store.find(TestTable, TestTable.is_high == 1)
        self.assertEquals(rs.count(), 11)

        error_msg = '"is_high" violates not-null constraint'
        with self.assertRaisesRegex(psycopg2.IntegrityError, error_msg):
            self.store.execute("INSERT INTO test_table(te_id, is_high) VALUES (69, NULL)")

    def test_add_default_column_integer(self):
        for _ in range(10):
            TestTable(self.store)

        add_default_to_column(
            self.store,
            TestTable,
            column_name='power_level',
            default=666,
        )

        rs = self.store.find(TestTable, TestTable.power_level == 666)
        self.assertEquals(rs.count(), 10)

        TestTable(self.store)
        rs = self.store.find(TestTable, TestTable.power_level == 666)
        self.assertEquals(rs.count(), 11)

        error_msg = '"power_level" violates not-null constraint'
        with self.assertRaisesRegex(psycopg2.IntegrityError, error_msg):
            self.store.execute("INSERT INTO test_table(te_id, power_level) VALUES (69, NULL)")
