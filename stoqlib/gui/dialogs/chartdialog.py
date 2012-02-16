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

import datetime
import json

from dateutil.relativedelta import relativedelta
import gtk
from kiwi.currency import currency
from kiwi.python import Settable
from kiwi.ui.objectlist import ObjectList, Column
from kiwi.ui.widgets.combo import ProxyComboBox
from twisted.web.client import getPage

from stoqlib.api import api
from stoqlib.lib.daemonutils import start_daemon
from stoqlib.lib.dateconstants import get_month_names
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.webview import WebView

_ = stoqlib_gettext


reports = {
    'day': [dict(name='time', title=_('Day'), expand=True),
            dict(name='revenue', title=_("Revenue"), data_type=currency),
            dict(name='expense', title=_("Expense"), data_type=currency),
            dict(name='profit', title=_("Profit"), data_type=currency)],
    'month': [dict(name='time', title=_('Month'), expand=True),
              dict(name='revenue', title=_("Revenue"), data_type=currency),
              dict(name='expense', title=_("Expense"), data_type=currency),
              dict(name='profit', title=_("Profit"), data_type=currency)],
    'year': [dict(name='time', title=_('Year'), expand=True),
             dict(name='revenue', title=_("Revenue"), data_type=currency),
             dict(name='expense', title=_("Expense"), data_type=currency),
             dict(name='profit', title=_("Profit"), data_type=currency)]
    }


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
        self.vbox.pack_start(hbox, False, False)
        hbox.show()

        label = gtk.Label('Period')
        hbox.pack_start(label, False, False)
        label.show()

        self.period_type = ProxyComboBox()
        self.period_type.connect(
            'content-changed',
            self._on_period_type__content_changed)
        hbox.pack_start(self.period_type, False, False)
        self.period_type.show()

        self.period_values = ProxyComboBox()
        self.period_values.connect(
            'content-changed',
            self._on_period_values__content_changed)
        hbox.pack_start(self.period_values, False, False)
        self.period_values.show()

        self._view = WebView()
        self._view.get_view().connect(
            'load-finished',
            self._on_view__document_load_finished)
        self.vbox.pack_start(self._view, True, True)

        self.results = ObjectList()
        self.vbox.pack_start(self.results, True, True)

        self._setup_daemon()

    @api.async
    def _setup_daemon(self):
        daemon = yield start_daemon()
        self._daemon_uri = daemon.base_uri

        proxy = daemon.get_client()
        yield proxy.callRemote('start_webservice')

        self.period_type.prefill([
            ('Month', 'month'),
            ('Year', 'year'),
            ('Day', 'day'),
            ])

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
            kwargs = kwargs.copy()
            name = kwargs.pop('name')
            columns.append(Column(name, **kwargs))
        self.results.set_columns(columns)

        items = []
        for item in response['items']:
            settable = Settable(**item)
            items.append(settable)
        self.results.add_list(items, clear=True)
        self.results.show()

    def _load_finished(self):
        self._view.js_function_call(
            "plot", self._js_data, self._js_options)

    @api.async
    def _show_one(self, kind, start, end):
        report_name = kind
        report = reports[kind]
        report_kwargs = dict(start=start.strftime('%Y-%m-%d'),
                             end=end.strftime('%Y-%m-%d'))

        # Get chart datab
        response = yield self._invoke_chart(report_name, **report_kwargs)
        self._render_chart(report, response)

    def _update_period_values(self):
        today = datetime.datetime.today()
        values = []

        period_type = self.period_type.get_selected()
        if period_type == 'year':
            values = []
            values.append((('All years'),
                           (datetime.date(1900, 1, 1),
                            today.date())))
            values.append((('Last 5 years'),
                           (datetime.date(today.year - 5, 1, 1),
                            today.date())))
        elif period_type == 'month':
            date = datetime.datetime(today.year, 1, 1)
            for y in range(4):
                start = date
                end = date + relativedelta(month=12, day=31)
                values.append((str(date.year), (start.date(), end.date())))
                date -= relativedelta(years=1)
            start = today - relativedelta(years=1)
            end = today
            values.append((_('Last 12 months'), (start.date(), end.date())))
        elif period_type == 'day':
            date = today + relativedelta(day=1)
            year = date.year
            month_names = get_month_names()
            for m in range(6):
                start = date
                end = date + relativedelta(day=31)
                month_name = month_names[start.month - 1]
                if date.year != year:
                    month_name += ' ' + str(date.year)
                values.append((month_name, (start.date(), end.date())))
                date -= relativedelta(months=1)

            start = today - relativedelta(days=30)
            end = today
            values.append((_('Last 30 days'), (start.date(), today.date())))
        else:
            return
        self.period_values.prefill(values)

    #
    # Callbacks
    #

    def _on_view__document_load_finished(self, view, frame):
        self._load_finished()

    def _on_period_type__content_changed(self, combo):
        self._update_period_values()

    def _on_period_values__content_changed(self, combo):
        kind = self.period_type.get_selected()
        value = self.period_values.get_selected()
        if not value:
            return
        start, end = value
        if self._current == (kind, start, end):
            return
        self._show_one(kind, start, end)
        self._current = kind, start, end
