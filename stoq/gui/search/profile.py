# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s): Bruno Rafael Garcia           <brg@async.com.br>
##
"""
stoq/gui/search/profile.py
    
    Search dialogs for profile objects
"""

import gettext

from kiwi.ui.widgets.list import Column
from stoqlib.gui.base.search import SearchEditor

from stoq.domain.profile import UserProfile
from stoq.gui.editors.profile import UserProfileEditor

_ = gettext.gettext


class UserProfileSearch(SearchEditor):
    title = _("User Profile Search")
    table = UserProfile
    editor_class = UserProfileEditor
    size = (465, 390)

    def __init__(self, conn):
        SearchEditor.__init__(self, conn, self.table, self.editor_class, 
                              title=self.title)
        self._setup_widgets()

    def _setup_widgets(self):
        self.set_searchbar_labels(_('Profiles Matching:'))
        self.set_result_strings(_('profile'), _('profiles'))
                        
    #
    # SearchDialog Hooks
    #

    def get_columns(self):
        return [Column('name', _('Profile'), data_type=str, sorted=True)]
