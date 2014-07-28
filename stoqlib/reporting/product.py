# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2014 Async Open Source <http://www.async.com.br>
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

from stoqlib.reporting.report import (ObjectListReport,
                                      ObjectTreeReport,
                                      TableReport)
from stoqlib.lib.formatters import format_quantity
from stoqlib.lib.translation import stoqlib_gettext as _


class ProductReport(ObjectListReport):
    """ This report show a list of all products returned by a SearchBar,
    listing both its description and its balance in the stock selected.
    """
    title = _("Product Listing")
    filter_format_string = _("on branch <u>%s</u>")


class ProductBrandReport(ObjectListReport):
    """ This report show a list of all products brand returned by a SearchBar,
    listing both its brand and its product quantity in the stock selected.
    """
    title = _("Brand Listing")
    filter_format_string = _("on branch <u>%s</u>")
    summary = ['quantity']


class ProductBrandByBranchReport(ObjectTreeReport):
    """ This report show a list of all products brand by branch returned by
     a SearchBar, listing both its brand and its product quantity in the stock
     selected.
    """
    title = _("Brand by branch Listing")
    filter_format_string = _("on branch <u>%s</u>")
    summary = ['quantity']

    def has_parent(self, obj):
        return obj.company

    # Overriding the method to summarize correctly
    def accumulate(self, obj):
        if not obj.company:
            self._summary['quantity'] += obj.quantity


class SimpleProductReport(ObjectListReport):
    title = _("Product Listing")
    summary = ['stock']


class ProductPriceReport(TableReport):
    """ This report show a list of all products returned by a SearchBar,
    listing both its description and price in the selected stock.
    """
    title = _("Product Listing")
    filter_format_string = _("on branch <u>%s</u>")

    def __init__(self, filename, products, *args, **kwargs):
        branch_name = kwargs.pop('branch_name')
        self.main_object_name = (_("product from branch %s") % branch_name,
                                 _("products from branch %s") % branch_name)
        TableReport.__init__(self, filename, products, *args, **kwargs)

    def get_columns(self):
        return [dict(title=_('Code'), align='right'),
                dict(title=_('Description')),
                dict(title=_('Price'), align='right')]

    def get_row(self, obj):
        return [obj.code, obj.description, obj.price]


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


class ProductCountingReport(TableReport):
    """This report shows a list of all products returned by a Searchbar
    and it leaves several fields in blank, like quantity, partial value
    and total value. These fields must be filled out in the counting
    process, manually.
    """
    title = _("Product Counting")
    main_object_name = (_("product"), _("products"))

    def get_columns(self):
        columns = [
            dict(title=_('Code'), align='right'),
            dict(title=_('Description')),
            dict(title=_('Fiscal Class')),
            dict(title=_('Quantity'), align='right'),
            dict(title=_('Unit')),
        ]
        return columns

    def get_row(self, obj):
        return [obj.code, obj.description, obj.tax_constant.description, '',
                obj.unit_description]


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
