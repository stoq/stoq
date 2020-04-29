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

from stoqlib.l10n.l10n import get_l10n_field
from stoqlib.lib.cardinals.cardinals import get_cardinal_function
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.defaults import DECIMAL_PRECISION, QUANTITY_PRECISION

_ = stoqlib_gettext


#
#  Quantity/Percentage formatters
#


def format_quantity(quantity):
    if (quantity * 100 % 100) == 0:
        return '%.0f' % quantity
    return '%.*f' % (QUANTITY_PRECISION, quantity)


def get_formatted_percentage(value):
    return "%.*f %%" % (DECIMAL_PRECISION, value)


#
#  Price formatters
#


def get_price_format_str():
    return '%%.%sf' % DECIMAL_PRECISION


def get_price_as_cardinal(value):
    function = get_cardinal_function('to_words_as_money')
    currency_names = get_l10n_field('currency_names')
    return function(value, currency_names)


def get_formatted_price(float_value, symbol=True, precision=DECIMAL_PRECISION):
    return format_price(float_value, symbol=symbol,
                        precision=precision)


def get_formatted_cost(float_value, symbol=True):
    from stoqlib.lib.parameters import sysparam
    precision = sysparam.get_int('COST_PRECISION_DIGITS')
    return get_formatted_price(float_value, symbol=symbol,
                               precision=precision)


#
#  Date formatters
#


def get_full_date(date):
    """Return a date in it's full format taking l10n in consideration

    For example, for Brazil, it will return something like:
      01 de janeiro de 2012
    In the generic case, it will return something like:
      January 01, 2012

    """
    full_date_format = get_l10n_field("full_date_format")
    return date.strftime(full_date_format)


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
        # This is for the new mobile numbers with 9 digits
        return '%s-%s' % (phone[:5], phone[5:9])
    elif digits == 10:
        # 0[3589]00 XXX-XXX
        if phone[:4] in ['0300', '0500', '0800', '0900']:
            return '%s %s-%s' % (phone[:4], phone[4:7],
                                 phone[7:])
        return '(%s) %s-%s' % (phone[:2], phone[2:6], phone[6:10])
    elif digits == 11:
        # 0[3589]00 XXX-XXX
        if phone[:4] in ['0300', '0500', '0800', '0900']:
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


def format_address(address, include_district=True):
    """Format the given address to a string.

    This expects an |address|, but any object containing the following
    attributes would suffice: `street`, `streetnumber`, `district` and `complement`
    """
    if include_district:
        district = address.district
    else:
        district = None

    if address.street and district and address.complement:
        number = address.streetnumber or _(u'N/A')
        return u'%s %s, %s, %s' % (address.street, number, address.complement, district)
    elif address.street and district:
        number = address.streetnumber or _(u'N/A')
        return u'%s %s, %s' % (address.street, number, district)
    elif address.street and address.streetnumber and address.complement:
        return u'%s %s, %s' % (address.street, address.streetnumber, address.complement)
    elif address.street and address.streetnumber:
        return u'%s %s' % (address.street, address.streetnumber)
    elif address.street:
        return address.street
    else:
        return u''


#
#  Sellable formatters
#


def format_sellable_description(sellable, batch=None):
    """Gets the formatted description for *sellable*

    If batch is ``None``, the description will be the same as
    *sellable.get_description()*. But if is given, it's number will
    be appended to the description, like::

        Normal description:

            "Cellphone"

        With batch information:

            "Cellphone [Batch: 123456]"

    """
    description = sellable.get_description()
    if batch is None:
        return description

    return u'%s [%s: %s]' % (description, _("Batch"), batch.batch_number)


#
#  Document formatters
#


def raw_document(document):
    return ''.join(c for c in document if c.isdigit())


def format_cpf(document):
    return '%s.%s.%s-%s' % (document[0:3], document[3:6], document[6:9],
                            document[9:11])


def format_cnpj(document):
    return '%s.%s.%s/%s-%s' % (document[0:2], document[2:5], document[5:8],
                               document[8:12], document[12:])


def format_document(document):
    if len(document) == 11:
        return format_cpf(document)
    elif len(document) == 14:
        return format_cnpj(document)
    else:
        raise ValueError('Document format not valid')


class TextTable(object):
    """Formats a textual table with columns

    Sample usage:

    >>> table = TextTable(28, ('A', 'B', 'Column'))
    >>> table.append((u'Desc', 1234, 'asd'))
    >>> table.append((u'Really Long Desc', 1, 'qwe'))
    >>> print(str(table))
    A                  B  Column
    ----------------------------
    Desc            1234     asd
    Really Long...     1     qwe
    ----------------------------

    """

    def __init__(self, width, titles=None, expand_col=0, separators=True,
                 format_func=None):
        self._expand_col = expand_col
        self._width = width
        self._titles = titles
        self._items = []
        self._separators = separators
        self._format_func = format_func
        self._sizes = []
        if titles:
            self._sizes = [len(str(i)) for i in self._titles]

    def append(self, item):
        self._items.append(item)
        if not self._sizes:
            self._sizes = [0] * len(item)

        for i, value in enumerate(item):
            self._sizes[i] = max(self._sizes[i], len(str(value)))

    def _organize(self, item):
        column_separator = '  '
        # space required by all columns that don't expand
        fixed_size = sum([size for (index, size) in enumerate(self._sizes)
                          if index != self._expand_col])
        fixed_size += (len(self._sizes) - 1) * len(column_separator)

        parts = []
        for i, value in enumerate(item):
            if i == self._expand_col:
                # This column adjusts it self to the avaiable space
                if len(value) > self._width - fixed_size:
                    parts.append(value[:self._width - fixed_size - 3] + '...')
                else:
                    parts.append(value.ljust(self._width - fixed_size))
            else:
                parts.append(str(value).rjust(self._sizes[i]))

        if self._format_func:
            parts = self._format_func(parts)
        return column_separator.join(parts)

    def __str__(self):
        lines = []
        if self._titles:
            lines.append(self._organize(self._titles))
        if self._separators:
            lines.append('-' * self._width)
        for item in self._items:
            lines.append(self._organize(item))
        if self._separators:
            lines.append('-' * self._width)
        return u'\n'.join(lines)
