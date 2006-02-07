# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s):       Johan Dahlin                <jdahlin@async.com.br>
##
""" SQLObject columns and helpers """

from formencode.validators import Validator
from kiwi.datatypes import currency
from sqlobject.col import SOFloatCol, FloatCol
from sqlobject.converters import registerConverter

def _CurrencyConverter(value, db):
    return repr(float(value))
registerConverter(currency, _CurrencyConverter)

class _PriceValidator(Validator):

    def to_python(self, value, state):
        return currency(float(value))

    def from_python(self, value, state):
        # repr(value) is not enough, since it may include the symbol,
        # so convert it to a float first
        return value

class SOPriceCol(SOFloatCol):
    def createValidators(self):
        return [_PriceValidator()] + super(SOPriceCol, self).createValidators()

class PriceCol(FloatCol):
    baseClass = SOPriceCol

