# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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

"""Search dialogs for magento"""

import gtk
from kiwi.ui.objectlist import SearchColumn, Column

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.base.search import SearchEditor

from gui.editor.magentoeditor import MagentoConfigEditor
from domain.magentoconfig import MagentoConfig

_ = stoqlib_gettext


class MagentoConfigSearch(SearchEditor):
    """Search for L{MagentoConfig} objects"""

    title = _('Magento config search')
    table = MagentoConfig
    search_table = MagentoConfig
    editor_class = MagentoConfigEditor
    searchbar_result_strings = (_('config'), _('configs'))
    size = (600, 450)

    #
    #  SearchEditor hooks
    #

    def create_filters(self):
        self.set_text_field_columns(['url'])

    def get_columns(self):
        return [Column('id', title=_('#'), data_type=int,
                       order=gtk.SORT_DESCENDING),
                SearchColumn('url', title=_('Server URL'), data_type=str,
                             expand=True),
               ]
