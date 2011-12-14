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
from twisted.web.static import File
from kiwi.environ import environ

from stoqlib.api import api
from stoqlib.database.orm import AND, OR
from stoqlib.domain.payment.views import InPaymentView
from stoqlib.domain.payment.views import OutPaymentView
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class CalendarEvents(Resource):
    def render_GET(self, resource):
        start = datetime.datetime.fromtimestamp(
            float(resource.args['start'][0]))
        end = datetime.datetime.fromtimestamp(
            float(resource.args['end'][0]))
        trans = api.new_transaction()
        events = []
        for pv in InPaymentView.select(
            OR(AND(InPaymentView.q.paid_date >= start,
                   InPaymentView.q.paid_date <= end),
               AND(InPaymentView.q.due_date >= start,
                   InPaymentView.q.due_date <= end)),
            connection=trans):
            self._create_in_payment(pv, events)
        for pv in OutPaymentView.select(
            OR(AND(OutPaymentView.q.paid_date >= start,
                   OutPaymentView.q.paid_date <= end),
               AND(OutPaymentView.q.due_date >= start,
                   OutPaymentView.q.due_date <= end)),
            connection=trans):
            self._create_out_payment(pv, events)
        events = self._summarize_events(events)
        return json.dumps(events)

    def _create_in_payment(self, payment_view, events):
        payment = payment_view.payment
        className = "in-payment"
        if payment.is_paid() or payment.status == payment.STATUS_CONFIRMED:
            if payment_view.drawee:
                title = _("Payment (%s) from %s was received") % (
                    payment.paid_value,
                    payment_view.drawee,)
            else:
                title = _("Payment (%s) was received") % (payment.paid_value, )
            start = payment.paid_date
            className = "in-payment-paid"
        elif payment.is_pending():
            if payment_view.drawee:
                title = _("Payment (%s) from %s is due") % (
                    payment.value,
                    payment_view.drawee,)
            else:
                title = _("Payment (%s) due") % (payment.value, )
            start = payment.due_date
            if start < datetime.datetime.today():
                className = "in-payment-late"
            else:
                className = "in-payment-due"
        elif payment.is_cancelled():
            return
        else:
            # FIXME: bug?
            return
        events.append({"title": title,
                       "id": payment.id,
                       "type": "in-payment",
                       "start": start,
                       "url": "dialog://payment?id=" + str(payment.id),
                       "className": className})

    def _create_out_payment(self, payment_view, events):
        payment = payment_view.payment
        supplier_name = payment_view.supplier_name
        className = "out-payment"

        if payment.is_paid() or payment.status == payment.STATUS_CONFIRMED:
            if supplier_name:
                title = _("%s (%s) to %s was paid") % (
                    payment.description,
                    payment.value, supplier_name,)
            else:
                title = _("%s (%s) was paid") % (payment.description,
                                                 payment.value, )
            start = payment.paid_date
            className = "out-payment-paid"
        elif payment.is_pending():
            if supplier_name:
                title = _("%s (%s) to %s is due") % (
                    payment.description,
                    payment.value, supplier_name,)
            else:
                title = _("%s (%s) due") % (
                    payment.description, payment.value, )
            start = payment.due_date
            if start < datetime.datetime.today():
                className = "out-payment-late"
            else:
                className = "out-payment-due"
        elif payment.is_cancelled():
            return
        else:
            # FIXME: bug?
            return

        events.append({"title": title,
                       "id": payment.id,
                       "type": "out-payment",
                       "start": start,
                       "url": "dialog://payment?id=" + str(payment.id),
                       "className": className})

    def _summarize_events(self, events):
        perDay = {}
        # summarize per day
        for event in events:
            start = str(event["start"].date())
            event["start"] = start
            if start in perDay:
                perDay[start].append(event)
            else:
                perDay[start] = [event]

        # Display max 2 per days, and create a new summary event
        # for the remaning
        normal_events = []
        for date, date_events in perDay.items():
            normal_events.extend(date_events[:2])
            if len(date_events) > 2:
                summary_events = self._create_summary_events(
                    date, date_events[2:])
                normal_events.extend(summary_events)
        return normal_events

    def _create_summary_events(self, date, events):
        assert type(date) == str, type(date)
        in_payment_events = [e for e in events if e["type"] == "in-payment"]
        out_payment_events = [e for e in events if e["type"] == "out-payment"]
        events = []
        if in_payment_events:
            title = _("%d+ accounts receivable") % (len(in_payment_events), )
            url = "dialog://in-payment-list?ids=%s" % (
                "|".join([str(e["id"]) for e in in_payment_events]), )
            events.append(dict(title=title,
                               url=url,
                               start=date,
                               className="summarize"))
        if out_payment_events:
            title = _("%d+ accounts payable") % (len(out_payment_events), )
            url = "dialog://out-payment-list?date=%s" % (date, )
            events.append(dict(title=title,
                               url=url,
                               start=date,
                               className="summarize"))
        return events


class WebResource(Resource):

    def __init__(self):
        Resource.__init__(self)
        path = environ.get_resource_paths('html')[0]
        self.putChild('static', File(path))
        self.putChild('calendar-events.json', CalendarEvents())
