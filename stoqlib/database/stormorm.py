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

# This file is full of hacks to mimic the SQLObject API
# The migration plan is to:
# - Mimic the SQLObject api & behavior exactly
# - Run both of them for a couple of weeks to find all bugs
# - Remove the SQLObject support
# - Clean up the API

"""Simple ORM abstraction layer"""

from kiwi.db.sqlobj import SQLObjectQueryExecuter
from kiwi.datatypes import currency

from storm.database import create_database
from storm.expr import NamedFunc, Join, Update, SQL
from storm.properties import RawStr
from storm.store import Store
from storm.tracer import debug

from storm.sqlobject import PropertyAdapter
from storm.sqlobject import (BoolCol, DateTimeCol, DecimalCol,
                             ForeignKey, IntCol, StringCol)
from storm.sqlobject import (SQLObjectNotFound,
                             SQLObjectMoreThanOneResultError)
from storm.sqlobject import SQLMultipleJoin, SingleJoin
from storm.sqlobject import SQLObjectBase, SQLObjectMeta
from storm.sqlobject import AND, Alias, IN, LIKE, OR, _IGNORED
from storm.sqlobject import SQLObjectResultSet

from stoqlib.lib.defaults import DECIMAL_PRECISION, DECIMAL_SIZE


class Viewable(object):
    @classmethod
    def select(cls, store=None, *where):
        attributes, columns = zip(*cls.columns.items())
        for values in store.using(*cls.tables).find(columns, *where):
            instance = cls()
            for attribute, value in zip(attributes, values):
                setattr(instance, attribute, value)
            yield instance


class BLOBCol(PropertyAdapter, RawStr):
    pass


class PriceCol(DecimalCol):
    size = DECIMAL_SIZE
    precision = DECIMAL_PRECISION

    def parse_set(self, value, from_db):
        return currency(value)


class FuncClass(object):
    def __getattr__(self, attr):
        return type(attr, (NamedFunc,), {'name': attr})

const = func = FuncClass()

class Transaction(object):
    def __init__(self, conn):
        # FIXME: s.d.runtime uses this
        self._connection = conn

    def query(self, stmt):
        return self._connection.execute(stmt)

    def commit(self, close=False):
        self._connection.commit()
        if close:
            self._connection.close()

    def tableExists(self, table_name):
        return self._connection.tableExists(table_name)

    viewExists = tableExists

    def dropView(self, view_name):
        return self._connection.dropView(view_name)

    def dropTable(self, table_name, cascade=False):
        return self._connection.dropTable(table_name, cascade)

    def tableHasColumn(self, table_name, column_name):
        return self._connection.tableHasColumn(table_name, column_name)


class Connection(object):
    def __init__(self, db):
        print 'Connection(%r)' % (db,)
        self.db = db
        self.store = None

    def makeConnection(self):
        print 'Connection.makeConnection()'
        self.store =  Store(self.db)

    def close(self):
        print 'Connection.close(): %r' % (self.store, )

    def tableExists(self, tableName):
        res = self.store.execute(
            SQL("SELECT COUNT(relname) FROM pg_class WHERE relname = ?",
                (tableName, )))
        return res.get_one()[0]

    viewExists = tableExists

    def dropView(self, view_name):
        self.store.execute(SQL("DROP VIEW ?", (view_name, )))
        return True

    def dropTable(self, table_name, cascade=False):
        self.store.execute(SQL("DROP TABLE ? ?" % (
            table_name,
            cascade and 'CASCADE' or '')))

    def tableHasColumn(self, table_name, column_name):
        res = self.store.execute(SQL(
            """SELECT 1 FROM pg_class, pg_attribute
             WHERE pg_attribute.attrelid = pg_class.oid AND
                   pg_class.relname=? AND
                   attname=?""", (table_name, column_name)))
        return bool(res.get_one())

    def createDatabase(self, name, ifNotExists=False):
        print 'Connection.createDatabase(%r, %r)' % (name, ifNotExists)
        if ifNotExists and self.databaseExists(name):
            return False

        if self.store:
            self.store.close()
        try:
            conn = self.db.raw_connect()
            cur = conn.cursor()
            cur.execute('COMMIT')
            cur.execute('CREATE DATABASE "%s"' % (name, ))
            cur.close()
            del cur, conn
        finally:
            self.makeConnection()
        return True

    def dropDatabase(self, name, ifExists=False):
        print 'Connection.dropDatabase(%r, %r)' % (name, ifExists)
        if ifExists and not self.databaseExists(name):
            return False

        if self.store:
            self.store.close()
        try:
            conn = self.db.raw_connect()
            cur = conn.cursor()
            cur.execute('COMMIT')
            cur.execute('DROP DATABASE "%s"' % (name, ))
            cur.close()
            del cur, conn
        finally:
            self.makeConnection()
        return True

    def databaseExists(self, name):
        print 'Connection.databaseExists(%r)' % (name, )
        res = self.execute(
            SQL("SELECT COUNT(*) FROM pg_database WHERE datname=?",
                (name, )))
        return res.get_one()[0]

    def commit(self):
        self.store.commit()

    def execute(self, query):
        print 'Connection.execute(%r)' % (query, )
        return self.store.execute(query)

    def sqlrepr(self, name):
        return name

def connectionForURI(uri):
    return Connection(create_database(uri))

def export_csv(*args, **kwargs):
    print 'export_csv:IMPLEMENT ME'

def sqlIdentifier(*args, **kwargs):
    print 'sqlIdentifier:IMPLEMENT ME'
    return True

def orm_enable_debugging():
    debug(True)

# MainObject

class ORMObjectMeta(SQLObjectMeta):
    def __new__(cls, name, bases, dict):
        dict['sqlmeta'] = cls

        v = SQLObjectMeta.__new__(cls, name, bases, dict)
        cls.soClass = v
        if SQLObjectBase in bases:
            return v
        return v

    @classmethod
    def addColumn(meta, column):
        cls = meta.soClass
        kwargs = column.kwargs.copy()
        name = kwargs['name']
        propName = name + 'ID'
        dbName = name + '_id'
        if dbName.startswith('_'):
            dbName = dbName[1:]
        property_registry = cls._storm_property_registry
        property_registry.add_property(cls, column, propName)
        setattr(cls, propName, IntCol(dbName))


class ORMObject(SQLObjectBase):
    __metaclass__ = ORMObjectMeta

    def __init__(self, *args, **kwargs):
        self._connection = kwargs.get('connection')
        SQLObjectBase.__init__(self, *args, **kwargs)

    def _init(self, id, *args, **kwargs):
        self._connection = kwargs.get('connection')
        if self._connection is None:
            self._get_store()
        SQLObjectBase._init(self, id, *args, **kwargs)

    @classmethod
    def _get_store(cls):
        from stoqlib.database.runtime import get_connection
        cls._connection = cls.connection = get_connection()
        return cls.connection.store

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
DecimalCol = DecimalCol
ForeignKey = ForeignKey
IntCol = IntCol
MultipleJoin = SQLMultipleJoin
SingleJoin = SingleJoin
StringCol = StringCol
UnicodeCol = StringCol

# Column classes
Col = PropertyAdapter
SOBoolCol = BoolCol
SODateTimeCol = DateTimeCol
SODecimalCol = DecimalCol
SOForeignKey = ForeignKey
SOIntCol = IntCol
SOStringCol = StringCol
SOUnicodeCol = UnicodeCol

# SQLBuilder
Alias = Alias
AND = AND
IN = IN
INNERJOINOn = Join
ISNOTNULL = None
LEFTJOINOn = Join
LIKE = LIKE
OR = OR

# Misc
export_csv = export_csv
SelectResults = SQLObjectResultSet
NoDefault = _IGNORED
Update = Update
