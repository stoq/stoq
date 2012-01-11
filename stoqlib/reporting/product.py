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

from decimal import Decimal

from stoqlib.reporting.template import (SearchResultsReport, PriceReport,
                                        ObjectListReport)
from stoqlib.reporting.base.tables import ObjectTableColumn as OTC
from stoqlib.lib.formatters import format_quantity, get_formatted_price
from stoqlib.lib.translation import stoqlib_gettext as _
from stoqlib.domain.product import ProductHistory
from stoqlib.domain.views import (SoldItemView, ProductFullStockView,
                                  ProductFullStockItemView,
                                  ProductClosedStockView)


class ProductReport(ObjectListReport):
    """ This report show a list of all products returned by a SearchBar,
    listing both its description and its balance in the stock selected.
    """
    # This should be properly verified on SearchResultsReport. Waiting for
    # bug 2517
    obj_type = ProductFullStockView
    report_name = _("Product Listing")
    filter_format_string = _("on branch <u>%s</u>")

    def __init__(self, filename, objectlist, products, *args, **kwargs):
        self._products = products
        branch_name = kwargs['branch_name']
        self.main_object_name = (_("product from branch %s") % branch_name,
                                 _("products from branch %s") % branch_name)
        ObjectListReport.__init__(self, filename, objectlist, products,
                                  ProductReport.report_name,
                                  landscape=True,
                                  *args, **kwargs)
        self._setup_items_table()

    def _setup_items_table(self):
        totals = [(p.cost or Decimal(0),
                   p.price or Decimal(0),
                   p.stock or Decimal(0)) for p in self._products]
        cost, price, stock = zip(*totals)
        self.add_summary_by_column(_(u'Cost'), get_formatted_price(sum(cost)))
        self.add_summary_by_column(_(u'Price'), get_formatted_price(sum(price)))
        self.add_summary_by_column(_(u'Stock Total'), format_data(sum(stock)))

        self.add_object_table(self._products, self.get_columns(),
                              summary_row=self.get_summary_row())


class SimpleProductReport(ObjectListReport):
    obj_type = ProductFullStockView
    report_name = _("Product Listing")
    filter_format_string = _("on branch <u>%s</u>")

    def __init__(self, filename, objectlist, products, *args, **kwargs):
        self._products = products
        branch_name = kwargs['branch_name']
        self.main_object_name = (_("product from branch %s") % branch_name,
                                 _("products from branch %s") % branch_name)
        ObjectListReport.__init__(self, filename, objectlist, products,
                                  ProductReport.report_name,
                                  landscape=True,
                                  *args, **kwargs)
        self._setup_items_table()

    def _setup_items_table(self):
        total = sum([p.stock for p in self._products], Decimal(0))
        self.add_summary_by_column(_(u'Quantity'), format_quantity(total))
        self.add_object_table(self._products, self.get_columns(),
                              summary_row=self.get_summary_row())


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
    # This should be properly verified on SearchResultsReport. Waiting for
    # bug 2517
    obj_type = ProductHistory
    report_name = _("Product Listing")
    main_object_name = (_("product"), _("products"))

    def __init__(self, filename, objectlist, products, *args, **kwargs):
        self._products = products
        ObjectListReport.__init__(self, filename, objectlist, products,
                                  ProductReport.report_name,
                                  landscape=True,
                                  *args, **kwargs)
        self._setup_items_table()

    def _setup_items_table(self):
        totals = [(p.quantity_sold or Decimal(0),
                   p.quantity_received or Decimal(0),
                   p.quantity_transfered or Decimal(0),
                   p.quantity_produced or Decimal(0),
                   p.quantity_consumed or Decimal(0),
                   p.quantity_lost or Decimal(0)) for p in self._products]

        (sold, received, transfered, produced, consumed, lost) = zip(*totals)

        self.add_summary_by_column(_(u'Sold'), format_data(sum(sold)))
        self.add_summary_by_column(_(u'Received'), format_data(sum(received)))
        self.add_summary_by_column(_(u'Transfered'),
                                   format_data(sum(transfered)))
        self.add_summary_by_column(_(u'Produced'), format_data(sum(produced)))
        self.add_summary_by_column(_(u'Consumed'), format_data(sum(consumed)))
        self.add_summary_by_column(_(u'Lost'), format_data(sum(lost)))

        self.add_object_table(self._products, self.get_columns(),
                              summary_row=self.get_summary_row())


class ProductsSoldReport(ObjectListReport):
    """ This report lists all products sold with the average stock cost for
    a given period of time.
    """
    obj_type = SoldItemView
    report_name = _("Products Sold Listing")
    main_object_name = (_("product sold"), _("products sold"))

    def __init__(self, filename, objectlist, products, *args, **kwargs):
        self._products = products
        ObjectListReport.__init__(self, filename, objectlist, products,
                                  self.report_name,
                                  landscape=True,
                                  *args, **kwargs)

        self.add_object_table(self._products, self.get_columns(),
                              summary_row=self.get_summary_row())


class ProductCountingReport(SearchResultsReport):
    """This report shows a list of all products returned by a Searchbar
    and it leaves several fields in blank, like quantity, partial value
    and total value. These fields must be filled out in the counting
    process, manually.
    """
    obj_type = ProductFullStockView
    report_name = _("Product Counting")
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
    report_name = _("Product Stock Report")
    main_object_name = (_("product"), _("products"))
    obj_type = ProductFullStockItemView

    def __init__(self, filename, objectlist, stock_products, *args, **kwargs):
        self._stock_products = stock_products
        ObjectListReport.__init__(self, filename, objectlist, stock_products,
                                  ProductStockReport.report_name,
                                  landscape=1, *args, **kwargs)
        self._setup_table()

    def _setup_table(self):
        totals = [(p.maximum_quantity or Decimal(0),
                   p.minimum_quantity or Decimal(0),
                   p.stock or Decimal(0),
                   p.to_receive_quantity or Decimal(0))
                       for p in self._stock_products]

        maximum, minimum, stocked, to_receive = zip(*totals)

        self.add_summary_by_column(_(u'Maximum'), format_quantity(sum(maximum)))
        self.add_summary_by_column(_(u'Minimum'), format_quantity(sum(minimum)))
        self.add_summary_by_column(_(u'In Stock'),
                                   format_quantity(sum(stocked)))
        self.add_summary_by_column(_(u'To Receive'),
                                   format_quantity(sum(to_receive)))

        self.add_object_table(self._stock_products, self.get_columns(),
                              summary_row=self.get_summary_row())


class ProductClosedStockReport(ProductStockReport):
    report_name = _("Closed Product Stock Report")
    main_object_name = (_("product"), _("products"))
    obj_type = ProductClosedStockView

    def _setup_table(self):
        self.add_object_table(self._stock_products, self.get_columns(),
                              summary_row=self.get_summary_row())
