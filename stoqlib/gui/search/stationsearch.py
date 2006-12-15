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
## Author(s):   J. Victor Martins         <jvdm@sdf.lonestar.org>
##
""" Search dialog for station objects """

from kiwi.ui.objectlist import Column

from stoqlib.domain.interfaces import IBranch
from stoqlib.domain.station import BranchStation
from stoqlib.domain.person import Person
from stoqlib.gui.base.columns import AccessorColumn
from stoqlib.gui.base.search import SearchEditor
from stoqlib.gui.editors.stationeditor import StationEditor
from stoqlib.gui.slaves.filterslave import FilterSlave
from stoqlib.lib.defaults import ALL_BRANCHES, ALL_ITEMS_INDEX
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

class StationSearch(SearchEditor):
    title = _("Branch Station Search")
    table = BranchStation
    editor_class = StationEditor
    searchbar_result_strings = _("Station"), _("Stations")
    filter_label = _('Branch')
    size = (-1, 450)

    #
    # SearchDialog Hooks
    #

    def get_filter_slave(self):
        statuses = [ALL_BRANCHES]
        # FIXME: Implement and use IDescribable on PersonAdaptToBranch
        for branch in Person.iselect(IBranch, connection=self.conn):
            statuses.append((branch.person.name, branch))
        self.filter_slave = FilterSlave(statuses, selected=ALL_ITEMS_INDEX)
        self.filter_slave.set_filter_label(self.filter_label)
        return self.filter_slave

    def after_search_bar_created(self):
        self.filter_slave.connect('status-changed',
                                   self.search_bar.search_items)

    def get_columns(self):
        return [Column('name', _('Name'), data_type=str, sorted=True,
                       width=190, searchable=True),
                Column('is_active', _('Active'), data_type=bool,
                       sorted=False, searchable=False, width=50),
                AccessorColumn("branch",
                               BranchStation.get_branch_name,
                               title=_('Branch'), data_type=str,
                               expand=True),
                ]

    def get_extra_query(self):
        branch = self.filter_slave.get_selected_status()
        if branch != ALL_ITEMS_INDEX:
            return BranchStation.q.branchID == branch.id

