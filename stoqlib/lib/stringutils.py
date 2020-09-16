# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU Lesser General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
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
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

"""Utilities for manipulating strings"""

import unicodedata


def _increment(value):
    # Make sure the new value is at least the same size the old one was.
    # For example, this will make '009' become '010' instead of just '10'
    return str(int(value) + 1).zfill(len(value))


def next_value_for(value):
    """Generate the next value for value.

    For instance 4 -> 5, 99 -> 100, A83 -> A84 etc::

      >>> next_value_for('999')
      '1000'
      >>> next_value_for('1')
      '2'
      >>> next_value_for('abc')
      'abd'
      >>> next_value_for('XYZ')
      'XZ0'
      >>> next_value_for('AB00099')
      'AB00100'

    :param unicode value:
    :returns:
    :rtype: unicode
    """
    if not value:
        return '1'
    if value.isdigit():
        return _increment(value)

    last = value[-1]
    if last.isdigit():
        l = ''
        # Get the greatest part in the string's end that is a number.
        # For instance: 'ABC123' will get '123'
        for c in reversed(value):
            if not c.isdigit():
                break
            l = c + l
        value = value[:-len(l)] + _increment(l)
    elif last.isalpha():
        last = chr(ord(last) + 1)
        if last.isalpha():
            value = value[:-1] + last
        else:
            value_len = len(value)
            value = next_value_for(value[:-1])
            # If the next_value_for didn't increased the string length, we
            # need to. For instance: 'ABZ' would make the line above return
            # 'AC' and thus the next value for the sequence is 'AC0'. It should
            # be fine for '99Z' because it would generate '100'
            if len(value) <= value_len:
                value += '0'
    else:
        value += '0'

    return value


def max_value_for(values):
    """Get the maximum value from the values

    Python compares strings from left to right and thus comparisons
    like '9' > '10' would be true.

    This avoid that problem by 0-"padding" the strings to the same length
    of the longest string on the sequence. Because of that, the return value
    will be in that format. For instance::

        >>> max_value_for(['1', '2'])
        '2'
        >>> max_value_for(['99', '100'])
        '100'
        >>> max_value_for(['99', '0001'])
        '0099'

    :param values: a sequence of strings
    :returns: the greatest string on the sequence
    """
    max_length = max(len(v) for v in values)
    return max(v.zfill(max_length) for v in values)


def strip_accents(string):
    """Remove the accentuantion of a string
    Taken from http://www.python.org.br/wiki/RemovedorDeAcentos

    :param string: a string, either in str or unicode format
    :returns: the string without accentuantion
    """

    string = unicodedata.normalize('NFKD', string)
    return string.encode('ASCII', 'ignore').decode()
