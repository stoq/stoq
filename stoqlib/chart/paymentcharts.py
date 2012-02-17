##
## Copyright (C) 2011-2012 Async Open Source <http://www.async.com.br>
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

from dateutil.relativedelta import relativedelta
from kiwi.currency import currency

from stoqlib.chart.chart import Chart
from stoqlib.lib.dateconstants import (get_month_names,
                                       get_short_month_names)
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class YearlyPayments(Chart):
    columns = [dict(name='year', title=_('Year'), expand=True),
               dict(name='revenue', title=_("Revenues"), data_type=currency),
               dict(name='expense', title=_("Expenses"), data_type=currency),
               dict(name='profit', title=_("Gross profits"), data_type=currency)]

    in_payments_query = """
 SELECT extract(year FROM paid_date),
        SUM(paid_value)
   FROM payment
  WHERE payment.payment_type = 0 AND
        payment.paid_date >= '$start' AND payment.paid_date < '$end'
 GROUP BY extract(year FROM paid_date)
 ORDER BY extract(year FROM paid_date);"""

    out_payments_query = """
 SELECT extract(year FROM paid_date),
        SUM(paid_value)
   FROM payment
  WHERE payment.payment_type = 1 AND
        payment.paid_date >= '$start' AND payment.paid_date < '$end'
 GROUP BY extract(year FROM paid_date)
 ORDER BY extract(year FROM paid_date);"""

    start_date = datetime.date(1900, 1, 1)

    @classmethod
    def get_combo_labels(cls):
        today = datetime.date.today()
        values = []
        values.append((_('All years'),
                       (cls.start_date,
                        today)))
        values.append((_('Last 5 years'),
                       (datetime.date(today.year - 5, 1, 1),
                        today)))
        return values

    def run(self, args):
        start = args['start']
        end = args['end']

        if start == self.start_date:
            description = _("Total revenue, expenses and gross profit for all years")
        else:
            description = _("Total revenue, expenses and gross profit between %s and %s") % (
                start.year, end.year)

        ns = dict(start=start.strftime('%Y-%m-%d'),
                  end=end.strftime('%Y-%m-%d'))

        years = {}
        tmpl = string.Template(self.in_payments_query).substitute(ns)
        for year, total_in in self.execute(tmpl):
            if not year:
                continue
            if not year in years:
                years[year] = {}
            years[year]['in'] = total_in or 0

        tmpl = string.Template(self.out_payments_query).substitute(ns)
        for year, total_out in self.execute(tmpl):
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
                'year': int(year),
                'revenue': int(revenue),
                'expense': int(expense),
                'profit': int(profit)})

        return {'data': [revenues, expenses, profits],
                'description': description,
                'items': items}


class MonthlyPayments(Chart):
    columns = [dict(name='time', title=_('Month'), expand=True),
               dict(name='revenue', title=_("Revenues"), data_type=currency),
               dict(name='expense', title=_("Expenses"), data_type=currency),
               dict(name='profit', title=_("Gross profits"), data_type=currency)]

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

    @classmethod
    def get_combo_labels(cls):
        values = []
        today = datetime.date.today()
        date = datetime.date(today.year, 1, 1)
        # FIXME: Check database to determine range
        for y in range(4):
            start = date
            end = date + relativedelta(month=12, day=31)
            values.append((str(date.year), (start, end)))
            date -= relativedelta(years=1)
        start = today - relativedelta(years=1)
        end = today
        values.append((_('Last 12 months'), (start, end)))
        return values

    def run(self, args):
        start = args['start']
        end = args['end']

        if (start.month == 1 and start.day == 1 and
            end.month == 12 and end.day == 31):
            description = _("Total revenue, expenses and gross profit for %s") % (start.year, )
        else:
            description = _("Total revenue, expenses and gross profit for all months in a year")

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
                          'profit': int(total_in - total_out),
                          'year': year,
                          'month': month})

        return {'data': [revenues, expenses, profits],
                'description': description,
                'items': items}


class DailyPayments(Chart):
    columns = [dict(name='time', title=_('Day'), expand=True),
               dict(name='revenue', title=_("Revenues"), data_type=currency),
               dict(name='expense', title=_("Expenses"), data_type=currency),
               dict(name='profit', title=_("Gross profits"), data_type=currency)]

    daily_in_payments = """
  SELECT extract(day FROM paid_date),
         SUM(paid_value)
    FROM payment
   WHERE payment_type = 0 AND
         payment.paid_date >= '$start' AND payment.paid_date < '$end'
GROUP BY extract(day FROM paid_date)
ORDER BY extract(day FROM paid_date);"""

    daily_out_payments = """
  SELECT extract(day FROM paid_date),
         SUM(paid_value)
    FROM payment
   WHERE payment_type = 1 AND
         payment.paid_date >= '$start' AND payment.paid_date < '$end'
GROUP BY extract(day FROM paid_date)
ORDER BY extract(day FROM paid_date);"""

    @classmethod
    def get_combo_labels(cls):
        values = []
        today = datetime.date.today()
        date = today + relativedelta(day=1)
        year = date.year
        month_names = get_month_names()
        # FIXME: Check database to determine range
        for m in range(6):
            start = date
            end = date + relativedelta(day=31)
            month_name = month_names[start.month - 1]
            if date.year != year:
                month_name += ' ' + str(date.year)
            values.append((month_name, (start, end)))
            date -= relativedelta(months=1)

        start = today - relativedelta(days=30)
        end = today
        values.append((_('Last 30 days'), (start, today)))

        return values

    def run(self, args):
        start = args['start']
        end = args['end']

        if (start + relativedelta(days=31)) == end:
            month_name = get_month_names()[start.month - 1]
            link = 'chart://show_one/type=YearlyPayments&start=%d-01-01&end=%d-12-31' % (
                start.year, start.year)
            description = _('Revenue, expenses and gross profit for %s <a href="%s">%s</a>') % (
                month_name, link, start.year)
        else:
            description = _("Revenue, expenses and gross profit per day")

        ns = dict(start=start.strftime('%Y-%m-%d'),
                  end=end.strftime('%Y-%m-%d'))

        days = {}
        for i in range(1, 32):
            days[i] = {'in': 0, 'out': 0}
        tmpl = string.Template(self.daily_in_payments).substitute(ns)
        for day, total_in in self.conn.queryAll(tmpl):
            days[day]['in'] = total_in

        tmpl = string.Template(self.daily_out_payments).substitute(ns)
        for day, total_out in self.conn.queryAll(tmpl):
            days[day]['out'] = total_out

        revenues = []
        expenses = []
        profits = []

        items = []
        for day, values in sorted(days.items()):
            total_in = values.get('in', 0)
            total_out = values.get('out', 0)
            revenues.append(float(total_in))
            expenses.append(float(total_out))
            profits.append(float(total_in - total_out))
            items.append({
                'short_title': day,
                'revenuse': int(total_in),
                'expense': int(total_out),
                'profit': int(total_in - total_out),
                })

        return {'data': [revenues, expenses, profits],
                'description': description,
                'items': items}
