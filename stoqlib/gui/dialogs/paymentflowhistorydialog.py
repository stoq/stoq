# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2010 Async Open Source <http://www.async.com.br>
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
"""Payment Flow History Report Dialog"""

from storm.expr import And, Eq, Or

from stoqlib.database.expr import Date
from stoqlib.gui.dialogs.daterangedialog import DateRangeDialog
from stoqlib.gui.utils.printing import print_report
from stoqlib.lib.message import info
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.payment import PaymentFlowHistoryReport

_ = stoqlib_gettext

# A few comments for the payment_flow_query:
# - The first table in the FROM clause is the list of all possible dates
# (due_date and paid_date) in the results. This is done so that the subsequent
# subselect can be joined properly
# - In that same subselect, we use IS NOT NULL to avoid an empty row for
# payments that were not received yet.
# - We filter out statuses (0, 5) to not include PREVIEW and CANCELED payments
# - payment_type = 1 are OUT_PAYMENTS  and 0 are IN_PAYMENTS


payment_flow_query = """
SELECT all_payment_dates.date,
       COALESCE(payments_to_pay.count, 0) as to_pay_payments,
       COALESCE(payments_to_pay.to_pay, 0) as to_pay,
       COALESCE(payments_paid.count, 0) as paid_payments,
       COALESCE(payments_paid.paid, 0) as paid,
       COALESCE(payments_to_receive.count, 0) as to_receive_payments,
       COALESCE(payments_to_receive.to_receive, 0) as to_receive,
       COALESCE(payments_received.count, 0) as received_payments,
       COALESCE(payments_received.received, 0) as received

FROM (SELECT date(due_date) as date FROM payment
      UNION SELECT date(paid_date) as date FROM payment WHERE
      paid_date IS NOT NULL) as all_payment_dates

-- To pay (out payments)
LEFT JOIN (SELECT DATE(due_date) as date, count(1) as count, sum(value) as to_pay
           FROM payment WHERE payment_type = 'out' AND status not in ('preview', 'cancelled')
           GROUP BY DATE(due_date))
     AS payments_to_pay ON (all_payment_dates.date = payments_to_pay.date)

-- Paid (out payments)
LEFT JOIN (SELECT DATE(paid_date) as date, count(1) as count, sum(value) as paid
           FROM payment WHERE payment_type = 'out'
           AND payment.status not in ('preview', 'cancelled')
           GROUP BY DATE(paid_date))
     AS payments_paid ON (all_payment_dates.date = payments_paid.date)

-- To receive (in payments)
LEFT JOIN (SELECT DATE(due_date) as date, count(1) as count, sum(value) as to_receive
           FROM payment WHERE payment_type = 'in'
           AND payment.status not in ('preview', 'cancelled')
           GROUP BY DATE(due_date))
     AS payments_to_receive ON (all_payment_dates.date = payments_to_receive.date)

-- Received (in payments)
LEFT JOIN (SELECT DATE(paid_date) as date, count(1) as count, sum(value) as received
           FROM payment WHERE payment_type = 'in'
           AND payment.status not in ('preview', 'cancelled')
           GROUP BY DATE(paid_date))
     AS payments_received ON (all_payment_dates.date = payments_received.date)
ORDER BY all_payment_dates.date;
"""


class PaymentFlowDay(object):

    def __init__(self, store, row, previous_day=None):
        """Payment Flow History for a given date

        :param row: A list of values from the payment_flow_query above
        :param previous_day: The `previous_day <PaymentFlowDay>`. This is used
          to calculate the expected and real balances for each day (based on the
          previous dates).
        """
        (date, to_pay_count, to_pay, paid_count, paid, to_receive_count,
         to_receive, received_count, received) = row

        self.history_date = date
        # values
        self.to_pay = to_pay
        self.to_receive = to_receive
        self.paid = paid
        self.received = received
        # counts
        self.to_pay_payments = to_pay_count
        self.to_receive_payments = to_receive_count
        self.paid_payments = paid_count
        self.received_payments = received_count

        if previous_day:
            self.previous_balance = previous_day.balance_real
        else:
            self.previous_balance = 0

        # Today's balance is the previous day balance, plus the payments we
        # received, minus what we paid. expected if for the payments we should
        # have paid/received
        self.balance_expected = self.previous_balance + to_receive - to_pay
        self.balance_real = self.previous_balance + received - paid

        self.store = store

    def get_divergent_payments(self):
        """Returns a :class:`Payment` sequence that meet the following requirements:

        * The payment due date, paid date or cancel date is the current
          PaymentFlowHistory date.
        * The payment was paid/received with different values (eg with
          discount or surcharge).
        * The payment was scheduled to be paid/received on the current,
          but it was not.
        * The payment was not expected to be paid/received on the current date.
        """
        from stoqlib.domain.payment.payment import Payment
        date = self.history_date
        query = And(Or(Date(Payment.due_date) == date,
                       Date(Payment.paid_date) == date,
                       Date(Payment.cancel_date) == date),
                    Or(Eq(Payment.paid_value, None),
                       Payment.value != Payment.paid_value,
                       Eq(Payment.paid_date, None),
                       Date(Payment.due_date) != Date(Payment.paid_date)))
        return self.store.find(Payment, query)

    @classmethod
    def get_flow_history(cls, store, start, end):
        """Get the payment flow history for a given date interval

        This will return a list of PaymentFlowDay, one for each date that has
        payments registered and are in the interval specified.
        """
        history = []
        previous_entry = None

        for row in store.execute(payment_flow_query).get_all():
            entry = cls(store, row, previous_entry)
            if entry.history_date > end:
                break

            # We only store entries for dates higher than the user requested, but
            # we still need to create the entries from the beginning, so we
            # have the real balances
            if entry.history_date >= start:
                history.append(entry)
            previous_entry = entry

        return history


class PaymentFlowHistoryDialog(DateRangeDialog):
    title = _(u'Payment Flow History Dialog')
    desc = _("Select a date or a range to be visualised in the report:")
    size = (-1, -1)

    def __init__(self, store):
        """A dialog to print the PaymentFlowHistoryReport report.

        :param store: a store
        """
        self.store = store
        DateRangeDialog.__init__(self, title=self.title, header_text=self.desc)

    #
    # BasicDialog
    #

    def confirm(self):
        DateRangeDialog.confirm(self)
        start = self.retval.start
        end = self.retval.end

        results = PaymentFlowDay.get_flow_history(self.store, start, end)
        if not results:
            info(_('No payment history found.'))
            return False

        print_report(PaymentFlowHistoryReport, payment_histories=results)
        return True
