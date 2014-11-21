# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
##
## Copyright (C) 2012-2013 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

from kiwi.environ import environ
import xlwt

from stoqlib.lib.translation import stoqlib_gettext as _

# Styles
# Some commonly used styles.

STYLE_WHITE = "font: color white;"
STYLE_BOLD = "font: bold true;"
STYLE_THICK_BORDERS = "borders: left thick, right thick, top thick, bottom thick;"


def get_style_color(color):
    return "pattern: pattern solid, fore_color %s;" % (color, )


def write_app_hyperlink(sheet, row):
    url = u"http://www.stoq.com.br/"
    formula = xlwt.Formula(u'HYPERLINK("%s";"%s - %s")' % (
        url, _(u"Stoq Retail Management"), url))

    style = xlwt.easyxf(
        "font: height 250;"
        "alignment: vertical center, horizontal center;")
    sheet.write_merge(r1=row, r2=row,
                      c1=0, c2=15,
                      label=formula, style=style)
    sheet.row(row).height = 1000


def write_app_logo(sheet):
    filename = environ.get_resource_filename('stoq', 'pixmaps', 'stoq_logo.bmp')
    sheet.insert_bitmap(filename, 0, 0,
                        x=2, y=2, scale_x=0.75, scale_y=0.25)


def get_number_format():
    return '#,##0.00'


def get_date_format():
    # Translators: This is the default date format in excel
    # columns, see the xlwt python library for more information
    return _('YY-MMM-D')
