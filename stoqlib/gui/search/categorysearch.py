# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source <http://www.async.com.br>
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
##
##
""" A dialog for sellable categories selection, offering buttons for
creation and edition.
"""

import sets

from kiwi.ui.objectlist import Column

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.base.search import SearchEditor
from stoqlib.gui.base.columns import AccessorColumn
from stoqlib.gui.editors.category import (BaseSellableCategoryEditor,
                                          SellableCategoryEditor)
from stoqlib.domain.sellable import (AbstractSellableCategory,
                                     BaseSellableCategory,
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

class SellableCatSearch(SearchEditor):
    size = (700, 500)
    title = _('Sellable Category Search')

    def __init__(self, conn):
        # I'm using AbstractSellableCategory here because I want to be able of
        # to search in sellable category *and* its base category data as well.
        SearchEditor.__init__(self, conn, AbstractSellableCategory,
                              SellableCategoryEditor)
        self.set_result_strings(_('category'), _('categories'))
        self.set_searchbar_labels(_('Categories Matching:'))

    def get_columns(self):
        return [AccessorColumn("description",
                               SellableCategory.get_full_description,
                               title=_('Description'), data_type=str,
                               expand=True),
                Column("suggested_markup", _("Suggested Markup (%)"),
                       data_type=str, width=170),
                Column("salesperson_comission",
                       _("Suggested Commission (%)"), data_type=str,
                       width=190),
                ]

    def filter_results(self, abstract_objects):
        sellable_objs = SellableCategory.select(connection=self.conn)
        base_ids = sets.Set([s.base_category.id for s in sellable_objs])

        # Discard all base categories that aren't used.
        base_objs = BaseSellableCategory.select(connection=self.conn)
        reject = sets.Set([base.id for base in base_objs])
        reject = reject - (reject & base_ids)

        # Discard all base categories that doesn't match the search criteria
        abstract_ids = sets.Set([a.id for a in abstract_objects])
        abstract_ids = abstract_ids - (abstract_ids & reject)

        return [s for s in sellable_objs
                    if (s.id in abstract_ids
                        or s.base_category.id in abstract_ids)]

    # XXX: I need to overwrite SearchEditor's get_searchlist_model because
    # its search_table differs from the objects in the Kiwi list -- but we
    # need this, since we want to search in AbstractSellableCategory and
    # prefill the list with SellableCategory objects (which have a foreign
    # key to AbstractSellableCategory).
    def get_searchlist_model(self, model):
        return model
