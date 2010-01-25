# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2009 Async Open Source <http://www.async.com.br>
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
##  Author(s):  George Kussumoto        <george@async.com.br>
##
""" Production report implementation """

from decimal import Decimal

from stoqlib.reporting.template import ObjectListReport
from stoqlib.lib.validators import format_quantity
from stoqlib.lib.translation import stoqlib_gettext as _
from stoqlib.domain.views import ProductionItemView


class ProductionItemReport(ObjectListReport):
    """ This report show a list of all production items returned by a SearchBar,
    listing both its description, category and its quantities.
    """
    # This should be properly verified on SearchResultsReport. Waiting for
    # bug 2517
    obj_type = ProductionItemView
    report_name = _("Production Item Listing")
    filter_format_string = _("on branch <u>%s</u>")

    def __init__(self, filename, production_items, *args, **kwargs):
        self._production_items = production_items
        ObjectListReport.__init__(self, filename, production_items,
                                  ProductionItemReport.report_name,
                                  landscape=True, *args, **kwargs)
        self._setup_items_table()

    def _setup_items_table(self):
        totals = [(p.quantity or Decimal(0),
                   p.produced or Decimal(0),
                   p.lost or Decimal(0)) for p in self._production_items]
        qty, produced, lost = zip(*totals)
        self.add_summary_by_column(_(u'To Produce'), format_quantity(sum(qty)))
        self.add_summary_by_column(_(u'Produced'),
                                   format_quantity(sum(produced)))
        self.add_summary_by_column(_(u'Lost'), format_quantity(sum(lost)))

        self.add_object_table(self._production_items, self.get_columns(),
                              summary_row=self.get_summary_row())
