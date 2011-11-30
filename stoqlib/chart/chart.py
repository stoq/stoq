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
""" Charting """

import pprint

from kiwi.python import namedAny
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class DateArgument(object):
    pass


class Month(DateArgument):
    pass


class Year(DateArgument):
    pass


class Chart(object):
    def __init__(self, conn):
        self.conn = conn
        self.args = {}

    def set_argument(self, name, value):
        self.args[name] = value

    def execute(self, query):
        return self.conn.queryAll(query)

    def pretty_run(self):
        return pprint.pformat(list(sorted(self.run())))

    def run(self):
        pass

# Relative to stoqlib.chart
_charts = {'paymentchart': ['MonthlyPaymentsChart']}


def get_chart_class(chart_name):
    location = _charts.get(chart_name)
    if not location:
        raise ValueError(chart_name)
    return namedAny(location)
