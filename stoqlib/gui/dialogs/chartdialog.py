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
""" Chart Generation Dialog """

import datetime
import json

import gtk
from dateutil.relativedelta import relativedelta
from kiwi.python import Settable
from kiwi.ui.objectlist import ObjectList, Column
from kiwi.ui.widgets.combo import ProxyComboBox
from twisted.web.client import getPage

from stoqlib.api import api
from stoqlib.chart.chart import get_chart_class
from stoqlib.lib.daemonutils import start_daemon
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.webview import WebView

_ = stoqlib_gettext


class ChartDialog(gtk.Window):
    def __init__(self):
        self._js_data = None
        self._js_options = None
        self._current = None

        gtk.Window.__init__(self)
        self.set_size_request(800, 480)

        self.vbox = gtk.VBox()
        self.add(self.vbox)
        self.vbox.show()

        hbox = gtk.HBox()
        self.vbox.pack_start(hbox, False, False, 6)
        hbox.show()

        label = gtk.Label('Period:')
        hbox.pack_start(label, False, False, 6)
        label.show()

        self.chart_type = ProxyComboBox()
        self.chart_type.connect(
            'content-changed',
            self._on_chart_type__content_changed)
        hbox.pack_start(self.chart_type, False, False, 6)
        self.chart_type.show()

        self.period_values = ProxyComboBox()
        self.period_values.connect(
            'content-changed',
            self._on_period_values__content_changed)
        hbox.pack_start(self.period_values, False, False, 6)
        self.period_values.show()

        self._view = WebView()
        self._view.get_view().connect(
            'load-finished',
            self._on_view__document_load_finished)
        self.vbox.pack_start(self._view, True, True)

        self.results = ObjectList()
        self.results.connect(
            'row-activated',
            self._on_results__row_activated)
        self.vbox.pack_start(self.results, True, True)

        self._setup_daemon()

    @api.async
    def _setup_daemon(self):
        daemon = yield start_daemon()
        self._daemon_uri = daemon.base_uri

        proxy = daemon.get_client()
        yield proxy.callRemote('start_webservice')

        self.chart_type.prefill([
            ('Year', 'YearlyPayments'),
            ('Month', 'MonthlyPayments'),
            ('Day', 'DailyPayments'),
            ])

    @api.async
    def _invoke_chart(self, chart_type_name, **report_kwargs):
        def _get_chart_url(**kwargs):
            params = []
            for key, value in kwargs.items():
                params.append(key + '=' + str(value))
            return '%s/web/chart.json?%s' % (
                self._daemon_uri, '&'.join(params))

        url = _get_chart_url(type=chart_type_name, **report_kwargs)
        page = yield getPage(url)
        data = json.loads(page)
        api.asyncReturn(data)

    def _render_chart(self, chart_class, response):
        self._render_javascript(chart_class, response)
        self._render_objectlist(chart_class, response)

    def _render_javascript(self, chart_class, response):
        ticks = [item['short_title'] for item in response['items']]

        self._js_data = response['data']

        options = {}
        options['description'] = response['description']
        options['series'] = [dict(label=c['title']) for c in chart_class.columns][1:]
        options['xaxis_ticks'] = ticks
        self._js_options = options

        self._view.load_uri('%s/web/static/chart.html' % (
                            self._daemon_uri,))

    def _render_objectlist(self, chart_class, response):
        columns = []
        for kwargs in chart_class.columns:
            kwargs = kwargs.copy()
            name = kwargs.pop('name')
            columns.append(Column(name, **kwargs))
        self.results.set_columns(columns)

        items = []
        for item in response['items']:
            settable = Settable(**item)
            settable.chart_class = chart_class
            items.append(settable)
        self.results.add_list(items, clear=True)
        self.results.show()

    def _load_finished(self):
        self._view.js_function_call(
            "plot", self._js_data, self._js_options)

    @api.async
    def _show_one(self, chart_type_name, start, end):
        chart_class = get_chart_class(chart_type_name)
        report_kwargs = dict(start=start.strftime('%Y-%m-%d'),
                             end=end.strftime('%Y-%m-%d'))

        # Get chart datab
        response = yield self._invoke_chart(chart_type_name, **report_kwargs)
        self._render_chart(chart_class, response)

    def _update_period_values(self):
        chart_type_name = self.chart_type.get_selected()
        chart_class = get_chart_class(chart_type_name)
        values = chart_class.get_combo_labels()
        self.period_values.prefill(values)

    #
    # Callbacks
    #

    def _on_view__document_load_finished(self, view, frame):
        self._load_finished()

    def _on_chart_type__content_changed(self, combo):
        self._update_period_values()

    def _on_period_values__content_changed(self, combo):
        kind = self.chart_type.get_selected()
        value = self.period_values.get_selected()
        if not value:
            return
        start, end = value
        if self._current == (kind, start, end):
            return
        self._show_one(kind, start, end)
        self._current = kind, start, end

    def _on_results__row_activated(self, results, item):
        chart_type_name = item.chart_class.__name__
        if chart_type_name == 'YearlyPayments':
            start = datetime.date(item.year, 1, 1)
            end = datetime.date(item.year, 12, 31)
            chart_type_name = 'MonthlyPayments'
        elif chart_type_name == 'MonthlyPayments':
            start = datetime.date(item.year, item.month, 1)
            end = start + relativedelta(days=31)
            chart_type_name = 'DailyPayments'
        else:
            return
        self._show_one(chart_type_name, start, end)
