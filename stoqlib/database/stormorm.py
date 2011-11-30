# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (c) 2006, 2007 Canonical
## Copyright (C) 2008-2011 Async Open Source <http://www.async.com.br>
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
##            Gustavo Niemeyer <gustavo@niemeyer.net>
##

# This file is full of hacks to mimic the SQLObject API
# The migration plan is to:
# - Mimic the SQLObject api & behavior exactly
# - Run both of them for a couple of weeks to find all bugs
# - Remove the SQLObject support
# - Clean up the API

"""Simple ORM abstraction layer"""

import re
import datetime
import decimal
import warnings

from kiwi.db.stormintegration import StormQueryExecuter
from kiwi.datatypes import currency

from storm import expr, Undef
from storm.base import Storm
from storm.database import create_database
from storm.exceptions import StormError, NotOneError
from storm.expr import (
    SQL, SQLRaw, Desc, And, Or, Not, In, Like, AutoTables, LeftJoin,
    Alias, Update, Join, NamedFunc)
from storm.info import get_cls_info, get_obj_info, ClassAlias
from storm.properties import (
    RawStr, Int, Bool, Float, DateTime, Date, TimeDelta, Unicode,
    Decimal, PropertyColumn)
from storm.properties import SimpleProperty, PropertyPublisherMeta
from storm.references import Reference, ReferenceSet
from storm.store import AutoReload, Store
from storm.tracer import debug
from storm.tz import tzutc
from storm.variables import (Variable, BoolVariable, DateVariable,
                             DateTimeVariable, RawStrVariable, DecimalVariable,
                             IntVariable)

from stoqlib.database.exceptions import ORMTestError

_IGNORED = object()


class SQLObjectNotFound(StormError):
    pass


class SQLObjectStyle(object):

    longID = False

    def idForTable(self, table_name):
        if self.longID:
            return self.tableReference(table_name)
        else:
            return "id"

    def pythonClassToAttr(self, class_name):
        return self._lowerword(class_name)

    def instanceAttrToIDAttr(self, attr_name):
        return attr_name + "ID"

    def pythonAttrToDBColumn(self, attr_name):
        return self._mixed_to_under(attr_name)

    def dbColumnToPythonAttr(self, column_name):
        return self._under_to_mixed(column_name)

    def pythonClassToDBTable(self, class_name):
        return class_name[0].lower() + self._mixed_to_under(class_name[1:])

    def dbTableToPythonClass(self, table_name):
        return table_name[0].upper() + self._under_to_mixed(table_name[1:])

    def pythonClassToDBTableReference(self, class_name):
        return self.tableReference(self.pythonClassToDBTable(class_name))

    def tableReference(self, table_name):
        return table_name + "_id"

    def _mixed_to_under(self, name, _re=re.compile("[A-Z]+")):
        if name.endswith("ID"):
            return self._mixed_to_under(name[:-2] + "_id")
        name = _re.sub(self._mixed_to_under_sub, name)
        if name.startswith("_"):
            return name[1:]
        return name

    def _mixed_to_under_sub(self, match):
        m = match.group(0).lower()
        if len(m) > 1:
            return "_%s_%s" % (m[:-1], m[-1])
        else:
            return "_%s" % m

    def _under_to_mixed(self, name, _re=re.compile("_.")):
        if name.endswith("_id"):
            return self._under_to_mixed(name[:-3] + "ID")
        return _re.sub(self._under_to_mixed_sub, name)

    def _under_to_mixed_sub(self, match):
        return match.group(0)[1].upper()

    @staticmethod
    def _capword(s):
        return s[0].upper() + s[1:]

    @staticmethod
    def _lowerword(s):
        return s[0].lower() + s[1:]


# Not a metaclass, more the 'sqlmeta' attribute
class _SQLMeta(object):
    def __init__(self, cls):
        self.soClass = cls

    @property
    def columnList(self):
        cls = self.soClass
        info = get_cls_info(cls)
        return info.columns

    def addColumn(self, column):
        cls = self.soClass
        kwargs = column.kwargs.copy()
        name = kwargs['name']
        propName = name + 'ID'
        dbName = name + '_id'
        if dbName.startswith('_'):
            dbName = dbName[1:]

        # This is completely wrong but enough for our usage
        if column.kwargs.get('forceDBName'):
            ref = Reference(getattr(cls, propName),
                            '%s.id' % column.foreignKey)
            setattr(cls, name, ref)
            return

        property_registry = cls._storm_property_registry
        property_registry.add_property(cls, column, propName)

    def delColumn(self, attr_name):
        cls = self.soClass
        info = get_cls_info(cls)
        delattr(cls, attr_name)
        columns = []
        for col in info.columns:
            if col.name != attr_name:
                columns.append(col)
        info.columns = tuple(columns)
        del info.attributes[attr_name]


class SQLObjectMeta(PropertyPublisherMeta):

    @staticmethod
    def _get_attr(attr, bases, dict):
        value = dict.get(attr)
        if value is None:
            for base in bases:
                value = getattr(base, attr, None)
                if value is not None:
                    break
        return value

    def __new__(cls, name, bases, dict):
        if Storm in bases or SQLObjectBase in bases:
            # Do not parse abstract base classes.
            return type.__new__(cls, name, bases, dict)

        style = cls._get_attr("_style", bases, dict)
        if style is None:
            dict["_style"] = style = SQLObjectStyle()

        table_name = cls._get_attr("_table", bases, dict)
        if table_name is None:
            table_name = style.pythonClassToDBTable(name)

        id_name = cls._get_attr("_idName", bases, dict)
        if id_name is None:
            id_name = style.idForTable(table_name)

        # Handle this later to call _parse_orderBy() on the created class.
        default_order = cls._get_attr("_defaultOrder", bases, dict)

        dict["__storm_table__"] = table_name

        attr_to_prop = {}
        for attr, prop in dict.items():
            attr_to_prop[attr] = attr
            if isinstance(prop, ForeignKey):
                db_name = prop.kwargs.get("dbName", None)
                local_prop_name = style.instanceAttrToIDAttr(attr)
                if db_name is None:
                    if local_prop_name.endswith('ID'):
                        db_name = attr + '_id'
                    else:
                        db_name = attr
                dict[local_prop_name] = local_prop = Int(
                    db_name, allow_none=not prop.kwargs.get("notNull", False),
                    validator=prop.kwargs.get("storm_validator", None))
                dict[attr] = Reference(local_prop,
                                       "%s.<primary key>" % prop.foreignKey)
                attr_to_prop[attr] = local_prop_name
            elif isinstance(prop, PropertyAdapter):
                db_name = prop.dbName or attr
                method_name = prop.alternateMethodName
                if method_name is None and prop.alternateID:
                    method_name = "by" + db_name[0].upper() + db_name[1:]
                if method_name is not None:
                    def func(cls, key, attr=attr):
                        store = cls._get_store()
                        obj = store.find(cls, getattr(cls, attr) == key).one()
                        if obj is None:
                            raise SQLObjectNotFound
                        return obj
                    func.func_name = method_name
                    dict[method_name] = classmethod(func)
            elif isinstance(prop, SQLMultipleJoin):
                # Generate addFoo/removeFoo names.
                def define_add_remove(dict, prop):
                    capitalised_name = (prop._otherClass[0].capitalize() +
                                        prop._otherClass[1:])

                    def add(self, obj):
                        prop._get_bound_reference_set(self).add(obj)
                    add.__name__ = "add" + capitalised_name
                    dict.setdefault(add.__name__, add)

                    def remove(self, obj):
                        prop._get_bound_reference_set(self).remove(obj)
                    remove.__name__ = "remove" + capitalised_name
                    dict.setdefault(remove.__name__, remove)
                define_add_remove(dict, prop)

        id_type = dict.setdefault("_idType", int)
        id_cls = {int: Int, str: RawStr, unicode: AutoUnicode}[id_type]
        dict["id"] = id_cls(id_name, primary=True, default=AutoReload)
        attr_to_prop[id_name] = "id"

        # Notice that obj is the class since this is the metaclass.
        obj = super(SQLObjectMeta, cls).__new__(cls, name, bases, dict)
        obj.sqlmeta = _SQLMeta(obj)

        property_registry = obj._storm_property_registry

        property_registry.add_property(obj, getattr(obj, "id"),
                                       "<primary key>")

        # Let's explore this same mechanism to register table names,
        # so that we can find them to handle prejoinClauseTables.
        property_registry.add_property(obj, getattr(obj, "id"),
                                       "<table %s>" % table_name)

        for fake_name, real_name in attr_to_prop.items():
            prop = getattr(obj, real_name)
            if fake_name != real_name:
                property_registry.add_property(obj, prop, fake_name)
            attr_to_prop[fake_name] = prop

        obj._attr_to_prop = attr_to_prop

        if default_order is not None:
            cls_info = get_cls_info(obj)
            cls_info.default_order = obj._parse_orderBy(default_order)

        return obj


class DotQ(object):
    """A descriptor that mimics the SQLObject 'Table.q' syntax"""

    def __get__(self, obj, cls=None):
        return BoundDotQ(cls)


class BoundDotQ(object):

    def __init__(self, cls):
        self._cls = cls

    def __getattr__(self, attr):
        if attr.startswith("__"):
            raise AttributeError(attr)
        elif attr == "id":
            cls_info = get_cls_info(self._cls)
            return cls_info.primary_key[0]
        else:
            return getattr(self._cls, attr)


class DotQAlias(object):

    def __get__(self, obj, cls=None):
        return BoundDotQAlias(obj)


class BoundDotQAlias(object):

    def __init__(self, alias):
        self._alias = alias

    def __getattr__(self, attr):
        if attr.startswith("__"):
            raise AttributeError(attr)
        elif attr == "id":
            #self._alias.name + '.id'
            return
        else:
            return getattr(self._alias, attr)


class Alias(Alias):
    q = DotQAlias()


class SQLObjectBase(Storm):
    """The root class of all SQLObject-emulating classes in your application.

    The general strategy for using Storm's SQLObject emulation layer
    is to create an application-specific subclass of SQLObjectBase
    (probably named "SQLObject") that provides an implementation of
    _get_store to return an instance of L{storm.store.Store}. It may
    even be implemented as returning a global L{Store} instance. Then
    all database classes should subclass that class.
    """
    __metaclass__ = SQLObjectMeta

    q = DotQ()
    _SO_creating = False

    def __init__(self, *args, **kwargs):
        self._connection = kwargs.get('connection')
        store = self._get_store()
        store.add(self)
        try:
            self._create(None, **kwargs)
        except:
            store.remove(self)
            raise

    def __storm_loaded__(self):
        self._init(None)

    def _create(self, _id_, **kwargs):
        store = self._get_store()
        if self._connection is None:
            self._connection = kwargs.pop('connection', store._connection)
        self._SO_creating = True
        self.set(**kwargs)
        del self._SO_creating
        self._init(None)

    def _init(self, id, *args, **kwargs):
        self._connection = kwargs.get('connection',
                                      getattr(self, '_connection', None))
        if self._connection is None:
            self._get_store()

        store = get_obj_info(self)['store']
        if store.transactions:
            self._connection = store.transactions[-1]

    def set(self, **kwargs):
        for attr, value in kwargs.iteritems():
            setattr(self, attr, value)

    def destroySelf(self):
        Store.of(self).remove(self)

    @classmethod
    def _get_store(cls):
        from stoqlib.database.runtime import get_connection
        cls._connection = cls.connection = get_connection()
        return cls.connection.store

    @classmethod
    def delete(cls, id, connection=None):
        # destroySelf() should be extended to support cascading, so
        # we'll mimic what SQLObject does here, even if more expensive.
        obj = cls.get(id)
        obj.destroySelf()

    @classmethod
    def get(cls, id, connection=None):
        id = cls._idType(id)
        store = cls._get_store()
        obj = store.get(cls, id)
        if obj is None:
            raise SQLObjectNotFound("Object not found")
        return obj

    @classmethod
    def _parse_orderBy(cls, orderBy):
        result = []
        if not isinstance(orderBy, (tuple, list)):
            orderBy = (orderBy, )
        for item in orderBy:
            if isinstance(item, basestring):
                desc = item.startswith("-")
                if desc:
                    item = item[1:]
                item = cls._attr_to_prop.get(item, item)
                if desc:
                    item = Desc(item)
            result.append(item)
        return tuple(result)

    @classmethod
    def select(cls, *args, **kwargs):
        return SQLObjectResultSet(cls, *args, **kwargs)

    @classmethod
    def selectBy(cls, orderBy=None, connection=None, **kwargs):
        return SQLObjectResultSet(cls, orderBy=orderBy, by=kwargs,
                                  connection=connection)

    @classmethod
    def selectOne(cls, *args, **kwargs):
        return SQLObjectResultSet(cls, *args, **kwargs)._one()

    @classmethod
    def selectOneBy(cls, connection=None, **kwargs):
        return SQLObjectResultSet(cls, by=kwargs,
                                  connection=connection)._one()

    @classmethod
    def selectFirst(cls, *args, **kwargs):
        return SQLObjectResultSet(cls, *args, **kwargs)._first()

    @classmethod
    def selectFirstBy(cls, orderBy=None, **kwargs):
        result = SQLObjectResultSet(cls, orderBy=orderBy, by=kwargs)
        return result._first()

    def syncUpdate(self):
        self._get_store().flush()

    def sync(self):
        store = self._get_store()
        store.flush()
        store.autoreload(self)


class ORMObject(SQLObjectBase):
    pass


class SQLObjectResultSet(object):
    """SQLObject-equivalent of the ResultSet class in Storm.

    Storm handles joins in the Store interface, while SQLObject
    does that in the result one.  To offer support for prejoins,
    we can't simply wrap our ResultSet instance, and instead have
    to postpone the actual find until the very last moment.
    """

    def __init__(self, cls, clause=None, clauseTables=None, orderBy=None,
                 limit=None, distinct=None, selectAlso=None, join=None,
                 by={}, prepared_result_set=None, slice=None, having=None,
                 connection=None):
        self._cls = cls
        self._clause = clause
        self._clauseTables = clauseTables
        self._orderBy = orderBy
        self._limit = limit
        self._join = join
        self._distinct = distinct
        self._selectAlso = selectAlso

        # Parameters not mapping SQLObject:
        self._by = by
        self._slice = slice
        self._prepared_result_set = prepared_result_set
        self._finished_result_set = None

    def _copy(self, **kwargs):
        copy = self.__class__(self._cls, **kwargs)
        for name, value in self.__dict__.iteritems():
            if name[1:] not in kwargs and name != "_finished_result_set":
                setattr(copy, name, value)
        return copy

    def _prepare_result_set(self):
        store = self._cls._get_store()

        args = []
        if self._clause:
            args.append(self._clause)

        for key, value in self._by.items():
            args.append(getattr(self._cls, key) == value)

        tables = []

        if self._clauseTables is not None:
            tables.extend(self._clauseTables)

        find_spec = self._cls

        if tables:
            # If we are adding extra tables, make sure the main table
            # is included.
            tables.insert(0, self._cls.__storm_table__)
            # Inject an AutoTables expression with a dummy true value to
            # be ANDed in the WHERE clause, so that we can introduce our
            # tables into the dynamic table handling of Storm without
            # disrupting anything else.
            args.append(AutoTables(SQL("1=1"), tables))

        if self._selectAlso is not None:
            if type(find_spec) is not tuple:
                find_spec = (find_spec, SQL(self._selectAlso))
            else:
                find_spec += (SQL(self._selectAlso), )

        if self._join:
            store = store.using(self._cls.__storm_table__, self._join)
        return store.find(find_spec, *args)

    def _finish_result_set(self):
        if self._prepared_result_set is not None:
            result = self._prepared_result_set
        else:
            result = self._prepare_result_set()

        if self._orderBy is not None:
            result.order_by(*self._cls._parse_orderBy(self._orderBy))

        if self._limit is not None or self._distinct is not None:
            result.config(limit=self._limit, distinct=self._distinct)

        if self._slice is not None:
            result = result[self._slice]

        return result

    @property
    def _result_set(self):
        if self._finished_result_set is None:
            self._finished_result_set = self._finish_result_set()
        return self._finished_result_set

    def _one(self):
        """Internal API for the base class."""
        return detuplelize(self._result_set.one())

    def _first(self):
        """Internal API for the base class."""
        return detuplelize(self._result_set.first())

    def __iter__(self):
        for item in self._result_set:
            yield detuplelize(item)

    def __getitem__(self, index):
        if isinstance(index, slice):
            if not index.start and not index.stop:
                return self

            if index.start and index.start < 0 or (
                index.stop and index.stop < 0):
                L = list(self)
                if len(L) > 100:
                    warnings.warn('Negative indices when slicing are slow: '
                                  'fetched %d rows.' % (len(L), ))
                start, stop, step = index.indices(len(L))
                assert step == 1, "slice step must be 1"
                index = slice(start, stop)
            return self._copy(slice=index)
        else:
            if index < 0:
                L = list(self)
                if len(L) > 100:
                    warnings.warn('Negative indices are slow: '
                                  'fetched %d rows.' % (len(L), ))
                return detuplelize(L[index])
            return detuplelize(self._result_set[index])

    def __contains__(self, item):
        result_set = self._result_set
        return item in result_set

    def __nonzero__(self):
        result_set = self._result_set
        return not result_set.is_empty()

    def count(self):
        result_set = self._result_set
        return result_set.count()

    def orderBy(self, orderBy):
        return self._copy(orderBy=orderBy)

    def limit(self, limit):
        return self._copy(limit=limit)

    def distinct(self):
        return self._copy(distinct=True, orderBy=None)

    def union(self, otherSelect, unionAll=False, orderBy=()):
        result1 = self._copy()._result_set.order_by()
        result2 = otherSelect._copy()._result_set.order_by()
        result_set = result1.union(result2, all=unionAll)
        return self._copy(
            prepared_result_set=result_set, distinct=False, orderBy=orderBy)

    def except_(self, otherSelect, exceptAll=False, orderBy=()):
        result1 = self._copy()._result_set.order_by()
        result2 = otherSelect._copy()._result_set.order_by()
        result_set = result1.difference(result2, all=exceptAll)
        return self._copy(
            prepared_result_set=result_set, distinct=False, orderBy=orderBy)

    def intersect(self, otherSelect, intersectAll=False, orderBy=()):
        result1 = self._copy()._result_set.order_by()
        result2 = otherSelect._copy()._result_set.order_by()
        result_set = result1.intersection(result2, all=intersectAll)
        return self._copy(
            prepared_result_set=result_set, distinct=False, orderBy=orderBy)

    def sum(self, attribute):
        if isinstance(attribute, basestring):
            attribute = SQL(attribute)
        result_set = self._result_set
        return result_set.sum(attribute)

    def max(self, attribute):
        if isinstance(attribute, basestring):
            attribute = SQL(attribute)
        result_set = self._result_set
        return result_set.max(attribute)


def detuplelize(item):
    """If item is a tuple, return first element, otherwise the item itself.

    The tuple syntax is used to implement prejoins, so we have to hide from
    the user the fact that more than a single object are being selected at
    once.
    """
    if type(item) is tuple:
        return item[0]
    return item


class PropertyAdapter(object):

    _kwargs = {}

    def __init__(self, dbName=None, notNull=False, default=Undef,
                 alternateID=None, unique=_IGNORED, name=_IGNORED,
                 alternateMethodName=None, length=_IGNORED, immutable=None,
                 forceDBName=None,
                 storm_validator=None, notNone=Undef):
        if default is None and notNull:
            raise RuntimeError("Can't use default=None and notNull=True")

        self.dbName = dbName
        self.alternateID = alternateID
        self.alternateMethodName = alternateMethodName

        # XXX Implement handler for:
        #
        #   - immutable (causes setting the attribute to fail)
        #
        # XXX Implement tests for ignored parameters:
        #
        #   - unique (for tablebuilder)
        #   - length (for tablebuilder for StringCol)
        #   - name (for _columns stuff)

        if callable(default):
            default_factory = default
            default = Undef
        else:
            default_factory = Undef
        if notNone is not Undef:
            allow_none = notNone
        elif notNull is not Undef:
            allow_none = notNone
        else:
            allow_none = Undef
        super(PropertyAdapter, self).__init__(dbName, allow_none=allow_none,
                                              default_factory=default_factory,
                                              default=default,
                                              validator=storm_validator,
                                              **self._kwargs)


class AutoUnicodeVariable(Variable):
    """Unlike UnicodeVariable, this will try to convert str to unicode."""
    __slots__ = ()

    def parse_set(self, value, from_db):
        if not isinstance(value, basestring):
            raise TypeError("Expected basestring, found %s" % repr(type(value)))
        return unicode(value)


class AutoUnicode(SimpleProperty):
    variable_class = AutoUnicodeVariable


class StringCol(PropertyAdapter, AutoUnicode):
    pass


class IntCol(PropertyAdapter, Int):
    pass


class BoolCol(PropertyAdapter, Bool):
    pass


class FloatCol(PropertyAdapter, Float):
    pass


class UtcDateTimeCol(PropertyAdapter, DateTime):
    _kwargs = {"tzinfo": tzutc()}


class DateTimeCol(PropertyAdapter, DateTime):
    pass


class DateCol(PropertyAdapter, Date):
    pass


class IntervalCol(PropertyAdapter, TimeDelta):
    pass


class DecimalCol(PropertyAdapter, Decimal):
    pass


class UnicodeCol(PropertyAdapter, Unicode):
    pass


class ForeignKey(object):

    def __init__(self, foreignKey, **kwargs):
        self.foreignKey = foreignKey
        self.kwargs = kwargs


class SQLMultipleJoin(ReferenceSet):

    def __init__(self, otherClass=None, joinColumn=None,
                 intermediateTable=None, otherColumn=None, orderBy=None):
        if intermediateTable:
            args = ("<primary key>",
                    "%s.%s" % (intermediateTable, joinColumn),
                    "%s.%s" % (intermediateTable, otherColumn),
                    "%s.<primary key>" % otherClass)
        else:
            args = ("<primary key>", "%s.%s" % (otherClass, joinColumn))
        ReferenceSet.__init__(self, *args)
        self._orderBy = orderBy
        self._otherClass = otherClass

    def __get__(self, obj, cls=None):
        if obj is None:
            return self
        bound_reference_set = ReferenceSet.__get__(self, obj)
        target_cls = bound_reference_set._target_cls
        where_clause = bound_reference_set._get_where_clause()
        return SQLObjectResultSet(target_cls, where_clause,
                                  orderBy=self._orderBy)

    def _get_bound_reference_set(self, obj):
        assert obj is not None
        return ReferenceSet.__get__(self, obj)


SQLRelatedJoin = SQLMultipleJoin


class SingleJoin(Reference):

    def __init__(self, otherClass, joinColumn):
        joinColumn = joinColumn.replace('_id', 'ID')
        super(SingleJoin, self).__init__(
            "<primary key>", "%s.%s" % (otherClass, joinColumn),
            on_remote=True)


class CONTAINSSTRING(Like):

    def __init__(self, expr, string):
        string = string.replace("!", "!!") \
                       .replace("_", "!_") \
                       .replace("%", "!%")
        Like.__init__(self, expr, "%" + string + "%", SQLRaw("'!'"))


class DeclarativeMeta(type):
    def __new__(meta, class_name, bases, new_attrs):
        cls = type.__new__(meta, class_name, bases, new_attrs)
        cls.__classinit__.im_func(cls, new_attrs)
        return cls


class Declarative(object):
    __metaclass__ = DeclarativeMeta

    def __classinit__(cls, new_attrs):
        pass


class SQLObjectView(object):

    def __init__(self, cls, columns):
        self.cls = cls
        self.columns = columns.copy()

    def __getattr__(self, attr):
        if not attr in self.columns:
            raise AttributeError("%s object has no attribute %s" % (
                self.cls.__name__, attr))
        return self.columns[attr]


class Viewable(Declarative):
    _connection = None
    clause = None

    def __classinit__(cls, new_attrs):
        cols = new_attrs.get('columns')
        if not cols:
            return

        group_by = []
        for name, col in cols.items():
            if has_sql_call(col):
                col = cols[name] = expr.Alias(col, name)
            else:
                group_by.append(col)

            setattr(cls, name, col)
        cls.group_by = group_by

        cls.q = SQLObjectView(cls, cols)

        tables = [cols['id'].table]
        for join in new_attrs.get('joins', []):
            tables.append(join)

        cls.tables = tables

    def get_connection(self):
        return None

    @classmethod
    def select(cls, clause=None, having=None, connection=None):
        attributes, columns = zip(*cls.columns.items())

        if connection is None:
            from stoqlib.database.runtime import get_connection
            connection = get_connection()
        store = connection.store
        clauses = []
        if clause:
            clauses.append(clause)

        if cls.clause:
            clauses.append(cls.clause)

        if clauses:
            clauses = [AND(*clauses)]

        def _load_view_objects(result, values):
            instance = cls()
            for attribute, value in zip(attributes, values):
                # Convert values according to the column specification
                if hasattr(cls.columns[attribute], 'variable_factory'):
                    var = cls.columns[attribute].variable_factory.func()
                    if value is not None:
                        value = var.parse_set(value, False)
                setattr(instance, attribute, value)
            return instance

        results = store.using(*cls.tables).find(columns, *clauses)
        if cls.group_by:
            results = results.group_by(*cls.group_by)

        results._load_objects = _load_view_objects
        return results


class Field(SQL):
    def __init__(self, table, column):
        SQL.__init__(self, '%s.%s' % (table, column))


class BLOBCol(PropertyAdapter, RawStr):
    pass


class PriceVariable(DecimalVariable):
    def parse_set(self, value, from_db):
        return currency('%0.2f' % value)


class PriceCol(DecimalCol):
    variable_class = PriceVariable


class QuantityVariable(DecimalVariable):
    def parse_set(self, value, from_db):
        return currency('%0.2f' % value)


class QuantityCol(DecimalCol):
    variable_class = QuantityVariable


class MyDateTimeVariable(DateTimeVariable, DateVariable):
    def parse_set(self, value, from_db):
        if isinstance(value, datetime.date):
            value = datetime.datetime(value.year, value.month, value.day)

        return DateTimeVariable.parse_set(self, value, from_db)


class DateTimeCol(DateTimeCol):
    variable_class = MyDateTimeVariable


class ConstantSpace(object):
    def __getattr__(self, attr):
        # Workarround arround an issue in inspect.isclass
        if attr == '__bases__':
            raise AttributeError
        return type(attr, (NamedFunc, ), {'name': attr})


class Transaction(object):
    def __init__(self, conn):
        # FIXME: s.d.runtime uses this
        self._connection = conn
        self.store = conn.store
        self.store.transactions.append(self)

    def query(self, stmt):
        return self._connection.execute(stmt)

    def queryAll(self, query):
        res = self.store.execute(
            SQL(query))
        return res.get_all()

    def commit(self, close=False):
        self._connection.commit()
        if close:
            self._connection.close()
            self.store.transactions.remove(self)

    def rollback(self):
        self._connection.rollback()

    def begin(self):
        pass

    def tableExists(self, table_name):
        return self._connection.tableExists(table_name)

    viewExists = tableExists

    def dropView(self, view_name):
        return self._connection.dropView(view_name)

    def dropTable(self, table_name, cascade=False):
        return self._connection.dropTable(table_name, cascade)

    def tableHasColumn(self, table_name, column_name):
        return self._connection.tableHasColumn(table_name, column_name)

    def block_implicit_flushes(self):
        self.store.block_implicit_flushes()

    def unblock_implicit_flushes(self):
        self.store.unblock_implicit_flushes()


class Connection(object):
    def __init__(self, db):
        self.db = db
        self.store = None

    def dbVersion(self):
        return (8, 3)

    def queryOne(self, query):
        res = self.store.execute(
            SQL(query))
        return res.get_one()

    def queryAll(self, query):
        res = self.store.execute(
            SQL(query))
        return res.get_all()

    def find(self, table=None, *args, **kwargs):
        if issubclass(table, Viewable):
            return table.select(args)
        else:
            return self.store.find(table, *args, **kwargs)

    def makeConnection(self):
        self.store = Store(self.db)
        if not hasattr(self.store, 'transactions'):
            self.store.transactions = []

    def close(self):
        pass

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
        #print 'Connection.createDatabase(%r, %r)' % (name, ifNotExists)
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
        res = self.execute(
            SQL("SELECT COUNT(*) FROM pg_database WHERE datname=?",
                (name, )))
        return res.get_one()[0]

    def commit(self):
        self.store.commit()

    def rollback(self):
        self.store.rollback()

    def execute(self, query):
        return self.store.execute(query)

    def sqlrepr(self, name):
        return name

    def block_implicit_flushes(self):
        self.store.block_implicit_flushes()

    def unblock_implicit_flushes(self):
        self.store.unblock_implicit_flushes()


def connectionForURI(uri):
    return Connection(create_database(uri))


def has_sql_call(column):
    if isinstance(column, PropertyColumn):
        return False

    if isinstance(column, expr.NamedFunc):
        if column.name in ('SUM', 'AVG', 'MIN', 'MAX'):
            return True

    elif isinstance(column, expr.CompoundExpr):
        for e in column.exprs:
            if has_sql_call(e):
                return True

    elif isinstance(column, expr.BinaryExpr):
        if has_sql_call(column.expr1) or has_sql_call(column.expr2):
            return True

    return False


def sqlIdentifier(*args, **kwargs):
    return True


def export_csv(*args, **kwargs):
    pass


def orm_startup():
    pass


def orm_enable_debugging():
    debug(True)


def orm_get_columns(table):
    for name, v in table._attr_to_prop.items():
        if not isinstance(v, PropertyColumn):
            continue
        yield getattr(table, name), name


def orm_get_random(column):
    if isinstance(column, Reference):
        return None

    variable = column.variable_factory.func

    if issubclass(variable, AutoUnicodeVariable):
        value = u''
    elif issubclass(variable, RawStrVariable):
        value = ''
    elif issubclass(variable, DateTimeVariable):
        value = datetime.datetime.now()
    elif issubclass(variable, IntVariable):
        value = None
    elif issubclass(variable, PriceVariable):
        value = currency(20)
    elif issubclass(variable, BoolVariable):
        value = False
    elif isinstance(variable, QuantityVariable):
        value = decimal.Decimal(1)
    elif issubclass(variable, DecimalVariable):
        value = decimal.Decimal(1)
    else:
        raise ValueError(column)

    return value


def orm_get_unittest_value(klass, test, tables_dict, name, column):
    value = None
    if isinstance(column, PropertyColumn):
        if column.variable_factory.keywords['value'] is not Undef:
            value = column.variable_factory.keywords['value']
        else:
            try:
                value = orm_get_random(column)
            except ValueError:
                raise ORMTestError("No default for %r" % (column, ))

    elif isinstance(column, Reference):
        if name in ('te_created', 'te_modified'):
            return None
        if isinstance(column._remote_key, str):
            cls = tables_dict[column._remote_key.split('.')[0]]
        else:
            cls = column._remote_key[0].cls
        value = test.create_by_type(cls)
        if value is None:
            raise ORMTestError("No example for %s" % cls)
    return value

orm_name = 'storm'

#debug(True)

# Exceptions

# ORMObject.get raises this
ORMObjectNotFound = SQLObjectNotFound
# ORMObject.selectOneBy raises this
ORMObjectMoreThanOneResultError = NotOneError

ORMObjectQueryExecuter = StormQueryExecuter

# Columns
BLOBCol = BLOBCol
BoolCol = BoolCol
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
SOPriceCol = PriceCol
AbstractDecimalCol = DecimalCol


def MyJoin(table1, table2, clause):
    return Join(table2, clause)


def MyLeftJoin(table1, table2, clause):
    return LeftJoin(table2, clause)


# SQLBuilder
const = ConstantSpace()
Alias = ClassAlias
AND = And
IN = In
INNERJOINOn = MyJoin


def ISNOTNULL(arg):
    return arg != None

LEFTJOINOn = MyLeftJoin
LIKE = Like
NOT = Not
OR = Or
DESC = Desc
SQLConstant = SQL


# Misc
export_csv = export_csv
SelectResults = SQLObjectResultSet
NoDefault = _IGNORED
Update = Update
