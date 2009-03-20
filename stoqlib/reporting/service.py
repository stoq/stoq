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
##  Author(s):  Fabio Morbec            <fabio@async.com.br>
##              George Y. Kussumoto     <george@async.com.br>
##
""" Services report implementation """

from decimal import Decimal

from kiwi.currency import format_price

from stoqlib.domain.service import ServiceView
from stoqlib.reporting.template import SearchResultsReport, PriceReport
from stoqlib.reporting.base.tables import ObjectTableColumn as OTC
from stoqlib.lib.translation import stoqlib_gettext as _

class ServiceReport(SearchResultsReport):
    """This report show a list of services returned by a SearchBar,
    listing both its description, cost, price and contribution margin.
    """
    obj_type = ServiceView
    report_name = _("Service Listing")
    filter_format_string = _("on branch <u>%s</u>")
    main_object_name = _("services")

    def __init__(self, filename, services, *args, **kwargs):
        self._services = services
        SearchResultsReport.__init__(self, filename, services,
                                     ServiceReport.report_name,
                                     landscape=True,
                                     *args, **kwargs)
        self._setup_items_table()

    def _get_columns(self):
        return [
            OTC(_("Code"), lambda obj: obj.code, width=100, truncate=True),
            OTC(_("Description"), lambda obj: obj.description, truncate=True),
            OTC(_("Cost"), lambda obj: obj.cost, width=90, truncate=True),
            OTC(_("Price"), lambda obj: obj.price, width=90, truncate=True),
            OTC(_("C.M."), lambda obj: obj.price - obj.cost, width=90,
                truncate=True),
            # FIXME: This column should be virtual, waiting for bug #2764
            OTC(_("Unit"), lambda obj: obj.get_unit(),
                width=60, virtual=False),
            ]

    def _setup_items_table(self):
        total_cost = total_price = total_cm = 0
        for item in self._services:
            total_cost += item.cost or Decimal(0)
            total_price += item.price or Decimal(0)
            total_cm += item.price - item.cost or Decimal(0)
        summary_row = ["",  _("Total:"), format_price(total_cost, False, 2),
                       format_price(total_price, False, 2),
                       format_price(total_cm, False, 2), ""]
        self.add_object_table(self._services, self._get_columns(),
                              summary_row=summary_row)


class ServicePriceReport(PriceReport):
    """This report show a list of services and it's prices."""
    report_name = _("Service Listing")

    def __init__(self, filename, services, *args, **kwargs):
        # XXX: We should not change main_object_name here
        PriceReport.main_object_name = ''
        PriceReport.__init__(self, filename, services, *args, **kwargs)
