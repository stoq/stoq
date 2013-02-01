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
from kiwi.currency import currency

from storm.properties import RawStr, Int, Bool, DateTime, Decimal, Unicode
from storm.variables import (DateVariable, DateTimeVariable,
                             DecimalVariable)

from stoqlib.lib.defaults import QUANTITY_PRECISION


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


# Columns, we're keeping the Col suffix to avoid clashes between
# decimal.Decimal and storm.properties.Decimal
BLOBCol = RawStr
BoolCol = Bool
DecimalCol = Decimal
IntCol = Int
UnicodeCol = Unicode
