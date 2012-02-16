# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011 Async Open Source <http://www.async.com.br>
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

import datetime
import json

from twisted.web.resource import Resource
from twisted.web.static import File
from kiwi.environ import environ

from stoqlib.api import api
from stoqlib.chart.chart import get_chart_class
from stoqlib.net.calendarevents import CalendarEvents


def _iso_to_datetime(iso):
    # 2001-02-03 -> datetime
    return datetime.date(*map(int, iso.split('-')))


class ChartResource(Resource):
    def render_GET(self, resource):
        if not 'type' in resource.args:
            raise TypeError

        chart_type = resource.args['type'][0]
        chart_class = get_chart_class(chart_type)
        if chart_class is None:
            raise TypeError("chart_class")

        if (not 'start' in resource.args or
            not 'end' in resource.args):
            raise TypeError
        start_str = resource.args['start'][0]
        end_str = resource.args['end'][0]

        args = dict(start=_iso_to_datetime(start_str),
                    end=_iso_to_datetime(end_str))

        chart = chart_class(api.get_connection())
        response = chart.run(args)
        return json.dumps(response)


class WebResource(Resource):

    def __init__(self):
        Resource.__init__(self)
        path = environ.get_resource_paths('html')[0]
        self.putChild('static', File(path))
        self.putChild('calendar-events.json', CalendarEvents())
        self.putChild('chart.json', ChartResource())
