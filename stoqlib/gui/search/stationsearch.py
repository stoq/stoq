# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2007 Async Open Source <http://www.async.com.br>
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Search dialog for station objects """

from kiwi.enums import SearchFilterPosition
from kiwi.ui.objectlist import Column

from stoqlib.domain.station import BranchStation
from stoqlib.gui.base.columns import AccessorColumn
from stoqlib.gui.base.search import SearchEditor
from stoqlib.gui.editors.stationeditor import StationEditor
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class StationSearch(SearchEditor):
    title = _("Computer Search")
    table = BranchStation
    editor_class = StationEditor
    searchbar_result_strings = _("Computer"), _("Computers")
    size = (-1, 450)
    advanced_search = False

    #
    # SearchDialog Hooks
    #

    def create_filters(self):
        self.set_text_field_columns(['name'])
        branch_filter = self.create_branch_filter()
        self.add_filter(branch_filter,
                        SearchFilterPosition.TOP, ['branchID'])

    def get_columns(self):
        return [Column('name', _('Name'), data_type=str, sorted=True,
                       width=190, searchable=True),
                AccessorColumn("branch",
                               BranchStation.get_branch_name,
                               title=_('Branch'), data_type=str,
                               expand=True),
                Column('is_active', _('Active'), data_type=bool,
                       sorted=False, searchable=False, width=80),
                ]
