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

__tests__ = 'stoqlib/domain/base.py'

import json

import mock
from storm.exceptions import NotOneError
from storm.references import Reference

from stoqlib.database.properties import (IntCol, UnicodeCol, BoolCol, IdCol,
                                         IdentifierCol)
from stoqlib.domain.base import Domain

from stoqlib.domain.test.domaintest import DomainTest


class Ding(Domain):
    __storm_table__ = 'ding'
    int_field = IntCol(default=0)
    str_field = UnicodeCol(default=u'')


class Dong(Domain):
    __storm_table__ = 'dong'
    bool_field = BoolCol(default=False)
    ding_id = IdCol()
    ding = Reference(ding_id, Ding.id)


class Dung(Domain):
    __storm_table__ = 'dung'
    identifier = IdentifierCol()
    ding_id = IdCol()
    ding = Reference(ding_id, Ding.id)


class TestSelect(DomainTest):

    @classmethod
    def setUpClass(cls):
        DomainTest.setUpClass()
        RECREATE_SQL = """
        DROP TABLE IF EXISTS dung;
        DROP TABLE IF EXISTS dong;
        DROP TABLE IF EXISTS ding;

        CREATE TABLE ding (
            id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
            te_id bigint UNIQUE REFERENCES transaction_entry(id),
            int_field integer default 0,
            str_field text default ''
        );
        CREATE TABLE dong (
            id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
            te_id bigint UNIQUE REFERENCES transaction_entry(id),
            bool_field boolean default false,
            ding_id uuid REFERENCES ding(id) ON UPDATE CASCADE
        );
        CREATE TABLE dung (
            id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
            identifier SERIAL NOT NULL,
            te_id bigint UNIQUE REFERENCES transaction_entry(id),
            ding_id uuid REFERENCES ding(id) ON UPDATE CASCADE
        );
        """
        cls.store.execute(RECREATE_SQL)
        cls.store.commit()

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

    def test_validate_attr(self):
        with self.assertRaisesRegexp(
                TypeError,
                ("expected_type <type 'object'> needs to be a "
                 "<class 'storm.properties.Property'> subclass")):
            Ding.validate_attr(Ding.str_field, expected_type=object)

        with self.assertRaisesRegexp(
                TypeError,
                ("attr str_field needs to be a "
                 "<class 'storm.properties.Bool'> instance")):
            Ding.validate_attr(Ding.str_field, expected_type=BoolCol)

        with self.assertRaisesRegexp(
                ValueError, "Domain Ding does not have a column bool_field"):
            Ding.validate_attr(Dong.bool_field)

        # Those should pass
        for cls, field, expected_type in [
                (Ding, Ding.str_field, UnicodeCol),
                (Ding, Ding.int_field, IntCol),
                (Dong, Dong.bool_field, BoolCol)]:
            cls.validate_attr(field)
            cls.validate_attr(field, expected_type=expected_type)

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

    def test_max_value(self):
        self.assertEqual(Ding.get_max_value(self.store, Ding.str_field), u'')

        Ding(store=self.store, str_field=u'1')
        self.assertEqual(Ding.get_max_value(self.store, Ding.str_field), u'1')
        Ding(store=self.store, str_field=u'2')
        self.assertEqual(Ding.get_max_value(self.store, Ding.str_field), u'2')
        Ding(store=self.store, str_field=u'10')
        self.assertEqual(Ding.get_max_value(self.store, Ding.str_field), u'10')
        Ding(store=self.store, str_field=u'9')
        self.assertEqual(Ding.get_max_value(self.store, Ding.str_field), u'10')
        Ding(store=self.store, str_field=u'001')
        self.assertEqual(Ding.get_max_value(self.store, Ding.str_field), u'010')
        Ding(store=self.store, str_field=u'a')
        self.assertEqual(Ding.get_max_value(self.store, Ding.str_field), u'010')
        Ding(store=self.store, str_field=u'aa')
        self.assertEqual(Ding.get_max_value(self.store, Ding.str_field), u'0aa')
        Ding(store=self.store, str_field=u'99')
        self.assertEqual(Ding.get_max_value(self.store, Ding.str_field), u'0aa')
        Ding(store=self.store, str_field=u'999')
        self.assertEqual(Ding.get_max_value(self.store, Ding.str_field), u'999')
        Ding(store=self.store, str_field=u'AB0000')
        self.assertEqual(Ding.get_max_value(self.store, Ding.str_field), u'AB0000')
        Ding(store=self.store, str_field=u'AB0001')
        self.assertEqual(Ding.get_max_value(self.store, Ding.str_field), u'AB0001')
        Ding(store=self.store, str_field=u'AB9')
        self.assertEqual(Ding.get_max_value(self.store, Ding.str_field), u'AB0001')
        Ding(store=self.store, str_field=u'AB0010')
        self.assertEqual(Ding.get_max_value(self.store, Ding.str_field), u'AB0010')

    def test_check_unique_value_exists(self):
        ding_1 = Ding(store=self.store, str_field=u'Ding_1')
        ding_2 = Ding(store=self.store, str_field=u'Ding_2')

        self.assertIsNone(ding_1.check_unique_value_exists(
            Ding.str_field, u'Ding_0'))
        self.assertIsNone(ding_1.check_unique_value_exists(
            Ding.str_field, u'Ding_0', case_sensitive=False))

        self.assertIsNone(ding_1.check_unique_value_exists(
            Ding.str_field, u'Ding_1'))
        self.assertIsNone(ding_1.check_unique_value_exists(
            Ding.str_field, u'Ding_1', case_sensitive=False))

        self.assertEqual(ding_1.check_unique_value_exists(
            Ding.str_field, u'Ding_2'), ding_2)
        self.assertIsNone(ding_1.check_unique_value_exists(
            Ding.str_field, u'ding_2'))
        self.assertEqual(ding_1.check_unique_value_exists(
            Ding.str_field, u'Ding_2', case_sensitive=False), ding_2)
        self.assertEqual(ding_1.check_unique_value_exists(
            Ding.str_field, u'ding_2', case_sensitive=False), ding_2)

        with mock.patch('stoqlib.domain.base.log.warning') as warning:
            ding_1.str_field = u'XXX'
            ding_2.str_field = u'XXX'
            ding_3 = Ding(store=self.store, str_field=u'XXX')

            ding_3.check_unique_value_exists(Ding.str_field, u"XXX")
            warning.assert_called_once_with(
                "more than one result found when trying to "
                "check_unique_tuple_exists on table 'Ding' for values: "
                "u'str_field => XXX'")

    def test_check_unique_tuple_exists(self):
        ding_1 = Ding(store=self.store, str_field=u'Ding_1', int_field=1)
        ding_2 = Ding(store=self.store, str_field=u'Ding_2', int_field=2)

        self.assertIsNone(ding_1.check_unique_tuple_exists(
            {Ding.str_field: u'Ding_0', Ding.int_field: 0}))
        self.assertIsNone(ding_1.check_unique_tuple_exists(
            {Ding.str_field: u'Ding_0', Ding.int_field: 1}))
        self.assertIsNone(ding_1.check_unique_tuple_exists(
            {Ding.str_field: u'Ding_1', Ding.int_field: 1}))
        self.assertEqual(ding_1.check_unique_tuple_exists(
            {Ding.str_field: u'Ding_2', Ding.int_field: 2}), ding_2)

        self.assertEqual(ding_1.check_unique_tuple_exists(
            {Ding.str_field: u'ding_2', Ding.int_field: 2},
            case_sensitive=False), ding_2)
        self.assertEqual(ding_1.check_unique_tuple_exists(
            {Ding.str_field: u'Ding_2', Ding.int_field: 2},
            case_sensitive=False), ding_2)

        self.assertIsNone(ding_1.check_unique_tuple_exists({}))
        self.assertIsNone(ding_1.check_unique_tuple_exists(
            {Ding.str_field: u'', Ding.int_field: 0}))
        self.assertIsNone(ding_1.check_unique_tuple_exists(
            {Ding.str_field: None, Ding.int_field: None}))

        with mock.patch('stoqlib.domain.base.log.warning') as warning:
            ding_1.str_field = u'XXX'
            ding_1.int_field = 1
            ding_2.str_field = u'XXX'
            ding_2.int_field = 1
            ding_3 = Ding(store=self.store, str_field=u'XXX', int_field=1)

            ding_3.check_unique_tuple_exists({Ding.str_field: u"XXX",
                                              Ding.int_field: 1})
            warning.assert_called_once_with(
                "more than one result found when trying to "
                "check_unique_tuple_exists on table 'Ding' for values: "
                "u'int_field => 1, str_field => XXX'")

    def test_can_remove(self):
        ding = Ding(store=self.store)
        dung = Dung(store=self.store)
        dong = Dong(store=self.store)
        self.assertTrue(ding.can_remove())

        dung.ding = ding
        self.assertFalse(ding.can_remove())
        self.assertTrue(ding.can_remove(skip=[('dung', 'ding_id')]))

        dong.ding = ding
        self.assertFalse(ding.can_remove())
        self.assertFalse(ding.can_remove(skip=[('dung', 'ding_id')]))
        self.assertFalse(ding.can_remove(skip=[('dong', 'ding_id')]))
        self.assertTrue(ding.can_remove(skip=[('dong', 'ding_id'),
                                              ('dung', 'ding_id')]))

    def test_get_temporary_identifier(self):
        dung = Dung(store=self.store)
        dung.identifier = Dung.get_temporary_identifier(self.store)
        self.assertEquals(dung.identifier, -1)

        new_dung = Dung(store=self.store)
        new_dung.identifier = Dung.get_temporary_identifier(self.store)
        self.assertEquals(new_dung.identifier, -2)

    def test_serialize(self):
        ding = Ding(store=self.store, str_field=u'Sambiquira', int_field=666)
        self.assertEquals(ding.serialize(), {
            'id': ding.id,
            'te_id': ding.te_id,
            'str_field': 'Sambiquira',
            'int_field': 666,
        })

        dong = Dong(store=self.store, bool_field=False)
        self.assertEquals(dong.serialize(), {
            'id': dong.id,
            'te_id': dong.te_id,
            'bool_field': False,
            'ding_id': None,
        })

        dung = Dung(store=self.store)
        dung.identifier = Dung.get_temporary_identifier(self.store)
        dung.ding = ding
        self.assertEquals(dung.serialize(), {
            'id': dung.id,
            'te_id': dung.te_id,
            'identifier': str(dung.identifier),
            'ding_id': ding.id,
        })

        # json.loads can properly load a json.dumped from serialize
        json.loads(json.dumps(ding.serialize()))
        json.loads(json.dumps(dong.serialize()))
        json.loads(json.dumps(dung.serialize()))
