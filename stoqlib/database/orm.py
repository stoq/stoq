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

# This makes sure that we can import SQLObject/formencode when running
# from the testsuite
from stoqlib.lib.kiwilibrary import library
library   # pyflakes

from formencode.validators import Validator
from kiwi.datatypes import currency
from kiwi.db.query import NumberQueryState, StringQueryState, \
     DateQueryState, DateIntervalQueryState, QueryExecuter, \
     NumberIntervalQueryState
from kiwi.interfaces import ISearchFilter
from sqlobject.main import SQLObjectNotFound, SQLObjectIntegrityError
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
from sqlobject.sqlbuilder import (AND, NOT, DESC, Alias, NOTIN, IN, INNERJOINOn,
                                  ISNOTNULL, LEFTJOINOn, LIKE, OR, Update, Field,
                                  NoDefault, SQLExpression, const, sqlIdentifier, func)
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

    return value

orm_name = 'sqlobject'

# Exceptions

# ORMObject.get raises this
ORMObjectNotFound = SQLObjectNotFound
# ORMObject.selectOneBy raises this
ORMObjectIntegrityError = SQLObjectIntegrityError


class _FTI(SQLExpression):
    def __init__(self, q):
        self.q = q

    def __sqlrepr__(self, db):
        return self.q


class ORMObjectQueryExecuter(QueryExecuter):
    def __init__(self, conn=None):
        QueryExecuter.__init__(self)
        self.conn = conn
        self.table = None
        self._query_callbacks = []
        self._filter_query_callbacks = {}
        self._query = self._default_query
        self._full_text_indexes = {}

    #
    # Public API
    #

    def set_table(self, table):
        """
        Sets the SQLObject table/object for this executer
        :param table: a SQLObject subclass
        """
        self.table = table

    def add_query_callback(self, callback):
        """
        Adds a generic query callback

        :param callback: a callable
        """
        if not callable(callback):
            raise TypeError
        self._query_callbacks.append(callback)

    def add_filter_query_callback(self, search_filter, callback):
        """
        Adds a query callback for the filter search_filter

        :param search_filter: a search filter
        :param callback: a callable
        """
        if not ISearchFilter.providedBy(search_filter):
            raise TypeError
        if not callable(callback):
            raise TypeError
        l = self._filter_query_callbacks.setdefault(search_filter, [])
        l.append(callback)

    def set_query(self, callback):
        """
        Overrides the default query mechanism.
        :param callback: a callable which till take two arguments:
          (query, connection)
        """
        if callback is None:
            callback = self._default_query
        elif not callable(callback):
            raise TypeError

        self._query = callback

    #
    # QueryBuilder
    #

    def search(self, states):
        """
        Execute a search.
        :param states:
        """
        if self.table is None:
            raise ValueError("table cannot be None")
        table = self.table
        queries = []
        self._having = []
        for state in states:
            search_filter = state.filter
            assert state.filter

            # Column query
            if search_filter in self._columns:
                query = self._construct_state_query(
                    table, state, self._columns[search_filter])
                if query:
                    queries.append(query)
            # Custom per filter/state query.
            elif search_filter in self._filter_query_callbacks:
                for callback in self._filter_query_callbacks[search_filter]:
                    query = callback(state)
                    if query:
                        queries.append(query)
            else:
                if (self._query == self._default_query and
                    not self._query_callbacks):
                    raise ValueError(
                        "You need to add a search column or a query callback "
                        "for filter %s" % (search_filter))

        for callback in self._query_callbacks:
            query = callback(states)
            if query:
                queries.append(query)

        if queries:
            query = AND(*queries)
        else:
            query = None

        having = None
        if self._having:
            having = AND(self._having)

        result = self._query(query, having, self.conn)
        return result.limit(self.get_limit())

    #
    # Private
    #

    def _add_having(self, clause):
        self._having.append(clause)

    def _default_query(self, query, having, conn):
        return self.table.select(query, having=having, connection=conn)

    def _construct_state_query(self, table, state, columns):
        queries = []
        having_queries = []

        for column in columns:
            query = None
            table_field = getattr(table.q, column)

            # If the field has an aggregate function (sum, avg, etc..), then
            # this clause should be in the HAVING part of the query.
            use_having = table_field.hasSQLCall()

            if isinstance(state, NumberQueryState):
                query = self._parse_number_state(state, table_field)
            elif isinstance(state, NumberIntervalQueryState):
                query = self._parse_number_interval_state(state, table_field)
            elif isinstance(state, StringQueryState):
                query = self._parse_string_state(state, table_field)
            elif isinstance(state, DateQueryState):
                query = self._parse_date_state(state, table_field)
            elif isinstance(state, DateIntervalQueryState):
                query = self._parse_date_interval_state(state, table_field)
            else:
                raise NotImplementedError(state.__class__.__name__)

            if query and use_having:
                having_queries.append(query)
                query = None

            if query:
                queries.append(query)

        if having_queries:
            self._add_having(OR(*having_queries))

        if queries:
            return OR(*queries)

    def _postgres_has_fti_index(self, table_name, column_name):
        # Assume that the PostgreSQL full text index columns are
        # named xxx_fti where xxx is the name of the column
        res = self.conn.queryOne(
            """SELECT 1
            FROM information_schema.columns
            WHERE table_name = %s AND
                  column_name = %s AND
                  udt_name = 'tsvector';""" % (
            self.conn.sqlrepr(table_name),
            self.conn.sqlrepr(column_name)))
        return bool(res)

    def _check_has_fulltext_index(self, table_name, field_name):
        fullname = table_name + field_name
        if fullname in self._full_text_indexes:
            return self._full_text_indexes[fullname]
        else:
            value = False
            if 'postgres' in self.conn.__class__.__module__:
                value = self._postgres_has_fti_index(table_name,
                                                     field_name + '_fti')
            self._full_text_indexes[fullname] = value
        return value

    def _parse_number_state(self, state, table_field):
        if state.value is not None:
            return table_field == state.value

    def _parse_number_interval_state(self, state, table_field):
        queries = []
        if state.start is not None:
            queries.append(table_field >= state.start)
        if state.end is not None:
            queries.append(table_field <= state.end)
        if queries:
            return AND(*queries)

    def _parse_string_state(self, state, table_field):
        if not state.text:
            return

        if self._check_has_fulltext_index(table_field.tableName,
                                          table_field.fieldName):
            value = state.text.lower()
            # FTI operators:
            #  & = AND
            #  | = OR
            value = value.replace(' ', ' & ')
            retval = _FTI("%s.%s_fti @@ %s::tsquery" % (
                table_field.tableName,
                table_field.fieldName,
                self.conn.sqlrepr(value)))
        else:
            fieldName = table_field.fieldName
            text = '%%%s%%' % state.text.lower()

            table_field = func.LOWER(table_field)
            # Skip a couple of fields that do not contain real
            # "string" data, perhaps we should have a way of mark this
            # directly in the columns
            if fieldName not in ['barcode', 'phone_number', 'cpf',
                                 'rg_number', 'cnpj', 'code']:
                table_field = func.stoq_normalize_string(table_field)
                text = func.stoq_normalize_string(text)

            retval = LIKE(table_field, text)

        if state.mode == StringQueryState.NOT_CONTAINS:
            retval = NOT(retval)

        return retval

    def _parse_date_state(self, state, table_field):
        if state.date:
            return func.DATE(table_field) == state.date

    def _parse_date_interval_state(self, state, table_field):
        queries = []
        if state.start:
            queries.append(table_field >= state.start)
        if state.end:
            queries.append(func.DATE(table_field) <= state.end)
        if queries:
            return AND(*queries)


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
NOTIN = NOTIN
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
