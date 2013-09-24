# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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

import xlwt
import xlwt.Utils

from stoqlib.api import api
from stoqlib.domain.account import Account
from stoqlib.lib.dateutils import (get_month_intervals_for_year,
                                   get_month_names)
from stoqlib.lib.parameters import sysparam
from stoqlib.exporters.xlsutils import (STYLE_BOLD,
                                        STYLE_THICK_BORDERS,
                                        STYLE_WHITE,
                                        get_number_format,
                                        get_style_color,
                                        write_app_hyperlink,
                                        write_app_logo)
from stoqlib.lib.message import warning
from stoqlib.lib.translation import stoqlib_gettext as _


HEADER_TOP_STYLE = xlwt.easyxf(
    STYLE_WHITE + get_style_color("gray80") +
    "borders: left thick, right thick, bottom thick;" +
    "alignment: horizontal right;")
HEADER_LEFT_STYLE = xlwt.easyxf(
    STYLE_WHITE + get_style_color("gray80") +
    "borders: right thick, top thick, bottom thick;")
AVERAGE_STYLE = xlwt.easyxf(
    STYLE_BOLD + STYLE_THICK_BORDERS + get_style_color("light_turquoise"),
    num_format_str=get_number_format())
SUM_STYLE = xlwt.easyxf(
    STYLE_BOLD + STYLE_THICK_BORDERS + get_style_color("pale_blue"),
    num_format_str=get_number_format())
NUMBER_STYLE = xlwt.easyxf(
    STYLE_THICK_BORDERS,
    num_format_str=get_number_format())


class FinancialIntervalReport(object):
    def __init__(self, store, year):
        self.exporter = None
        self.store = store
        self.year = year

    def _prepare_items(self, items, account, start, end):
        total = account.get_total_for_interval(start, end)
        items.append((account.description, total))

        for child in Account.get_children_for(self.store, parent=account):
            self._prepare_items(items, child, start, end)

    def get_data(self):
        sheets = {}
        for account in Account.get_children_for(self.store, parent=None):
            if sysparam.compare_object('IMBALANCE_ACCOUNT', account):
                continue

            columns = []
            for start, end in get_month_intervals_for_year(self.year):
                column = []
                self._prepare_items(column, account, start, end)
                columns.append(column)

            # Skip empty sheets
            if sum(item[1] for c in columns for item in c) == 0:
                continue

            sheets[account.description] = columns

        return sheets

    def run(self):
        data = self.get_data()
        if not data:
            warning(_("Cannot generate report, create some transactions first"))
            return False
        self.exporter = XLSFinancialExporter(data)
        self.exporter.process()
        return True

    def write(self, temporary):
        self.exporter.write(temporary)


class XLSFinancialExporter(object):
    def __init__(self, data):
        self.data = data

    def process(self):
        self._wb = xlwt.Workbook(encoding='utf8')
        summary_sheet = self._wb.add_sheet(_(u"Summary"))

        # sheet name -> [jan sum, feb sum, ..., dec sum]
        sheets = {}

        for account_name in sorted(self.data):
            columns = self.data[account_name]
            n_columns = len(columns)
            n_rows = len(columns[0])

            sheet = self._wb.add_sheet(account_name)
            self._write_logo(sheet, n_rows + 4)
            self._write_headers(sheet, n_columns)
            self._write_formulas(sheet, n_rows, n_columns)
            names = [item[0] for item in columns[0]]
            self._write_account_cells(sheet, names)

            sum_cells = []
            for x, items in enumerate(columns):
                for y, item in enumerate(items):
                    sheet.write(2 + y, 1 + x, item[1], NUMBER_STYLE)
                sum_cells.append((n_rows + 3, 1 + x))

            sheets[account_name] = sum_cells

        self._write_summary_sheet(summary_sheet, sheets)

    def _write_summary_sheet(self, sheet, sheets):
        n_rows = len(sheets)
        n_columns = max(map(len, sheets.values()))

        self._write_logo(sheet, n_rows + 4)
        self._write_headers(sheet, n_columns)
        self._write_formulas(sheet, n_rows, n_columns)

        # Write out account names as link to the other pages
        sheet_names = sorted(sheets)
        sheet_cells = [
            xlwt.Formula('HYPERLINK("#\'%s\'!%s", "%s")' % (
                         name, 'B3', name)) for name in sheet_names]
        self._write_account_cells(sheet, sheet_cells)

        for y, sheet_name in enumerate(sheet_names):
            columns = sheets[sheet_name]
            for x, col in enumerate(columns):
                ref_x, ref_y = col
                formula = "'%s'!%s" % (
                    sheet_name,
                    xlwt.Utils.rowcol_to_cell(ref_x, ref_y))
                if x == n_columns + 1:
                    style = SUM_STYLE
                elif x == n_columns:
                    style = AVERAGE_STYLE
                else:
                    style = NUMBER_STYLE
                sheet.write(y + 2, 1 + x, xlwt.Formula(formula), style)

    def _write_logo(self, sheet, end_x):
        write_app_logo(sheet)
        write_app_hyperlink(sheet, 0)
        write_app_hyperlink(sheet, end_x)

    def _write_headers(self, sheet, n_columns):
        for x in range(n_columns):
            month_name = get_month_names()[x]
            sheet.write(1, 1 + x, month_name, HEADER_TOP_STYLE)

        sheet.write(1, n_columns + 1, _(u'Average'), HEADER_TOP_STYLE)
        sheet.write(1, n_columns + 2, _(u'Total'), HEADER_TOP_STYLE)

    def _write_formulas(self, sheet, n_rows, n_columns):
        first_data_row = 1
        last_data_row = n_rows + 1
        first_data_col = 1
        last_data_col = n_columns

        # For each column
        for x in range(n_columns):
            # Monthly average
            formula = 'AVERAGE(%s:%s)' % (
                xlwt.Utils.rowcol_to_cell(first_data_row, 1 + x),
                xlwt.Utils.rowcol_to_cell(last_data_row, 1 + x))
            sheet.write(n_rows + 2, 1 + x,
                        xlwt.Formula(formula), AVERAGE_STYLE)

            # Monthly total
            formula = 'SUM(%s:%s)' % (
                xlwt.Utils.rowcol_to_cell(first_data_row, 1 + x),
                xlwt.Utils.rowcol_to_cell(last_data_row, 1 + x))
            sheet.write(n_rows + 3, 1 + x,
                        xlwt.Formula(formula), SUM_STYLE)

        # For each row
        for y in range(n_rows):
            # Write out average
            formula = 'Average(%s:%s)' % (
                xlwt.Utils.rowcol_to_cell(2 + y, first_data_col),
                xlwt.Utils.rowcol_to_cell(2 + y, last_data_col))
            sheet.write(2 + y, n_columns + 1,
                        xlwt.Formula(formula), AVERAGE_STYLE)

            # Write out total
            formula = 'SUM(%s:%s)' % (
                xlwt.Utils.rowcol_to_cell(2 + y, first_data_col),
                xlwt.Utils.rowcol_to_cell(2 + y, last_data_col))
            sheet.write(2 + y, n_columns + 2,
                        xlwt.Formula(formula), SUM_STYLE)

        # Bottom, right: monthly total
        formula = 'SUM(%s:%s)' % (
            xlwt.Utils.rowcol_to_cell(first_data_row, n_columns + 1),
            xlwt.Utils.rowcol_to_cell(last_data_row, n_columns + 1))
        sheet.write(n_rows + 3, n_columns + 1,
                    xlwt.Formula(formula), SUM_STYLE)

        # Bottom, rightmost: yearly total
        formula = 'SUM(%s:%s)' % (
            xlwt.Utils.rowcol_to_cell(first_data_row, n_columns + 2),
            xlwt.Utils.rowcol_to_cell(last_data_row, n_columns + 2))
        sheet.write(n_rows + 3, n_columns + 2,
                    xlwt.Formula(formula), SUM_STYLE)

    def _write_account_cells(self, sheet, cells):
        for y, cell in enumerate(cells):
            sheet.write(2 + y, 0, cell, HEADER_LEFT_STYLE)

        n_rows = len(cells)
        sheet.write(n_rows + 2, 0, _(u'Average'), HEADER_LEFT_STYLE)
        sheet.write(n_rows + 3, 0, _(u'Total'), HEADER_LEFT_STYLE)

    def write(self, temporary):
        self._wb.save(temporary.name)


if __name__ == '__main__':
    import os
    import tempfile
    ec = api.prepare_test()
    store_ = api.get_default_store()
    fir = FinancialIntervalReport(store_, year=2012)
    with tempfile.NamedTemporaryFile(suffix='.xls', delete=False) as temporary_:
        if fir.run():
            fir.write(temporary_)
        os.system("soffice %s" % (temporary_.name, ))
