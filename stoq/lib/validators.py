# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2004 Async Open Source <http://www.async.com.br>
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
"""
lib/validators.py:

    Validators for stoq applications.
"""

import datetime

from kiwi.datatypes import format_price

from stoq.lib.parameters import sysparam
from stoq.lib.runtime import get_connection

def is_date_in_interval(date, start_date, end_date):
    """Check if a certain date is in an interval. The function accepts 
    None values for start_date and end_date and, in this case, return True
    if there is no interval to check."""
    assert isinstance(date, datetime.datetime)
    q1 = q2 = True
    if start_date:
        assert isinstance(start_date, datetime.datetime)
        q1 = date >= start_date
    if end_date:
        assert isinstance(end_date, datetime.datetime)
        q2 = date <= end_date
    return q1 and q2

def compare_float_numbers(float_number1, float_number2):
    difference = abs(float_number1 - float_number2)
    conn = get_connection()
    tolerance = sysparam(conn).COMPARISON_FLOAT_TOLERANCE
    return difference <= tolerance

def format_quantity(quantity):
    conn = get_connection()
    if (quantity * 100 % 100) == 0:
        return '%.0f' % quantity
    precision = sysparam(conn).STOCK_BALANCE_PRECISION
    return '%. *f' % (precision, quantity)

def get_price_format_str():
    conn = get_connection()
    precision = sysparam(conn).SELLABLE_PRICE_PRECISION
    return '%%.%sf' % precision

def get_formatted_price(float_value):
    conn = get_connection()
    precision = sysparam(conn).SELLABLE_PRICE_PRECISION
    return format_price(float_value, precision=precision)


