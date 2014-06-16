# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2007 Async Open Source <http://www.async.com.br>
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
""" Search dialogs for profile objects """

from kiwi.ui.objectlist import Column

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.search.searcheditor import SearchEditor
from stoqlib.domain.profile import UserProfile
from stoqlib.gui.editors.profileeditor import UserProfileEditor


_ = stoqlib_gettext


class UserProfileSearch(SearchEditor):
    title = _("User Profile Search")
    search_spec = UserProfile
    editor_class = UserProfileEditor
    size = (465, 390)
    advanced_search = False
    search_label = _('Profiles Matching:')

    def create_filters(self):
        self.set_text_field_columns(['name'])

    #
    # SearchDialog Hooks
    #

    def get_columns(self):
        return [Column('name', _('Profile'), data_type=str,
                       expand=True, sorted=True)]
