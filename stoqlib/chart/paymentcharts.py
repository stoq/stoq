# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011 Async Open Source <http://www.async.com.br>
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
""" Payment charts """

import datetime
import string

from stoqlib.chart.chart import Chart
from stoqlib.database.runtime import get_connection
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class YearlyPaymentsChart(Chart):
    name = _("Monthly payments")

    description = _("Total revenue, expenses and profit for all years")

    in_payments_query = """
 SELECT extract(year FROM paid_date),
        SUM(paid_value)
   FROM payment, payment_adapt_to_in_payment
  WHERE payment.id = payment_adapt_to_in_payment.original_id
 GROUP BY extract(year FROM paid_date)
 ORDER BY extract(year FROM paid_date);"""

    out_payments_query = """
 SELECT extract(year FROM paid_date),
        SUM(paid_value)
   FROM payment, payment_adapt_to_out_payment
  WHERE payment.id = payment_adapt_to_out_payment.original_id
 GROUP BY extract(year FROM paid_date)
 ORDER BY extract(year FROM paid_date);"""

    def run(self):
        """
        @returns: (year, total in payments, total out payments, profit)
        """

        years = {}
        for year, total_in in self.execute(self.in_payments_query):
            if not year:
                continue
            if not year in years:
                years[year] = {}
            years[year]['in'] = total_in or 0

        for year, total_out in self.execute(self.out_payments_query):
            if not year:
                continue
            if not year in years:
                years[year] = {}
            years[year]['out'] = total_out or 0

        data = dict(revenue=[],
                    expense=[],
                    profit=[],
                    dates=[])
        for year, values in years.items():
            total_in = values.get('in', 0)
            total_out = values.get('out', 0)
            data['revenue'].append(float(total_in))
            data['expense'].append(float(total_out))
            data['profit'].apppend(float(total_in - total_out))
            data['date'] = year
            yield data


class MonthlyPaymentsChart(Chart):
    name = _("Monthly payments")
    description = _("Total revenue, expenses and profit for all months in a year")

    in_payments_query = """
SELECT $date_columns,
        SUM(paid_value)
   FROM payment, payment_adapt_to_in_payment
  WHERE payment.id = payment_adapt_to_in_payment.original_id AND
        $year_query
 GROUP BY $date_columns
 ORDER BY $date_columns
"""

    out_payments_query = """
SELECT $date_columns,
        SUM(paid_value)
   FROM payment, payment_adapt_to_out_payment
  WHERE payment.id = payment_adapt_to_out_payment.original_id AND
        $year_query
 GROUP BY $date_columns
 ORDER BY $date_columns
"""

    def run(self):
        if 'year' in self.args:
            year_query = "extract(year FROM paid_date) = %s" % (
                self.conn.sqlrepr(self.args['year']))
        elif 'last' in self.args:
            year_query = "(NOW() - paid_date)::INTERVAL < %s::INTERVAL" % (
                self.conn.sqlrepr(self.args['last']))
        else:
            raise TypeError("missing argument: year/last")

        date_columns = "extract(year FROM paid_date)||'-'||lpad(extract(month FROM paid_date)::char, 2, '0')"
        months = {}
        tmpl = string.Template(self.in_payments_query).substitute(
            dict(date_columns=date_columns,
                 year_query=year_query))
        res = self.execute(tmpl)
        for date, total_in in res:
            year, month = map(int, date.split('-'))
            months.setdefault((year, month), {})['in'] = total_in or 0

        tmpl = string.Template(self.out_payments_query).substitute(
            dict(date_columns=date_columns,
                 year_query=year_query))
        res = self.execute(tmpl)
        for date, total_out in res:
            year, month = map(int, date.split('-'))
            months.setdefault((year, month), {})['out'] = total_out or 0

        data = []
        revenue = []
        expense = []
        profit = []

        keys = sorted(months)
        for key in keys:
            values = months[key]
            year, month = key
            total_in = values.get('in', 0)
            total_out = values.get('out', 0)
            unixtime = datetime.date(year, month, 1).strftime('%s')
            revenue.append([float(unixtime) * 1000, float(total_in)])
            expense.append([float(unixtime) * 1000, -float(total_out)])
            profit.append([float(unixtime) * 1000, float(total_in - total_out)])
        data.append(dict(label=_("Revenue"), data=revenue))
        data.append(dict(label=_("Expense"), data=expense))
        data.append(dict(label=_("Profit"), data=profit))
        return data


def daily_payments(year, month):
    """
    @year: year to show payments for
    @month: month to show payments for
    @returns: (month, total in payments, total out payments, profit)
    """
    conn = get_connection()

    if 2100 > year < 1900:
        raise ValueError(year)
    if 12 > month < 1:
        raise ValueError(month)

    daily_in_payments = """
  SELECT extract(day FROM paid_date),
         SUM(paid_value)
    FROM payment, payment_adapt_to_in_payment
   WHERE payment.id = payment_adapt_to_in_payment.original_id AND
         extract(month FROM paid_date) = $month AND
         extract(year FROM paid_date) = $year
GROUP BY extract(day FROM paid_date)
ORDER BY extract(day FROM paid_date);"""

    daily_out_payments = """
  SELECT extract(day FROM paid_date),
         SUM(paid_value)
    FROM payment, payment_adapt_to_out_payment
   WHERE payment.id = payment_adapt_to_out_payment.original_id AND
         extract(month FROM paid_date) = $month AND
         extract(year FROM paid_date) = $year
GROUP BY extract(day FROM paid_date)
ORDER BY extract(day FROM paid_date);"""
    days = {}
    for i in range(1, 32):
        days[i] = {'in': 0, 'out': 0}
    tmpl = string.Template(daily_in_payments).substitute(dict(month=month, year=year))
    for day, total_in in conn.queryAll(tmpl):
        days[day]['in'] = total_in

    tmpl = string.Template(daily_out_payments).substitute(dict(month=month, year=year))
    for day, total_out in conn.queryAll(tmpl):
        days[day]['out'] = total_out

    for day, values in days.items():
        total_in = values.get('in', 0)
        total_out = values.get('out', 0)
        yield [day, total_in, total_out, total_in - total_out]
