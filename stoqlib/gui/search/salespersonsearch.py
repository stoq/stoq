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

from stoqlib.database.queryexecuter import DateQueryState, DateIntervalQueryState
from stoqlib.domain.sale import SalesPersonSalesView, Sale
from stoqlib.gui.search.searchcolumns import SearchColumn, Column
from stoqlib.gui.search.searchdialog import SearchDialog
from stoqlib.gui.search.searchfilters import DateSearchFilter
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class SalesPersonSalesSearch(SearchDialog):
    title = _("Salesperson Total Sales")
    search_spec = SalesPersonSalesView
    size = (-1, 450)
    text_field_columns = [SalesPersonSalesView.name]
    branch_filter_column = Sale.branch_id

    #
    # SearchDialog Hooks
    #

    def create_filters(self):
        self.search.set_query(self.executer_query)
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
                       data_type=currency),
                # Column('paid_value', title=_('Paid'),
                #        data_type=currency, visible=True),
                ]

    def setup_widgets(self):
        self.search.set_summary_label('total_amount', label=_(u'Total:'),
                                      format='<b>%s</b>')

    # TODO: Maybe this can be removed
    def executer_query(self, store):
        date = self.date_filter.get_state()
        if isinstance(date, DateQueryState):
            date = date.date
        elif isinstance(date, DateIntervalQueryState):
            date = (date.start, date.end)

        resultset = self.search_spec.find_by_date(store, date)
        return resultset
