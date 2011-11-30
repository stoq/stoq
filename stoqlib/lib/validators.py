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

from decimal import Decimal
import datetime
import posixpath
import re

from kiwi.datatypes import converter, ValidationError

from stoqlib.lib.formatters import raw_phone_number, raw_postal_code
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

POSTAL_CODE_CHAR_LEN = 8

#
# Date validatores
#


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

#
# Phone number validators
#


def validate_phone_number(phone_number):
    phone_number = raw_phone_number(phone_number)
    digits = len(phone_number)
    if digits == 11:
        return phone_number[:1] == '0'
    return digits in range(7, 11)

#
# Adress validators
#


def validate_postal_code(postal_code):
    if not postal_code:
        return False
    return len(raw_postal_code(postal_code)) == POSTAL_CODE_CHAR_LEN


def validate_area_code(code):
    """Validates Brazilian area codes"""
    if isinstance(code, basestring):
        try:
            code = converter.from_string(int, code)
        except ValidationError:
            return False

    # Valid brazilian codes are on the range of 10-99
    return 10 <= code <= 99


def validate_state(state):
    state_code = ("RO", "AC", "AM", "RR", "PA", "AP", "TO", "MA", "PI",
                  "CE", "RN", "PB", "PE", "AL", "SE", "BA", "MG", "ES",
                  "RJ", "SP", "PR", "SC", "RS", "MS", "MT", "GO", "DF")
    if state.upper() in state_code:
        return True
    return False

#
# Document Validators
#


def validate_cpf(cpf):
    cpf = ''.join(re.findall('\d', str(cpf)))

    if not cpf or len(cpf) < 11:
        return False

    # With the first 9 digits, we calculate the last two digits (verifiers)
    new = map(int, cpf)[:9]

    while len(new) < 11:
        s = sum([(len(new) + 1 - i) * v for i, v in enumerate(new)]) % 11

        if s > 1:
            verifier_digit = 11 - s
        else:
            verifier_digit = 0

        if cpf[len(new)] != str(verifier_digit):
            return False
        else:
            new.append(verifier_digit)

    return True


def validate_cnpj(cnpj):
    """Validates a cnpj.

    @param cnpj: the cnpj to validate. Can be a string or number. If its a
    string, only the digits will be used.
    """
    cnpj = ''.join(re.findall('\d', str(cnpj)))

    if not cnpj or len(cnpj) < 14:
        return False

    # With the first 12 digts, we calculate the last 2 digits (verifiers)
    new = map(int, cnpj)[:12]

    verification_base = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

    while len(new) < 14:
        s = sum([x * y for (x, y) in zip(new, verification_base)]) % 11

        if s > 1:
            verifier_digit = 11 - s
        else:
            verifier_digit = 0

        if cnpj[len(new)] != str(verifier_digit):
            return False
        else:
            new.append(verifier_digit)
            verification_base.insert(0, 6)

    return True


def validate_cfop(cfop):
    """Validates C.F.O.P. code

    Valid C.F.O.P. format: '9.999', where 9 is any digit in 0-9.
    """
    if not isinstance(cfop, basestring):
        return False

    if not '.' in cfop:
        return False

    first_part, last_part = cfop.split('.')
    if not first_part.isdigit() or not last_part.isdigit():
        return False
    if not len(first_part) == 1 or not len(last_part) == 3:
        return False

    return True

#
# Misc validators
#


def _validate_type(type_, value):
    if isinstance(value, basestring):
        try:
            # Just converting to see if any errors are raised.
            converter.from_string(type_, value)
        except ValidationError:
            return False
    else:
        if not isinstance(value, type_):
            return False

    return True


def validate_int(value):
    """Validates an integer.

    Returns if the value is a valid integer, or, in case it's a string,
    if it can be converted to an integer.
    """
    return _validate_type(int, value)


def validate_decimal(value):
    """Validates an Decimal.

    Returns if the value is a valid Decimal, or, in case it's a string,
    if it can be converted to an Decimal.
    """
    return _validate_type(Decimal, value)


def validate_directory(path):
    """Find out if a directory exists"""
    return posixpath.exists(posixpath.expanduser(path))


def validate_percentage(value):
    """Se if a given value is a valid percentage.

    Works for int, float, Decimal and basestring (if it
    can be converted to Decimal).
    """
    if isinstance(value, basestring):
        try:
            value = converter.from_string(Decimal, value)
        except ValidationError:
            return False

    return 0 <= value <= 100


def validate_email(value):
    """Try to validate an email address.
    """
    exp = "^[^@]+@[a-zA-Z0-9][\w\.-]*[a-zA-Z0-9]\.[a-zA-Z][a-zA-Z\.]*[a-zA-Z]$"
    return re.match(exp, value) is not None
