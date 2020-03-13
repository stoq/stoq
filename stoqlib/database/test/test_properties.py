# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

#
# Copyright (C) 2016-2020 Stoq Tecnologia <http://stoq.link>
# All rights reserved
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., or visit: http://www.gnu.org/.
#
# Author(s): Stoq Team <stoq-devel@async.com.br>
#


from lxml import etree
import uuid

from stoqlib.database.properties import XmlCol, JsonCol, PointCol
from stoqlib.domain.base import Domain
from stoqlib.domain.test.domaintest import DomainTest


__tests__ = 'stoqlib/database/properties.py'


class TestTable(Domain):
    __storm_table__ = 'test_table'
    data = XmlCol()
    json = JsonCol()
    point = PointCol()


class TestColumns(DomainTest):

    @classmethod
    def setUpClass(cls):
        DomainTest.setUpClass()
        RECREATE_SQL = """
        DROP TABLE IF EXISTS test_table;

        CREATE TABLE test_table (
            id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
            te_id bigint UNIQUE REFERENCES transaction_entry(id),
            data xml,
            json jsonb,
            point point
        );
        """
        cls.store.execute(RECREATE_SQL)
        cls.store.commit()

    def test_xml(self):
        obj = TestTable()
        obj.data = etree.fromstring("""
        <?xml version="1.0" encoding="UTF-8"?>
        <note>
          <to>Nihey</to>
          <from>Ronaldo</from>
          <heading>Reminder</heading>
          <body>Wake Up!</body>
        </note>
        """.strip().encode())

        # Write the XML into the database
        self.store.add(obj)
        self.store.commit()

        # Retrieve the XML from the database
        self.store.reload(obj)
        self.assertTrue(isinstance(obj.data, etree._Element))

        # Check if putting a Null valued XML would be OK
        obj.data = None
        self.store.commit()

        # Retrieve the null valued XML
        self.store.reload(obj)
        self.assertIsNone(obj.data)

    def test_json(self):
        obj = TestTable()
        obj.json = dict(foo=1, bar=['any', 'type', 1, None], other={1: 2, 3: 4})

        # Write the object into the database
        self.store.add(obj)
        self.store.commit()

        # Retrieve the object from the database
        self.store.reload(obj)
        self.assertTrue(isinstance(obj.json, dict))

        # Check if erasing the value is possible
        obj.json = None
        self.store.commit()

        # Retrieve the null valued XML
        self.store.reload(obj)
        self.assertIsNone(obj.json)

    def test_point_as_tuple(self):
        test_id = str(uuid.uuid4())
        self.store.execute("""insert into test_table
            (id, point) values (?, ?)""", (test_id, '(-1, 1)'))

        obj = self.store.get(TestTable, test_id)
        self.assertEqual(obj.point, (-1, 1))

        obj.point = (1, 2)
        self.store.add(obj)
        self.store.commit()
        self.assertEqual(obj.point, (1, 2))

    def test_point_as_string(self):
        test_id = str(uuid.uuid4())
        self.store.execute("insert into test_table (id, point) values (?, ?)", (test_id, '-1, -2'))

        obj = self.store.get(TestTable, test_id)
        self.assertEqual(obj.point, (-1, -2))

        obj.point = '1, 2'
        self.store.add(obj)
        self.store.commit()
        self.assertEqual(obj.point, (1, 2))

    def test_point_as_point_function(self):
        test_id = str(uuid.uuid4())
        self.store.execute("""
            insert into test_table (id, point) values ('{}', point(-1, -3))""".format(test_id))

        obj = self.store.get(TestTable, test_id)
        self.assertEqual(obj.point, (-1, -3))
