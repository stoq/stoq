# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2007 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
""" Till report implementation """
import collections

from storm.expr import And, Eq

from stoqlib.api import api
from stoqlib.database.expr import Date
from stoqlib.domain.sale import Sale
from stoqlib.domain.payment.card import CreditCardData
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.payment.views import InPaymentView, OutPaymentView
from stoqlib.domain.till import TillEntry
from stoqlib.lib.translation import stoqlib_gettext as _
from stoqlib.reporting.report import ObjectListReport, HTMLReport

N_ = _


class TillHistoryReport(ObjectListReport):
    """This report show a list of the till history returned by a SearchBar,
    listing both its description, date and value.
    """
    title = _("Till History Listing")
    main_object_name = (_("till entry"), _("till entries"))
    summary = ['value']


class TillDailyMovementReport(HTMLReport):
    """This report shows all the financial transactions on till
    """
    template_filename = 'till/till.html'
    title = _('Daily Movement')
    complete_header = False

    def __init__(self, filename, store, start_date, end_date=None):
        self.start_date = start_date
        self.end_date = end_date
        self.branch = api.get_current_branch(store)

        query = And(Payment.status == Payment.STATUS_PAID,
                    Payment.branch_id == self.branch.id,
                    self._get_date_interval_query(Payment.paid_date))

        # Keys are the sale objects, and values are lists with all payments
        self.sales = collections.OrderedDict()

        # Keys are the returned sale objects, and values are lists with all payments
        self.return_sales = collections.OrderedDict()
        self.purchases = collections.OrderedDict()

        # lonely input and output payments
        self.lonely_in_payments = []
        self.lonely_out_payments = []

        # values are lists with the first element the summary of the input, and
        # the second the summary of the output
        method_summary = {}
        self.card_summary = {}

        for p in store.find(InPaymentView, query).order_by(Sale.identifier, Payment.identifier):
            if p.sale:
                if p.sale.status == Sale.STATUS_RETURNED:
                    continue
                sale_payments = self.sales.setdefault(p.sale, {})
                details = ''
                method_desc = p.method.get_description()
                if p.card_data:
                    if p.card_data.card_type == CreditCardData.TYPE_DEBIT:
                        method_desc += ' ' + _('Debit')
                    else:
                        method_desc += ' ' + _(u'Credit')
                    details = '%s - %s - %s' % (p.card_data.auth,
                                                p.card_data.provider.short_name or '',
                                                p.card_data.device.description or '')

                key = (method_desc, details)
                item = sale_payments.setdefault(key, [0, 0])
                item[0] += p.value
                item[1] += 1

            else:
                self.lonely_in_payments.append(p)

            method_summary.setdefault(p.method, [0, 0])
            method_summary[p.method][0] += p.value
            if p.card_data:
                type_desc = p.card_data.short_desc[p.card_data.card_type]
                key = (p.card_data.provider.short_name, type_desc)
                self.card_summary.setdefault(key, 0)
                self.card_summary[key] += p.value

        for p in store.find(OutPaymentView, query).order_by(Payment.identifier):
            if p.purchase:
                purchase_payments = self.purchases.setdefault(p.purchase, [])
                purchase_payments.append(p)
            elif p.sale:
                return_sales_payment = self.return_sales.setdefault(p.sale, [])
                return_sales_payment.append(p)
            else:
                self.lonely_out_payments.append(p)

            method_summary.setdefault(p.method, [0, 0])
            method_summary[p.method][1] += p.value

        self.method_summary = []
        for method, (in_value, out_value) in method_summary.items():
            self.method_summary.append((N_(method.description),
                                        in_value,
                                        out_value))
        self.method_summary.sort()

        # Till removals
        query = And(Eq(TillEntry.payment_id, None),
                    TillEntry.branch_id == self.branch.id,
                    self._get_date_interval_query(TillEntry.date),
                    TillEntry.value < 0)
        self.till_removals = store.find(TillEntry, query)

        # Till supply
        query = And(Eq(TillEntry.payment_id, None),
                    TillEntry.branch_id == self.branch.id,
                    self._get_date_interval_query(TillEntry.date),
                    TillEntry.value > 0)
        self.till_supplies = store.find(TillEntry, query)

        HTMLReport.__init__(self, filename)

    #
    #  HTMLReport
    #

    def get_subtitle(self):
        """Returns a subtitle text
        """
        if self.end_date:
            return _('Till movement on %s to %s') % (self.start_date,
                                                     self.end_date)
        return _('Till movement on %s') % self.start_date

    def has_in_payments(self):
        return bool(self.sales or self.lonely_in_payments)

    def has_out_payments(self):
        return bool(self.purchases or self.lonely_out_payments or self.return_sales)

    def has_till_entries(self):
        return bool(self.till_supplies or self.till_removals)

    #
    #  Private
    #

    def _get_date_interval_query(self, attr):
        if self.end_date is None:
            return Date(attr) == Date(self.start_date)
        return And(Date(attr) >= Date(self.start_date),
                   Date(attr) <= Date(self.end_date))
