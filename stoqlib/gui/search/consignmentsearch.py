# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2010 Async Open Source <http://www.async.com.br>
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
""" Search dialogs for consignment and related objects """

from decimal import Decimal

from kiwi.enums import SearchFilterPosition
from kiwi.ui.objectlist import SearchColumn

from stoqlib.domain.views import ConsignedItemAndStockView
from stoqlib.gui.base.search import SearchDialog
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class ConsignmentItemSearch(SearchDialog):
    title = _(u'Consignment Items Search')
    size = (-1, 450)
    table = search_table = ConsignedItemAndStockView

    #
    # SearchDialog Hooks
    #

    def create_filters(self):
        self.set_text_field_columns(['description'])
        # Branch
        branch_filter = self.create_branch_filter(_('In branch:'))
        self.add_filter(branch_filter, columns=['branch'],
                        position=SearchFilterPosition.TOP)

    def get_columns(self):
        return [SearchColumn('id', title=_(u'#'), data_type=int,
                             format='%03d', width=40),
                SearchColumn('order_id', title=_(u'Order'), data_type=int,
                             format='%03d'),
                SearchColumn('description', title=_(u'Description'),
                             data_type=str, width=250),
                SearchColumn('stocked', title=_(u'Stock'),
                             data_type=Decimal),
                SearchColumn('received', title=_(u'Consigned'),
                             data_type=Decimal),
                SearchColumn('sold', title=_(u'Sold'),
                             data_type=Decimal),
                SearchColumn('returned', title=_(u'Returned'),
                             data_type=Decimal)]
