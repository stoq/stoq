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
"""
stoq/gui/calendar.py:

    Calendar application.
"""

import urllib.request
import urllib.parse
import urllib.error

from dateutil.parser import parse
from dateutil.relativedelta import MO, relativedelta
from dateutil.tz import tzlocal, tzutc
from gi.repository import Gtk, GLib

from stoqlib.api import api
from stoqlib.domain.person import Client
from stoq.lib.gui.editors.callseditor import CallsEditor
from stoq.lib.gui.editors.paymenteditor import InPaymentEditor, OutPaymentEditor
from stoq.lib.gui.editors.workordereditor import WorkOrderEditor
from stoq.lib.gui.utils.keybindings import get_accels
from stoq.lib.gui.widgets.webview import WebView
from stoqlib.lib import dateutils
from stoqlib.lib.daemonutils import start_daemon
from stoqlib.lib.defaults import get_weekday_start
from stoqlib.lib.threadutils import (threadit,
                                     schedule_in_main_thread)
from stoqlib.lib.translation import stoqlib_gettext as _

from stoq.gui.shell.shellapp import ShellApp
from stoq.gui.widgets import ButtonGroup


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
        rect = view.get_allocation()
        self._update_calendar_size(rect.width, rect.height)

    def _startup(self):
        options = {}
        options['monthNames'] = dateutils.get_month_names()
        options['monthNamesShort'] = dateutils.get_short_month_names()
        options['dayNames'] = dateutils.get_day_names()
        options['dayNamesShort'] = dateutils.get_short_day_names()
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
            Gtk.Widget.get_default_direction() == Gtk.TextDirection.RTL)
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
            client_birthdays=events.get('client-birthdays', True),
            work_orders=events.get('work-orders', True),
        )

    def _save_user_settings(self):
        events = api.user_settings.get('calendar-events', {})
        events['in-payments'] = self._show_events['in_payments']
        events['out-payments'] = self._show_events['out_payments']
        events['purchase-orders'] = self._show_events['purchase_orders']
        events['client-calls'] = self._show_events['client_calls']
        events['client-birthdays'] = self._show_events['client_birthdays']
        events['work-orders'] = self._show_events['work_orders']

    def _update_calendar_size(self, width, height):
        self._calendar_run('option', 'aspectRatio', float(width) / height)

    def _update_title(self):
        # Workaround to get the current calendar date
        view = self.get_view()
        view.execute_script("document.title = $('.fc-header-title').text()")
        title = view.get_property('title')
        self.app.date_label.set_markup(
            '<big><b>%s</b></big>' % api.escape(title))

    #
    # Callbacks
    #

    def _on_view__document_load_finished(self, view, frame):
        self._load_finished()

    def _on_view__size_allocate(self, widget, req):
        self._update_calendar_size(req.width, req.height)

    #
    # WebView
    #

    def web_open_uri(self, kwargs):
        if kwargs['method'] == 'changeView':
            view = kwargs['view']
            if view == 'basicDay':
                self.app.day_button.set_active(True)
                jsdate = urllib.parse.unquote(kwargs['date'])
                date = parse_javascript_date(jsdate)
                self._calendar_run('gotoDate', date.year, date.month, date.day)
    #
    # Public API
    #

    def set_daemon_uri(self, uri):
        self._daemon_uri = uri

    def load(self):
        self._load_daemon_path('static/calendar-app.html')

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
        if not self._loaded:
            return
        self.js_function_call("update_options", self._show_events)

        self._calendar_run('refetchEvents')
        self._save_user_settings()


class CalendarApp(ShellApp):

    app_title = _('Calendar')
    gladefile = 'calendar'

    def __init__(self, window, store=None):
        # Create this here because CalendarView will update it.
        # It will only be shown on create_ui though
        self.date_label = Gtk.Label(label='')
        self._calendar = CalendarView(self)
        ShellApp.__init__(self, window, store=store)
        threadit(self._setup_daemon)

    def _setup_daemon(self):
        daemon = start_daemon()
        assert daemon.running
        self._calendar.set_daemon_uri(daemon.server_uri)
        schedule_in_main_thread(self._calendar.load)

    #
    # ShellApp overrides
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
            ('NewWorkOrder', None, _("Work order"),
             group.get('new_work_order'), _("Add a new work order")),
            # View
            ('Back', Gtk.STOCK_GO_BACK, _("Back"),
             group.get('go_back'), _("Go back")),
            ('Forward', Gtk.STOCK_GO_FORWARD, _("Forward"),
             group.get('go_forward'), _("Go forward")),
            ('Today', None, _("Show today"),
             group.get('show_today'), _("Show today")),
        ]
        self.calendar_ui = self.add_ui_actions(actions)
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
            ('ClientBirthdaysEvents', None, _("Client Birthdays"),
             None, _("Show client birthdays in the list")),
            ('WorkOrderEvents', None, _("Work orders"),
             None, _("Show work orders in the list")),
        ]
        self.add_ui_actions(toggle_actions, 'ToggleActions')

        events_info = dict(
            in_payments=(self.AccountsReceivableEvents, self.NewReceivable,
                         u'receivable'),
            out_payments=(self.AccountsPayableEvents, self.NewPayable,
                          u'payable'),
            purchase_orders=(self.PurchaseEvents, None, u'stock'),
            client_calls=(self.ClientCallEvents, self.NewClientCall, u'sales'),
            client_birthdays=(self.ClientBirthdaysEvents, None, u'sales'),
            work_orders=(self.WorkOrderEvents, self.NewWorkOrder, u'services'),
        )

        user = api.get_current_user(self.store)
        events = self._calendar.get_events()
        for event_name, value in events_info.items():
            view_action, new_action, app = value
            view_action.set_state(GLib.Variant.new_boolean(events[event_name]))

            # Disable feature if user does not have acces to required
            # application
            if not user.profile.check_app_permission(app):
                view_action.set_state(GLib.Variant.new_boolean(False))
                self.set_sensitive([view_action], False)
                if new_action:
                    self.set_sensitive([new_action], False)

            view_action.connect('change-state', self._view_option_state_changed)
        self._update_events()

    def create_ui(self):
        self.window.add_extra_items([
            self.ClientCallEvents,
            self.ClientBirthdaysEvents,
            self.AccountsPayableEvents,
            self.AccountsReceivableEvents,
            self.PurchaseEvents,
            self.WorkOrderEvents
        ], label=_('View'))
        self.window.add_new_items([self.NewClientCall,
                                   self.NewPayable,
                                   self.NewReceivable, self.NewWorkOrder])

        # Reparent the toolbar, to show the date next to it.
        self.hbox = Gtk.HBox()

        self.date_label.set_xalign(0)

        self.main_vbox.pack_start(self.hbox, False, False, 6)
        self.main_vbox.pack_start(self._calendar, True, True, 0)

        self.nav_header = ButtonGroup([
            self.window.create_button('fa-arrow-left-symbolic', action='calendar.Back'),
            self.window.create_button('fa-calendar-symbolic',
                                      action='calendar.Today',
                                      tooltip=_('Today')),
            self.window.create_button('fa-arrow-right-symbolic', action='calendar.Forward')
        ])

        self.month_button = Gtk.ToggleButton.new_with_label(_('Month'))
        self.week_button = Gtk.ToggleButton.new_with_label(_('Week'))
        self.day_button = Gtk.ToggleButton.new_with_label(_('Day'))
        self.view_header = ButtonGroup([
            self.month_button,
            self.week_button,
            self.day_button,
        ])
        view = api.user_settings.get('calendar-view', 'month')
        if view == 'basicDay':
            self.day_button.set_active(True)
        elif view == 'basicWeek':
            self.week_button.set_active(True)
        else:
            self.month_button.set_active(True)

        self.hbox.pack_start(self.nav_header, False, False, 6)
        self.hbox.pack_start(self.date_label, True, True, 6)
        self.hbox.pack_start(self.view_header, False, False, 6)
        self.main_vbox.show_all()

    def deactivate(self):
        self.window.header_bar.remove(self.nav_header)

    # Private

    def _update_events(self, *args):
        self._calendar.update_events(
            out_payments=self.AccountsPayableEvents.get_state().get_boolean(),
            in_payments=self.AccountsReceivableEvents.get_state().get_boolean(),
            purchase_orders=self.PurchaseEvents.get_state().get_boolean(),
            client_calls=self.ClientCallEvents.get_state().get_boolean(),
            client_birthdays=self.ClientBirthdaysEvents.get_state().get_boolean(),
            work_orders=self.WorkOrderEvents.get_state().get_boolean(),
        )

    def _new_client_call(self):
        with api.new_store() as store:
            self.run_dialog(CallsEditor, store, None, None, Client)

        if store.committed:
            self._update_events()

    def _new_work_order(self):
        with api.new_store() as store:
            self.run_dialog(WorkOrderEditor, store)

        if store.committed:
            self._update_events()

    def _new_payment(self, editor):
        with api.new_store() as store:
            self.run_dialog(editor, store)

        if store.committed:
            self._update_events()

    #
    # Kiwi callbacks
    #

    def _view_option_state_changed(self, action, value):
        action.set_state(value)
        self._update_events()

    # Toolbar

    def on_NewClientCall__activate(self, action):
        self._new_client_call()

    def on_NewPayable__activate(self, action):
        self._new_payment(OutPaymentEditor)

    def on_NewReceivable__activate(self, action):
        self._new_payment(InPaymentEditor)

    def on_NewWorkOrder__activate(self, action):
        self._new_work_order()

    def on_Back__activate(self, action):
        self._calendar.go_prev()

    def on_Today__activate(self, action):
        self._calendar.show_today()

    def on_Forward__activate(self, action):
        self._calendar.go_next()

    def _update_view_buttons(self, view):
        views = ['month', 'basicWeek', 'basicDay']
        self._calendar.change_view(view)
        children = self.view_header.get_children()
        index = views.index(view)
        for i, widget in enumerate(children):
            widget.set_active(i == index)

    def on_month_button__toggled(self, button):
        if button.get_active():
            self._update_view_buttons('month')

    def on_week_button__toggled(self, button):
        if button.get_active():
            self._update_view_buttons('basicWeek')

    def on_day_button__toggled(self, button):
        if button.get_active():
            self._update_view_buttons('basicDay')
