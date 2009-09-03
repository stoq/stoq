# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2009 Async Open Source <http://www.async.com.br>
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
## Author(s):   George Kussumoto    <george@async.com.br>
##
""" Search dialogs for production objects """


from decimal import Decimal

from kiwi.enums import SearchFilterPosition
from kiwi.ui.objectlist import SearchColumn
from kiwi.ui.search import ComboSearchFilter

from stoqlib.domain.person import PersonAdaptToBranch
from stoqlib.domain.product import ProductComponent
from stoqlib.domain.production import ProductionOrder
from stoqlib.domain.views import ProductComponentView, ProductionItemView
from stoqlib.gui.base.search import SearchDialog
from stoqlib.gui.editors.producteditor import ProductionProductEditor
from stoqlib.gui.search.productsearch import ProductSearch
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class ProductionProductSearch(ProductSearch):
    title = _(u'Production Product')
    table = ProductComponent
    search_table = ProductComponentView
    editor_class = ProductionProductEditor

    def executer_query(self, query, having, conn):
        branch = self.branch_filter.get_state().value
        if branch is not None:
            branch = PersonAdaptToBranch.get(branch, connection=conn)
        return ProductComponentView.select_by_branch(query, branch, connection=conn)

    #
    # SearchEditor Hooks
    #

    def get_editor_model(self, product_component):
        return product_component.product


class ProductionItemsSearch(SearchDialog):
    title = _(u'Production Items')
    table = search_table = ProductionItemView
    size = (750, 450)

    #
    # SearchDialog
    #

    def create_filters(self):
        self.set_text_field_columns(['description',])
        self.set_searchbar_labels(_(u'matching:'))

        statuses = [(desc, i) for i, desc in ProductionOrder.statuses.items()]
        statuses.insert(0, (_(u'Any'), None))
        status_filter = ComboSearchFilter(_('order status:'), statuses)
        self.add_filter(status_filter, columns=['order_status'],
                        position=SearchFilterPosition.TOP)

    def get_columns(self):
        return [SearchColumn('order_id', title=_(u'Order'), data_type=int,
                              sorted=True, format='%04d'),
                SearchColumn('category_description', title=_(u'Category'),
                              data_type=str, expand=True),
                SearchColumn('description', title=_(u'Description'),
                              data_type=str, expand=True),
                SearchColumn('unit_description', title=_(u'Unit'),
                              data_type=str),
                SearchColumn('quantity', title=_(u'Production'),
                              data_type=Decimal),]
