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

import gtk
from stoqlib.api import api
from stoqlib.gui.keybindings import get_accels
from stoqlib.gui.stockicons import (STOQ_CALENDAR_TODAY,
                                    STOQ_CALENDAR_WEEK,
                                    STOQ_CALENDAR_MONTH,
                                    STOQ_CALENDAR_LIST)
from stoqlib.gui.webview import WebView
from stoqlib.lib import dateconstants
from stoqlib.lib.daemonutils import start_daemon

from stoq.gui.application import AppWindow

_ = gettext.gettext


class CalendarView(WebView):
    def __init__(self, app):
        WebView.__init__(self)
        self.app = app
        self.get_view().connect(
            'load-finished',
            self._on_view__document_load_finished)

        self._load_user_settings()

    def _load_finished(self):
        self._startup()
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

        options['data'] = self._show_events
        self.js_function_call('startup', options)
        self._update_title()

    def _calendar_run(self, name, *args):
        self.js_function_call("$('#calendar').fullCalendar", name, *args)

    def _load_daemon_path(self, path):
        uri = '%s/%s' % (self._daemon_uri, path)
        self.load_uri(uri)

    def _load_user_settings(self):
        events = api.user_settings.get('calendar-events', {})
        self._show_events = dict(
            in_payments=events.get('in-payments', True),
            out_payments=events.get('out-payments', True),
            purchase_orders=events.get('purchase-orders', True))

    def _save_user_settings(self):
        events = api.user_settings.get('calendar-events', {})
        events['in-payments'] = self._show_events['in_payments']
        events['out-payments'] = self._show_events['out_payments']
        events['purchase-orders'] = self._show_events['purchase_orders']
        api.user_settings.flush()

    def _update_calendar_size(self, width, height):
        self._calendar_run('option', 'aspectRatio', float(width) / height)

    def _update_title(self):
        # Workaround to get the current calendar date
        self._view.execute_script("document.title = $('.fc-header-title').text()")
        title = self._view.get_property('title')
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
            ]
        self.add_ui_actions('', toggle_actions, 'ToggleActions',
                            'toggle')

        events = self._calendar.get_events()
        self.AccountsReceivableEvents.props.active = (
            events['in_payments'])
        self.AccountsPayableEvents.props.active = (
            events['out_payments'])
        self.PurchaseEvents.props.active = (
            events['purchase_orders'])
        self.AccountsReceivableEvents.connect(
            'notify::active', self._update_events)
        self.AccountsPayableEvents.connect(
            'notify::active', self._update_events)
        self.PurchaseEvents.connect(
            'notify::active', self._update_events)

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
        hbox = gtk.HBox()
        toolbar = self.uimanager.get_widget('/toolbar')
        toolbar.get_parent().remove(toolbar)
        hbox.pack_start(toolbar)

        # A label to show the current calendar date.
        self.date_label = gtk.Label('')
        self.date_label.show()
        hbox.pack_start(self.date_label, False, False, 6)
        hbox.show()

        self.main_vbox.pack_start(hbox, False, False)

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

    # Private

    def _update_events(self, *args):
        self._calendar.update_events(
            out_payments=self.AccountsPayableEvents.get_active(),
            in_payments=self.AccountsReceivableEvents.get_active(),
            purchase_orders=self.PurchaseEvents.get_active())

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

    def on_ViewDay__activate(self, action):
        self._calendar.change_view('basicDay')
