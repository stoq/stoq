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

import gettext
import json

from kiwi.environ import environ
import gtk
import webkit

from stoqlib.api import api
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.payment.views import InPaymentView
from stoqlib.domain.payment.views import OutPaymentView
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.paymenteditor import InPaymentEditor
from stoqlib.lib import dateconstants

from stoq.gui.application import AppWindow

_ = gettext.gettext


class CalendarView(gtk.ScrolledWindow):
    def __init__(self, app):
        self.app = app
        gtk.ScrolledWindow.__init__(self)
        self.set_shadow_type(gtk.SHADOW_ETCHED_IN)

        self._view = webkit.WebView()
        self._view.props.settings.props.enable_developer_extras = True

        insp = self._view.get_web_inspector()

        def inspect(inspector, view):
            w = gtk.Window()
            w.set_size_request(800, 600)
            sw = gtk.ScrolledWindow()
            w.add(sw)
            view = webkit.WebView()
            sw.add(view)
            w.show_all()
            return view
        insp.connect('inspect-web-view', inspect)
        self._view.connect(
            'navigation-policy-decision-requested',
            self._on_view__navigation_policy_decision_requested)
        self.add(self._view)
        self._view.show()
        self._view.load_uri('html://calendar-app.html')

        # FIXME: Use some signal to find out when the document is rendered
        import gobject
        gobject.idle_add(self._load_events)

    def _on_view__navigation_policy_decision_requested(self, view, frame,
                                                       request, action,
                                                       policy):
        uri = request.props.uri
        if uri.startswith('file:///'):
            return True
        if uri.startswith('html://'):
            policy.ignore()
            filename = uri[7:]
            filename = environ.find_resource('html', filename)
            self._view.load_uri('file://' + filename)
            return
        if uri.startswith('dialog://'):
            policy.ignore()
            data = uri[9:]
            doc, args = data.split('?', 1)
            kwargs = {}
            for arg in args.split(','):
                k, v = arg.split('=', 1)
                kwargs[k] = v
            self._run_dialog(doc, **kwargs)
            return

        gtk.show_uri(self.get_screen(), uri,
                     gtk.get_current_event_time())

    def _run_dialog(self, name, **kwargs):
        if name == 'payment':
            self._show_payment_details(**kwargs)

    def _show_payment_details(self, payment_id):
        trans = api.new_transaction()
        payment = trans.get(Payment.get(int(payment_id)))
        retval = run_dialog(InPaymentEditor, self.app, trans, payment)
        if api.finish_transaction(trans, retval):
            self.search.refresh()
        trans.close()

    def _startup(self):
        d = {}
        d['monthNames'] = dateconstants.get_month_names()
        d['monthNamesShort'] = dateconstants.get_short_month_names()
        d['dayNames'] = dateconstants.get_day_names()
        d['dayNamesShort'] = dateconstants.get_short_month_names()
        d['buttonText'] = {"today": _('today'),
                           "month": _('month'),
                           "week": _('week'),
                           "day": _('day')}
        s = "startup(%s);" % (json.dumps(d), )
        self._view.execute_script(s)

    def _load_events(self):
        self._startup()
        for pv in InPaymentView.select(connection=self.app.conn):
            self._add_payment(pv.payment, "red")
        for pv in OutPaymentView.select(connection=self.app.conn):
            self._add_payment(pv.payment, "blue")

    def _render_event(self, args):
        self._view.execute_script(
            "$('#calendar').fullCalendar('renderEvent', %s, true);" % (
            json.dumps(args)))

    def _add_payment(self, payment, color):
        event = {"title": payment.description,
                 "start": payment.due_date.isoformat(),
                 "url": "dialog://payment?payment_id=" + str(payment.id),
                 "color": color}
        self._render_event(event)

    def print_(self):
        self._view.execute_script('window.print()')


class CalendarApp(AppWindow):

    app_name = _('Calendar')
    app_icon_name = 'stoq-calendar-app'
    gladefile = 'calendar'
    embedded = True

    def __init__(self, app):
        AppWindow.__init__(self, app)

    #
    # AppWindow overrides
    #

    def create_actions(self):
        actions = [
            ('Print', gtk.STOCK_PRINT, _("Print..."),
             None, _('Print a transaction report')),
            ('ExportCSV', None, _('Export CSV...'), '<control>F10'),
            ("NewTask", gtk.STOCK_NEW, _("Task..."), '<control>t',
             _("Add a new task")),
            ]
        self.calendar_ui = self.add_ui_actions('', actions,
                                                filename='calendar.xml')
        self.help_ui = None

    def create_ui(self):
        self._calendar = CalendarView(self)
        self.main_vbox.pack_start(self._calendar)
        self._calendar.show()
        self.app.launcher.add_new_items([self.NewTask])

    def activate(self):
        self.app.launcher.SearchToolItem.set_sensitive(False)

    def deactivate(self):
        self.uimanager.remove_ui(self.calendar_ui)
        self.app.launcher.SearchToolItem.set_sensitive(True)

    #
    # Kiwi callbacks
    #

    # Toolbar

    def new_activate(self):
        pass

    # Calendar

    def on_Print__activate(self, action):
        self._calendar.print_()

    def on_ExportCSV__activate(self, action):
        pass
