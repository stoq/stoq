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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Search dialogs for production objects """


from decimal import Decimal

from stoqlib.domain.person import Branch
from stoqlib.domain.production import ProductionOrder
from stoqlib.domain.views import (ProductComponentWithClosedView,
                                  ProductionItemView)
from stoqlib.enums import SearchFilterPosition
from stoqlib.gui.search.searchcolumns import IdentifierColumn, SearchColumn
from stoqlib.gui.editors.producteditor import ProductionProductEditor
from stoqlib.gui.search.productsearch import (ProductSearch,
                                              ProductSearchQuantity)
from stoqlib.gui.search.searchfilters import ComboSearchFilter
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.production import ProductionItemReport

_ = stoqlib_gettext


class ProductionProductSearch(ProductSearch):
    title = _(u'Production Product')
    search_spec = ProductComponentWithClosedView
    editor_class = ProductionProductEditor

    #
    #  ProductSearch
    #

    def get_editor_class_for_object(self, obj):
        return self.editor_class

    def executer_query(self, store):
        branch_id = self.branch_filter.get_state().value
        if branch_id is None:
            branch = None
        else:
            branch = store.get(Branch, branch_id)
        return self.search_spec.find_by_branch(store, branch)

    def get_editor_model(self, product_component):
        return product_component.product


class ProductionItemsSearch(ProductSearch):
    title = _(u'Production Items')
    search_spec = ProductionItemView
    report_class = ProductionItemReport
    csv_data = None
    has_print_price_button = False
    text_field_columns = [ProductionItemView.description,
                          ProductionItemView.order_identifier_str]

    def __init__(self, store, hide_footer=True, hide_toolbar=True):
        ProductSearch.__init__(self, store, hide_footer=hide_footer,
                               hide_toolbar=hide_toolbar)

    #
    # SearchDialog
    #

    def create_filters(self):
        statuses = [(desc, i) for i, desc in ProductionOrder.statuses.items()]
        statuses.insert(0, (_(u'Any'), None))
        self.status_filter = ComboSearchFilter(_('order status:'), statuses)
        self.status_filter.select(ProductionOrder.ORDER_PRODUCING)
        self.add_filter(self.status_filter, columns=['order_status'],
                        position=SearchFilterPosition.TOP)

    def get_columns(self):
        return [IdentifierColumn('order_identifier', title=_(u"Order #"),
                                 sorted=True),
                SearchColumn('category_description', title=_(u'Category'),
                             data_type=str),
                SearchColumn('description', title=_(u'Description'),
                             data_type=str, expand=True),
                SearchColumn('unit_description', title=_(u'Unit'),
                             data_type=str),
                SearchColumn('quantity', title=_(u'To Produce'),
                             data_type=Decimal),
                SearchColumn('produced', title=_(u'Produced'),
                             data_type=Decimal),
                SearchColumn('lost', title=_(u'Lost'), data_type=Decimal,
                             visible=False)]


class ProductionHistorySearch(ProductSearchQuantity):
    title = _(u'Production History Search')
    report_class = ProductionItemReport
    csv_data = None
    show_production_columns = True
