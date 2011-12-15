# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011 Async Open Source <http://www.async.com.br>
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

"""Inventory report implementation"""

from stoqlib.domain.inventory import Inventory
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.template import ObjectListReport

_ = stoqlib_gettext


class InventoryReport(ObjectListReport):
    """Simple report for Inventory objs"""

    obj_type = Inventory
    report_name = _("Inventory Listing")
    main_object_name = (_("inventory entry"), _("inventory entries"))

    def __init__(self, filename, objectlist, entries, *args, **kwargs):
        self._entries = entries
        ObjectListReport.__init__(self, filename, objectlist, entries,
                                  self.report_name, *args, **kwargs)
        self._setup_table()

    def _setup_table(self):
        self.add_object_table(self._entries, self.get_columns(),
                              summary_row=self.get_summary_row())
