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
from kiwi.enums import SearchFilterPosition
from kiwi.ui.search import ComboSearchFilter
from kiwi.ui.objectlist import SearchColumn, ColoredColumn, Column

from stoqlib.domain.commission import CommissionView
from stoqlib.domain.person import SalesPerson
from stoqlib.reporting.sale import SalesPersonReport
from stoqlib.gui.base.search import SearchDialog, IdentifierColumn
from stoqlib.gui.printing import print_report
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class CommissionSearch(SearchDialog):
    title = _("Search for Commissions")
    size = (750, 450)
    search_table = CommissionView
    searching_by_date = True

    #
    # SearchDialog Hooks
    #

    def create_filters(self):
        self.set_text_field_columns(['salesperson_name'])
        self.set_searchbar_labels(_('matching:'))

        persons = [p.person.name for p in
                   self.store.find(SalesPerson)]
        persons = zip(persons, persons)
        persons.insert(0, (_('Anyone'), None))
        salesperson_filter = ComboSearchFilter(_('Sold by:'), persons)
        self.add_filter(salesperson_filter, SearchFilterPosition.TOP,
                        ['salesperson_name'])
        self._salesperson_filter = salesperson_filter

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
        if sysparam(self.store).SALE_PAY_COMMISSION_WHEN_CONFIRMED:
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
        salesperson_name = self._salesperson_filter.combo.get_selected()
        print_report(SalesPersonReport, list(self.results),
                     salesperson_name=salesperson_name,
                     filters=self.search.get_search_filters())
