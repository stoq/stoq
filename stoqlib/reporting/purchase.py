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
""" Purchase report implementation """

from kiwi.datatypes import currency

from stoqlib.reporting.base.tables import ObjectTableColumn as OTC
from stoqlib.reporting.base.flowables import RIGHT
from stoqlib.lib.validators import get_formatted_price
from stoqlib.lib.defaults import ALL_ITEMS_INDEX
from stoqlib.reporting.template import SearchResultsReport
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.domain.purchase import PurchaseOrder

_ = stoqlib_gettext

class PurchaseReport(SearchResultsReport):
    report_name = _("Purchase Order Report")
    main_object_name = _("orders")

    def __init__(self, filename, purchases, status, *args, **kwargs):
        if status:
            self._landscape_mode = status == ALL_ITEMS_INDEX
        self._purchases = purchases
        SearchResultsReport.__init__(self, filename, purchases,
                                     PurchaseReport.report_name,
                                     landscape=self._landscape_mode,
                                     *args, **kwargs)
        self._setup_table()

    def _get_columns(self):
        # XXX Bug #2430 will improve this part
        person_col_width = 180
        if self._landscape_mode:
            person_col_width += 169
        columns = [OTC(_("Number"), lambda obj: obj.get_order_number_str(),
                       width=60, align=RIGHT),
                   OTC(_("Date"), lambda obj: obj.get_open_date_as_string(),
                       width=70),
                   OTC(_("Supplier"), lambda obj: obj.get_supplier_name(),
                       width=person_col_width, truncate=True),
                   OTC(_("Ordered"),
                       lambda obj: get_formatted_price(obj.get_purchase_total()),
                       width=85, align=RIGHT),
                   OTC(_("Received"),
                       lambda obj: get_formatted_price(obj.get_received_total()),
                       width=85, align=RIGHT)]
        if self._landscape_mode:
            columns.insert(-2, OTC(_("Status"),
                                   lambda obj: obj.get_status_str(), width=80))
        return columns

    def _setup_table(self):
        totals = [(purchase.get_purchase_total(), purchase.get_received_total())
                      for purchase in self._purchases]
        ordered, received = zip(*totals)
        total_ordered, total_received = (sum(ordered, currency(0)),
                                         sum(received,currency(0)))
        summary_row = ["", "", _("Totals:"), get_formatted_price(total_ordered),
                       get_formatted_price(total_received)]
        if self._landscape_mode:
            summary_row.insert(0, "")
        self.add_object_table(self._purchases, self._get_columns(),
                              summary_row=summary_row)

