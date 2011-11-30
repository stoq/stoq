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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
""" Till report implementation """

from stoqlib.domain.till import TillEntry
from stoqlib.lib.translation import stoqlib_gettext as _
from stoqlib.lib.formatters import get_formatted_price
from stoqlib.reporting.template import ObjectListReport


class TillHistoryReport(ObjectListReport):
    """This report show a list of the till history returned by a SearchBar,
    listing both its description, date and value.
    """
    obj_type = TillEntry
    report_name = _("Till History Listing")
    main_object_name = (_("till entry"), _("till entries"))

    def __init__(self, filename, objectlist, till_entries, *args, **kwargs):
        self._till_entries = till_entries
        ObjectListReport.__init__(self, filename, objectlist, till_entries,
                                  TillHistoryReport.report_name,
                                  *args, **kwargs)
        self._setup_items_table()

    def _setup_items_table(self):
        total = sum([te.value or 0 for te in self._till_entries])
        self.add_summary_by_column(_(u'Value'), get_formatted_price(total))
        self.add_object_table(self._till_entries, self.get_columns(),
                              summary_row=self.get_summary_row())
