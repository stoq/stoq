# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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
## Author(s) : Raja Sooriamurthi    <raja@cs.indiana.edu>
##             Stoq Team <stoq-devel@async.com.br>
##
## NOTE: This a modified version of cardinals.py from:
## http://mail.python.org/pipermail/python-list/2000-October/643196.html
##
##


def to_words(num, unit_names=None):
    """
    Returns the integer as a cardinal number
    :param num: the integer
    :type: int
    :param unit_names: a list of unit names
    :type: list
    """

    if isinstance(num, float):
        raise TypeError("Float numbers are not supported")
    if not isinstance(num, int):
        raise TypeError("Value must be an integer")
    if num > 10 ** 66:
        raise ValueError("Value must be lesser than 10^66")
    if num > 1 and unit_names:
        return cardinal(num) + " " + unit_names[1]
    elif unit_names:
        return cardinal(num) + " " + unit_names[0]
    return cardinal(num)


def to_words_as_money(num, currency_names):
    """Returns a amount as a cardinal number
    :param num: the amount
    :type: int or float
    :param currency_names: a list of currency names
    Example:
    currency_names = ['dollar', 'dollars', 'cent', 'cents']
    :type: list
    """

    ints = int(num)
    decimals = num - int(num)

    intret = cardinal(ints)

    decret = ""
    if decimals:
        decstr = "%.02f" % decimals
        decstr = decstr.split(".")[1]
        decret = cardinal(int(decstr))

        # singular
        if decret == "one":
            decret = decret + " " + currency_names[2]
        # plural
        else:
            decret = decret + " " + currency_names[3]

        if intret != "zero":
            decret = " and " + decret

    # only cents
    if intret == "zero" and decret:
        return decret
    # singular
    elif intret == "zero" or intret == "one":
        return intret + " " + currency_names[0] + decret
    # plural
    else:
        return intret + " " + currency_names[1] + decret

#
# The dicts holds the string for conversion
#

nnames = {0: '',
          1: 'one',
          2: 'two',
          3: 'three',
          4: 'four',
          5: 'five',
          6: 'six',
          7: 'seven',
          8: 'eight',
          9: 'nine',
          10: 'ten',
          11: 'eleven',
          12: 'twelve',
          13: 'thirteen',
          14: 'fourteen',
          15: 'fifteen',
          16: 'sixteen',
          17: 'seventeen',
          18: 'eighteen',
          19: 'nineteen',
          20: 'twenty',
          30: 'thirty',
          40: 'forty',
          50: 'fifty',
          60: 'sixty',
          70: 'seventy',
          80: 'eighty',
          90: 'ninety',
          }

# these names obtained from CMUCL and Allegro CL's ~r format directive
# this is pretty much centered towards American terminology
# but can be easily modified for British terminology
# e.g., billion = 10^12 etc

illions = {0: '',
           3: 'thousand',
           6: 'million',
           9: 'billion',
           12: 'trillion',
           15: 'quadrillion',
           18: 'quintillion',
           21: 'sextillion',
           24: 'septillion',
           27: 'octillion',
           30: 'nonillion',
           33: 'decillion',
           36: 'undecillion',
           39: 'duodecillion',
           42: 'tredecillion',
           45: 'quattuordecillion',
           48: 'quindecillion',
           51: 'sexdecillion',
           54: 'septendecillion',
           57: 'octodecillion',
           60: 'novemdecillion',
           63: 'vigintillion',
           }

MAX_POWER = 63

# Don't know what 10^66 onwards is
# Hence if you to print a number >= 10^{63 + 3} an exception is raised
# in other wards the largest number that can be handled currently is
# cardinal (10L**66 - 1)
# Raja 10/09/2000

#
# the main function
#


def cardinal(n):
    """Returns the cardinal number of input n
    """

    if n == 0:
        return "zero"
    if n < 0:
        n = -n
        return "negative " + aux(n)
    return aux(n)

#
# aux: the work horse
#


def aux(n, power=0):
    out = ""
    if n == 0:
        return out

    q, r = divmod(n, 1000)
    out += aux(q, power + 3)
    if r > 0:
        out += p_100s(r)
        if power > 0:
            if power <= MAX_POWER:
                out = out.strip()
                out += " " + illions[power]
            else:
                raise ArithmeticError(
                    "don't know the word for 10^%s" % power)
    return out.strip()

#
# p_100s: handles 3-digit chunks
#


def p_100s(n):
    "print a cardinal description of a number < 1000"

    if n < 0 or n >= 1000:
        raise ValueError("%s does not lie in the range [0..99]" % n)

    out = ""
    if n == 0:
        return out

    h, t = divmod(n, 100)
    if h > 0:
        out += " %s hundred" % nnames[h]
    if t < 20:
        out += " " + nnames[t]
    elif t % 10 != 0:
        # there is a units digit
        # print something like 'thirty-four'
        out += " %s-%s" % (nnames[t / 10 * 10], nnames[t % 10])
    else:
        out += " %s" % nnames[t / 10 * 10]
    return out
