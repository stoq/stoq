# -*- Mode: Python; coding: iso-8859-1 -*-
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
"""
stoq/gui/calendar.py:

    Calendar application.
"""

import datetime
import gettext
import json

import gtk
import webkit

from stoqlib.api import api
from stoqlib.domain.payment.payment import Payment
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.paymenteditor import InPaymentEditor
from stoqlib.gui.keybindings import get_accels
from stoqlib.gui.stockicons import (STOQ_CALENDAR_TODAY,
                                    STOQ_CALENDAR_WEEK,
                                    STOQ_CALENDAR_MONTH)
from stoqlib.lib import dateconstants
from stoqlib.lib.daemonutils import start_daemon

from stoq.gui.application import AppWindow


_ = gettext.gettext


class CalendarView(gtk.ScrolledWindow):
    def __init__(self, app):
        self.app = app
        gtk.ScrolledWindow.__init__(self)
        self.set_shadow_type(gtk.SHADOW_ETCHED_IN)

        self._view = webkit.WebView()
        self._view.props.settings.props.enable_developer_extras = True

        self._view.get_web_inspector().connect(
            'inspect-web-view',
            self._on_inspector__inspect_web_view)
        self._view.connect(
            'navigation-policy-decision-requested',
            self._on_view__navigation_policy_decision_requested)
        self._view.connect(
            'load-finished',
            self._on_view__document_load_finished)
        self.add(self._view)
        self._view.show()

    def _load_finished(self):
        self._startup()

    def _startup(self):
        d = {}
        d['monthNames'] = dateconstants.get_month_names()
        d['monthNamesShort'] = dateconstants.get_short_month_names()
        d['dayNames'] = dateconstants.get_day_names()
        d['dayNamesShort'] = dateconstants.get_short_day_names()
        d['buttonText'] = {"today": _('today'),
                           "month": _('month'),
                           "week": _('week'),
                           "day": _('day')}
        self._js_function_call('startup', d)

    def _load_daemon_path(self, path):
        uri = '%s/%s' % (self._daemon_uri, path)
        self._view.load_uri(uri)

    def _run_dialog(self, name, **kwargs):
        if name == 'payment':
            self._show_payment_details(**kwargs)
        elif name == 'in-payment-list':
            self._show_in_payment_list(**kwargs)
        elif name == 'out-payment-list':
            self._show_out_payment_list(**kwargs)
        else:
            raise NotImplementedError(name)

    def _show_payment_details(self, id):
        trans = api.new_transaction()
        payment = trans.get(Payment.get(int(id)))
        retval = run_dialog(InPaymentEditor, self.app, trans, payment)
        if api.finish_transaction(trans, retval):
            self.refresh()
        trans.close()

    def _show_in_payment_list(self, date):
        y, m, d = map(int, date.split('-'))
        date = datetime.date(y, m, d)
        app = self.app.app.launcher.run_app_by_name(
            'receivable', params={'no-refresh': True})
        app.main_window.search_for_date(date)

    def _show_out_payment_list(self, date):
        y, m, d = map(int, date.split('-'))
        date = datetime.date(y, m, d)
        app = self.app.app.launcher.run_app_by_name(
            'payable', params={'no-refresh': True})
        app.main_window.search_for_date(date)

    def _js_function_call(self, function, *args):
        js_values = []
        for arg in args:
            if arg is True:
                value = 'true'
            elif arg is False:
                value = 'false'
            elif type(arg) in [str, int, float]:
                value = repr(arg)
            else:
                value = json.dumps(arg)
            js_values.append(value)

        self._view.execute_script('%s(%s)' % (
            function, ', '.join(js_values)))

    def _calendar_run(self, name, *args):
        self._js_function_call("$('#calendar').fullCalendar", name, *args)

    def _policy_decision(self, uri, policy):
        if uri.startswith('file:///'):
            policy.use()
        elif uri.startswith('http://localhost'):
            policy.use()
        elif uri.startswith('dialog://'):
            policy.ignore()
            data = uri[9:]
            doc, args = data.split('?', 1)
            kwargs = {}
            for arg in args.split(','):
                k, v = arg.split('=', 1)
                kwargs[k] = v
            self._run_dialog(doc, **kwargs)
        else:
            gtk.show_uri(self.get_screen(), uri,
                         gtk.get_current_event_time())

    def _create_view_for_inspector(self, introspector_view):
        window = gtk.Window()
        window.set_size_request(800, 600)
        sw = gtk.ScrolledWindow()
        window.add(sw)
        view = webkit.WebView()
        sw.add(introspector_view)
        window.show_all()
        return view

    #
    # Callbacks
    #

    def _on_inspector__inspect_web_view(self, inspector, view):
        return self._create_view_for_inspector(view)

    def _on_view__document_load_finished(self, view, frame):
        self._load_finished()

    def _on_view__navigation_policy_decision_requested(self, view, frame,
                                                       request, action,
                                                       policy):
        self._policy_decision(request.props.uri, policy)

    #
    # Public API
    #

    def set_daemon_uri(self, uri):
        self._daemon_uri = uri

    def load(self):
        self._load_daemon_path('web/static/calendar-app.html')

    def print_(self):
        self._view.execute_script('window.print()')

    def go_prev(self):
        self._calendar_run('prev')

    def show_today(self):
        self._calendar_run('today')

    def go_next(self):
        self._calendar_run('next')

    def change_view(self, view_name):
        self._calendar_run('changeView', view_name)

    def refresh(self):
        self.load()


class CalendarApp(AppWindow):

    app_name = _('Calendar')
    gladefile = 'calendar'
    embedded = True

    def __init__(self, app):
        AppWindow.__init__(self, app)
        self._setup_daemon()

    @api.async
    def _setup_daemon(self):
        daemon = yield start_daemon()
        self._calendar.set_daemon_uri(daemon.base_uri)

        proxy = daemon.get_client()
        yield proxy.callRemote('start_webservice')
        self._calendar.load()

    #
    # AppWindow overrides
    #

    def create_actions(self):
        group = get_accels('app.calendar')
        actions = [
            ('Back', gtk.STOCK_GO_BACK, _("Back"),
             group.get('go_back'), _("Go back")),
            ('Forward', gtk.STOCK_GO_FORWARD, _("Forward"),
             group.get('go_forward'), _("Go forward")),
            ('Today', STOQ_CALENDAR_TODAY, _("Show today"),
             group.get('show_today'), _("Show today")),
            ]
        self.calendar_ui = self.add_ui_actions('', actions,
                                                filename='calendar.xml')
        self.help_ui = None

        radio_actions = [
            ('ViewMonth', STOQ_CALENDAR_MONTH, _("View as month"),
             '', _("Show one month")),
            ('ViewWeek', STOQ_CALENDAR_WEEK, _("View as week"),
             '', _("Show one week")),
            ]
        self.add_ui_actions('', radio_actions, 'RadioActions',
                            'radio')
        self.ViewMonth.set_short_label(_("Month"))
        self.ViewWeek.set_short_label(_("Week"))
        self.ViewMonth.props.is_important = True
        self.ViewWeek.props.is_important = True
        self.ViewMonth.props.active = True

    def create_ui(self):
        self._calendar = CalendarView(self)
        self.main_vbox.pack_start(self._calendar)
        self._calendar.show()
        self.app.launcher.Print.set_tooltip(_("Print this calendar"))

    def activate(self, params):
        self.app.launcher.SearchToolItem.set_sensitive(False)
        # FIXME: Are we 100% sure we can always print something?
        self.app.launcher.Print.set_sensitive(True)

    def deactivate(self):
        self.uimanager.remove_ui(self.calendar_ui)
        self.app.launcher.SearchToolItem.set_sensitive(True)

    #
    # Kiwi callbacks
    #

    # Toolbar

    def new_activate(self):
        pass

    def print_activate(self):
        self._calendar.print_()

    def export_csv_activate(self):
        pass

    def on_Back__activate(self, action):
        self._calendar.go_prev()

    def on_Today__activate(self, action):
        self._calendar.show_today()

    def on_Forward__activate(self, action):
        self._calendar.go_next()

    def on_ViewMonth__activate(self, action):
        self._calendar.change_view('month')

    def on_ViewWeek__activate(self, action):
        self._calendar.change_view('basicWeek')
