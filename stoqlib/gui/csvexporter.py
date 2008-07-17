# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008 Async Open Source <http://www.async.com.br>
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
##  Author:     George Y. Kussumoto     <george@async.com.br>
##
"""CSV Exporter Utilities"""

from kiwi.ui.objectlist import Column, ObjectList


def objectlist2csv(objectlist, encoding):
    """Convert a instance of L{kiwi.ui.objectlist.ObjectList} to a CSV format.
    The column's title will be used as the field header and the colmns which
    is not displayed will also not be included in the CSV representation.

    @param objectlist: an L{kiwi.ui.objectlist.ObjectList} instance.
    @param encoding: the encode we should use when return the CSV content.
    @returns: a string containing the the CSV representation of the
              L{kiwi.ui.objectlist.ObjectList} instance.
    """
    if not isinstance(objectlist, ObjectList):
        raise TypeError("ObjectList instance required, got '%s' instead." %
                        objectlist.__class__.__name__)

    attributes = []
    title = ''
    for column in objectlist.get_treeview().get_columns():
        if not column.get_visible():
            continue

        header_widget = column.get_widget()
        if header_widget:
            title += header_widget.get_text() + ','
            attributes.append(column.attribute)

    # the header must be the first line of the CSV
    csv_lines = [title]

    for item in objectlist:
        csv_line = ','.join(
            [str(Column.get_attribute(item, attr, '')) for attr in attributes])
        csv_line = csv_line.replace('None', '')
        csv_line += ','
        csv_lines.append(csv_line.encode(encoding, 'replace'))

    return '\n'.join(csv_lines)
