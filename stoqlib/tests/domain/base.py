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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s):   Rudá Porto Filgueiras   <rudazz@gmail.com>
##              Evandro Vale Miquelito  <evandro@async.com.br>
##
""" Base module to be used by all domain test modules"""

import datetime
import decimal

from kiwi.datatypes import currency
from sqlobject.col import (SOUnicodeCol, SOIntCol, SODecimalCol, SODateTimeCol,
                           SODateCol, SOBoolCol, SOForeignKey)

from stoqlib.database import finish_transaction
from stoqlib.domain.columns import SOPriceCol
from stoqlib.lib.runtime import new_transaction

# Default values for automatic instance creation and set value tests.
STRING_TEST_VALUES = ('Instance Creation String','Set Test String')
DECIMAL_TEST_VALUES = (decimal.Decimal("24.38"),
                       decimal.Decimal("445.67"))
CURRENCY_TEST_VALUES = (currency(decimal.Decimal("98.42")),
                        currency(decimal.Decimal("876.98")))
INT_TEST_VALUES = (20, 55)
DATE_TEST_VALUES = (datetime.date.today(),
                    datetime.date.today() + datetime.timedelta(1))
DATETIME_TEST_VALUES = (datetime.datetime.now(),
                        datetime.datetime.now() + datetime.timedelta(1))
BOOL_TEST_VALUES = (True, False)

def column_type_data(column):
    """ This function returns tuples of values for each SQLObject
    column type:
    SOUnicodeCol, SODecimalCol, SOIntCOl, SODateCOl, SODateTimeCOl,
    SOBollCol. Any other column types receive None value.

    The first value of each pair is used to create an instance and are
    sent to the domain class constructor.

    The second value is used to update the attribute of created instance.
    """
    if isinstance(column, SOUnicodeCol):
        return STRING_TEST_VALUES
    elif isinstance(column, SOIntCol):
        return INT_TEST_VALUES
    elif isinstance(column, SOPriceCol):
        return CURRENCY_TEST_VALUES
    elif isinstance(column, SODecimalCol):
        return DECIMAL_TEST_VALUES
    elif isinstance(column, SODateCol):
        return DATE_TEST_VALUES
    elif isinstance(column, SODateTimeCol):
        return DATETIME_TEST_VALUES
    elif isinstance(column, SOBoolCol):
        return BOOL_TEST_VALUES
    elif isinstance(column, SOForeignKey):
        return None, None
    else:
        raise ValueError('Invalid column type, got %s'
                         % type(column))


class BaseDomainTest(object):
    """Base class to be used by all domain test classes.
    This class has some basic infrastructure:

    @param conn: an SQLObject Transaction instance
    @param _table: reference to a stoqlib domain class that will be
                   tested by the Test class.
    @param foreign_key_attrs: a dict with foreign keys used by the class
                              to be tested:
                             {'foreign_key_attrs_name': fk_class_reference}
                             where fk_class_reference is a stoqlib domain
                             class
    @param skip_attr: attributes that will not be automaticaly tested
    """
    foreign_key_attrs = None
    _table = None
    skip_attrs = ['model_modified','_is_valid_model','model_created',
                  'childName']

    def setup_class(cls):
        cls.conn = new_transaction()
        cls._table_count = cls._table.select(connection=cls.conn).count()
        cls._check_foreign_key_data()
        cls.insert_dict, cls.edit_dict = cls._generate_test_data()
        cls._generate_foreign_key_attrs()

    def teardown_class(cls):
        cls.conn.commit()
        finish_transaction(cls.conn)

    #
    # Class methods
    #

    @classmethod
    def _check_foreign_key_data(cls):
        cls._foreign_key_data = cls.get_foreign_key_data()
        for fkey_data in cls._foreign_key_data:
            assert fkey_data.get_connection() is cls.conn

    @classmethod
    def _check_foreign_key(cls, table, fkey_name):
        return fkey_name == table.sqlmeta.soClass.__name__

    @classmethod
    def _get_fkey_data_by_fkey_name(cls, fkey_name):
        for data in cls._foreign_key_data:
            table = type(data)
            if cls._check_foreign_key(table, fkey_name):
                return data
            table = table._parentClass
            if table and cls._check_foreign_key(table, fkey_name):
                return data

    @classmethod
    def _generate_test_data(cls):
        """This method uses column_type_data function and return two dicts:
        insert_args: 'column_name': value #used to instance creation.
        edit_args: 'column_name': value   #used to set_and_get test.
        """
        insert = dict()
        edit = dict()
        cols = column_type_data

        columns = cls._table.sqlmeta.columns.values()
        table = cls._table._parentClass
        if table:
            columns += table.sqlmeta.columns.values()

        extra_values = cls.get_extra_field_values()
        for column in columns:
            colname = column.origName
            if colname in cls.skip_attrs:
                continue
            data = cls._get_fkey_data_by_fkey_name(column.foreignKey)
            if data:
                insert[colname] = edit[colname] = data
            elif colname in extra_values.keys():
                insert[colname], edit[colname] = extra_values[colname]
            else:
                insert[colname], edit[colname] = cols(column)
        return insert, edit

    @classmethod
    def _generate_foreign_key_attrs(cls):
        """Create all foreign key objects using foreign_key_attrs dict and
        apeend to insert_dict attribute.
        """
        if cls.foreign_key_attrs and isinstance(cls.foreign_key_attrs, dict):
            for key, klass in cls.foreign_key_attrs.items():
                fk_test_instance = klass(connection=cls.conn)
                insert_dict, edit_dict = fk_test_instance._generate_test_data()
                fk_table = fk_test_instance._table
                fk_instance = fk_table(connection=cls.conn,
                                       **insert_dict)
                cls.insert_dict[key] = fk_instance

    #
    # General methods
    #

    def _check_set_and_get(self, test_value, db_value, key):
        assert test_value == db_value

    #
    # Hooks
    #

    @classmethod
    def get_foreign_key_data(cls):
        return []

    @classmethod
    def get_extra_field_values(cls):
        """This hook returns a dictionary of tuples. Each tuple has two values:
        an 'insert' and an 'edit' values. This list will be used when
        setting attributes in cls._table. The dict keys are attribute names
        of cls._table
        """
        return {}

    #
    # Tests
    #

    def test_1_create_instance(self):
        """ Create a domain class instance using insert_dict attribute and
        assert a new row in the database was inserted.
        """
        self._instance = self._table(connection=self.conn, **self.insert_dict)
        assert self._instance is not None
        self.conn.commit()
        self._table_count = long(self._table_count + 1)
        assert (self._table_count ==
                self._table.select(connection=self.conn).count())

    def test_2_set_and_get(self):
        """Update each common attribute of a domain class using edit_dict
        and verify if the value was updated.
        """
        for key, value in self.edit_dict.items():
            value = self.edit_dict[key]
            setattr(self._instance, key, value)
            db_value = getattr(self._instance, key)
            yield self._check_set_and_get, value, db_value, key
