# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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
##

from decimal import Decimal

from kiwi.currency import currency
from kiwi.db.query import DateQueryState, DateIntervalQueryState
from kiwi.ui.search import DateSearchFilter
from kiwi.ui.objectlist import SearchColumn, Column

from stoqlib.domain.sale import SalesPersonSalesView
from stoqlib.gui.base.search import SearchDialog
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class SalesPersonSalesSearch(SearchDialog):
    title = _("Salesperson Total Sales")
    search_table = SalesPersonSalesView
    size = (600, 450)

    #
    # SearchDialog Hooks
    #

    def create_filters(self):
        self.set_text_field_columns(['name'])
        self.set_searchbar_labels(_('matching:'))
        self.executer.set_query(self.executer_query)

        date_filter = DateSearchFilter(_('Date:'))
        self.search.add_filter(date_filter)
        self.date_filter = date_filter

    def get_columns(self):
        return [SearchColumn('name', title=_('Name'), data_type=str,
                             expand=True, sorted=True),
                Column('total_quantity', title=_('Sold items'),
                       data_type=Decimal),
                Column('total_sales', title=_('Total sales'),
                       data_type=Decimal),
                Column('total_amount', title=_('Total amount'),
                       data_type=currency), ]

    def setup_widgets(self):
        self.search.set_summary_label('total_amount', label=_(u'Total:'),
                                      format='<b>%s</b>')

    def executer_query(self, query, having, conn):
        date = self.date_filter.get_state()
        if isinstance(date, DateQueryState):
            date = date.date
        elif isinstance(date, DateIntervalQueryState):
            date = (date.start, date.end)

        return self.search_table.select_by_date(date, query, connection=conn)
