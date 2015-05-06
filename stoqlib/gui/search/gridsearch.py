# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2015 Async Open Source <http://www.async.com.br>
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
""" Search dialogs for grid configuration implementation"""

from kiwi.ui.objectlist import Column

from stoqlib.domain.product import GridGroup, GridAttribute
from stoqlib.gui.editors.grideditor import GridGroupEditor, GridAttributeEditor
from stoqlib.gui.search.searcheditor import SearchEditor
from stoqlib.lib.message import warning
from stoqlib.lib.translation import stoqlib_gettext


_ = stoqlib_gettext


class GridGroupSearch(SearchEditor):
    title = _("Grid Group Search")
    search_spec = GridGroup
    text_field_columns = ['description']
    editor_class = GridGroupEditor
    size = (-1, 390)
    advanced_search = False
    search_label = _('Attribute Group Matching:')

    #
    # SearchDialog Hooks
    #

    def get_columns(self):
        return [Column('description', _('Attribute group'), data_type=str,
                       expand=True, sorted=True),
                Column('is_active', _('Active'), data_type=bool)]


class GridAttributeSearch(SearchEditor):
    title = _("Grid Attribute Search")
    search_spec = GridAttribute
    text_field_columns = ['description']
    editor_class = GridAttributeEditor
    size = (-1, 390)
    advanced_search = False
    search_label = _('Attribute Matching:')

    #
    # SearchDialog Hooks
    #

    def get_columns(self):
        return [Column('description', _('Attribute'), data_type=str,
                       expand=True, sorted=True),
                Column('is_active', _('Active'), data_type=bool),
                Column('group.description', _('Group'), data_type=str)]

    #
    # Callbacks
    #

    def _on_toolbar__new(self, toolbar):
        if not self.store.find(GridGroup, is_active=True).any():
            warning(_("You need an active grid group."))
        else:
            self.run()
