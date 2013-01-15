# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (c) 2006, 2007 Canonical
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

# This file is full of hacks to mimic the SQLObject API
# TODO:
# - Remove .q and access properties directly
# - Replace select/get/etc with storm.find()

"""Simple ORM abstraction layer"""

import datetime
import decimal
import warnings

from kiwi.db.stormintegration import StormQueryExecuter
from kiwi.currency import currency
from kiwi.python import Settable
from storm import Undef
from storm.base import Storm
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

from stoqlib.lib.defaults import QUANTITY_PRECISION
from stoqlib.database.debug import StoqlibDebugTracer
from stoqlib.database.viewable import MyAlias, Viewable

from stoqlib.database.exceptions import ORMTestError, ORMObjectNotFound

# Exceptions


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

    # FIXME: Remove
    @classmethod
    def get(cls, obj_id, store=None):
        warnings.warn("use store.get() or store.fetch()", DeprecationWarning,
                      stacklevel=2)
        obj = store.get(cls, int(obj_id))
        if obj is None:
            raise ORMObjectNotFound("Object not found")
        return obj

    # FIXME: Remove
    @classmethod
    def select(cls, *args, **kwargs):
        warnings.warn("use store.find()", DeprecationWarning, stacklevel=2)
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

    # FIXME: Remove
    def sync(self):
        warnings.warn("use store.flush()", DeprecationWarning, stacklevel=2)
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


class BLOBCol(RawStr):
    pass


class PriceVariable(DecimalVariable):
    def parse_set(self, value, from_db):
        # XXX: We cannot reduce the precision when converting to currency, since
        # sometimes we need a cost of a product to have more than 2 digits
        return currency(DecimalVariable.parse_set(value, from_db))


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
    def __init__(self, store=None, **kwargs):
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


AutoReload = AutoReload

# Columns, we're keeping the Col suffix to avoid clashes between
# decimal.Decimal and storm.properties.Decimal
BLOBCol = RawStr
BoolCol = Bool
DecimalCol = Decimal
IntCol = Int
StringCol = AutoUnicode
UnicodeCol = AutoUnicode
