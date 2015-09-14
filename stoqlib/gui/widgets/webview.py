# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011-2012 Async Open Source <http://www.async.com.br>
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

import logging
import json
import urlparse

import gtk
import webkit

from stoqlib.api import api
from stoqlib.lib.dateutils import localdate
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.paymenteditor import get_dialog_for_payment
from stoqlib.gui.utils.openbrowser import open_browser

log = logging.getLogger(__name__)

USER_AGENT = ("Mozilla/5.0 (X11; Linux x86_64) "
              "AppleWebKit/535.4+ (KHTML, like Gecko) "
              "Version/5.0 Safari/535.4+ Stoq")

# urlparse.urlparse() requires you to register your custom url
# scheme to be able to use result.query


def register_scheme(scheme):
    for method in filter(lambda s: s.startswith('uses_'), dir(urlparse)):
        getattr(urlparse, method).append(scheme)
register_scheme('stoq')


class WebView(gtk.ScrolledWindow):
    def __init__(self):
        gtk.ScrolledWindow.__init__(self)
        self.set_shadow_type(gtk.SHADOW_ETCHED_IN)

        self._view = webkit.WebView()
        settings = self._view.props.settings
        settings.props.enable_developer_extras = True
        settings.props.user_agent = USER_AGENT
        settings.props.enable_default_context_menu = False

        self._view.get_web_inspector().connect(
            'inspect-web-view',
            self._on_inspector__inspect_web_view)
        self._view.connect(
            'navigation-policy-decision-requested',
            self._on_view__navigation_policy_decision_requested)
        self.add(self._view)
        self._view.show()

    def _dialog_payment_details(self, id):
        from stoqlib.domain.payment.payment import Payment
        store = api.new_store()
        payment = store.get(Payment, id)
        dialog_class = get_dialog_for_payment(payment)
        retval = run_dialog(dialog_class, self.app, store, payment)
        if store.confirm(retval):
            self.refresh()
        store.close()

    def _dialog_purchase(self, id):
        from stoqlib.domain.purchase import PurchaseOrder
        from stoqlib.gui.dialogs.purchasedetails import PurchaseDetailsDialog

        store = api.new_store()
        purchase = store.get(PurchaseOrder, id)
        retval = run_dialog(PurchaseDetailsDialog, self.app, store, purchase)
        if store.confirm(retval):
            self.refresh()
        store.close()

    def _dialog_call(self, id):
        from stoqlib.domain.person import Calls
        from stoqlib.gui.editors.callseditor import CallsEditor

        store = api.new_store()
        model = store.get(Calls, id)
        retval = run_dialog(CallsEditor, self.app, store, model, None, None)
        if store.confirm(retval):
            self.refresh()
        store.close()

    def _dialog_client(self, id):
        from stoqlib.domain.person import Client
        from stoqlib.gui.dialogs.clientdetails import ClientDetailsDialog

        with api.new_store() as store:
            model = store.get(Client, id)
            run_dialog(ClientDetailsDialog, self.app, store, model)

    def _dialog_work_order(self, id):
        from stoqlib.domain.workorder import WorkOrder
        from stoqlib.gui.editors.workordereditor import WorkOrderEditor

        with api.new_store() as store:
            model = store.get(WorkOrder, id)
            user = api.get_current_user(store)
            visual_mode = not user.profile.check_app_permission(u'services')
            run_dialog(WorkOrderEditor, self.app, store, model,
                       visual_mode=visual_mode)

    def _show_search_by_date(self, date, app_name):
        y, m, d = map(int, date.split('-'))
        date = localdate(y, m, d).date()
        self.app.window.hide_app(empty=True)
        shell_app = self.app.window.run_application(
            app_name, refresh=False)
        shell_app.search_for_date(date)

    def _show_in_payments_by_date(self, date):
        self._show_search_by_date(date, u'receivable')

    def _show_out_payments_by_date(self, date):
        self._show_search_by_date(date, u'payable')

    def _show_purchases_by_date(self, date):
        self._show_search_by_date(date, u'purchase')

    def _show_work_orders_by_date(self, date):
        self._show_search_by_date(date, u'services')

    def _show_client_birthdays_by_date(self, date):
        from stoqlib.gui.search.personsearch import ClientSearch

        with api.new_store() as store:
            y, m, d = map(int, date.split('-'))
            date = localdate(y, m, d).date()
            run_dialog(ClientSearch, self.app, store, birth_date=date)

    def _show_client_calls_by_date(self, date):
        from stoqlib.gui.search.callsearch import ClientCallsSearch

        store = api.new_store()
        y, m, d = map(int, date.split('-'))
        date = localdate(y, m, d).date()
        run_dialog(ClientCallsSearch, self.app, store, date=date)
        store.close()

    def _uri_run_dialog(self, result, kwargs):
        path = result.path
        if path == '/payment':
            self._dialog_payment_details(**kwargs)
        elif path == '/purchase':
            self._dialog_purchase(**kwargs)
        elif path == '/call':
            self._dialog_call(**kwargs)
        elif path == '/birthday':
            self._dialog_client(**kwargs)
        elif path == '/workorder':
            self._dialog_work_order(**kwargs)
        else:
            raise NotImplementedError(path)

    def _uri_show(self, result, kwargs):
        path = result.path
        if path == '/in-payments-by-date':
            self._show_in_payments_by_date(**kwargs)
        elif path == '/out-payments-by-date':
            self._show_out_payments_by_date(**kwargs)
        elif path == '/purchases-by-date':
            self._show_purchases_by_date(**kwargs)
        elif path == '/work-orders-by-date':
            self._show_work_orders_by_date(**kwargs)
        elif path == '/client-calls-by-date':
            self._show_client_calls_by_date(**kwargs)
        elif path == '/client-birthdays-by-date':
            self._show_client_birthdays_by_date(**kwargs)
        else:
            raise NotImplementedError(path)

    def _uri_self(self, result, kwargs):
        self.web_open_uri(kwargs)

    def _parse_stoq_uri(self, uri):
        result = urlparse.urlparse(uri)
        kwargs = {}
        for arg in result.query.split(','):
            k, v = arg.split('=', 1)
            kwargs[k] = v

        if result.hostname == 'dialog':
            self._uri_run_dialog(result, kwargs)
        elif result.hostname == 'show':
            self._uri_show(result, kwargs)
        elif result.hostname == 'self':
            self._uri_self(result, kwargs)
        else:
            raise NotImplementedError(result.hostname)

    def _policy_decision(self, uri, policy):
        if uri.startswith('file:///'):
            policy.use()
        elif uri.startswith('http://localhost'):
            policy.use()
        elif uri.startswith('stoq://'):
            policy.ignore()
            self._parse_stoq_uri(uri)
        else:
            open_browser(uri, self.get_screen())

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

    def _on_view__navigation_policy_decision_requested(self, view, frame,
                                                       request, action,
                                                       policy):
        self._policy_decision(request.props.uri, policy)

    #
    # Public API
    #

    def refresh(self):
        pass

    def get_view(self):
        return self._view

    def print_(self):
        self._view.execute_script('window.print()')

    def load_uri(self, uri):
        log.info("Loading uri: %s" % (uri, ))
        self._view.load_uri(uri)

    def load_string(self, html, mime_type='text/html',
                    encoding='utf-8'):
        log.info("Loading html: %r" % (html, ))
        self._view.load_string(html, mime_type, encoding, '')

    def js_function_call(self, function, *args):
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

    def web_open_uri(self, kwargs):
        pass


def show_html(html):
    w = gtk.Window()
    w.set_size_request(600, 400)
    wv = WebView()
    wv.load_string(html)
    w.add(wv)
    w.show_all()
