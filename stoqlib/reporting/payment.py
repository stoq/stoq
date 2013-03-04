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

from stoqlib.reporting.report import ObjectListReport, HTMLReport
from stoqlib.lib.translation import stoqlib_gettext as _
from stoqlib.lib.formatters import get_formatted_price


class _BasePaymentReport(ObjectListReport):
    """Base report for Payable and Receivable reports"""
    title = _("Payment Report")
    main_object_name = (_("payment"), _("payments"))
    summary = ['value', 'paid_value']


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


class PaymentFlowHistoryReport(HTMLReport):
    title = _(u'Payment Flow History')
    template_filename = 'payment_flow_history/payment_flow_history.html'
    complete_header = False

    def __init__(self, filename, payment_histories):
        self.payment_histories = payment_histories
        HTMLReport.__init__(self, filename)

    def get_subtitle(self):
        return ''


class AccountTransactionReport(ObjectListReport):
    main_object_name = (_("transaction"), _("transactions"))

    def __init__(self, filename, objectlist, transactions, account, *args, **kwargs):
        self.title = _("Transactions for account %s") % (account.description, )
        ObjectListReport.__init__(self, filename, objectlist, transactions,
                                  self.title, *args, **kwargs)
