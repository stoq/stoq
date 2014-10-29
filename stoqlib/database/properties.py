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
##

import datetime
import decimal
import warnings

from kiwi.currency import currency

from storm.properties import RawStr, Int, Bool, DateTime, Decimal, Unicode
from storm.properties import SimpleProperty
from storm.store import AutoReload
from storm.variables import (DateVariable, DateTimeVariable,
                             DecimalVariable, IntVariable,
                             Variable)

from stoqlib.lib.defaults import QUANTITY_PRECISION


class Identifier(int):

    def __new__(cls, value):
        instance = super(Identifier, cls).__new__(cls, value)
        instance.prefix = ''
        return instance

    def __str__(self):
        return '%s%05d' % (self.prefix, self)

    def __unicode__(self):
        return unicode(str(self))


class _IdentifierVariable(IntVariable):
    def parse_get(self, value, to_db):
        return Identifier(value)


class IdentifierCol(Int):
    """A numeric identifier for an object

    This should be using when defining an identifier column to have
    some facilities, like formating it to a predefined pattern when
    converted to str/unicode. For instance::

        >>> from stoqlib.domain.base import Domain
        >>> from stoqlib.database.runtime import new_store
        >>>
        >>> class TestProduct(Domain):
        ...     identifier = IdentifierCol()
        >>>
        >>> store = new_store()
        >>> p = TestProduct(store=store)
        >>> p.identifier = 666
        >>>
        >>> p.identifier
        666
        >>> str(p.identifier)
        '00666'
        >>> unicode(p.identifier)
        u'00666'
        >>>
        >>> store.rollback(close=True)

    """

    variable_class = _IdentifierVariable

    def __init__(self):
        super(IdentifierCol, self).__init__(default=AutoReload)

    def __get__(self, obj, cls=None):
        # This will get the column definition or the variable
        data = super(IdentifierCol, self).__get__(obj, cls)
        # if there is an object, then its the variable
        if obj and hasattr(obj, 'branch'):
            data.prefix = obj.branch.acronym or ''
        return data


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


class EnumVariable(Variable):
    __slots__ = ()

    def parse_set(set, value, from_db):
        return value

    def parse_get(self, value, to_db):
        if isinstance(value, str):
            value = unicode(value)
        return value


class EnumCol(SimpleProperty):
    variable_class = EnumVariable


class MyDateTimeVariable(DateTimeVariable, DateVariable):
    def parse_set(self, value, from_db):
        if type(value) is datetime.date:
            warnings.warn("Using datetime.date is deprecated, pass in "
                          "datetime.datetime instead", stacklevel=4)
            value = datetime.datetime(value.year, value.month, value.day)

        return DateTimeVariable.parse_set(self, value, from_db)


class DateTimeCol(DateTime):
    variable_class = MyDateTimeVariable


class UUIDVariable(Variable):
    __slots__ = ()

    # FIXME: There's a cache invalidation bug in Storm that breaks
    #        test_transaction.testCacheInvalidation that prevents us from
    #        being able to use uuid instances
    def parse_set(self, value, from_db):
        # if from_db and isinstance(value, basestring):
        #     value = uuid.UUID(value)
        # elif not isinstance(value, uuid.UUID):
        #      raise TypeError("Expected UUID, found %r: %r"
        #                      % (type(value), value))

        return unicode(value)


class UUIDCol(SimpleProperty):
    variable_class = UUIDVariable

# Columns, we're keeping the Col suffix to avoid clashes between
# decimal.Decimal and storm.properties.Decimal
BLOBCol = RawStr
BoolCol = Bool
DecimalCol = Decimal
IdCol = UUIDCol
IntCol = Int
UnicodeCol = Unicode
