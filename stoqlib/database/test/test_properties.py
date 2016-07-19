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

__tests__ = 'stoqlib/database/properties.py'

from lxml import etree

from stoqlib.database.properties import XmlCol
from stoqlib.domain.base import Domain
from stoqlib.domain.test.domaintest import DomainTest


class XmlTable(Domain):
    __storm_table__ = 'xml_table'
    data = XmlCol()


class TestSelect(DomainTest):

    @classmethod
    def setUpClass(cls):
        DomainTest.setUpClass()
        RECREATE_SQL = """
        DROP TABLE IF EXISTS xml_table;

        CREATE TABLE xml_table (
            id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
            te_id bigint UNIQUE REFERENCES transaction_entry(id),
            data xml
        );
        """
        cls.store.execute(RECREATE_SQL)
        cls.store.commit()

    def test_xml(self):
        xml_table = XmlTable()
        xml_table.data = etree.fromstring("""
        <?xml version="1.0" encoding="UTF-8"?>
        <note>
          <to>Nihey</to>
          <from>Ronaldo</from>
          <heading>Reminder</heading>
          <body>Wake Up!</body>
        </note>
        """.strip())

        # Write the XML into the database
        self.store.add(xml_table)
        self.store.commit()

        # Retrieve the XML from the database
        self.store.reload(xml_table)
        self.assertTrue(isinstance(xml_table.data, etree._Element))

        # Check if putting a Null valued XML would be OK
        xml_table.data = None
        self.store.commit()

        # Retrieve the null valued XML
        self.store.reload(xml_table)
        self.assertIsNone(xml_table.data)
