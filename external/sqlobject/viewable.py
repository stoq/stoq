import copy

from sqlobject.dbconnection import Iteration
from sqlobject.declarative import DeclarativeMeta, setup_attributes
from sqlobject.sqlbuilder import (SQLCall, SQLObjectField, SQLObjectTable,
                                  NoDefault, AND)
from sqlobject.col import SOIntCol
from sqlobject.sresults import SelectResults
from sqlobject.styles import underToMixed
from sqlobject.classregistry import registry


class ViewableMeta(object):
    table = None
    defaultOrder = None
    columnList = []
    columnNames = []
    idName = 'id'
    columns = {}
    parentClass = None


class DynamicViewColumn(object):

    def __init__(self, cls, name):
        self.origName = self.name = self.dbName = name
        self.soClass = cls


class SQLObjectView(object):

    def __init__(self, cls):
        self.cls = cls

    def __getattr__(self, attr):
        return self.cls.sqlmeta.columns[attr].value


class Viewable(object):
    __metaclass__ = DeclarativeMeta

    sqlmeta = ViewableMeta
    columns = {}
    clause = None

    def __classinit__(cls, new_attrs):
        setup_attributes(cls, new_attrs)

        columns = new_attrs['columns']
        if not columns:
            return

        cols = columns.copy()
        if not 'id' in cols:
            raise TypeError("You need a id column in %r" % Viewable)

        idquery = cols.pop('id')
        cls.sqlmeta.table = idquery.tableName

        for colName in sorted(cols):
            cls.addColumn(colName, cols[colName])

        cls.q = SQLObjectView(cls)

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

                # Let's modify origName so it can be used in introspection, but first
                # make a copy of the column.
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
        instance.__dict__.update(zip(cls.sqlmeta.columnNames,
                                      selectResults))

        return instance

    @classmethod
    def select(cls, clause=None, clauseTables=None,
               orderBy=NoDefault, limit=None,
               lazyColumns=False, reversed=False,
               distinct=False, connection=None,
               join=None, columns=None):
        if clause:
            clause = AND(clause, cls.clause)
        else:
            clause = cls.clause

        return ViewableSelectResults(cls, clause,
                                     clauseTables=clauseTables,
                                     orderBy=orderBy,
                                     limit=limit,
                                     lazyColumns=lazyColumns,
                                     reversed=reversed,
                                     distinct=distinct,
                                     connection=connection,
                                     join=cls.joins,
                                     ns=cls.columns)

def queryForSelect(conn, select):
    ops = select.ops
    join = ops.get('join')
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
    q = conn._addWhereClause(select, q, limit=0)

    groupBy = False
    for item in ns.values():
        if isinstance(item, SQLCall):
            groupBy = True
            break

    if groupBy:
        items = []
        for item in ns.values():
            if not isinstance(item, SQLCall):
                items.append(str(item))
        items.append(str(select.ops['ns']['id']))
        q += " GROUP BY %s" % ', '.join(items)

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

    def lazyIter(self):
        conn = self._getConnection()
        return iter(list(ViewableIteration(
            conn, conn.getConnection(), self, keepConnection=True)))


_cache = {}
def table_from_name(name):
    # O(1), but initially expensive
    global _cache
    if not _cache:
        for table in registry(None).allClasses():
            _cache[table.sqlmeta.table] = table
    return _cache[name]

