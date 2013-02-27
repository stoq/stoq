# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2008 Async Open Source <http://www.async.com.br>
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
""" Products report implementation """

from stoqlib.reporting.template import SearchResultsReport, PriceReport
from stoqlib.reporting.report import ObjectListReport
from stoqlib.reporting.base.tables import ObjectTableColumn as OTC
from stoqlib.lib.formatters import format_quantity
from stoqlib.lib.translation import stoqlib_gettext as _


class ProductReport(ObjectListReport):
    """ This report show a list of all products returned by a SearchBar,
    listing both its description and its balance in the stock selected.
    """
    title = _("Product Listing")
    filter_format_string = _("on branch <u>%s</u>")


class SimpleProductReport(ObjectListReport):
    title = _("Product Listing")
    filter_format_string = _("on branch <u>%s</u>")
    summary = ['stock']


class ProductPriceReport(PriceReport):
    """ This report show a list of all products returned by a SearchBar,
    listing both its description and price in the selected stock.
    """
    report_name = _("Product Listing")
    filter_format_string = _("on branch <u>%s</u>")

    def __init__(self, filename, products, *args, **kwargs):
        branch_name = kwargs['branch_name']
        self.main_object_name = (_("product from branch %s") % branch_name,
                                 _("products from branch %s") % branch_name)
        PriceReport.__init__(self, filename, products, *args, **kwargs)


class ProductQuantityReport(ObjectListReport):
    """ This report show a list of all products returned by a SearchBar,
    listing both its description, quantity solded and quantity received.
    """
    title = _("Product Listing")
    main_object_name = (_("product"), _("products"))
    summary = ['quantity_sold', 'quantity_received', 'quantity_transfered',
               'quantity_produced', 'quantity_lost', 'quantity_consumed']


class ProductsSoldReport(ObjectListReport):
    """ This report lists all products sold with the average stock cost for
    a given period of time.
    """
    title = _("Products Sold Listing")
    main_object_name = (_("product sold"), _("products sold"))


class ProductCountingReport(SearchResultsReport):
    """This report shows a list of all products returned by a Searchbar
    and it leaves several fields in blank, like quantity, partial value
    and total value. These fields must be filled out in the counting
    process, manually.
    """
    title = _("Product Counting")
    main_object_name = (_("product"), _("products"))

    def __init__(self, filename, products, *args, **kwargs):
        self._products = products
        SearchResultsReport.__init__(self, filename, products,
                                     ProductCountingReport.report_name,
                                     *args, **kwargs)
        self._setup_items_table()

    def _get_columns(self):
        return [
            OTC(_("Code"), lambda obj: obj.code, width=100, truncate=True),
            OTC(_("Description"), lambda obj:
                obj.description, truncate=True),
            OTC(_("Fiscal Class"), lambda obj: obj.tax_constant.description,
                width=80, truncate=True),
            OTC(_("Quantity"), None, width=80, truncate=True),
            # FIXME: This column should be virtual, waiting for bug #2764
            OTC(_("Unit"), lambda obj: obj.get_unit_description(),
                width=60, truncate=True),
            ]

    def _setup_items_table(self):
        self.add_object_table(self._products, self._get_columns())


def format_data(data):
    # must return zero or relatory show None instead of 0
    if data is None:
        return 0
    return format_quantity(data)


class ProductStockReport(ObjectListReport):
    title = _("Product Stock Report")
    main_object_name = (_("product"), _("products"))


class ProductClosedStockReport(ObjectListReport):
    title = _("Closed Product Stock Report")
    main_object_name = (_("product"), _("products"))
