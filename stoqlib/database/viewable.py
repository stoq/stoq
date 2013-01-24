# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008-2013 Async Open Source <http://www.async.com.br>
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

"""DeprecatedViewable"""

# FIXME: This file be replaced by something, all this code needs to go

from storm import Undef
from storm.expr import (Alias, And, BinaryExpr, CompoundExpr,
                        FuncExpr, JoinExpr, PrefixExpr, Select)
from storm.properties import PropertyColumn

from stoqlib.database.exceptions import ORMObjectNotFound


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


class DeprecatedViewableAlias(Alias):
    q = DotQAlias()


def _has_sql_call(column):
    if isinstance(column, PropertyColumn):
        return False

    if isinstance(column, FuncExpr):
        if column.name in ('SUM', 'AVG', 'MIN', 'MAX', 'COUNT'):
            return True
        for e in column.args:
            if _has_sql_call(e):
                return True

    elif isinstance(column, CompoundExpr):
        for e in column.exprs:
            if _has_sql_call(e):
                return True

    elif isinstance(column, BinaryExpr):
        if _has_sql_call(column.expr1) or _has_sql_call(column.expr2):
            return True

    elif isinstance(column, Alias):
        if _has_sql_call(column.expr):
            return True

    return False


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


class DeprecatedViewable(Declarative):
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

            if isinstance(col, Alias):
                col = col.expr

            if not _has_sql_call(col):
                group_by.append(col)
            else:
                needs_group_by = True

            cols[name] = Alias(col, name)
            setattr(cls, name, col)

        if needs_group_by:
            cls.group_by = group_by
        else:
            cls.group_by = []

        cls.q = SQLObjectView(cls, cols)

        if isinstance(cols['id'], Alias):
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
                # If the table is actually another DeprecatedViewable, join with a Subselect
                table = join.right
                if isinstance(table, DeprecatedViewableAlias) and issubclass(table.expr, DeprecatedViewable):
                    subselect = table.expr.get_select()
                    subselect = Alias(subselect, table.name)
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
        if isinstance(query, CompoundExpr):
            for e in query.exprs:
                cls._get_tables_for_query(tables, e)

        # This is a == or <= or =>, etc..
        elif isinstance(query, BinaryExpr):
            for e in [query.expr1, query.expr2]:
                if not isinstance(e, PropertyColumn):
                    continue

                q_table = e.cls
                # See if the table this property if from is in the list of
                # tables. Else, add it
                for table in tables:
                    if isinstance(table, JoinExpr):
                        if isinstance(table.right, Alias):
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

        elif isinstance(query, PrefixExpr):
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
            clauses = [And(*clauses)]

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
