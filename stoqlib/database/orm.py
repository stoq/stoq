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
# - Replace get/etc with storm.find()

"""Simple ORM abstraction layer"""

import datetime
import decimal
import warnings

from kiwi.currency import currency
from storm.base import Storm
from storm.properties import RawStr, Int, Bool, DateTime, Decimal
from storm.properties import SimpleProperty
from storm.store import Store
from storm.variables import (Variable, DateVariable,
                             DateTimeVariable, DecimalVariable)

from stoqlib.database.exceptions import ORMObjectNotFound

from stoqlib.lib.defaults import QUANTITY_PRECISION


class SQLObjectBase(Storm):
    """The root class of all SQLObject-emulating classes in your application.

    The general strategy for using Storm's SQLObject emulation layer
    is to create an application-specific subclass of SQLObjectBase
    (probably named "SQLObject") that provides an implementation of
    get_store to return an instance of :class:`storm.store.Store`. It may
    even be implemented as returning a global :class:`Store` instance. Then
    all database classes should subclass that class.
    """

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


# Columns, we're keeping the Col suffix to avoid clashes between
# decimal.Decimal and storm.properties.Decimal
BLOBCol = RawStr
BoolCol = Bool
DecimalCol = Decimal
IntCol = Int
StringCol = AutoUnicode
UnicodeCol = AutoUnicode
