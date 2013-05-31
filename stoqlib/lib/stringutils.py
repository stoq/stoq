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


def next_value_for(value):
    """Generate the next value for value.

    For instance 4 -> 5, 99 -> 100, A83 -> A84 etc::

      >>> next_value_for(u'999')
      u'1000'
      >>> next_value_for(u'1')
      u'2'

    :param unicode value:
    :returns:
    :rtype: unicode
    """
    if not value:
        value = u'1'
    elif value.isdigit():
        value = unicode(int(value) + 1)
    elif value.isalnum() and value[-1].isdigit():
        l = u''
        for c in reversed(value):
            if not c.isdigit():
                break
            l = c + l
        value = value[:-len(l)] + unicode(int(l) + 1)
    else:
        # FIXME: We can do a lot better here, by getting the next
        #        character for instance.
        value += u'1'
    return value
