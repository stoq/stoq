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
##  Author(s):  Fabio Morbec              <fabio@async.com.br>
##
##
""" Payment receival report implementation """

from decimal import Decimal

from stoqlib.reporting.template import SearchResultsReport
from stoqlib.reporting.base.flowables import RIGHT
from stoqlib.reporting.base.tables import ObjectTableColumn as OTC
from stoqlib.lib.translation import stoqlib_gettext as _
from stoqlib.lib.validators import get_formatted_price

class _BasePaymentReport(SearchResultsReport):
    """Base report for Payable and Receivable reports"""
    report_name = _("Payment Report")
    main_object_name = "payments"

    def __init__(self, filename, payments, *args, **kwargs):
        self._payments = payments
        SearchResultsReport.__init__(self, filename, payments,
                                     _BasePaymentReport.report_name,
                                     landscape=True, *args, **kwargs)
        self._setup_table()

    def _setup_table(self):
        total_value = sum([item.value for item in self._payments],
                          Decimal(0))
        summary_row = ["", "", "", "", "", _("Total:"),
                       get_formatted_price(total_value)]
        self.add_object_table(self._payments, self.get_columns(), width=745,
                              summary_row=summary_row)


class ReceivablePaymentReport(_BasePaymentReport):
    """
    This report shows a list of receivable payments. For each payment it shows:
    payment number, description, drawee, due date, paid date, status and value.
    """

    def get_columns(self):
        return [OTC(_("Number"),
                    lambda obj: obj.id, width=60),
                OTC(_("Description"),
                    lambda obj: obj.description, width=150),
                OTC(_("Drawee"),
                    lambda obj: obj.drawee, width=50,
                    expand=True, expand_factor=1),
                OTC(_("Due date"),
                    lambda obj: format_date(obj.due_date), width=80),
                OTC(_("Paid date"),
                    lambda obj: format_date(obj.paid_date), width=80),
                OTC(_("Status"),
                    lambda obj: obj.get_status_str(), width=50),
                OTC(_("Value"),
                    lambda obj: get_formatted_price(obj.value), width=100,
                    align=RIGHT)
            ]


class PayablePaymentReport(_BasePaymentReport):
    """
    This report shows a list of payable payments. For each payment it shows:
    payment number, description, supplier, due date, paid date,
    status and value.
    """

    def get_columns(self):
        return [OTC(_("Number"),
                    lambda obj: obj.id, width=60),
                OTC(_("Description"),
                    lambda obj: obj.description, width=150),
                OTC(_("Supplier"),
                    lambda obj: obj.supplier_name, width=50,
                    expand=True, expand_factor=1),
                OTC(_("Due date"),
                    lambda obj: format_date(obj.payment.due_date), width=80),
                OTC(_("Paid date"),
                    lambda obj: format_date(obj.payment.paid_date), width=80),
                OTC(_("Status"),
                    lambda obj: obj.get_status_str(), width=50),
                OTC(_("Value"),
                    lambda obj: get_formatted_price(obj.value), width=100,
                    align=RIGHT)
            ]


def format_date(date):
    # we need to format date because an error is raised when date is None
    if date is not None:
        return date.strftime("%x")
    return ""
