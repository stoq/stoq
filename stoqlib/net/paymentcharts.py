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
import json
import string

from twisted.web.resource import Resource

from stoqlib.api import api
from stoqlib.lib.dateconstants import (get_month_names,
                                       get_short_month_names)
from stoqlib.lib.translation import stoqlib_gettext


_ = stoqlib_gettext


class Chart(object):
    def __init__(self, conn):
        self.conn = conn

    def execute(self, query):
        return self.conn.queryAll(query)

    def run(self):
        pass


class YearlyPaymentsChart(Chart):
    name = _("Monthly payments")

    description = _("Total revenue, expenses and profit for all years")

    in_payments_query = """
 SELECT extract(year FROM paid_date),
        SUM(paid_value)
   FROM payment
  WHERE payment.payment_type = 0
 GROUP BY extract(year FROM paid_date)
 ORDER BY extract(year FROM paid_date);"""

    out_payments_query = """
 SELECT extract(year FROM paid_date),
        SUM(paid_value)
   FROM payment
  WHERE payment.payment_type = 1
 GROUP BY extract(year FROM paid_date)
 ORDER BY extract(year FROM paid_date);"""

    def run(self, args):
        """
        :returns: (year, total in payments, total out payments, profit)
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

        revenues = []
        expenses = []
        profits = []

        items = []
        for year, values in sorted(years.items()):
            total_in = values.get('in', 0)
            total_out = values.get('out', 0)
            revenue = float(total_in)
            expense = float(total_out)
            profit = float(total_in - total_out)
            revenues.append(revenue)
            expenses.append(expense)
            profits.append(profit)
            items.append({
                'short_title': year,
                'time': int(year),
                'revenue': int(revenue),
                'expense': int(expense),
                'profit': int(profit)})

        return {'series': [_('Revenue'),
                           _('Expenses'),
                           _('Profits')],
                'data': [revenues, expenses, profits],
                'items': items}


class MonthlyPaymentsChart(Chart):
    name = _("Monthly payments")
    description = _("Total revenue, expenses and profit for all months in a year")

    in_payments_query = """
  SELECT $date_columns,
         SUM(paid_value)
    FROM payment
   WHERE payment_type = 0 AND
         status = 2 AND
         payment.paid_date >= '$start' AND payment.paid_date < '$end'
GROUP BY $date_columns
ORDER BY $date_columns;
"""

    out_payments_query = """
 SELECT $date_columns,
        SUM(paid_value)
   FROM payment
  WHERE payment_type = 1 AND
        status = 2 AND
        payment.paid_date >= '$start' AND payment.paid_date < '$end'
 GROUP BY $date_columns
 ORDER BY $date_columns;
"""

    def run(self, args):
        start = datetime.date(*map(int, args['start'][0].split('-')))
        end = datetime.date(*map(int, args['end'][0].split('-')))

        date_columns = "extract(year FROM paid_date)||'-'||lpad(extract(month FROM paid_date)::char, 2, '0')"
        months = {}
        ns = dict(date_columns=date_columns,
                  start=start.strftime('%Y-%m-%d'),
                  end=end.strftime('%Y-%m-%d'))

        tmpl = string.Template(self.in_payments_query).substitute(ns)
        res = self.execute(tmpl)
        for date, total_in in res:
            year, month = map(int, date.split('-'))
            months.setdefault((year, month), {})['in'] = total_in or 0

        tmpl = string.Template(self.out_payments_query).substitute(ns)
        res = self.execute(tmpl)
        for date, total_out in res:
            year, month = map(int, date.split('-'))
            months.setdefault((year, month), {})['out'] = total_out or 0

        revenues = []
        expenses = []
        profits = []

        items = []
        keys = sorted(months)
        for key in keys:
            values = months[key]
            year, month = key
            month = int(month)
            total_in = values.get('in', 0)
            total_out = values.get('out', 0)

            revenues.append(float(total_in))
            expenses.append(float(total_out))
            profits.append(float(total_in - total_out))

            items.append({'short_title': '%s' % (get_short_month_names()[month - 1], ),
                          'time': '%s, %d' % (get_month_names()[month - 1], year),
                          'revenue': int(total_in),
                          'expense': int(total_out),
                          'profit': int(total_in - total_out)})

        return {'series': [_('Revenue'),
                           _('Expenses'),
                           _('Profits')],
                'data': [revenues, expenses, profits],
                'items': items}


class DailyPaymentsChart(Chart):

    daily_in_payments = """
  SELECT extract(day FROM paid_date),
         SUM(paid_value)
    FROM payment
   WHERE payment_type = 0 AND
         extract(month FROM paid_date) = $month AND
         extract(year FROM paid_date) = $year
GROUP BY extract(day FROM paid_date)
ORDER BY extract(day FROM paid_date);"""

    daily_out_payments = """
  SELECT extract(day FROM paid_date),
         SUM(paid_value)
    FROM payment
   WHERE payment_type = 1 AND
         extract(month FROM paid_date) = $month AND
         extract(year FROM paid_date) = $year
GROUP BY extract(day FROM paid_date)
ORDER BY extract(day FROM paid_date);"""

    def run(self, args):
        """
        @year: year to show payments for
        @month: month to show payments for
        :returns: (month, total in payments, total out payments, profit)
        """
        # FIXME:
        return {'series': [_('Revenue'),
                           _('Expenses'),
                           _('Profits')],
                'data': [],
                'items': {}}

        year = int(args['year'][0])
        if 2100 > year < 1900:
            raise ValueError(year)
        month = int(args['month'][0])
        if 12 > month < 1:
            raise ValueError(month)

        days = {}
        for i in range(1, 32):
            days[i] = {'in': 0, 'out': 0}
        tmpl = string.Template(self.daily_in_payments).substitute(
            dict(month=month, year=year))
        for day, total_in in self.conn.queryAll(tmpl):
            days[day]['in'] = total_in

        tmpl = string.Template(self.daily_out_payments).substitute(
            dict(month=month, year=year))
        for day, total_out in self.conn.queryAll(tmpl):
            days[day]['out'] = total_out

        for day, values in days.items():
            total_in = values.get('in', 0)
            total_out = values.get('out', 0)
            #yield [float(day), float(total_in), float(total_out), float(total_in - total_out)]


class PaymentCharts(Resource):
    def render_GET(self, resource):
        chart_type = resource.args['type'][0]

        conn = api.get_connection()
        if chart_type == 'year':
            chart_class = YearlyPaymentsChart
        elif chart_type == 'month':
            chart_class = MonthlyPaymentsChart
        elif chart_type == 'daily':
            chart_class = DailyPaymentsChart
        else:
            raise AssertionError

        chart = chart_class(conn)
        response = chart.run(resource.args)
        return json.dumps(response)
