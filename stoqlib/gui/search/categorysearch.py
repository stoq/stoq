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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
""" A dialog for sellable categories selection, offering buttons for
creation and edition.
"""

from decimal import Decimal

from kiwi.ui.objectlist import SearchColumn

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.base.search import SearchEditor
from stoqlib.gui.editors.categoryeditor import (BaseSellableCategoryEditor,
                                                SellableCategoryEditor)
from stoqlib.domain.sellable import SellableCategory
from stoqlib.domain.views import SellableCategoryView

_ = stoqlib_gettext


class SellableCategorySearch(SearchEditor):
    size = (750, 500)
    title = _('Sellable Category Search')

    searchbar_label = _('Categories Matching:')
    result_strings = _('category'), _('categories')
    table = search_table = SellableCategoryView
    editor = SellableCategoryEditor

    def __init__(self, conn):
        SearchEditor.__init__(self, conn, SellableCategory, self.editor)
        self.set_searchbar_labels(self.searchbar_label)
        self.set_result_strings(*self.result_strings)

    def create_filters(self):
        self.set_text_field_columns(['description'])
        self.executer.add_query_callback(self._get_query)

    def get_columns(self):
        return [
            SearchColumn("description", _("Description"), data_type=str,
                         sorted=True, expand=True),
            SearchColumn("suggested_markup", _("Suggested Markup (%)"),
                         data_type=Decimal, width=180),
            SearchColumn("commission", _("Commission (%)"), data_type=Decimal,
                         width=140),
            SearchColumn("installments_commission",
                         _("Installments Commission (%)"),
                         data_type=Decimal, width=220),
            ]

    def get_editor_model(self, commission_source_category_view):
        """Search Editor hook"""
        return commission_source_category_view.category

    #
    # Private
    #

    def _get_query(self, states):
        return SellableCategory.q.categoryID != None


class BaseSellableCatSearch(SellableCategorySearch):
    title = _('Base Sellable Category Search')
    searchbar_label = _('Base Categories Matching:')
    result_strings = _('base category'), _('base categories')
    editor = BaseSellableCategoryEditor

    def create_filters(self):
        self.set_text_field_columns(['description'])
        self.executer.add_query_callback(self._get_query)

    #
    # Private
    #

    def _get_query(self, states):
        return SellableCategory.q.categoryID == None
