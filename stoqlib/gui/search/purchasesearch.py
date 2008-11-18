# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008 Async Open Source <http://www.async.com.br>
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
## Author(s):   George Y. Kussumoto     <george@async.com.br>
##
""" Search dialogs for purchase and related objects """

import datetime
from decimal import Decimal

from kiwi.enums import SearchFilterPosition
from kiwi.ui.search import DateSearchFilter, Any, Today
from kiwi.ui.objectlist import Column

from stoqlib.domain.views import PurchasedItemAndStockView
from stoqlib.gui.base.search import (SearchEditor, ThisWeek, NextWeek,
                                     ThisMonth, NextMonth)
from stoqlib.gui.editors.purchaseeditor import PurchaseItemEditor
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class PurchasedItemsSearch(SearchEditor):
    title = _('Purchased Items Search')
    size = (775, 450)
    table = search_table = PurchasedItemAndStockView
    editor_class = PurchaseItemEditor

    def __init__(self, conn):
        SearchEditor.__init__(self, conn=conn)
        self.hide_new_button()

    #
    # SearchDialog Hooks
    #

    def create_filters(self):
        self.set_text_field_columns(['description'])
        # Date
        date_filter = DateSearchFilter(_('Receival expected in:'))
        # custom options
        date_filter.clear_options()
        date_filter.add_custom_options()
        for opt in [Any, Today, ThisWeek, NextWeek, ThisMonth, NextMonth]:
            date_filter.add_option(opt)

        date_filter.select(Today)
        self.add_filter(date_filter, columns=['expected_receival_date'])
        # Branch
        branch_filter = self.create_branch_filter(_('In branch:'))
        self.add_filter(branch_filter, columns=['branch'],
                        position=SearchFilterPosition.TOP)

    #
    # SearchEditor Hooks
    #

    def update_widgets(self):
        selected = self.results.get_selected() is not None
        self.set_edit_button_sensitive(selected)

    def get_columns(self):
        return [Column('product_id', title=_('# '), data_type=int,
                        sorted=True, format='%03d'),
                Column('description', title=_('Description'), data_type=str,
                        expand=True),
                Column('purchased', title=_('Purchased'), data_type=Decimal,
                        width=100),
                Column('received', title=_('Received'),
                        data_type=Decimal, width=100),
                Column('stocked', title=_('In Stock'), data_type=Decimal,
                        width=100),
                Column('purchased_date', title=_('Purchased date'),
                        data_type=datetime.date),
                Column('expected_receival_date', title=_('Expected receival'),
                        data_type=datetime.date),]

    def get_editor_model(self, model):
        return model.purchase_item
