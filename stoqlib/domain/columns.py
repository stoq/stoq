# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
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
## Author(s):       Johan Dahlin                <jdahlin@async.com.br>
##                  Evandro Vale Miquelito      <evandro@async.com.br>
##
##
""" SQLObject columns and helpers """

import decimal

from formencode.validators import Validator
from kiwi.datatypes import currency
from sqlobject.col import SODecimalCol, Col, SOIntCol
from sqlobject.sqlbuilder import func
from sqlobject.converters import registerConverter

from stoqlib.domain.parameter import ParameterData
from stoqlib.lib.runtime import get_connection
from stoqlib.lib.parameters import (sysparam,
                                    DEFAULT_DECIMAL_PRECISION,
                                    DEFAULT_DECIMAL_SIZE)


def _CurrencyConverter(value, db):
    return repr(float(value))
registerConverter(currency, _CurrencyConverter)


#
# Validators
#


class _PriceValidator(Validator):

    def to_python(self, value, state):
        # Do not allow empty strings or None Values
        value = value or currency(0)
        if not isinstance(value, decimal.Decimal):
            value = decimal.Decimal(str(value))
        return currency(value)

    def from_python(self, value, state):
        return value

class _DecimalValidator(Validator):

    def to_python(self, value, state):
        # Do not allow empty strings or None Values
        value = value or 0
        if not isinstance(value, decimal.Decimal):
            value = decimal.Decimal(str(value))
        return value

    def from_python(self, value, state):
        return value


#
# Abstract Classes
#


class AbstractDecimalCol(SODecimalCol):
    def __init__(self, **kw):
        conn = get_connection()
        if conn.tableExists(ParameterData.get_db_table_name()):
            param = sysparam(conn)
            kw['size'] = param.DECIMAL_SIZE or DEFAULT_DECIMAL_SIZE
            kw['precision'] = (param.DECIMAL_PRECISION or
                               DEFAULT_DECIMAL_PRECISION)
        else:
            kw['size'] = DEFAULT_DECIMAL_SIZE
            kw['precision'] = DEFAULT_DECIMAL_PRECISION
        SODecimalCol.__init__(self, **kw)

    def createValidators(self):
        return ([_DecimalValidator()] +
                super(AbstractDecimalCol, self).createValidators())

class SOPriceCol(AbstractDecimalCol):
    def createValidators(self):
        return [_PriceValidator()] + super(SOPriceCol, self).createValidators()

class SOAutoIncCol(SOIntCol):
    def __init__(self, **kw):
        kw['default'] = func.nextval(kw.pop('seq_name'))
        kw['alternateID'] = True
        SOIntCol.__init__(self, **kw)


#
# Custom SQLObject columns
#


class DecimalCol(Col):
    baseClass = AbstractDecimalCol

class PriceCol(DecimalCol):
    baseClass = SOPriceCol

class AutoIncCol(Col):
    """This column defines an auto increment integer column. Domain classes
    must always supply a 'sequence name' argument when instantiating this
    column.

    @cvar seq_name: the postgres database sequence name
    """
    baseClass = SOAutoIncCol

    def __init__(self, seq_name, *args, **kw):
        kw['seq_name'] = seq_name
        Col.__init__(self, *args, **kw)
