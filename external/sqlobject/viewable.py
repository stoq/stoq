# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU Lesser General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##

import copy

from sqlobject.dbconnection import Iteration
from sqlobject.declarative import DeclarativeMeta, setup_attributes
from sqlobject.main import sqlhub
from sqlobject.sqlbuilder import (SQLCall, SQLObjectField,
                                  NoDefault, AND)
from sqlobject.sresults import SelectResults
from sqlobject.classregistry import registry


class ViewableMeta(object):
    table = None
    defaultOrder = None
    columnList = None
    columnNames = None
    idName = 'id'
    columns = None
    parentClass = None


class DynamicViewColumn(object):

    def __init__(self, cls, name):
        self.origName = self.name = self.dbName = name
        self.soClass = cls


class SQLObjectView(object):

    def __init__(self, cls, columns):
        self.cls = cls
        self.columns = columns.copy()

    def __getattr__(self, attr):
        if attr == 'id':
            return SQLObjectField(self.cls.sqlmeta.table,
                                  self.cls.sqlmeta.idName, attr)
        if not attr in self.columns:
            raise AttributeError("%s object has no attribute %s" % (
                self.cls.__name__, attr))
        return self.columns[attr]


class Viewable(object):
    """
    Viewable is a class which allows you to break out of the normal SQLObject
    hierarchy and create a new object representing a query which joins a number
    of tables. It was designed to allow you to use expression columns
    and LEFT JOINS.

    A typical query which a viewable can create looks like this::

          SELECT DISTINCT
            sale_id AS id,
            person.name AS salesperson_name,
            sum(quantity * price) AS subtotal,
            sum(quantity) AS total_quantity

          FROM sale_item, person_adapt_to_sales_person, person, sale

            LEFT JOIN person_adapt_to_client
            ON (sale.client_id = person_adapt_to_client.id)

            LEFT JOIN person AS client_person
            ON (person_adapt_to_client.original_id = client_person.id)

          WHERE sale_item.sale_id = sale_id

          GROUP BY sale_item.sale_id, sale.id,
                   client_person.name,
                   person.name;

    Which can also be expressed in following way by subclassing Viewable:;

        class SaleViewable(Viewable):
            columns = dict(
                id=Sale.q.id,
                name=Person.q.name,
                subtotal=func.SUM(SaleItem.q.quantity * SaleItem.q.price)
                total_quantity=func.SUM(SaleItem.q.quantity)
                )

            joins = [
                LEFTJOINOn(None, PersonAdaptToClient,
                           PersonAdaptToClient.q.id == Sale.q.clientID),
                LEFTJOINOn(None, Person,
                           Person.q.id == PersonAdaptToClient.q.originalID),
                ]

            clause = AND(
                SaleItem.q.saleID == Sale.q.id,
                )

    You don't need to explicitly set the GROUP BY columns, Viewable is smart
    enough to figure out the columns which needs to be grouped.

    @cvar columns: a dictionary with column name mapping to an
       SQLObject expression, functions can be used here
    @cvar joins: a list of XXXJOINOn objects, the first argument should always
       be None, the second should be the table joining in and the third the
       expression to join in the other table
    @cvar clause: optional WHERE clause of the table, can be used instead of a
       INNERJOINOn object in the joins list
    @cvar hidden_columns: a string list of columns which means that the
      column will not included in the SELECT part, but you will still be able
      to query for it using the Viewable.q.column magic
    """
    __metaclass__ = DeclarativeMeta

    _connection = sqlhub

    sqlmeta = ViewableMeta
    columns = {}
    clause = None
    hidden_columns = []

    def __classinit__(cls, new_attrs):
        if not cls.__bases__ == (object,):
            cls.sqlmeta = type('sqlmeta', (cls.sqlmeta,), {})
            cls.sqlmeta.columns = {}
            cls.sqlmeta.columnList = []
            cls.sqlmeta.columnNames = []

        setup_attributes(cls, new_attrs)

        columns = new_attrs.get('columns', getattr(cls, 'columns', None))

        if not columns:
            return

        cls.q = SQLObjectView(cls, columns)

        cols = columns.copy()
        if not 'id' in cols:
            raise TypeError("You need a id column in %r" % cls)

        idquery = cols.pop('id')
        cls.sqlmeta.table = idquery.tableName

        for hidden in cls.hidden_columns:
            if not hidden in columns:
                raise TypeError(
                    "%s specified in hidden_columns is not a column" % (
                    hidden))
            del cols[hidden]
            del columns[hidden]

        assert not cls.sqlmeta.columns
        for colName in sorted(cols):
            cls.addColumn(colName, cols[colName])

    def __hash__(self):
        return self.id

    def __cmp__(self, other):
        if self.__class__ != other.__class__:
            return -1
        return cmp(self.id, other.id)

    @classmethod
    def addColumn(cls, name, query):
        col = None
        if isinstance(query, SQLObjectField):
            table = table_from_name(query.tableName)
            fieldName = query.fieldName
            if fieldName != 'id':
                # O(N)
                for col in table.sqlmeta.columnList:
                    if col.dbName == fieldName:
                        break
                else:
                    raise AssertionError(table.sqlmeta.table + '.' + name)

                # Let's modify origName so it can be used in introspection,
                # but first make a copy of the column.
                col = copy.copy(col)
                col.origName = name

        if not col:
            col = DynamicViewColumn(cls, name)

        col.value = query
        cls.sqlmeta.columns[name] = col
        cls.sqlmeta.columnList.append(col)
        cls.sqlmeta.columnNames.append(name)

    @classmethod
    def delColumn(cls, name):
        col = cls.sqlmeta.columns.pop(name)
        cls.sqlmeta.columnList.remove(col)
        cls.sqlmeta.columnNames.remove(name)

    @classmethod
    def get(cls, idValue, selectResults=None, connection=None):
        if not selectResults:
            selectResults = []

        instance = cls()
        instance.id = idValue
        for name, value in zip(cls.sqlmeta.columnNames, selectResults):
            col = cls.sqlmeta.columns[name]

            if hasattr(col, 'to_python') and col.to_python:
                instance.__dict__[name] = col.to_python(value, None)
            else:
                instance.__dict__[name] = value

        instance._connection = connection

        return instance

    @classmethod
    def select(cls, clause=None, clauseTables=None,
               orderBy=NoDefault, limit=None,
               lazyColumns=False, reversed=False,
               distinct=False, connection=None,
               join=None, columns=None, having=None):
        if cls.clause:
            if clause:
                clause = AND(clause, cls.clause)
            else:
                clause = cls.clause
        if columns:
            cls.columns.update(columns)

        return ViewableSelectResults(cls, clause,
                                     clauseTables=clauseTables,
                                     orderBy=orderBy,
                                     limit=limit,
                                     lazyColumns=lazyColumns,
                                     reversed=reversed,
                                     distinct=distinct,
                                     connection=connection,
                                     join=cls.joins,
                                     having=having,
                                     ns=cls.columns)

    def sync(self):
        obj = self.select(
            self.q.id == self.id,
            connection=self.get_connection()).getOne()

        for attr in self.sqlmeta.columnNames:
            setattr(self, attr, getattr(obj, attr, None))

    def get_connection(self):
        return self._connection

def queryForSelect(conn, select):
    ops = select.ops
    join = ops.get('join')
    having = ops.get('having')

    cls = select.sourceClass
    if join:
        tables = conn._fixTablesForJoins(select)
    else:
        tables = select.tables
    if ops.get('distinct', False):
        q = 'SELECT DISTINCT '
    else:
        q = 'SELECT '

    if ops.get('lazyColumns', 0):
        q += "%s.%s FROM %s" % (
            cls.sqlmeta.table, cls.sqlmeta.idName,
            ", ".join(tables))
    else:
        ns = select.ops['ns'].copy()
        q += '%s AS id, %s FROM %s' % (
            ns.pop('id'),
            ', '.join(['%s AS %s' % (ns[item], item)
                       for item in sorted(ns.keys())]),
            ", ".join(tables))

    if join:
        q += conn._addJoins(select, tables)

        if not tables:
            q = q[:-1]

    q += " WHERE"
    q = conn._addWhereClause(select, q, limit=0, order=0)

    groupBy = False
    for item in ns.values():
        if isinstance(item, SQLCall):
            groupBy = True
            break

    if groupBy:
        items = []
        for item in ns.values():
            # If the field has an aggregate function, than it should not be
            # in the GROUP BY clause
            if not item.hasSQLCall():
                items.append(str(item))
        items.append(str(select.ops['ns']['id']))
        q += " GROUP BY %s" % ', '.join(items)

    if having:
        q += " HAVING %s" % ' AND '.join([str(i) for i in having])

    if ops.get('dbOrderBy'):
        q = conn._queryAddOrderByClause(select, q)

    start = ops.get('start', 0)
    end = ops.get('end', None)
    if start or end:
        q = conn._queryAddLimitOffset(q, start, end)

    return q


class ViewableIteration(Iteration):

    def __init__(self, dbconn, rawconn, select, keepConnection=False):
        self.dbconn = dbconn
        self.rawconn = rawconn
        self.select = select
        self.keepConnection = keepConnection
        self.cursor = rawconn.cursor()
        self.query = queryForSelect(dbconn, select)
        if dbconn.debug:
            dbconn.printDebug(rawconn, self.query, 'Select')
        self.dbconn._executeRetry(self.rawconn, self.cursor, self.query)


class ViewableSelectResults(SelectResults):
    IterationClass = ViewableIteration

    def __init__(self, sourceClass, clause, clauseTables=None,
                 **ops):
        SelectResults.__init__(self, sourceClass, clause, clauseTables, **ops)

        # The table we're joining from must be the last one in the FROM-clause
        table = sourceClass.sqlmeta.table
        if self.tables[-1] != table:
            self.tables.remove(table)
            self.tables.append(table)

    def __str__(self):
        return queryForSelect(self._getConnection(), self)


_cache = {}
def table_from_name(name):
    # O(1), but initially expensive
    global _cache
    def _rebuild():
        for table in registry(None).allClasses():
            _cache[table.sqlmeta.table] = table

    if not name in _cache:
        _rebuild()
    return _cache[name]
