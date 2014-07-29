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

from kiwi.ui.objectlist import Column

from stoqlib.domain.views import ConsignedItemAndStockView
from stoqlib.gui.search.searchcolumns import IdentifierColumn, SearchColumn
from stoqlib.gui.search.searchdialog import SearchDialog
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class ConsignmentItemSearch(SearchDialog):
    title = _(u'Consignment Items Search')
    size = (-1, 450)
    search_spec = ConsignedItemAndStockView
    branch_filter_column = ConsignedItemAndStockView.branch
    text_field_columns = [ConsignedItemAndStockView.description,
                          ConsignedItemAndStockView.order_identifier_str]

    #
    # SearchDialog Hooks
    #

    def get_columns(self):
        return [IdentifierColumn('order_identifier', title=_(u"Order #")),
                SearchColumn('code', title=_(u'Code'), data_type=str,
                             width=40),
                SearchColumn('description', title=_(u'Description'),
                             data_type=str, width=250, expand=True),
                Column('stocked', title=_(u'Stock'),
                       data_type=Decimal),
                Column('received', title=_(u'Consigned'),
                       data_type=Decimal),
                Column('sold', title=_(u'Sold'),
                       data_type=Decimal),
                Column('returned', title=_(u'Returned'),
                       data_type=Decimal)]
