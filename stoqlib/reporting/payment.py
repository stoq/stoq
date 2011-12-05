# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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
""" Payment receival report implementation """

from decimal import Decimal

from stoqlib.reporting.base.tables import ObjectTableColumn as OTC
from stoqlib.reporting.base.flowables import RIGHT
from stoqlib.reporting.template import BaseStoqReport, ObjectListReport
from stoqlib.lib.translation import stoqlib_gettext as _
from stoqlib.lib.formatters import get_formatted_price


class _BasePaymentReport(ObjectListReport):
    """Base report for Payable and Receivable reports"""
    report_name = _("Payment Report")
    main_object_name = (_("payment"), _("payments"))

    def __init__(self, filename, objectlist, payments, *args, **kwargs):
        self._payments = payments
        ObjectListReport.__init__(self, filename, objectlist, payments,
                                  _BasePaymentReport.report_name,
                                  landscape=True, *args, **kwargs)
        self._setup_table()

    def _setup_table(self):
        total_value = sum([item.value for item in self._payments],
                          Decimal(0))
        self.add_summary_by_column(_(u'Value'),
                                   get_formatted_price(total_value))
        self.add_object_table(self._payments, self.get_columns(),
                              summary_row=self.get_summary_row())


class ReceivablePaymentReport(_BasePaymentReport):
    """
    This report shows a list of receivable payments. For each payment it shows:
    payment number, description, drawee, due date, paid date, status and value.
    """


class PayablePaymentReport(_BasePaymentReport):
    """
    This report shows a list of payable payments. For each payment it shows:
    payment number, description, supplier, due date, paid date,
    status and value.
    """


class BillCheckPaymentReport(_BasePaymentReport):
    """This report shows a list of Gpayments and some information about the
    bill or check method payment (if available) like: the bank id, the bank
    branch, the bank account. The field payment_number in the report can be
    the check number or the bill number.
    """


class CardPaymentReport(_BasePaymentReport):
    """This report shows a list of information about the card method payment.
    For each payment it show: payment number, description, drawee,
    credit provider, due date, value, fee and fee calculation."""

    def _setup_table(self):
        total_value = sum([item.value for item in self._payments],
                          Decimal(0))
        total_fee_calc = sum([item.fee_calc for item in self._payments],
                             Decimal(0))
        self.add_summary_by_column(_(u'Value'),
                                   get_formatted_price(total_value))
        self.add_summary_by_column(_(u'Fee'),
                                   get_formatted_price(total_fee_calc))
        self.add_object_table(self._payments, self.get_columns(),
                              summary_row=self.get_summary_row())


class PaymentFlowHistoryReport(BaseStoqReport):
    report_name = _(u'Payment Flow History')

    def __init__(self, filename, payment_histories, *args, **kwargs):
        self._payment_histories = payment_histories
        BaseStoqReport.__init__(self, filename,
                                PaymentFlowHistoryReport.report_name,
                                landscape=True, *args, **kwargs)
        self.add_blank_space(5)
        self._setup_payment_histories_table()

    def _setup_payment_histories_table(self):
        for payment_history in self._payment_histories:
            history_date = payment_history.history_date.strftime('%x')
            self.add_paragraph(_(u'Day: %s' % history_date), style='Title')
            self._add_history_table(payment_history)

    def _add_history_table(self, history):
        self.add_object_table([history], self._get_payment_history_columns())
        if (history.to_receive_payments != history.received_payments or
            history.to_pay_payments != history.paid_payments or
            history.to_receive != history.received or
            history.to_pay != history.to_pay):
            payments = list(history.get_divergent_payments())
            if payments:
                self.add_object_table(payments, self._get_payment_columns())
        self.add_blank_space(10)

    def _get_payment_history_columns(self):
        return [
            OTC(_(u'Last balance'), lambda obj:
                '%s' % get_formatted_price(obj.get_last_day_real_balance()),
                align=RIGHT),
            OTC(_(u'To receive'), lambda obj:
                    '%s' % get_formatted_price(obj.to_receive), align=RIGHT),
            OTC(_(u'To pay'), lambda obj:
                    '%s' % get_formatted_price(obj.to_pay), align=RIGHT),
            OTC(_(u'Received'), lambda obj:
                    '%s' % get_formatted_price(obj.received), align=RIGHT),
            OTC(_(u'Paid'), lambda obj: '%s' % get_formatted_price(obj.paid),
                align=RIGHT),
            OTC(_(u'Bal. expected'), lambda obj:
                    '%s' % get_formatted_price(obj.balance_expected),
                    align=RIGHT),
            OTC(_(u'Bal. real'), lambda obj:
                    '%s' % get_formatted_price(obj.balance_real), align=RIGHT)]

    def _get_payment_columns(self):
        return [
            OTC(_(u'# '), lambda obj: '%04d' % obj.id, width=45),
            OTC(_(u'Status'), lambda obj: '%s' % obj.get_status_str(),
                width=75),
            OTC(_(u'Description'), lambda obj: '%s' % obj.description,
                expand=True, truncate=True),
            OTC(_(u'Value'), lambda obj:
                                '%s' % get_formatted_price(obj.value),
                                align=RIGHT, width=120),
            OTC(_(u'Paid/Received'), lambda obj:
                    '%s' % get_formatted_price(obj.paid_value or Decimal(0)),
                    align=RIGHT, width=120),
            OTC(_(u'Due date'), lambda obj:
                    '%s' % obj.due_date.strftime('%x'), width=80),
            OTC(_(u'Paid date'), lambda obj:
                    '%s' % obj.get_paid_date_string(), width=80),
        ]

    def get_title(self):
        return self.report_name


class AccountTransactionReport(ObjectListReport):
    report_name = _("Transaction Report")
    main_object_name = (_("transaction"), _("transactions"))

    def __init__(self, filename, objectlist, transactions, account, *args, **kwargs):
        self._transactions = transactions
        self._account = account
        ObjectListReport.__init__(self, filename, objectlist, transactions,
                                  self.report_name,
                                  landscape=True, *args, **kwargs)
        self._setup_table()

    def _setup_table(self):
        total_value = sum([item.value for item in self._transactions],
                          Decimal(0))
        self.add_summary_by_column(_(u'Value'),
                                   get_formatted_price(total_value))
        self.add_object_table(self._transactions, self.get_columns(),
                              summary_row=self.get_summary_row())

    def get_title(self):
        return _("Transactions for account %s") % (self._account.description, )
