# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012-2013 Async Open Source <http://www.async.com.br>
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
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
"""XLS exporter"""

import datetime
import tempfile

from kiwi.currency import currency
import xlwt

from stoqlib.exporters.xlsutils import (get_date_format,
                                        get_number_format,
                                        write_app_hyperlink,
                                        write_app_logo)
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class XLSExporter(object):
    def __init__(self, name=None):
        self._current_column = 1
        self._n_columns = -1
        self._column_styles = None
        self._headers = None

        self._wb = xlwt.Workbook(encoding='utf8')
        if not name:
            name = _('Stoq sheet')
        self._ws = self._wb.add_sheet(name)

        self._setup()

    #
    # Private
    #

    def _setup(self):
        self._header_font = xlwt.Font()
        self._header_font.bold = True

        self._header_style = xlwt.XFStyle()
        self._header_style.font = self._header_font

        self._style_date = xlwt.XFStyle()
        self._style_date.num_format_str = get_date_format()

        self._style_general = xlwt.XFStyle()
        self._style_general.num_format_str = 'general'

        self._style_number = xlwt.XFStyle()
        self._style_number.num_format_str = get_number_format()

    def _add_row(self, columns, style=None):
        if len(columns) - 1 > self._n_columns:
            raise ValueError(columns, self._n_columns)
        for i, column in enumerate(columns):
            self._write_one(i, column, style=style)
        self._current_column += 1

    def _write_one(self, i, data, style=None):
        if style is None:
            style = self._column_styles[i]

        if data is None:
            data = ''
        else:
            if isinstance(data, datetime.date):
                data = data.strftime('%Y-%m-%d')
            elif isinstance(data, str):
                data = unicode(data, 'utf-8')

        self._ws.write(self._current_column, i, data, style)

    #
    # Public API
    #

    def set_column_headers(self, headers):
        self._headers = headers

    def set_column_types(self, column_types):
        css = []
        for i, column_type in enumerate(column_types):
            if column_type in (datetime.datetime, datetime.date):
                style = self._style_date
            elif column_type in [int, long, float, currency]:
                style = self._style_number
            else:
                style = self._style_general
            css.append(style)

        self._column_styles = css
        self._n_columns = len(column_types)

    def add_cells(self, cells):
        write_app_logo(self._ws)
        write_app_hyperlink(self._ws, 0)

        if self._headers:
            self._add_row(self._headers, style=self._header_style)

        for y, line in enumerate(cells):
            self._add_row(line)

    def save(self, prefix=''):
        if prefix:
            prefix = 'Stoq-%s-' % (prefix, )
        else:
            prefix = 'Stoq-'

        temporary = tempfile.NamedTemporaryFile(
            prefix=prefix,
            suffix='.xls', delete=False)
        self._wb.save(temporary.name)

        return temporary

    def add_from_object_list(self, objectlist, data=None):
        columns = objectlist.get_visible_columns()
        self.set_column_types([
            c.data_type for c in columns])
        self.set_column_headers([
            getattr(c, 'long_title', None) or c.title for c in columns])
        self.add_cells(objectlist.get_cell_contents(data))
