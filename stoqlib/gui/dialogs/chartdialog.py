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
""" Chart Generation Dialog """

import json

import gtk
from twisted.web.client import getPage

from stoqlib.api import api
from stoqlib.lib.daemonutils import start_daemon
from stoqlib.gui.webview import WebView


class ChartDialog(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self)
        self.set_size_request(800, 480)
        self._view = WebView()
        self._view.get_view().connect(
            'load-finished',
            self._on_view__document_load_finished)
        self.add(self._view)

        self._setup_daemon()

    @api.async
    def _setup_daemon(self):
        daemon = yield start_daemon()
        self._daemon_uri = daemon.base_uri

        proxy = daemon.get_client()
        yield proxy.callRemote('start_webservice')

        def _get_chart_url(**kwargs):
            params = []
            for key, value in kwargs.items():
                params.append(key + '=' + str(value))
            print params
            return '%s/web/payment-chart.json?%s' % (
                self._daemon_uri, '&'.join(params))

        #url = _get_chart_url(type='daily', year=2011, month=12)
        url = _get_chart_url(type='month', year=2011)
        page = yield getPage(url)
        opt = {}
        opt['data'] = json.loads(page)
        opt['options'] = {
            "xaxis": {"mode": "time"},
            # XXX: _JS_DAY is not defined
            #"bars": {"show": True, "barWidth": 20 * 1},
            "points": {"show": True},
            "lines": {"show": True},
            "grid": {"hoverable": True,
                     "clickable": True},
        }
        self._opt = opt
        self._view.load_uri('%s/web/static/chart.html' % (
                            self._daemon_uri,))

    def _load_finished(self):
        print self._opt
        self._view.js_function_call("plot", self._opt, "foobar")

    #
    # Callbacks
    #

    def _on_view__document_load_finished(self, view, frame):
        self._load_finished()
