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
## Author(s):   George Y. Kussumoto     <george@async.com.br>
##
""" Search dialogs for loans and related objects """

from decimal import Decimal

from kiwi.datatypes import currency
from kiwi.enums import SearchFilterPosition
from kiwi.ui.objectlist import SearchColumn
from kiwi.ui.search import ComboSearchFilter

from stoqlib.domain.loan import Loan
from stoqlib.domain.views import LoanItemView
from stoqlib.gui.base.search import SearchDialog
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class LoanItemSearch(SearchDialog):
    title = _(u'Loan Items Search')
    size = (780, 450)
    table = search_table = LoanItemView

    #
    # SearchDialog Hooks
    #

    def create_filters(self):
        self.set_text_field_columns(['description'])
        # status filter
        statuses = [(desc, i) for i, desc in Loan.statuses.items()]
        statuses.insert(0, (_(u'Any'), None))
        status_filter = ComboSearchFilter(_(u'with status:'), statuses)
        status_filter.select(None)
        self.add_filter(status_filter, columns=['loan_status'],
                        position=SearchFilterPosition.TOP)

    def get_columns(self):
        return [SearchColumn('id', title=_(u'#'), data_type=int,
                             format='%03d'),
                SearchColumn('loan_id', title=_(u'Loan'), data_type=int,
                             format='%03d', sorted=True),
                SearchColumn('description', title=_(u'Description'),
                             data_type=str, expand=True),
                SearchColumn('quantity', title=_(u'Quantity'),
                             data_type=Decimal),
                SearchColumn('price', title=_(u'Price'),
                             data_type=currency),
                SearchColumn('total', title=_(u'Total'),
                             data_type=currency),]
