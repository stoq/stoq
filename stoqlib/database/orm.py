# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (c) 2006, 2007 Canonical
## Copyright (C) 2008-2012 Async Open Source <http://www.async.com.br>
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
# TODO:
# - Remove .q and access properties directly
# - Replace select/selectBy/etc with storm.find()

"""Simple ORM abstraction layer"""

import datetime
import decimal

from kiwi.db.stormintegration import StormQueryExecuter
from kiwi.currency import currency
from kiwi.python import Settable
from psycopg2 import IntegrityError
from storm import expr, Undef
from storm.base import Storm
from storm.exceptions import StormError, NotOneError
from storm.expr import (
    SQL, SQLRaw, Desc, And, Or, Not, In, Like, LeftJoin,
    Alias, Update, Join, NamedFunc, Select, compile as expr_compile,
    is_safe_token)
from storm.info import get_cls_info, ClassAlias
from storm.properties import (RawStr, Int, Bool, DateTime, Decimal,
    PropertyColumn)
from storm.properties import SimpleProperty
from storm.references import Reference, ReferenceSet
from storm.store import AutoReload, Store
from storm.tracer import install_tracer
from storm.variables import (Variable, BoolVariable, DateVariable,
                             DateTimeVariable, RawStrVariable, DecimalVariable,
                             IntVariable)

from stoqlib.lib.defaults import DECIMAL_PRECISION, QUANTITY_PRECISION
from stoqlib.database.debug import StoqlibDebugTracer


# Exceptions

class ORMObjectNotFound(StormError):
    # ORMObject.get raises this
    pass


class ORMTestError(Exception):
    pass


NotOneError = NotOneError
IntegrityError = IntegrityError


class ORMObjectQueryExecuter(StormQueryExecuter):

    def get_post_result(self, result):
        descs, query = self.table.post_search_callback(result)
        # This should not be present in the query, since post_search_callback
        # should only use aggregate functions.
        query.order_by = Undef
        query.group_by = Undef
        store = self.store
        values = store.execute(query).get_one()
        assert len(descs) == len(values), (descs, values)
        data = {}
        for desc, value in zip(descs, list(values)):
            data[desc] = value
        return Settable(**data)


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
            return getattr(self._alias.expr, attr)


class MyAlias(Alias):
    q = DotQAlias()


def GetAlias(klass, name):
    # If it is a viewable we should use our own Alias that handles it
    # correctly. We cant use ClassAlias as that depends on __storm_id__ and
    # __storm_table__
    if issubclass(klass, Viewable):
        return MyAlias(klass, name)
    else:
        return ClassAlias(klass, name)


class SQLObjectBase(Storm):
    """The root class of all SQLObject-emulating classes in your application.

    The general strategy for using Storm's SQLObject emulation layer
    is to create an application-specific subclass of SQLObjectBase
    (probably named "SQLObject") that provides an implementation of
    get_store to return an instance of :class:`storm.store.Store`. It may
    even be implemented as returning a global :class:`Store` instance. Then
    all database classes should subclass that class.
    """

    q = DotQ()

    def __init__(self, store=None, **kwargs):
        self._store = store
        if store is None:
            store = Store.of(self)
        if store:
            store.add(self)

        for attr, value in kwargs.iteritems():
            # FIXME: storm is not setting foreign keys correctly if the
            # value is None (NULL)
            if value is not None:
                setattr(self, attr, value)

    def __eq__(self, other):
        if type(self) is not type(other):
            return False

        from stoqlib.lib.parameters import is_developer_mode
        if is_developer_mode():
            # Check this only in develper mode to get as many potential errors
            # as possible.
            assert Store.of(self) is Store.of(other)
        return self.id == other.id

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def store(self):
        return Store.of(self)

    @classmethod
    def get(cls, obj_id, store=None):
        obj = store.get(cls, int(obj_id))
        if obj is None:
            raise ORMObjectNotFound("Object not found")
        return obj

    @classmethod
    def select(cls, *args, **kwargs):
        args = list(args)
        query = None
        if args:
            query = args.pop(0)
        store = kwargs.pop('store')

        # args and kwargs should be empty, otherwise we will have to handle the
        # remaining callsites properly
        assert not kwargs, kwargs
        assert not args, args
        if query:
            results = store.find(cls, query)
        else:
            results = store.find(cls)

        return results

    @classmethod
    def selectBy(cls, store=None, **kwargs):
        return store.find(cls, **kwargs)

    def syncUpdate(self):
        self.store.flush()

    def sync(self):
        store = self.store
        store.flush()
        store.autoreload(self)


class AutoUnicodeVariable(Variable):
    """Unlike UnicodeVariable, this will try to convert str to unicode."""
    __slots__ = ()

    def parse_set(self, value, from_db):
        if not isinstance(value, basestring):
            raise TypeError("Expected basestring, found %s" % repr(type(value)))
        return unicode(value)


class AutoUnicode(SimpleProperty):
    variable_class = AutoUnicodeVariable


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
        # This is an Alias, so we should return the original name (as this
        # is used to construct queries clauses)
        return self.columns[attr].expr


class Viewable(Declarative):
    _store = None
    clause = None

    def __classinit__(cls, new_attrs):
        cols = new_attrs.get('columns')
        if not cols and hasattr(cls, 'columns'):
            cols = cls.columns
        if not cols:
            return

        hidden_columns = new_attrs.get('hidden_columns', [])
        group_by = []
        needs_group_by = False
        for name, col in cols.items():
            if name in hidden_columns:
                del cols[name]
                continue

            if isinstance(col, expr.Alias):
                col = col.expr

            if not has_sql_call(col):
                group_by.append(col)
            else:
                needs_group_by = True

            cols[name] = expr.Alias(col, name)
            setattr(cls, name, col)

        if needs_group_by:
            cls.group_by = group_by
        else:
            cls.group_by = []

        cls.q = SQLObjectView(cls, cols)

        if isinstance(cols['id'], expr.Alias):
            first_table = cols['id'].expr.table
        else:
            first_table = cols['id'].table

        if 'joins' not in new_attrs and hasattr(cls, 'joins'):
            # Joins are not defined for this class, but are defined in the base
            # class. We should not reconstruct the list of queries
            tables = []
        else:
            # Joins is defined in this class, but not in the base class. So we
            # should build the list of tables to be used here
            tables = [first_table]

            for join in new_attrs.get('joins', []):
                # If the table is actually another Viewable, join with a Subselect
                table = join.right
                if isinstance(table, MyAlias) and issubclass(table.expr, Viewable):
                    subselect = table.expr.get_select()
                    subselect = expr.Alias(subselect, table.name)
                    join = join.__class__(subselect, join.on)
                tables.append(join)

            cls.tables = tables

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        if self.__class__ == other.__class__:
            return self.id == other.id
        return False

    @property
    def store(self):
        return self._store

    def sync(self):
        """Update the values of this object from the database
        """
        # Flush to make sure we get the latest values.
        self._store.flush()
        new_obj = self.get(self.id, self._store)
        self.__dict__.update(new_obj.__dict__)

    @classmethod
    def get_select(cls):
        attributes, columns = zip(*cls.columns.items())
        return Select(columns, cls.clause or Undef, cls.tables,
                      group_by=cls.group_by or Undef)

    @classmethod
    def _get_tables_for_query(cls, tables, query):
        """This method will check the joins defined in the viewable and the
        query specified to see if there is any table used in the clause that is
        not in the joins.

        We should avoid using implicit joins, but until we fix all uses of it,
        this will make it work. FIX:

        - ProductFullStockView with Sellable.get_unblocked_sellables_query
        """
        # This is a AND or OR
        if isinstance(query, expr.CompoundExpr):
            for e in query.exprs:
                cls._get_tables_for_query(tables, e)

        # This is a == or <= or =>, etc..
        elif isinstance(query, expr.BinaryExpr):
            for e in [query.expr1, query.expr2]:
                if not isinstance(e, PropertyColumn):
                    continue

                q_table = e.cls
                # See if the table this property if from is in the list of
                # tables. Else, add it
                for table in tables:
                    if isinstance(table, expr.JoinExpr):
                        if isinstance(table.right, expr.Alias):
                            # XXX: I am not sure if this is correct. If the join
                            # is an alias, we should query that using the alias
                            # and not the origianl table name
                            #table = table.right.expr
                            pass
                        else:
                            table = table.right

                    if table == q_table:
                        break
                else:
                    # Adding just the table. storm is smart enougth to add the
                    # query for the join
                    tables.append(q_table)

        elif isinstance(query, expr.PrefixExpr):
            return cls._get_tables_for_query(tables, query.expr)

        elif query:
            raise AssertionError(query)

        return tables

    @classmethod
    def select(cls, clause=None, having=None, store=None, order_by=None,
               distinct=None):
        attributes, columns = zip(*cls.columns.items())

        # FIXME: This should probably be removed
        if store is None:
            from stoqlib.database.runtime import get_default_store
            store = get_default_store()
        clauses = []
        if clause:
            clauses.append(clause)

        if cls.clause:
            clauses.append(cls.clause)

        if clauses:
            clauses = [AND(*clauses)]

        # Pass a copy since _get_tables_for_query will modify the list
        tables = cls._get_tables_for_query(cls.tables[:], clause)

        def _load_view_objects(result, values):
            instance = cls()
            instance._store = store
            for attribute, value in zip(attributes, values):
                # Convert values according to the column specification
                if hasattr(cls.columns[attribute], 'variable_factory'):
                    var = cls.columns[attribute].variable_factory.func()
                    if value is not None:
                        value = var.parse_set(value, False)
                setattr(instance, attribute, value)
            return instance

        results = store.using(*tables).find(columns, *clauses)
        if cls.group_by:
            results = results.group_by(*cls.group_by)
        if order_by:
            results = results.order_by(order_by)
        if distinct:
            results.config(distinct=True)

        results._load_objects = _load_view_objects
        return results

    @classmethod
    def get(cls, obj_id, store):
        obj = cls.select(cls.id == obj_id, store=store)[0]
        if obj is None:
            raise ORMObjectNotFound("Object not found")
        return obj


class Field(SQL):
    def __init__(self, table, column):
        SQL.__init__(self, '%s.%s' % (table, column))


class BLOBCol(RawStr):
    pass


class PriceVariable(DecimalVariable):
    def parse_set(self, value, from_db):
        return currency('%0.*f' % (DECIMAL_PRECISION, value))


class PriceCol(Decimal):
    variable_class = PriceVariable


class QuantityVariable(DecimalVariable):
    def parse_set(self, value, from_db):
        return decimal.Decimal('%0.*f' % (QUANTITY_PRECISION, value))


class QuantityCol(Decimal):
    variable_class = QuantityVariable


class PercentCol(Decimal):
    pass


class MyDateTimeVariable(DateTimeVariable, DateVariable):
    def parse_set(self, value, from_db):
        if type(value) is datetime.date:
            value = datetime.datetime(value.year, value.month, value.day)

        return DateTimeVariable.parse_set(self, value, from_db)


class DateTimeCol(DateTime):
    variable_class = MyDateTimeVariable


class ConstantSpace(object):
    def __getattr__(self, attr):
        # Workarround arround an issue in inspect.isclass
        if attr == '__bases__':
            raise AttributeError
        return type(attr, (NamedFunc, ), {'name': attr})


def has_sql_call(column):
    if isinstance(column, PropertyColumn):
        return False

    if isinstance(column, expr.NamedFunc):
        if column.name in ('SUM', 'AVG', 'MIN', 'MAX', 'COUNT'):
            return True
        for e in column.args:
            if has_sql_call(e):
                return True

    elif isinstance(column, expr.CompoundExpr):
        for e in column.exprs:
            if has_sql_call(e):
                return True

    elif isinstance(column, expr.BinaryExpr):
        if has_sql_call(column.expr1) or has_sql_call(column.expr2):
            return True

    elif isinstance(column, expr.Alias):
        if has_sql_call(column.expr):
            return True

    return False


def sqlIdentifier(identifier):
    return (not expr_compile.is_reserved_word(identifier) and
            is_safe_token(identifier))


def export_csv(*args, **kwargs):
    pass


def orm_startup():
    pass


def orm_enable_debugging():
    install_tracer(StoqlibDebugTracer())


def orm_get_columns(table):
    for name, v in table.__dict__.items():
        if not isinstance(v, (PropertyColumn, Reference)):
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


class ORMTypeInfo(object):
    def __init__(self, orm_type):
        self.orm_type = orm_type

    def get_column_names(self):
        info = get_cls_info(self.orm_type)
        for name, attr in info.attributes.items():
            yield name

    def get_foreign_columns(self):
        info = get_cls_info(self.orm_type)
        for name, attr in info.attributes.items():
            if not name.endswith('_id'):
                continue

            name = name[:-2]
            ref = getattr(self.orm_type, name)
            other_class = ref._remote_key.split('.')[0]
            yield name, other_class

    def get_single_joins(self):

        for name, v in self.orm_type.__dict__.items():
            if not isinstance(v, Reference):
                continue
            other_class = v._remote_key.split('.')[0]
            yield name, other_class

        for name, v in self.orm_type.__dict__.items():
            if not isinstance(v, ReferenceSet):
                continue
            other_class = v._remote_key1.split('.')[0]
            yield name, other_class


class ORMObject(SQLObjectBase):
    pass


AutoReload = AutoReload

# Columns, we're keeping the Col suffix to avoid clashes between
# decimal.Decimal and storm.properties.Decimal
BLOBCol = RawStr
BoolCol = Bool
DecimalCol = Decimal
IntCol = Int
StringCol = AutoUnicode
UnicodeCol = AutoUnicode


# SQLBuilder
const = ConstantSpace()
func = const
#Alias = ClassAlias
Alias = GetAlias
AND = And
IN = In


class ILike(Like):
    oper = ' ILIKE '


Join = Join
LeftJoin = LeftJoin
LIKE = Like
ILIKE = ILike
NOT = Not
OR = Or
DESC = Desc
SQLConstant = SQL


# Misc
export_csv = export_csv
Update = Update
debug = orm_enable_debugging
