# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008 Async Open Source <http://www.async.com.br>
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

"""Simple ORM abstraction layer"""

import datetime
from decimal import Decimal

from formencode.validators import Validator
from kiwi.datatypes import currency
from kiwi.db.sqlobj import SQLObjectQueryExecuter
from sqlobject import (SQLObjectNotFound,
                       SQLObjectMoreThanOneResultError)
from sqlobject.col import DateTimeCol as _DateTimeCol
from sqlobject.col import (BoolCol, BLOBCol,
                           ForeignKey, IntCol, StringCol, UnicodeCol)
from sqlobject.col import (Col, SOCol, SOBoolCol, SODateTimeCol, SODecimalCol,
                           SOForeignKey, SOIntCol, SOStringCol, SOUnicodeCol)
from sqlobject.converters import registerConverter
from sqlobject.dbconnection import connectionForURI, Transaction
from sqlobject.joins import MultipleJoin as _MultipleJoin, SingleJoin
from sqlobject.joins import SOSingleJoin, SOMultipleJoin
from sqlobject.main import sqlhub, SQLObject
from sqlobject.sqlbuilder import (AND, Alias, IN, INNERJOINOn, ISNOTNULL,
                                  LEFTJOINOn, LIKE, OR, Update, Field,
                                  NoDefault, const, sqlIdentifier, DESC)
from sqlobject.sresults import SelectResults
from sqlobject.util.csvexport import export_csv
from sqlobject.viewable import Viewable

from stoqlib.database.exceptions import ORMTestError
from stoqlib.lib.defaults import DECIMAL_PRECISION, QUANTITY_PRECISION

# Currency


def _CurrencyConverter(value, db):
    return str(Decimal(value))
registerConverter(currency, _CurrencyConverter)

# Decimal


class AbstractDecimalCol(SODecimalCol):
    def __init__(self, **kw):
        kw['size'] = 10
        kw['precision'] = DECIMAL_PRECISION
        SODecimalCol.__init__(self, **kw)


class AbstractQuantityCol(SODecimalCol):
    def __init__(self, **kw):
        kw['size'] = 10
        kw['precision'] = QUANTITY_PRECISION
        SODecimalCol.__init__(self, **kw)


class DecimalCol(Col):
    baseClass = AbstractDecimalCol


class QuantityCol(DecimalCol):
    baseClass = AbstractQuantityCol


class PercentCol(DecimalCol):
    baseClass = AbstractDecimalCol


# Price

class _PriceValidator(Validator):

    def to_python(self, value, state):
        # Do not allow empty strings or None Values
        if value is not None:
            if not isinstance(value, Decimal):
                value = Decimal(str(value))
            return currency(value)

    def from_python(self, value, state):
        return value


class SOPriceCol(AbstractDecimalCol):
    def createValidators(self):
        return [_PriceValidator()] + super(SOPriceCol, self).createValidators()


class PriceCol(DecimalCol):
    baseClass = SOPriceCol


# MainObject

class ORMObject(SQLObject):
    pass


def orm_enable_debugging():
    from stoqlib.database.runtime import get_connection
    conn = get_connection()
    conn.debug = True


def orm_startup():
    from stoqlib.database.runtime import get_connection
    sqlhub.threadConnection = get_connection()


def orm_get_columns(table):
    columns = table.sqlmeta.columnList[:]

    parent = table.sqlmeta.parentClass
    while parent:
        columns.extend(orm_get_columns(parent))
        parent = parent.sqlmeta.parentClass

    return [(c, c.origName) for c in columns]


def orm_get_random(column):
    if column is SOForeignKey:
        raise ValueError

    if isinstance(column, SOUnicodeCol):
        value = u''
    elif isinstance(column, SOStringCol):
        value = ''
    elif isinstance(column, SODateTimeCol):
        value = datetime.datetime.now()
    elif isinstance(column, SOIntCol):
        value = None
    elif isinstance(column, SOPriceCol):
        value = currency(20)
    elif isinstance(column, SOBoolCol):
        value = False
    elif isinstance(column, AbstractQuantityCol):
        value = Decimal(1)
    elif isinstance(column, AbstractDecimalCol):
        value = Decimal(1)
    else:
        raise ValueError

    return value


def orm_get_unittest_value(klass, test, tables_dict, name, column):
    if column.default is not NoDefault:
        value = column.default
    else:
        if isinstance(column, SOForeignKey):
            if name in ('te_created', 'te_modified'):
                return None
            value = test.create_by_type(column.foreignKey)
            if value is None:
                raise ORMTestError("No example for %s" % column.foreignKey)
        else:
            try:
                value = orm_get_random(column)
            except ValueError:
                raise ORMTestError("No default for %r" % column)

    if not klass._inheritable and name == 'childName':
        return None
    return value

orm_name = 'sqlobject'

# Exceptions

# ORMObject.get raises this
ORMObjectNotFound = SQLObjectNotFound
# ORMObject.selectOneBy raises this
ORMObjectMoreThanOneResultError = SQLObjectMoreThanOneResultError

ORMObjectQueryExecuter = SQLObjectQueryExecuter

# Columns
BLOBCol = BLOBCol
BoolCol = BoolCol
#DateTimeCol = DateTimeCol
# FIXME: There are a lot of callsites in stoq that set datetime columns as
# only date and later use those as datetime. Untill we fix all those
# callsites, disable cache for datetime columns


class DateTimeCol(_DateTimeCol):
    def __init__(self, *args, **kwargs):
        kwargs['noCache'] = True
        _DateTimeCol.__init__(self, *args, **kwargs)

ForeignKey = ForeignKey
IntCol = IntCol
SingleJoin = SingleJoin
StringCol = StringCol
UnicodeCol = UnicodeCol


class MySOMultipleJoin(SOMultipleJoin):
    def performJoin(self, inst):
        column = self.joinColumn[:-3] + 'ID'
        query = getattr(self.otherClass.q, column) == inst.id
        order = 'id'
        if self.orderBy != NoDefault:
            order = self.orderBy
        return self.otherClass.select(query,
                        connection=inst.get_connection()).orderBy(order)


class MultipleJoin(_MultipleJoin):
    baseClass = MySOMultipleJoin


# Column classes
Col = Col
SOCol = SOCol
SOBoolCol = SOBoolCol
SODateTimeCol = SODateTimeCol
SODecimalCol = SODecimalCol
SOForeignKey = SOForeignKey
SOIntCol = SOIntCol
SOStringCol = SOStringCol
SOUnicodeCol = SOUnicodeCol

SOSingleJoin = SOSingleJoin
SOMultipleJoin = SOMultipleJoin

# SQLBuilder
Alias = Alias
Field = Field
AND = AND
IN = IN
INNERJOINOn = INNERJOINOn
ISNOTNULL = ISNOTNULL
LEFTJOINOn = LEFTJOINOn
LIKE = LIKE
const = const
OR = OR
sqlIdentifier = sqlIdentifier
DESC = DESC


class ILIKE(LIKE):
    op = 'ILIKE'

# Connections
connectionForURI = connectionForURI
Transaction = Transaction

# Misc
export_csv = export_csv
SelectResults = SelectResults
NoDefault = NoDefault
Update = Update
Viewable = Viewable
