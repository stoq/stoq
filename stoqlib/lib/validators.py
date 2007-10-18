# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source <http://www.async.com.br>
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
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
"""Validators for stoq applications"""

import datetime
import re

from kiwi.datatypes import format_price

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.defaults import DECIMAL_PRECISION

_ = stoqlib_gettext

POSTAL_CODE_CHAR_LEN = 8


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

def format_quantity(quantity):
    if (quantity * 100 % 100) == 0:
        return '%.0f' % quantity
    return '%.*f' % (DECIMAL_PRECISION, quantity)

def get_price_format_str():
    return '%%.%sf' % DECIMAL_PRECISION

def get_formatted_price(float_value):
    return format_price(float_value, precision=DECIMAL_PRECISION)

#
# Phone number validators
#

def validate_phone_number(phone_number):
    phone_number = raw_phone_number(phone_number)
    digits = len(phone_number)
    if digits == 11:
        return phone_number[:1] == '0'
    return digits in range(7, 11)

def raw_phone_number(phone_number):
    return re.sub('[^0-9]', '', phone_number)

def _format_phone_number(digits, phone):
    if digits == 11 and phone[:1] == '0':
        phone = phone[1:]
        digits -= 1
    if digits == 7:
        return '%s-%s' % (phone[:3], phone[3:7])
    if digits == 8:
        return '%s-%s' % (phone[:4], phone[4:8])
    if digits == 9:
        return '(%s) %s-%s' % (phone[:2], phone[2:5], phone[5:9])
    if digits == 10:
        return '(%s) %s-%s' % (phone[:2], phone[2:6], phone[6:10])
    return phone

def format_phone_number(phone_number):
    if validate_phone_number(phone_number):
        phone_number = raw_phone_number(phone_number)
        return _format_phone_number(len(phone_number), phone_number)
    return phone_number

def validate_postal_code(postal_code):
    if not postal_code:
        return False
    return len(raw_postal_code(postal_code)) == POSTAL_CODE_CHAR_LEN

def raw_postal_code(postal_code):
    return re.sub("[^0-9]", '', postal_code)

def format_postal_code(postal_code):
    if not validate_postal_code(postal_code):
        return postal_code
    postal_code = raw_postal_code(postal_code)
    return "%s-%s" % (postal_code[:5],
                      postal_code[5:8])
