# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Search dialogs for commission objects """

from decimal import Decimal
import datetime

from kiwi.currency import currency
from kiwi.ui.objectlist import ColoredColumn, Column
from storm.expr import And

from stoqlib.api import api
from stoqlib.domain.commission import CommissionView
from stoqlib.domain.person import SalesPerson, Branch
from stoqlib.enums import SearchFilterPosition
from stoqlib.reporting.sale import SalesPersonReport
from stoqlib.gui.search.searchcolumns import IdentifierColumn, SearchColumn
from stoqlib.gui.search.searchdialog import SearchDialog
from stoqlib.gui.search.searchfilters import ComboSearchFilter
from stoqlib.gui.utils.printing import print_report
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class CommissionSearch(SearchDialog):
    title = _("Search for Commissions")
    size = (-1, 450)
    search_spec = CommissionView
    searching_by_date = True

    #
    # SearchDialog Hooks
    #

    def create_filters(self):
        self.set_text_field_columns(['salesperson_name', 'identifier_str'])

        items = api.for_combo(self.store.find(SalesPerson), empty=_("Anyone"))
        self._salesperson_filter = ComboSearchFilter(_("Sold by:"), items)
        self.add_filter(self._salesperson_filter, SearchFilterPosition.TOP,
                        callback=self._get_salesperson_query)

    def get_columns(self):
        columns = [
            IdentifierColumn('identifier', title=_('Sale #'), sorted=True),
            SearchColumn('salesperson_name', title=_('Salesperson'),
                         data_type=str, expand=True),
            # This column evals to an integer, and due to a bug
            # in kiwi, its not searchable
            Column('commission_percentage', title=_('Commission (%)'),
                   data_type=Decimal, format="%.2f"),
            # negative commissions are shown in red color
            ColoredColumn('commission_value', title=_('Commission'),
                          color='red', data_func=lambda x: x < 0,
                          data_type=currency)]

        # FIXME: The date here depends on the parameter. We could use
        # it as a property on the view, but then it would not be searchable.
        # Find a better way of handling this sometime in the future.
        if sysparam.get_bool('SALE_PAY_COMMISSION_WHEN_CONFIRMED'):
            columns.append(SearchColumn('confirm_date', title=_('Date'),
                                        data_type=datetime.date))
        else:
            columns.append(SearchColumn('paid_date', title=_('Date'),
                                        data_type=datetime.date))

        columns.extend([
            Column('payment_amount', title=_('Payment value'),
                   data_type=currency),
            Column('total_amount', title=_('Sale total'),
                   data_type=currency)])

        return columns

    def on_print_button_clicked(self, button):
        salesperson = self._salesperson_filter.combo.get_selected()
        print_report(SalesPersonReport, list(self.results),
                     salesperson=salesperson,
                     filters=self.search.get_search_filters())

    #
    #  Callbacks
    #

    def _get_salesperson_query(self, state):
        queries = []

        if api.sysparam.get_bool('SYNCHRONIZED_MODE'):
            current = api.get_current_branch(self.store)
            queries.append(Branch.id == current.id)

        salesperson = state.value
        if salesperson:
            queries.append(CommissionView.salesperson_id == salesperson.id)

        if queries:
            return And(*queries)
