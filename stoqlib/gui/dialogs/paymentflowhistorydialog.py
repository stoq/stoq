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


import gtk
from kiwi.ui.search import (DateSearchFilter, Today, Yesterday, LastWeek,
                            LastMonth)

from stoqlib.database.orm import const, AND, OR
from stoqlib.gui.base.dialogs import BasicDialog
from stoqlib.gui.printing import print_report
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
           FROM payment WHERE payment_type = 1 AND status not in (0, 5)
           GROUP BY DATE(due_date))
     AS payments_to_pay ON (all_payment_dates.date = payments_to_pay.date)

-- Paid (out payments)
LEFT JOIN (SELECT DATE(paid_date) as date, count(1) as count, sum(value) as paid
           FROM payment WHERE payment_type = 1 AND payment.status not in (0, 5)
           GROUP BY DATE(paid_date))
     AS payments_paid ON (all_payment_dates.date = payments_paid.date)

-- To receive (in payments)
LEFT JOIN (SELECT DATE(due_date) as date, count(1) as count, sum(value) as to_receive
           FROM payment WHERE payment_type = 0 AND payment.status not in (0, 5)
           GROUP BY DATE(due_date))
     AS payments_to_receive ON (all_payment_dates.date = payments_to_receive.date)

-- Received (in payments)
LEFT JOIN (SELECT DATE(paid_date) as date, count(1) as count, sum(value) as received
           FROM payment WHERE payment_type = 0 AND payment.status not in (0, 5)
           GROUP BY DATE(paid_date))
     AS payments_received ON (all_payment_dates.date = payments_received.date)
ORDER BY all_payment_dates.date;
"""


class PaymentFlowDay(object):

    def __init__(self, connection, row, previous_day=None):
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

        self.connection = connection

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
        query = AND(OR(const.DATE(Payment.q.due_date) == date,
                       const.DATE(Payment.q.paid_date) == date,
                       const.DATE(Payment.q.cancel_date) == date),
                    OR(Payment.q.paid_value == None,
                       Payment.q.value != Payment.q.paid_value,
                       Payment.q.paid_date == None,
                       const.DATE(Payment.q.due_date) != const.DATE(Payment.q.paid_date)))
        return Payment.select(query, connection=self.connection)

    @classmethod
    def get_flow_history(cls, trans, start, end):
        """Get the payment flow history for a given date interval

        This will return a list of PaymentFlowDay, one for each date that has
        payments registered and are in the interval specified.
        """
        history = []
        previous_entry = None

        for row in trans.queryAll(payment_flow_query):
            entry = cls(trans, row, previous_entry)
            if entry.history_date > end:
                break

            # We only store entries for dates higher than the user requested, but
            # we still need to create the entries from the beginning, so we
            # have the real balances
            if entry.history_date >= start:
                history.append(entry)
            previous_entry = entry

        return history


class PaymentFlowHistoryDialog(BasicDialog):
    title = _(u'Payment Flow History Dialog')
    desc = _("Select a date or a range to be visualised in the report:")
    size = (-1, -1)
    model_type = PaymentFlowDay

    def __init__(self, conn):
        """A dialog to print the PaymentFlowHistoryReport report.

        :param conn: a database connection
        """
        self.conn = conn
        BasicDialog.__init__(self, header_text='<b>%s</b>' % self.desc,
                             title=self.title)
        self._setup_widgets()

    #
    # BasicDialog
    #

    def confirm(self):
        state = self._date_filter.get_state()
        from kiwi.db.query import DateQueryState
        if isinstance(state, DateQueryState):
            start, end = state.date, state.date
        else:
            start, end = state.start, state.end

        results = PaymentFlowDay.get_flow_history(self.conn, start, end)
        if not results:
            info(_('No payment history found.'))
            return False

        print_report(PaymentFlowHistoryReport, payment_histories=results)
        return True

    #
    # Private
    #

    def _setup_widgets(self):
        self.ok_button.set_label(gtk.STOCK_PRINT)

        self._date_filter = DateSearchFilter(_(u'Date:'))
        #FIXME: add a remove_option method in DateSearchFilter.
        self._date_filter.clear_options()
        self._date_filter.add_custom_options()
        for option in [Today, Yesterday, LastWeek, LastMonth]:
            self._date_filter.add_option(option)
        self._date_filter.select(position=0)

        self.vbox.pack_start(self._date_filter, False, False)
        self._date_filter.show_all()
