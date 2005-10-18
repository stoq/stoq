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
"""
gui/search/category.py:

   A dialog for sellable categories selection, offering buttons for
   creation and edition.
"""

import gettext
import sets

from sqlobject.sqlbuilder import INNERJOINOn
from stoqlib.gui.search import SearchEditor
from stoqlib.gui.columns import ForeignKeyColumn

from stoq.domain.sellable import (AbstractSellableCategory,
                                  BaseSellableCategory,
                                  SellableCategory)
from stoq.gui.editors.category import (BaseSellableCategoryEditor,
                                       SellableCategoryEditor)

_ = gettext.gettext

class BaseSellableCatSearch(SearchEditor):
    size = (700, 500)
    title = _('Base Sellable Category Search')
    table = BaseSellableCategory
    editor_class = BaseSellableCategoryEditor

    def __init__(self, parent_conn=None):
        SearchEditor.__init__(self, self.table, self.editor_class,
                              parent_conn=parent_conn, hide_footer=True)
        self.set_searchbar_labels(_('Base Categories Matching:'))
        self.set_result_strings(_('base category'), _('base categories'))
                
    def get_columns(self):
        return [ForeignKeyColumn(AbstractSellableCategory,
                                 'description', _('Description'), str, 
                                 obj_field='category_data', sorted=True,
                                 width=300),
                ForeignKeyColumn(AbstractSellableCategory,
                                 'suggested_markup', _('Suggested Markup (%)'), 
                                 float, obj_field='category_data', width=180),
                ForeignKeyColumn(AbstractSellableCategory, 
                                 'salesperson_comission', 
                                 _('Suggested Commission (%)'), 
                                 float, obj_field='category_data')]

    def get_query_args(self):
        return dict(join=INNERJOINOn(BaseSellableCategory, 
                                     AbstractSellableCategory,
                                     AbstractSellableCategory.q.id==
                                     BaseSellableCategory.q.category_dataID))


class SellableCatSearch(SearchEditor):
    size = (800, 500)
    title = _('Sellable Category Search')

    def __init__(self, parent_conn=None):
        editor = SellableCategoryEditor
        table = SellableCategory
        search_table = AbstractSellableCategory
        SearchEditor.__init__(self, table, editor,
                              search_table=search_table, 
                              parent_conn=parent_conn,
                              hide_footer=True)
        self.set_result_strings(_('category'), _('categories'))
        self.set_searchbar_labels(_('Categories Matching:'))


    #
    # Hooks
    #
        


    def get_columns(self):
        return [ForeignKeyColumn(AbstractSellableCategory,
                                 'description',
                                 _('Base Category'), str, 
                                 obj_field='base_category.category_data',
                                 sorted=True, width=210),
                ForeignKeyColumn(AbstractSellableCategory, 
                                 'description', _('Description'), str,
                                 obj_field='category_data', width=210),
                ForeignKeyColumn(AbstractSellableCategory, 
                                 'suggested_markup', 
                                 _('Suggested Markup (%)'), str, 
                                 obj_field='category_data', width=170),
                ForeignKeyColumn(AbstractSellableCategory, 
                                 'salesperson_comission', 
                                 _('Suggested Commission (%)'), str, 
                                 obj_field='category_data', )]


    def filter_results(self, abstract_objects):
        sellable_objs = SellableCategory.select(connection=self.conn)
        base_ids = sets.Set([s.base_category.id for s in sellable_objs])

        base_objs = BaseSellableCategory.select(connection=self.conn)
        reject = sets.Set([b.category_data.id for b in base_objs])
        reject = reject - (reject & base_ids)

        abstract_ids = sets.Set([a.id for a in abstract_objects])
        abstract_ids = abstract_ids - (abstract_ids & reject)

        return [s for s in sellable_objs 
                    if s.category_data.id in abstract_ids 
                        or s.base_category.category_data.id in abstract_ids]
