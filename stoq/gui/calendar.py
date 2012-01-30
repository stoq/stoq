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
import urllib

from dateutil.parser import parse
from dateutil.relativedelta import MO, relativedelta
from dateutil.tz import tzlocal, tzutc
import gtk

from stoqlib.api import api
from stoqlib.domain.interfaces import IClient
from stoqlib.gui.editors.callseditor import CallsEditor
from stoqlib.gui.editors.paymenteditor import (InPaymentEditor,
                                               OutPaymentEditor)
from stoqlib.gui.keybindings import get_accels
from stoqlib.gui.stockicons import (STOQ_CALENDAR_TODAY,
                                    STOQ_CALENDAR_WEEK,
                                    STOQ_CALENDAR_MONTH,
                                    STOQ_CALENDAR_LIST)
from stoqlib.gui.webview import WebView
from stoqlib.lib import dateconstants
from stoqlib.lib.daemonutils import start_daemon
from stoqlib.lib.defaults import get_weekday_start

from stoq.gui.application import AppWindow

_ = gettext.gettext


def parse_javascript_date(jsdate):
    dt = parse(jsdate, fuzzy=True)
    dt = dt.replace(tzinfo=tzlocal())
    date = dt.astimezone(tzutc())
    date += relativedelta(months=-1)
    return date


class CalendarView(WebView):
    def __init__(self, app):
        self._loaded = False
        WebView.__init__(self)
        self.app = app
        self.get_view().connect(
            'load-finished',
            self._on_view__document_load_finished)

        self._load_user_settings()

    def _load_finished(self):
        self._startup()
        self._loaded = True
        view = self.get_view()
        view.connect('size-allocate', self._on_view__size_allocate)
        x, y, width, height = view.get_allocation()
        self._update_calendar_size(width, height)

    def _startup(self):
        options = {}
        options['monthNames'] = dateconstants.get_month_names()
        options['monthNamesShort'] = dateconstants.get_short_month_names()
        options['dayNames'] = dateconstants.get_day_names()
        options['dayNamesShort'] = dateconstants.get_short_day_names()
        options['buttonText'] = {"today": _('today'),
                                 "month": _('month'),
                                 "week": _('week'),
                                 "day": _('day')}
        options['defaultView'] = api.user_settings.get(
            'calendar-view', 'month')

        # FIXME: This should not be tied to the language, rather be
        #        picked up from libc, but it's a bit of work to translate
        #        one into another so just take a shortcut
        options['columnFormat'] = {
            # month column format, eg "Mon", see:
            # http://arshaw.com/fullcalendar/docs/text/columnFormat/
            'month': _('ddd'),
            # week column format: eg, "Mon 9/7", see:
            # http://arshaw.com/fullcalendar/docs/text/columnFormat/
            'week': _('ddd M/d'),
            # day column format : eg "Monday 9/7", see:
            # http://arshaw.com/fullcalendar/docs/text/columnFormat/
            'day': _('dddd M/d'),
            }

        options['timeFormat'] = {
            # for agendaWeek and agendaDay, eg "5:00 - 6:30", see:
            # http://arshaw.com/fullcalendar/docs/text/timeFormat/
            'agenda': _('h:mm{ - h:mm}'),
            # for all other views, eg "7p", see:
            # http://arshaw.com/fullcalendar/docs/text/timeFormat/
            '': _('h(:mm)t'),
            }

        options['titleFormat'] = {
            # month title, eg "September 2009", see:
            # http://arshaw.com/fullcalendar/docs/text/titleFormat/
            'month': _('MMMM yyyy'),
            # week title, eg "Sep 7 - 13 2009" see:
            # http://arshaw.com/fullcalendar/docs/text/titleFormat/
            'week': _("MMM d[ yyyy]{ '&#8212;'[ MMM] d yyyy}"),
            # day time, eg "Tuesday, Sep 8, 2009" see:
            # http://arshaw.com/fullcalendar/docs/text/titleFormat/
            'day': _('dddd, MMM d, yyyy'),
            }

        if get_weekday_start() == MO:
            firstday = 1
        else:
            firstday = 0

        options['firstDay'] = firstday
        options['isRTL'] = (
            gtk.widget_get_default_direction() == gtk.TEXT_DIR_RTL)
        options['data'] = self._show_events
        options['loading_msg'] = _('Loading calendar content, please wait...')
        self.js_function_call('startup', options)
        self._update_title()

    def _calendar_run(self, name, *args):
        if not self._loaded:
            return
        self.js_function_call("$('#calendar').fullCalendar", name, *args)

    def _load_daemon_path(self, path):
        uri = '%s/%s' % (self._daemon_uri, path)
        self.load_uri(uri)

    def _load_user_settings(self):
        events = api.user_settings.get('calendar-events', {})
        self._show_events = dict(
            in_payments=events.get('in-payments', True),
            out_payments=events.get('out-payments', True),
            purchase_orders=events.get('purchase-orders', True),
            client_calls=events.get('client-calls', True),
            )

    def _save_user_settings(self):
        events = api.user_settings.get('calendar-events', {})
        events['in-payments'] = self._show_events['in_payments']
        events['out-payments'] = self._show_events['out_payments']
        events['purchase-orders'] = self._show_events['purchase_orders']
        events['client-calls'] = self._show_events['client_calls']

    def _update_calendar_size(self, width, height):
        self._calendar_run('option', 'aspectRatio', float(width) / height)

    def _update_title(self):
        # Workaround to get the current calendar date
        view = self.get_view()
        view.execute_script("document.title = $('.fc-header-title').text()")
        title = view.get_property('title')
        self.app.date_label.set_markup('<big><b>%s</b></big>' % title)

    #
    # Callbacks
    #

    def _on_view__document_load_finished(self, view, frame):
        self._load_finished()

    def _on_view__size_allocate(self, widget, req):
        x, y, width, height = req
        self._update_calendar_size(width, height)

    #
    # WebView
    #

    def web_open_uri(self, kwargs):
        if kwargs['method'] == 'changeView':
            view = kwargs['view']
            if view == 'basicDay':
                self.app.ViewDay.set_active(True)
                jsdate = urllib.unquote(kwargs['date'])
                date = parse_javascript_date(jsdate)
                self._calendar_run('gotoDate', date.year, date.month, date.day)
    #
    # Public API
    #

    def set_daemon_uri(self, uri):
        self._daemon_uri = uri

    def load(self):
        self._load_daemon_path('web/static/calendar-app.html')

    def go_prev(self):
        self._calendar_run('prev')
        self._update_title()

    def show_today(self):
        self._calendar_run('today')
        self._update_title()

    def go_next(self):
        self._calendar_run('next')
        self._update_title()

    def change_view(self, view_name):
        self._calendar_run('removeEvents')
        self._calendar_run('changeView', view_name)
        self._calendar_run('refetchEvents')
        api.user_settings.set('calendar-view', view_name)
        self._update_title()

    def refresh(self):
        self.load()

    def get_events(self):
        return self._show_events

    def update_events(self, **events):
        self._show_events.update(**events)
        self.js_function_call("update_options", self._show_events)

        self._calendar_run('refetchEvents')
        self._save_user_settings()


class CalendarApp(AppWindow):

    app_name = _('Calendar')
    gladefile = 'calendar'
    embedded = True

    def __init__(self, app):
        self._calendar = CalendarView(self)
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
            # File
            ('NewClientCall', None, _("Client call"),
             group.get('new_client_call'), _("Add a new client call")),
            ('NewPayable', None, _("Account payable"),
             group.get('new_payable'), _("Add a new account payable")),
            ('NewReceivable', None, _("Account receivable"),
             group.get('new_receivable'), _("Add a new account receivable")),
            # View
            ('Back', gtk.STOCK_GO_BACK, _("Back"),
             group.get('go_back'), _("Go back")),
            ('Forward', gtk.STOCK_GO_FORWARD, _("Forward"),
             group.get('go_forward'), _("Go forward")),
            ('Today', STOQ_CALENDAR_TODAY, _("Show today"),
             group.get('show_today'), _("Show today")),
            ('CalendarEvents', None, _("Calendar events")),
            ('CurrentView', None, _("Display view as")),
            ]
        self.calendar_ui = self.add_ui_actions('', actions,
                                                filename='calendar.xml')
        self.set_help_section(_("Calendar help"), 'app-calendar')

        toggle_actions = [
            ('AccountsPayableEvents', None, _("Accounts payable"),
             None, _("Show accounts payable in the list")),
            ('AccountsReceivableEvents', None, _("Accounts receivable"),
             None, _("Show accounts receivable in the list")),
            ('PurchaseEvents', None, _("Purchases"),
             None, _("Show purchases in the list")),
            ('ClientCallEvents', None, _("Client Calls"),
             None, _("Show client calls in the list")),
            ]
        self.add_ui_actions('', toggle_actions, 'ToggleActions',
                            'toggle')

        events_info = dict(
            in_payments=(self.AccountsReceivableEvents, self.NewReceivable,
                         'receivable'),
            out_payments=(self.AccountsPayableEvents, self.NewPayable,
                          'payable'),
            purchase_orders=(self.PurchaseEvents, None, 'stock'),
            client_calls=(self.ClientCallEvents, self.NewClientCall, 'sales'),
        )

        user = api.get_current_user(self.conn)
        events = self._calendar.get_events()
        for event_name, value in events_info.items():
            view_action, new_action, app = value
            view_action.props.active = events[event_name]
            # Disable feature if user does not have acces to required
            # application
            if not user.profile.check_app_permission(app):
                view_action.props.active = False
                view_action.set_sensitive(False)
                if new_action:
                    new_action.set_sensitive(False)

            view_action.connect('notify::active', self._update_events)

        radio_actions = [
            ('ViewMonth', STOQ_CALENDAR_MONTH, _("View as month"),
             '', _("Show one month")),
            ('ViewWeek', STOQ_CALENDAR_WEEK, _("View as week"),
             '', _("Show one week")),
            ('ViewDay', STOQ_CALENDAR_LIST, _("View as day"),
             '', _("Show one day")),
            ]
        self.add_ui_actions('', radio_actions, 'RadioActions',
                            'radio')
        self.ViewMonth.set_short_label(_("Month"))
        self.ViewWeek.set_short_label(_("Week"))
        self.ViewDay.set_short_label(_("Day"))
        self.ViewMonth.props.is_important = True
        self.ViewWeek.props.is_important = True
        self.ViewDay.props.is_important = True

        view = api.user_settings.get('calendar-view', 'month')
        if view == 'month':
            self.ViewMonth.props.active = True
        elif view == 'basicWeek':
            self.ViewWeek.props.active = True
        else:
            self.ViewDay.props.active = True

    def create_ui(self):
        self.app.launcher.add_new_items([self.NewClientCall,
                                         self.NewPayable,
                                         self.NewReceivable])

        # Reparent the toolbar, to show the date next to it.
        self.hbox = gtk.HBox()
        toolbar = self.uimanager.get_widget('/toolbar')
        toolbar.reparent(self.hbox)

        # A label to show the current calendar date.
        self.date_label = gtk.Label('')
        self.date_label.show()
        self.hbox.pack_start(self.date_label, False, False, 6)
        self.hbox.show()

        self.main_vbox.pack_start(self.hbox, False, False)

        self.main_vbox.pack_start(self._calendar)
        self._calendar.show()
        self.app.launcher.Print.set_tooltip(_("Print this calendar"))

    def activate(self, params):
        self.app.launcher.SearchToolItem.set_sensitive(False)
        # FIXME: Are we 100% sure we can always print something?
        # self.app.launcher.Print.set_sensitive(True)

    def deactivate(self):
        # Put the toolbar back at where it was
        main_vbox = self.app.launcher.main_vbox
        toolbar = self.uimanager.get_widget('/toolbar')
        self.hbox.remove(toolbar)
        main_vbox.pack_start(toolbar, False, False)
        main_vbox.reorder_child(toolbar, 1)

        self.uimanager.remove_ui(self.calendar_ui)
        self.app.launcher.SearchToolItem.set_sensitive(True)

    # Private

    def _update_events(self, *args):
        self._calendar.update_events(
            out_payments=self.AccountsPayableEvents.get_active(),
            in_payments=self.AccountsReceivableEvents.get_active(),
            purchase_orders=self.PurchaseEvents.get_active(),
            client_calls=self.ClientCallEvents.get_active(),
            )

    def _new_client_call(self):
        with api.trans() as trans:
            self.run_dialog(CallsEditor, trans, None, None, IClient)

        if trans.committed:
            self._update_events()

    def _new_payment(self, editor):
        with api.trans() as trans:
            self.run_dialog(editor, trans)

        if trans.committed:
            self._update_events()

    #
    # Kiwi callbacks
    #

    # Toolbar

    def new_activate(self):
        self._new_client_call()

    def print_activate(self):
        self._calendar.print_()

    def export_csv_activate(self):
        pass

    def on_NewClientCall__activate(self, action):
        self._new_client_call()

    def on_NewPayable__activate(self, action):
        self._new_payment(OutPaymentEditor)

    def on_NewReceivable__activate(self, action):
        self._new_payment(InPaymentEditor)

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

    def on_ViewDay__activate(self, action):
        self._calendar.change_view('basicDay')
