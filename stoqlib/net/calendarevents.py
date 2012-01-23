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
from stoqlib.database.orm import AND
from stoqlib.domain.purchase import PurchaseOrderView
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.payment.views import InPaymentView
from stoqlib.domain.payment.views import OutPaymentView
from stoqlib.lib.translation import stoqlib_gettext, stoqlib_ngettext

_ = stoqlib_gettext


class CalendarEvents(Resource):
    def render_GET(self, resource):
        start = datetime.datetime.fromtimestamp(
            float(resource.args['start'][0]))
        end = datetime.datetime.fromtimestamp(
            float(resource.args['end'][0]))

        print resource.args
        trans = api.new_transaction()
        day_events = {}
        if resource.args.get('in_payments', [''])[0] == 'true':
            self._collect_inpayments(start, end, day_events, trans)
        if resource.args.get('out_payments', [''])[0] == 'true':
            self._collect_outpayments(start, end, day_events, trans)
        if resource.args.get('purchase_orders', [''])[0] == 'true':
            self._collect_purchase_orders(start, end, day_events, trans)

        group = resource.args.get('group', [''])[0] == 'true'
        events = self._summarize_events(day_events, group)
        trans.close()
        return json.dumps(events)

    def _collect_inpayments(self, start, end, day_events, trans):
        query = AND(InPaymentView.q.status == Payment.STATUS_PENDING,
                    InPaymentView.q.due_date >= start,
                    InPaymentView.q.due_date <= end)
        for pv in InPaymentView.select(query, connection=trans):
            date, ev = self._create_in_payment(pv)
            d = day_events.setdefault(date, dict(receivable=[],
                                        payable=[], purchases=[]))
            d['receivable'].append(ev)

    def _collect_outpayments(self, start, end, day_events, trans):
        query = AND(OutPaymentView.q.status == Payment.STATUS_PENDING,
                    OutPaymentView.q.due_date >= start,
                    OutPaymentView.q.due_date <= end)
        for pv in OutPaymentView.select(query, connection=trans):
            date, ev = self._create_out_payment(pv)
            d = day_events.setdefault(date, dict(receivable=[],
                                        payable=[], purchases=[]))
            d['payable'].append(ev)

    def _collect_purchase_orders(self, start, end, day_events, trans):
        query = AND(PurchaseOrderView.q.expected_receival_date >= start,
                    PurchaseOrderView.q.expected_receival_date <= end),
        for ov in PurchaseOrderView.select(query, connection=trans):
            date, ev = self._create_order(ov)
            d = day_events.setdefault(date, dict(receivable=[],
                                        payable=[], purchases=[]))
            d['purchases'].append(ev)

    def _create_in_payment(self, payment_view):
        title = payment_view.description
        if payment_view.drawee:
            title = _("%s from %s") % (payment_view.description,
                                       payment_view.drawee)

        start = payment_view.due_date.date()
        className = 'receivable'
        if start < datetime.date.today():
            className += " late"

        return start, {"title": title,
                "id": payment_view.id,
                "type": "in-payment",
                "start": str(start),
                "url": "stoq://dialog/payment?id=" + str(payment_view.id),
                "className": className}

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

        return start, {"title": title,
                "id": payment_view.id,
                "type": "out-payment",
                "start": str(start),
                "url": "stoq://dialog/payment?id=" + str(payment_view.id),
                "className": className}

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
        return normal_events

    def _create_summary_events(self, date, events):
        in_payment_events = events['receivable']
        out_payment_events = events['payable']
        purchase_events = events['purchases']

        events = []

        def add_event(title, url, date, class_name):
            if date < datetime.date.today():
                class_name += " late"
            events.append(dict(title=title,
                               url=url,
                               start=str(date),
                               className=class_name))
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
