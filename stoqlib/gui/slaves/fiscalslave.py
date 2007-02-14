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
##  Author(s): Evandro Vale Miquelito   <evandro@async.com.br>
##
""" Useful slaves for fiscal data

This whole module is Brazil-specific
"""


from kiwi.ui.delegates import GladeSlaveDelegate
from kiwi.utils import gsignal

from stoqlib.domain.person import PersonAdaptToBranch
from stoqlib.enums import FiscalBookEntry
from stoqlib.gui.slaves.filterslave import FilterSlave
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.defaults import (fiscal_book_entries,
                                  ALL_BRANCHES, ALL_ITEMS_INDEX)

_ = stoqlib_gettext


class FiscalBookEntryFilterSlave(GladeSlaveDelegate):
    """A slave which filter a colection of fiscal book entries by entry type
    (ICMS, IPI or ISS) and branch companies
    """
    gladefile = 'FiscalBookEntryFilterSlave'
    gsignal('status-changed')

    def __init__(self, conn):
        self.conn = conn
        GladeSlaveDelegate.__init__(self, gladefile=self.gladefile)
        self._setup_slaves()

    # the code below is duplicated and will be fixed on bug 2651
    # the duplicated code is in slaves/product.py
    def _setup_slaves(self):
        items = [(value, key)
                    for key, value in fiscal_book_entries.items()]
        self.entry_type_slave = FilterSlave(items, selected=FiscalBookEntry.ICMS)
        self.entry_type_slave.set_filter_label(_('Show entries of type'))
        self.entry_type_slave.connect("status-changed",
                                      self._on_entry_type_changed)

        table = PersonAdaptToBranch
        items = [(item.get_description(), item)
                    for item in table.get_active_branches(self.conn)]
        items.insert(0, ALL_BRANCHES)
        self.branch_slave = FilterSlave(items, selected=ALL_ITEMS_INDEX)
        self.branch_slave.set_filter_label(_('on branch'))
        self.branch_slave.connect("status-changed", self._on_branch_changed)

        self.attach_slave("entry_type_holder", self.entry_type_slave)
        self.attach_slave("branch_holder", self.branch_slave)

    def get_selected_entry_type(self):
        return self.entry_type_slave.get_selected_status()

    def get_selected_branch(self):
        return self.branch_slave.get_selected_status()

    #
    # Callbacks
    #

    def _on_entry_type_changed(self, *args):
        self.emit("status-changed")

    def _on_branch_changed(self, *args):
        self.emit("status-changed")
