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
from stoqlib.domain.sellable import SellableCategory

_ = stoqlib_gettext

class SellableCategorySearch(SearchEditor):
    size = (700, 500)
    title = _('Sellable Category Search')

    searchbar_label = _('Categories Matching:')
    result_strings = _('category'), _('categories')
    editor = SellableCategoryEditor

    def __init__(self, conn):
        SearchEditor.__init__(self, conn, SellableCategory, self.editor)
        self.set_searchbar_labels(self.searchbar_label)
        self.set_result_strings(*self.result_strings)

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

    def get_extra_query(self):
        return SellableCategory.q.categoryID != None

class BaseSellableCatSearch(SellableCategorySearch):
    size = (700, 500)
    title = _('Base Sellable Category Search')
    searchbar_label = _('Base Categories Matching:')
    result_strings = _('base category'), _('base categories')
    editor = BaseSellableCategoryEditor

    def get_columns(self):
        columns = SellableCategorySearch.get_columns(self)
        del columns[-1]
        columns.append(
            Column("salesperson_commission",
                   _("Salesperson Commission (%)"), data_type=float,
                   width=200),
            )
        return columns

    def get_extra_query(self):
        return SellableCategory.q.categoryID == None
