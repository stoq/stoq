# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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

import re

from kiwi.currency import format_price

from stoqlib.database.runtime import get_connection
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.defaults import DECIMAL_PRECISION, QUANTITY_PRECISION

_ = stoqlib_gettext


def format_quantity(quantity):
    if (quantity * 100 % 100) == 0:
        return '%.0f' % quantity
    return '%.*f' % (QUANTITY_PRECISION, quantity)


def get_formatted_percentage(value):
    return "%.*f %%" % (DECIMAL_PRECISION, value)


def get_price_format_str():
    return '%%.%sf' % DECIMAL_PRECISION


def get_formatted_price(float_value, symbol=True, precision=DECIMAL_PRECISION):
    return format_price(float_value, symbol=symbol,
                        precision=precision)


def get_formatted_cost(float_value, symbol=True):
    from stoqlib.lib.parameters import sysparam
    precision = sysparam(get_connection()).COST_PRECISION_DIGITS
    return get_formatted_price(float_value, symbol=symbol,
                               precision=precision)


#
#  Phone number formatters
#

def raw_phone_number(phone_number):
    return re.sub('[^0-9]', '', phone_number)


def format_phone_number(phone_number):
    phone = raw_phone_number(phone_number)
    digits = len(phone)
    # 190, 192, 193: emergency services
    # 1052, 1056: phone companies
    if digits == 3 or digits == 4:
        return phone
    elif digits == 5:
        return '%s %s' % (phone[:3], phone[3:])
    elif digits == 7:
        return '%s-%s' % (phone[:3], phone[3:7])
    elif digits == 8:
        return '%s-%s' % (phone[:4], phone[4:8])
    elif digits == 9:
        return '(%s) %s-%s' % (phone[:2], phone[2:5], phone[5:9])
    elif digits == 10:
        # 0[358]00 XXX-XXX
        if phone[1] in '358':
            return '%s %s-%s' % (phone[:4], phone[4:7],
                                 phone[7:])
        return '(%s) %s-%s' % (phone[:2], phone[2:6], phone[6:10])
    elif digits == 11:
        # 0[358]00 XXX-XXXX
        if phone[1] in '358':
            return '%s %s-%s' % (phone[:4], phone[4:7],
                                 phone[7:])
        if phone[:1] == '0':
            return '(%s) %s-%s' % (phone[1:3], phone[3:7], phone[7:11])
        else:
            return '(%s) %s-%s' % (phone[:2], phone[2:7], phone[7:11])
    elif digits == 12:
        # DDD 11 in São Paulo will have 9 numbers starting 2012-07-29
        if phone[:1] == '0':
            phone = phone[1:]
        return '(%s) %s-%s' % (phone[:2], phone[2:7], phone[7:11])

    return phone

#
#  Adress formatters
#


def raw_postal_code(postal_code):
    return re.sub("[^0-9]", '', postal_code)


def format_postal_code(postal_code):
    from stoqlib.lib.validators import validate_postal_code
    if not validate_postal_code(postal_code):
        return postal_code
    postal_code = raw_postal_code(postal_code)
    return "%s-%s" % (postal_code[:5],
                      postal_code[5:8])
