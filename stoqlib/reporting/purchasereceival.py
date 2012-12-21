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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
""" Purchase receival report implementation """

from decimal import Decimal

from stoqlib.reporting.template import ObjectListReport
from stoqlib.lib.translation import stoqlib_gettext as _
from stoqlib.lib.formatters import get_formatted_price


class PurchaseReceivalReport(ObjectListReport):
    report_name = _("Purchase Receival Report")
    main_object_name = (_("purchase"), _("purchases"))

    def __init__(self, filename, objectlist, receivings, *args, **kwargs):
        self._receivings = receivings
        ObjectListReport.__init__(self, filename, objectlist, receivings,
                                  PurchaseReceivalReport.report_name,
                                  landscape=True, *args, **kwargs)
        self._setup_table()

    def _setup_table(self):
        total_value = sum([item.invoice_total or Decimal(0)
                                for item in self._receivings])
        self.add_summary_by_column(_(u'Invoice Total'),
                                   get_formatted_price(total_value))
        self.add_object_table(self._receivings, self.get_columns(),
                              summary_row=self.get_summary_row())
