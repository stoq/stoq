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
""" Products report implementation """

import decimal

from stoqlib.reporting.template import SearchResultsReport
from stoqlib.reporting.template import BaseStoqReport
from stoqlib.reporting.base.tables import ObjectTableColumn as OTC
from stoqlib.reporting.base.flowables import RIGHT
from stoqlib.lib.defaults import ALL_ITEMS_INDEX
from stoqlib.lib.validators import format_quantity
from stoqlib.lib.translation import stoqlib_gettext as _
from stoqlib.domain.interfaces import IStorable

class ProductReport(SearchResultsReport):
    """ This report show a list of all products returned by a SearchBar,
    listing both its description and its balance in the stock selected.
    """
    report_name = _("Product Listing")
    main_object_name = _("products")
    filter_format_string = _("on branch <u>%s</u>")

    def __init__(self, filename, products, status=None, *args, **kwargs):
        self._products = products
        if status is None or status == ALL_ITEMS_INDEX:
            self._branch = None
        else:
            self._branch = status
        SearchResultsReport.__init__(self, filename, products,
                                     ProductReport.report_name,
                                     landscape=True,
                                     *args, **kwargs)
        self._setup_items_table()

    def _get_stock_balance(self, item):
        storable = IStorable(item.get_adapted(), item.get_connection())
        return storable.get_full_balance(self._branch)

    def _get_columns(self):
        return [OTC(_("Code"), lambda obj: obj.code, width=120, truncate=True),
                OTC(_("Description"), lambda obj: obj.get_description(),
                    width=265, expand=True, expand_factor=1, truncate=True),
                OTC(_("Supplier"),
                    lambda obj: obj.get_adapted().get_main_supplier_name(),
                    width=265, expand=True, expand_factor=1, truncate=True),
                OTC(_("Quantity"), lambda obj: format_quantity(
                                                 self._get_stock_balance(obj)),
                    width=60, align=RIGHT, truncate=True),
                OTC(_("Unit"), lambda obj: obj.get_unit_description(),
                    width=30, virtual=True)
                ]

    def _setup_items_table(self):
        total_qty = sum([self._get_stock_balance(item)
                             for item in self._products],
                        decimal.Decimal("0.0"))
        summary_row = ["", "", _("Total:"), format_quantity(total_qty), ""]
        self.add_object_table(self._products, self._get_columns(),
                              width=740, summary_row=summary_row)
