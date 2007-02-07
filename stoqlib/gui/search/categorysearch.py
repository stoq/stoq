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
##  Author(s):  Evandro Vale Miquelito      <evandro@async.com.br>
##              Johan Dahlin                <jdahlin@async.com.br>
##
##
""" A dialog for sellable categories selection, offering buttons for
creation and edition.
"""

from kiwi.ui.objectlist import Column

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.base.search import SearchEditor
from stoqlib.gui.editors.categoryeditor import (BaseSellableCategoryEditor,
                                                SellableCategoryEditor)
from stoqlib.domain.sellable import (BaseSellableCategory,
                                     SellableCategory)

_ = stoqlib_gettext

class BaseSellableCatSearch(SearchEditor):
    size = (700, 500)
    title = _('Base Sellable Category Search')

    def __init__(self, conn):
        SearchEditor.__init__(self, conn, BaseSellableCategory,
                              BaseSellableCategoryEditor)
        self.set_searchbar_labels(_('Base Categories Matching:'))
        self.set_result_strings(_('base category'), _('base categories'))

    def get_columns(self):
        return [Column("description", _("Description"), data_type=str,
                       sorted=True, expand=True),
                Column("suggested_markup", _("Suggested Markup (%)"),
                       data_type=float, width=200),
                Column("salesperson_commission",
                       _("Salesperson Commission (%)"), data_type=float,
                       width=200),
            ]

class SellableCategorySearch(SearchEditor):
    size = (700, 500)
    title = _('Sellable Category Search')

    def __init__(self, conn):
        SearchEditor.__init__(self, conn, SellableCategory,
                              SellableCategoryEditor)
        self.set_searchbar_labels(_('Categories Matching:'))
        self.set_result_strings(_('category'), _('categories'))

    def get_columns(self):
        return [
            Column("description", _("Description"), data_type=str,
                   sorted=True, expand=True),
            Column("suggested_markup", _("Suggested Markup (%)"),
                   data_type=str, width=170),
            Column("salesperson_commission",
                   _("Suggested Commission (%)"), data_type=str,
                   width=190),
            ]


