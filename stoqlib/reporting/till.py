# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2007 Async Open Source <http://www.async.com.br>
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
##
##
""" Till report implementation """

from stoqlib.domain.till import TillEntry
from stoqlib.lib.translation import stoqlib_gettext as _
from stoqlib.lib.validators import get_formatted_price
from stoqlib.reporting.template import SearchResultsReport
from stoqlib.reporting.base.tables import ObjectTableColumn as OTC

class TillHistoryReport(SearchResultsReport):
    """This report show a list of the till history returned by a SearchBar,
    listing both its description, date and value.
    """
    obj_type = TillEntry
    report_name = _("Till History Listing")
    main_object_name = _("till history")

    def __init__(self, filename, till_entries, *args, **kwargs):
        self._till_entries = till_entries
        SearchResultsReport.__init__(self, filename, till_entries,
                                     TillHistoryReport.report_name,
                                     *args, **kwargs)
        self._setup_items_table()

    def _get_columns(self):
        return [
            OTC(_("Code"), lambda obj: '%03d' % obj.id, width=60,
                truncate=True),
            OTC(_("Description"), lambda obj: obj.description, width=255,
                truncate=True, expand=True),
            OTC(_("Date"), lambda obj: obj.date.strftime("%x"),
                truncate=True, expand=True),
            OTC(_("Value"), lambda obj: get_formatted_price(obj.value),
                truncate=True, expand=True),
            ]

    def _setup_items_table(self):
        total_price  = 0
        for till_entry in self._till_entries:
            total_price += till_entry.value
        summary_row = ["", "", _("Total:"), get_formatted_price(total_price)]
        self.add_object_table(self._till_entries, self._get_columns(),
                              summary_row=summary_row)
