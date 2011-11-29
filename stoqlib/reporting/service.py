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
""" Services report implementation """

from decimal import Decimal


from stoqlib.domain.service import ServiceView
from stoqlib.reporting.template import PriceReport, ObjectListReport
from stoqlib.lib.translation import stoqlib_gettext as _
from stoqlib.lib.formatters import get_formatted_price


class ServiceReport(ObjectListReport):
    """This report show a list of services returned by a SearchBar,
    listing both its description, cost and price.
    """
    obj_type = ServiceView
    report_name = _("Service Listing")
    filter_format_string = _("on branch <u>%s</u>")
    main_object_name = (_("service"), _("services"))

    def __init__(self, filename, objectlist, services, *args, **kwargs):
        self._services = services
        ObjectListReport.__init__(self, filename, objectlist, services,
                                  ServiceReport.report_name,
                                  landscape=True,
                                  *args, **kwargs)
        self._setup_items_table()

    def _setup_items_table(self):
        cost = sum([s.cost or Decimal(0) for s in self._services])
        self.add_summary_by_column(_(u'Cost'), get_formatted_price(cost))

        self.add_object_table(self._services, self.get_columns(),
                              summary_row=self.get_summary_row())


class ServicePriceReport(PriceReport):
    """This report show a list of services and it's prices."""
    report_name = _("Service Listing")
    main_object_name = (_("service"), _("services"))
