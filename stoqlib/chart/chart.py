# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

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
""" Charting """

from kiwi.python import namedAny
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class Chart(object):
    description = None
    name = None
    series = []
    columns = []

    def __init__(self, conn):
        self.conn = conn

    @classmethod
    def get_combo_labels(cls):
        return []

    def execute(self, query):
        return self.conn.queryAll(query)

    def run(self, args):
        pass


# Relative to stoqlib.chart
_charts = {'MonthlyPayments': 'paymentcharts',
           'YearlyPayments': 'paymentcharts',
           'DailyPayments': 'paymentcharts'}


def get_chart_class(chart_name):
    location = _charts.get(chart_name)
    if not location:
        raise ValueError(chart_name)
    return namedAny('stoqlib.chart.%s.%s' % (location, chart_name))
