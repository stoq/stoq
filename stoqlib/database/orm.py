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
## Author(s):   Johan Dahlin  <jdahlin@async.com.br>
##

"""Simple ORM abstraction layer"""

from decimal import Decimal

from formencode.validators import Validator
from kiwi.datatypes import currency
from kiwi.db.sqlobj import SQLObjectQueryExecuter
from sqlobject import (connectionForURI, sqlhub, SQLObjectNotFound,
                       SQLObjectMoreThanOneResultError)
from sqlobject.col import (BoolCol, BLOBCol, DateTimeCol,
                           ForeignKey, IntCol, StringCol, UnicodeCol)
from sqlobject.col import (Col, SOBoolCol, SODateTimeCol, SODecimalCol,
                           SOForeignKey, SOIntCol, SOStringCol, SOUnicodeCol)
from sqlobject.converters import registerConverter
from sqlobject.dbconnection import Transaction
from sqlobject.joins import MultipleJoin, SingleJoin
from sqlobject.main import SQLObject
from sqlobject.sqlbuilder import (AND, Alias, IN, INNERJOINOn, ISNOTNULL,
                                  LEFTJOINOn, LIKE, OR, Update,
                                  NoDefault, const, sqlIdentifier)
from sqlobject.sresults import SelectResults
from sqlobject.util.csvexport import export_csv
from sqlobject.viewable import Viewable

from stoqlib.lib.defaults import DECIMAL_PRECISION


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

class DecimalCol(Col):
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

# Exceptions

# ORMObject.get raises this
ORMObjectNotFound = SQLObjectNotFound
# ORMObject.selectOneBy raises this
ORMObjectMoreThanOneResultError = SQLObjectMoreThanOneResultError

ORMObjectQueryExecuter = SQLObjectQueryExecuter

# Columns
BLOBCol = BLOBCol
BoolCol = BoolCol
DateTimeCol = DateTimeCol
ForeignKey = ForeignKey
IntCol = IntCol
MultipleJoin = MultipleJoin
SingleJoin = SingleJoin
StringCol = StringCol
UnicodeCol = UnicodeCol

# Column classes
Col = Col
SOBoolCol = SOBoolCol
SODateTimeCol = SODateTimeCol
SODecimalCol = SODecimalCol
SOForeignKey = SOForeignKey
SOIntCol = SOIntCol
SOStringCol = SOStringCol
SOUnicodeCol = SOUnicodeCol

# SQLBuilder
Alias = Alias
AND = AND
IN = IN
INNERJOINOn = INNERJOINOn
ISNOTNULL = ISNOTNULL
LEFTJOINOn = LEFTJOINOn
LIKE = LIKE
const = const
OR = OR
sqlIdentifier = sqlIdentifier

# Connections
connectionForURI = connectionForURI
Transaction = Transaction

# Misc
export_csv = export_csv
SelectResults = SelectResults
NoDefault = NoDefault
Update = Update
Viewable = Viewable
