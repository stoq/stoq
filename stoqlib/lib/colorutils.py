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

"""Utilities for working with colors"""

import random


_TANGO_PALETTE = set([
    u'#eeeeec',
    u'#d3d7cf',
    u'#babdb6',
    u'#fce94f',
    u'#edd400',
    u'#c4a000',
    u'#8ae234',
    u'#73d216',
    u'#4e9a06',
    u'#fcaf3e',
    u'#f57900',
    u'#ce5c00',
    u'#e9b96e',
    u'#c17d11',
    u'#8f5902',
    u'#729fcf',
    u'#3465a4',
    u'#204a87',
    u'#ad7fa8',
    u'#75507b',
    u'#5c3566',
    u'#888a85',
    u'#555753',
    u'#2e3436',
    u'#ef2929',
    u'#cc0000',
    u'#a40000',
])


def get_random_color(ignore=None):
    """Returns a random color from tango palette

    :param set ignore: a set of colors to be ignored
    :returns unicode: a random color, in hex format (e.g. u'#eeeeec')
    """
    colors = _TANGO_PALETTE.copy()
    if ignore:
        colors -= ignore

    try:
        return random.choice(list(colors))
    except IndexError:
        # Happens if all items are in ignore set. In this case,
        # returns a random color from _TANGO_PALETTE
        return random.choice(list(_TANGO_PALETTE))
