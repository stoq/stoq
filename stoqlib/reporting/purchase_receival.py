# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
##  Author(s):  Henrique Romano         <henrique@async.com.br>
##
##
""" Purchase receival report implementation """

import decimal

from stoqlib.reporting.template import SearchResultsReport
from stoqlib.reporting.base.tables import ObjectTableColumn as OTC
from stoqlib.lib.translation import stoqlib_gettext as _
from stoqlib.lib.validators import get_formatted_price

class PurchaseReceivalReport(SearchResultsReport):
    report_name = _("Purchase Receival Report")
    main_object_name = _("purchase receivals")

    def __init__(self, filename, data, *args, **kwargs):
        self._data = data
        SearchResultsReport.__init__(self, filename, data,
                                     PurchaseReceivalReport.report_name,
                                     landscape=True, *args, **kwargs)
        self._setup_table()

    def get_columns(self):
        return [OTC(_("Received Date"),
                    lambda obj: obj.receival_date.strftime("%x"), width=80),
                OTC(_("Purchase Order"), lambda obj:  obj.get_order_number(),
                    width=90, truncate=True),
                OTC(_("Supplier"), lambda obj: obj.get_supplier_name(),
                    width=190, truncate=True, expand=True, expand_factor=1),
                OTC(_("Branch"), lambda obj: obj.get_branch_name(),
                    width=190, truncate=True, expand=True, expand_factor=1),
                OTC(_("Invoice #"), lambda obj: obj.invoice_number, width=80),
                OTC(_("Invoice Total"),
                    lambda obj: get_formatted_price(obj.invoice_total),
                    width=100)
                ]

    def _setup_table(self):
        total_value = sum([item.invoice_total for item in self._data],
                          decimal.Decimal("0.0"))
        summary_row = ["", "", "", "", _("Total:"),
                       get_formatted_price(total_value)]
        self.add_object_table(self._data, self.get_columns(), width=745,
                              summary_row=summary_row)
