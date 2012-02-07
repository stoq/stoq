# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011-12 Async Open Source <http://www.async.com.br>
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
from kiwi.currency import currency
from kiwi.python import Settable
from kiwi.ui.objectlist import ObjectList, Column
from twisted.web.client import getPage

from stoqlib.api import api
from stoqlib.lib.daemonutils import start_daemon
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.webview import WebView

_ = stoqlib_gettext


reports = {
    'month': [dict(name='time', title=_('Time unit'), expand=True),
              dict(name='revenue', title=_("Revenue"), data_type=currency),
              dict(name='expense', title=_("Expense"), data_type=currency),
              dict(name='profit', title=_("Profit"), data_type=currency)]
    }


class ChartDialog(gtk.Window):
    def __init__(self):
        self._js_data = None
        self._js_options = None

        gtk.Window.__init__(self)
        self.set_size_request(800, 480)

        self.vbox = gtk.VBox()
        self.add(self.vbox)
        self.vbox.show()

        self._view = WebView()
        self._view.get_view().connect(
            'load-finished',
            self._on_view__document_load_finished)
        self.vbox.pack_start(self._view, True, True)

        self._setup_daemon()

    @api.async
    def _setup_daemon(self):
        daemon = yield start_daemon()
        self._daemon_uri = daemon.base_uri

        proxy = daemon.get_client()
        yield proxy.callRemote('start_webservice')

        # FIXME: This should be user options
        report_name = 'month'
        report = reports['month']
        report_kwargs = dict(year=2011)

        # Get chart data

        response = yield self._invoke_chart(report_name, **report_kwargs)
        self._render_chart(report, response)

    @api.async
    def _invoke_chart(self, report_name, **report_kwargs):
        def _get_chart_url(**kwargs):
            params = []
            for key, value in kwargs.items():
                params.append(key + '=' + str(value))
            return '%s/web/payment-chart.json?%s' % (
                self._daemon_uri, '&'.join(params))

        url = _get_chart_url(type=report_name, **report_kwargs)
        page = yield getPage(url)
        data = json.loads(page)
        api.asyncReturn(data)

    def _render_chart(self, report, response):
        self._render_javascript(report, response)
        self._render_objectlist(report, response)

    def _render_javascript(self, report, response):
        ticks = [item['short_title'] for item in response['items']]

        self._js_data = response['data']

        options = {}
        options['series'] = [dict(label=serie) for serie in response['series']]
        options['xaxis_ticks'] = ticks
        self._js_options = options

        self._view.load_uri('%s/web/static/chart.html' % (
                            self._daemon_uri,))

    def _render_objectlist(self, report, response):
        columns = []
        for kwargs in report:
            name = kwargs.pop('name')
            columns.append(Column(name, **kwargs))
        results = ObjectList(columns)

        for item in response['items']:
            settable = Settable(**item)
            results.append(settable)

        self.vbox.pack_start(results, True, True)
        results.show()

    def _load_finished(self):
        self._view.js_function_call(
            "plot", self._js_data, self._js_options)

    #
    # Callbacks
    #

    def _on_view__document_load_finished(self, view, frame):
        self._load_finished()
