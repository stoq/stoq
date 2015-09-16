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

import datetime
import json

from twisted.web.resource import Resource

from stoqlib.api import api
from stoqlib.domain.payment.views import InPaymentView, OutPaymentView
from stoqlib.domain.person import ClientCallsView
from stoqlib.domain.purchase import PurchaseOrderView
from stoqlib.domain.views import ClientWithSalesView
from stoqlib.domain.workorder import WorkOrderView
from stoqlib.lib.translation import stoqlib_gettext, stoqlib_ngettext

_ = stoqlib_gettext


def _color_to_rgb(c, alpha):
    c = c.strip()
    if c[0] == '#':
        c = c[1:]
    if len(c) != 6:
        return '#000'
    return 'rgba(%d, %d, %d, %f)' % (
        int(c[:2], 16),
        int(c[2:4], 16),
        int(c[4:], 16), alpha)


class CalendarEvents(Resource):
    def render_GET(self, resource):
        start = datetime.date.fromtimestamp(float(resource.args['start'][0]))
        end = datetime.date.fromtimestamp(float(resource.args['end'][0]))

        store = api.new_store()
        day_events = {}
        if resource.args.get('in_payments', [''])[0] == 'true':
            self._collect_inpayments(start, end, day_events, store)
        if resource.args.get('out_payments', [''])[0] == 'true':
            self._collect_outpayments(start, end, day_events, store)
        if resource.args.get('purchase_orders', [''])[0] == 'true':
            self._collect_purchase_orders(start, end, day_events, store)
        if resource.args.get('client_calls', [''])[0] == 'true':
            self._collect_client_calls(start, end, day_events, store)
        if resource.args.get('client_birthdays', [''])[0] == 'true':
            self._collect_client_birthdays(start, end, day_events, store)
        if resource.args.get('work_orders', [''])[0] == 'true':
            self._collect_work_orders(start, end, day_events, store)

        # When grouping, events of the same type will be shown as only one, to
        # save space.
        group = resource.args.get('group', [''])[0] == 'true'
        events = self._summarize_events(day_events, group)
        store.close()
        return json.dumps(events)

    @classmethod
    def _append_event(cls, events, date, section, event):
        d = events.setdefault(
            date,
            dict(receivable=[], payable=[], purchases=[],
                 client_calls=[], client_birthdays=[], work_orders=[]))
        d[section].append(event)

    #
    #   Database Quering
    #

    def _collect_client_birthdays(self, start, end, day_events, store):
        branch = api.get_current_branch(store)
        for v in ClientWithSalesView.find_by_birth_date(
                store, (start, end), branch=branch):
            for year in xrange(start.year, end.year + 1):
                date, ev = self._create_client_birthday(v, year)
                self._append_event(day_events, date, 'client_birthdays', ev)

    def _collect_client_calls(self, start, end, day_events, store):
        for v in ClientCallsView.find_by_date(store, (start, end)):
            date, ev = self._create_client_call(v)
            self._append_event(day_events, date, 'client_calls', ev)

    def _collect_inpayments(self, start, end, day_events, store):
        for pv in InPaymentView.find_pending(store, (start, end)):
            date, ev = self._create_in_payment(pv)
            self._append_event(day_events, date, 'receivable', ev)

    def _collect_outpayments(self, start, end, day_events, store):
        for pv in OutPaymentView.find_pending(store, (start, end)):
            date, ev = self._create_out_payment(pv)
            self._append_event(day_events, date, 'payable', ev)

    def _collect_purchase_orders(self, start, end, day_events, store):
        for ov in PurchaseOrderView.find_confirmed(store, (start, end)):
            date, ev = self._create_order(ov)
            self._append_event(day_events, date, 'purchases', ev)

    def _collect_work_orders(self, start, end, day_events, store):
        for v in WorkOrderView.find_pending(store, start, end):
            date, ev = self._create_work_order(v)
            self._append_event(day_events, date, 'work_orders', ev)

    #
    #   Events creation
    #

    def _create_client_birthday(self, client_view, year):
        date = client_view.birth_date.date()
        age = year - date.year
        date = date.replace(year=year)
        title = _("{client}'s birthday: {age} years").format(
            client=client_view.name, age=age)

        return date, {"title": title,
                      "id": client_view.id,
                      "type": "client-birthday",
                      "start": str(date),
                      "url": "stoq://dialog/birthday?id=" + str(client_view.id),
                      "className": 'client_birthday'}

    def _create_client_call(self, call_view):
        date = call_view.date.date()

        return date, {"title": call_view.name,
                      "id": call_view.id,
                      "type": "client-call",
                      "start": str(date),
                      "url": "stoq://dialog/call?id=" + str(call_view.id),
                      "className": 'client_call'}

    def _create_work_order(self, wo_view):
        date = wo_view.estimated_finish.date()
        title = '%s: %s (%s)' % (
            wo_view.identifier, wo_view.equipment, wo_view.client_name)
        tooltip = '<br />'.join(['%s: %s'] * 6) % (
            _("#"), wo_view.identifier,
            _("Status"), wo_view.status_str,
            _("Equipment"), wo_view.equipment,
            _("Category"), wo_view.category_name,
            _("Client"), wo_view.client_name,
            _("Salesperson"), wo_view.salesperson_name)

        return date, {
            'title': title,
            'tooltip': tooltip,
            'id': wo_view.id,
            'type': 'work-order',
            'start': str(date),
            'url': 'stoq://dialog/workorder?id=' + str(wo_view.id),
            'className': 'work_order'}

    def _create_in_payment(self, payment_view):
        title = payment_view.description
        if payment_view.drawee:
            title = _("%s from %s") % (payment_view.description,
                                       payment_view.drawee)

        start = payment_view.due_date.date()
        className = 'receivable'
        if start < datetime.date.today():
            className += " late"

        event = dict(id=payment_view.id,
                     className=className,
                     start=str(start),
                     title=title,
                     type="in-payment",
                     url="stoq://dialog/payment?id=" + str(payment_view.id))

        if payment_view.color:
            event['backgroundColor'] = _color_to_rgb(payment_view.color, 0.1)

        return start, event

    def _create_out_payment(self, payment_view):
        supplier_name = payment_view.supplier_name

        className = "payable"
        if supplier_name:
            title = _("%s to %s") % (
                payment_view.description, supplier_name,)
        else:
            title = _("%s") % (payment_view.description)

        start = payment_view.due_date.date()
        if start < datetime.date.today():
            className += " late"

        event = dict(id=payment_view.id,
                     className=className,
                     start=str(start),
                     title=title,
                     type="out-payment",
                     url="stoq://dialog/payment?id=" + str(payment_view.id))

        if payment_view.color:
            event['backgroundColor'] = _color_to_rgb(payment_view.color, 0.1)

        return start, event

    def _create_order(self, order_view):
        title = _("Receival from %s") % (
            order_view.supplier_name)

        start = order_view.expected_receival_date.date()

        className = "purchase"
        if start < datetime.date.today():
            className += " late"

        return start, {"title": title,
                       "id": order_view.id,
                       "date": str(start),
                       "type": "purchase",
                       "url": "stoq://dialog/purchase?id=" + str(order_view.id),
                       "className": className}

    #
    #   Events summarization
    #

    def _summarize_events(self, day_events, group):
        normal_events = []
        for date, events in day_events.items():
            if group:
                summary_events = self._create_summary_events(
                    date, events)
                normal_events.extend(summary_events)
            else:
                normal_events.extend(events['receivable'])
                normal_events.extend(events['payable'])
                normal_events.extend(events['purchases'])
                normal_events.extend(events['client_calls'])
                normal_events.extend(events['client_birthdays'])
                normal_events.extend(events['work_orders'])
        return normal_events

    def _create_summary_events(self, date, events):
        in_payment_events = events['receivable']
        out_payment_events = events['payable']
        purchase_events = events['purchases']
        client_calls = events['client_calls']
        client_birthdays = events['client_birthdays']
        work_orders = events['work_orders']

        events = []

        def add_event(title, url, date, class_name, show_late=True):
            if show_late and date < datetime.date.today():
                class_name += " late"
            events.append(dict(title=title,
                               url=url,
                               start=str(date),
                               className=class_name))
        if client_calls:
            if len(client_calls) == 1:
                events.append(client_calls[0])
            else:
                title_format = stoqlib_ngettext(_("%d client call"),
                                                _("%d client calls"),
                                                len(client_calls))
                title = title_format % len(client_calls)
                class_name = "client_call"
                url = "stoq://show/client-calls-by-date?date=%s" % (date,)
                add_event(title, url, date, class_name, False)

        if client_birthdays:
            if len(client_birthdays) == 1:
                events.append(client_birthdays[0])
            else:
                title_format = stoqlib_ngettext(_("%d client birthday"),
                                                _("%d client birthdays"),
                                                len(client_birthdays))
                title = title_format % len(client_birthdays)
                class_name = "client_birthday"
                url = "stoq://show/client-birthdays-by-date?date=%s" % (date,)
                add_event(title, url, date, class_name, False)

        if work_orders:
            if len(work_orders) == 1:
                events.append(work_orders[0])
            else:
                title_format = stoqlib_ngettext(_("%d work order"),
                                                _("%d work orders"),
                                                len(work_orders))
                title = title_format % len(work_orders)
                class_name = "work_order"
                url = "stoq://show/work-orders-by-date?date=%s" % (date,)
                add_event(title, url, date, class_name, False)

        if in_payment_events:
            if len(in_payment_events) == 1:
                events.append(in_payment_events[0])
            else:
                title_format = stoqlib_ngettext(_("%d account receivable"),
                                                _("%d accounts receivable"),
                                                len(in_payment_events))
                title = title_format % len(in_payment_events)
                class_name = "receivable"
                url = "stoq://show/in-payments-by-date?date=%s" % (date, )
                add_event(title, url, date, class_name)

        if out_payment_events:
            if len(out_payment_events) == 1:
                events.append(out_payment_events[0])
            else:
                title_format = stoqlib_ngettext(_("%d account payable"),
                                                _("%d accounts payable"),
                                                len(out_payment_events))
                title = title_format % len(out_payment_events)
                class_name = "payable"
                url = "stoq://show/out-payments-by-date?date=%s" % (date, )
                add_event(title, url, date, class_name)

        if purchase_events:
            if len(purchase_events) == 1:
                events.append(purchase_events[0])
            else:
                title_format = stoqlib_ngettext(_("%d purchase"),
                                                _("%d purchases"),
                                                len(purchase_events))
                title = title_format % len(purchase_events)
                url = "stoq://show/purchases-by-date?date=%s" % (date, )
                class_name = 'purchase'
                add_event(title, url, date, class_name)

        return events
