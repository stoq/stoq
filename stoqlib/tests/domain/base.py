# -*- Mode: Python; coding: iso-8859-1 -*-
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
## Author(s): Rudá Porto Filgueiras  <rudazz@gmail.com>
##
""" Base module to be used by all domain test modules"""

import datetime

from sqlobject.col import (SOStringCol, SOIntCol, SOFloatCol, SODateTimeCol,
                           SODateCol, SOBoolCol, SOForeignKey)

from stoqlib.lib.runtime import new_transaction

# Default values for automatic instance creation and set value tests.
STRING_TEST_VALUES = ('Instance Creation String','Set Test String')
FLOAT_TEST_VALUES = (24.38, 445.67)
INT_TEST_VALUES = (20, 55)
DATE_TEST_VALUES = (datetime.date.today(),
                    datetime.date.today() + datetime.timedelta(1))
DATETIME_TEST_VALUES = (datetime.datetime.now(),
                        datetime.datetime.now() + datetime.timedelta(1))
BOOL_TEST_VALUES = (True, False)

def column_type_data(column):
    """ This function returns tuples of values for each SQLObject
    column type:
    SOStringCol, SOFloatCol, SOIntCOl, SODateCOl, SODateTimeCOl,
    SOBollCol. Any other column types receive None value.

    The first value of each pair is used to create an instance and are
    sent to the domain class constructor.

    The second value is used to update the attribute of created instance.
    """
    if isinstance(column, SOStringCol):
        return STRING_TEST_VALUES
    elif isinstance(column, SOIntCol):
        return INT_TEST_VALUES
    elif isinstance(column, SOFloatCol):
        return FLOAT_TEST_VALUES
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
    This class has some base infrastructure:
    conn: connection object
    _table: reference to the domains class that will be tested by
    the Test class.
    foreign_key_attrs: a dict with foreign keys used by the class to be tested:
    {'foreign_key_attrs_name': fk_class_reference}
    skip_attr: attributes that will not be automaticaly tested
    """
    foreign_key_attrs = {}
    _table = None
    skip_attrs = ['model_modified','_is_valid_model','model_created']

    def __init__(self):
        self.conn = new_transaction()
        self._table_count = self._table.select(connection=self.conn).count()
        self.insert_dict, self.edit_dict = self._generate_test_data()
        self._generate_foreign_key_attrs()

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

    def _check_set_and_get(self, test_value, db_value, key):
        assert test_value == db_value

    def _generate_test_data(self):
        """This method uses column_type_data function and return two dicts:
        insert_args: 'column_name': value #used to instance creation.
        edit_args: 'column_name': value   #used to set_and_get test.
        """
        insert = dict()
        edit = dict()
        cols = column_type_data
        for column in self._table.sqlmeta.columns.values():
            if column.origName in self.skip_attrs:
                continue
            insert[column.origName], edit[column.origName] = cols(column)
        return insert, edit

    def _generate_foreign_key_attrs(self):
        """Create all foreign key objects using foreign_key_attrs dict and
        apeend to insert_dict attribute.
        """
        if self.foreign_key_attrs and isinstance(self.foreign_key_attrs, dict):
            for key, klass in self.foreign_key_attrs.items():
                fk_test_instance = klass()
                insert_dict, edit_dict = fk_test_instance._generate_test_data()
                fk_table = fk_test_instance._table
                fk_instance = fk_table(connection=self.conn,
                                       **insert_dict)
                self.insert_dict[key] = fk_instance
