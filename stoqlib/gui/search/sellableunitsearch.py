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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
""" Implementation of SellableUnit search """

from kiwi.ui.objectlist import Column, SearchColumn

from stoqlib.domain.sellable import SellableUnit
from stoqlib.gui.base.search import SearchEditor
from stoqlib.gui.editors.sellableuniteditor import SellableUnitEditor
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

#
#  Searchs
#


class SellableUnitSearch(SearchEditor):
    """A search for L{stoqlib.domain.sellable.SellableUnit}"""

    title = _("Search for Units")
    size = (-1, 450)
    table = search_table = SellableUnit
    editor_class = SellableUnitEditor
    searchbar_result_strings = _("Unit"), _("Units")

    #
    #  Private API
    #

    def _update_edit_button_visibility(self):
        selected = self.get_selection()

        can_edit = bool(selected and (selected.unit_index not in
                                      SellableUnit.SYSTEM_PRIMITIVES))
        self.set_edit_button_sensitive(can_edit)
        self.accept_edit_data = can_edit

    def _format_unit_index(self, value):
        return value in SellableUnit.SYSTEM_PRIMITIVES

    #
    #  SearchDialog Hooks
    #

    def update_widgets(self):
        self._update_edit_button_visibility()

    def create_filters(self):
        self.set_text_field_columns(['description'])

    def get_columns(self):
        return [SearchColumn('description', title=_('Description'),
                             data_type=str, width=150, sorted=True),
                Column('unit_index', title=_('System'),
                       format_func=self._format_unit_index, data_type=bool,
                       width=100),
                SearchColumn('allow_fraction', title=_('Fraction'),
                             data_type=bool)]
