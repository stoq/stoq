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

    def _on_inspector__inspect_web_view(self, inspector, view):
        w = gtk.Window()
        w.set_size_request(800, 600)
        sw = gtk.ScrolledWindow()
        w.add(sw)
        view = webkit.WebView()
        sw.add(view)
        w.show_all()
        return view

    def _on_view__document_load_finished(self, view, frame):
        self._load_finished()

    def _on_view__navigation_policy_decision_requested(self, view, frame,
                                                       request, action,
                                                       policy):
        uri = request.props.uri
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
            self.search.refresh()
        trans.close()

    def _show_in_payment_list(self, ids):
        ids = map(int, ids.split('|'))
        app = self.app.app.launcher.run_app_by_name('receivable')
        app.main_window.select_payment_ids(ids)

    def _show_out_payment_list(self, date):
        y, m, d = map(int, date.split('-'))
        date = datetime.date(y, m, d)
        app = self.app.app.launcher.run_app_by_name('payable')
        app.main_window.search_for_date(date)

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
        s = "startup(%s);" % (json.dumps(d), )
        self._view.execute_script(s)

    def _render_event(self, args):
        self._view.execute_script(
            "$('#calendar').fullCalendar('renderEvent', %s, true);" % (
            json.dumps(args)))

    def print_(self):
        self._view.execute_script('window.print()')

    def _load_daemon_path(self, path):
        uri = '%s/%s' % (self._daemon_uri, path)
        self._view.load_uri(uri)

    def set_daemon_uri(self, uri):
        self._daemon_uri = uri

    def go_prev(self):
        self._view.execute_script("$('#calendar').fullCalendar('prev');")

    def show_today(self):
        self._view.execute_script("$('#calendar').fullCalendar('today');")

    def go_next(self):
        self._view.execute_script("$('#calendar').fullCalendar('next');")

    def change_view(self, view_name):
        self._view.execute_script(
            "$('#calendar').fullCalendar('changeView', %r);" % (
            view_name, ))

    def load(self):
        self._load_daemon_path('web/static/calendar-app.html')


class CalendarApp(AppWindow):

    app_name = _('Calendar')
    app_icon_name = 'stoq-calendar-app'
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
        actions = [
            ("NewTask", gtk.STOCK_NEW, _("Task..."), '<control>t',
             _("Add a new task")),
            ('Back', gtk.STOCK_GO_BACK, _("Back"),
             '', _("Go back")),
            ('Forward', gtk.STOCK_GO_FORWARD, _("Forward"),
             '', _("Go forward")),
            ('Today', 'stoq-calendar-today', _("Show today"),
             '', _("Show today")),
            ]
        self.calendar_ui = self.add_ui_actions('', actions,
                                                filename='calendar.xml')
        self.help_ui = None

        radio_actions = [
            ('ViewMonth', 'stoq-calendar-month', _("View as month"),
             '', _("Show one month")),
            ('ViewWeek', 'stoq-calendar-week', _("View as week"),
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
        self.app.launcher.add_new_items([self.NewTask])
        self.app.launcher.Print.set_tooltip(_("Print this calendar"))

    def activate(self):
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
