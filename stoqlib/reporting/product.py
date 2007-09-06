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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
##  Author(s):  Henrique Romano         <henrique@async.com.br>
##              Evandro Miquelito       <evandro@async.com.br>
##              Fabio Morbec            <fabio@async.com.br>
##
##
""" Products report implementation """

from decimal import Decimal

from stoqlib.reporting.template import SearchResultsReport
from stoqlib.reporting.base.tables import ObjectTableColumn as OTC
from stoqlib.reporting.base.flowables import RIGHT
from stoqlib.lib.validators import format_quantity
from stoqlib.lib.translation import stoqlib_gettext as _
from stoqlib.domain.product import ProductHistory
from stoqlib.domain.views import SellableFullStockView

class ProductReport(SearchResultsReport):
    """ This report show a list of all products returned by a SearchBar,
    listing both its description and its balance in the stock selected.
    """
    # This should be properly verified on SearchResultsReport. Waiting for
    # bug 2517
    obj_type = SellableFullStockView
    report_name = _("Product Listing")
    main_object_name = _("products")
    filter_format_string = _("on branch <u>%s</u>")

    def __init__(self, filename, products, *args, **kwargs):
        self._products = products
        SearchResultsReport.__init__(self, filename, products,
                                     ProductReport.report_name,
                                     landscape=True,
                                     *args, **kwargs)
        self._setup_items_table()

    def _get_columns(self):
        return [
            OTC(_("Code"), lambda obj: '%03d' % obj.id, width=120,
                truncate=True),
            OTC(_("Description"), lambda obj: obj.description, truncate=True),
            OTC(_("Quantity"),
                lambda obj: format_quantity(obj.stock or 0), width=80,
                align=RIGHT, truncate=True),
            # FIXME: This column should be virtual, waiting for bug #2764
            OTC(_("Unit"), lambda obj: obj.unit, width=60, virtual=False),
            ]

    def _setup_items_table(self):
        total_qty = sum([item.stock or 0 for item in self._products],
                        Decimal(0))
        summary_row = ["", "", _("Total:"), format_quantity(total_qty), ""]
        self.add_object_table(self._products, self._get_columns(),
                              summary_row=summary_row)


def format_data(data):
    # must return zero or relatory show None instead of 0
    if data is None:
        return 0
    return format_quantity(data)


class ProductQuantityReport(SearchResultsReport):
    """ This report show a list of all products returned by a SearchBar,
    listing both its description, quantity solded and quantity received.
    """
    # This should be properly verified on SearchResultsReport. Waiting for
    # bug 2517
    obj_type = ProductHistory
    report_name = _("Product Listing")
    main_object_name = _("products")

    def __init__(self, filename, products, *args, **kwargs):
        self._products = products
        SearchResultsReport.__init__(self, filename, products,
                                     ProductReport.report_name,
                                     landscape=True,
                                     *args, **kwargs)
        self._setup_items_table()

    def _get_columns(self):
        return [
            OTC(_("Code"), lambda obj: '%03d' % obj.id, width=120,
                truncate=True),
            OTC(_("Description"), lambda obj: obj.description, truncate=True),
            OTC(_("Quantity Sold"), lambda obj:
                format_data(obj.quantity_sold), width=110,
                align=RIGHT, truncate=True),
            OTC(_("Quantity Transfered"), lambda obj:
                format_data(obj.quantity_transfered), width=110,
                align=RIGHT, truncate=True),
            OTC(_("Quantity Received"), lambda obj:
                format_data(obj.quantity_received), width=120,
                align=RIGHT, truncate=True)
            ]

    def _setup_items_table(self):
        qty_sold = qty_received = qty_transfered = 0
        for item in self._products:
            qty_sold += item.quantity_sold or Decimal(0)
            qty_received += item.quantity_received or Decimal(0)
            qty_transfered += item.quantity_transfered or Decimal(0)

        summary_row = ["", _("Total:"), format_data(qty_sold),
                       format_data(qty_transfered),
                       format_data(qty_received)]
        self.add_object_table(self._products, self._get_columns(),
                              summary_row=summary_row)
