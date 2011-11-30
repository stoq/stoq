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
""" Chart http server """

import cgi
import json

from twisted.internet import reactor
from twisted.web.resource import Resource
from twisted.web.server import Site
from twisted.web.static import File

from stoqlib.chart.chart import get_chart_class
from stoqlib.database.runtime import get_connection
from stoqlib.lib.template import render_template
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class RootResource(Resource):

    def render_GET(self, request):
        return _('Stoq Chart Server')

    def getChild(self, name, request):
        if name == '':
            return self
        return Resource.getChild(self, name, request)


class ChartChartResource(Resource):

    def _get_chart(self, request):
        conn = get_connection()

        if not '?' in request.uri:
            raise TypeError("Missing arguments")
        args = cgi.parse_qs(request.uri.split('?', 1)[1])
        chart_name = args.pop('name')

        chart_class = get_chart_class(chart_name)
        chart = chart_class(conn)
        for key, value in args.items():
            chart.set_argument(key, value[0])
        return chart

    def render_GET(self, request):
        chart = self._get_chart(request)
        opt = {}
        opt['data'] = chart.run()
        opt['options'] = {
            "xaxis": {"mode": "time"},
            # XXX: _JS_DAY is not defined
            #"bars": {"show": True, "barWidth": 20 * _JS_DAY},
            "points": {"show": False},
            "lines": {"show": False},
            "grid": {"hoverable": True,
                     "clickable": True},
        }
        return render_template('chart-time.html', chart=chart,
                               json=json.dumps(opt))


def start(port):
    root = RootResource()
    root.putChild('javascript', File('/usr/share/javascript/'))
    root.putChild('chart', ChartChartResource())

    site = Site(root)
    reactor.listenTCP(port, site)
