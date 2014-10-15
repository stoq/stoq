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

import gtk
from kiwi.currency import currency
from kiwi.ui.objectlist import ColoredColumn, Column
from storm.expr import And

from stoqlib.api import api
from stoqlib.domain.commission import CommissionView
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.person import Branch, SalesPerson
from stoqlib.enums import SearchFilterPosition
from stoqlib.reporting.sale import SalesPersonReport
from stoqlib.gui.base.gtkadds import set_bold
from stoqlib.gui.search.searchcolumns import IdentifierColumn, SearchColumn
from stoqlib.gui.search.searchdialog import SearchDialog
from stoqlib.gui.search.searchfilters import DateSearchFilter
from stoqlib.gui.utils.printing import print_report
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.formatters import get_formatted_price
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class CommissionSearch(SearchDialog):
    title = _("Search for Commissions")
    size = (800, 450)
    search_spec = CommissionView
    report_class = SalesPersonReport
    unlimited_results = True

    #
    # Private
    #

    def _update_summary(self, results):
        payments = sales = 0
        sale_ids = set()
        for obj in results:
            payments += obj.payment_amount
            # Each sale may appear more than once in the results (once for each payment)
            if obj.id not in sale_ids:
                # If the sale was returned, Dont include it in the summary
                if not obj.sale_returned:
                    sales += obj.total_amount
                sale_ids.add(obj.id)

        self.payments_label.set_label(_(u'Total payments: %s') % get_formatted_price(payments))
        self.sales_label.set_label(_(u'Total sales: %s') % get_formatted_price(sales))

    def _get_method_values(self):
        methods = PaymentMethod.get_active_methods(self.store)
        values = [(i.get_description(), i.method_name) for i in methods
                  if i.method_name != 'multiple']
        return values

    #
    # SearchDialog Hooks
    #

    def setup_widgets(self):
        hbox = gtk.HBox()
        hbox.set_spacing(6)

        self.vbox.pack_start(hbox, False, True)
        self.vbox.reorder_child(hbox, 2)
        self.vbox.set_spacing(6)

        hbox.pack_start(gtk.Label(), True, True)

        # Create two labels to show a summary for the search (kiwi's
        # SummaryLabel supports only one column)
        self.payments_label = gtk.Label()
        hbox.pack_start(self.payments_label, False, False)

        self.sales_label = gtk.Label()
        hbox.pack_start(self.sales_label, False, False)
        hbox.show_all()

        set_bold(self.payments_label)
        set_bold(self.sales_label)
        self.add_csv_button(_('Commissions'), _('commissions'))

    def create_filters(self):
        self.set_text_field_columns(['salesperson_name', 'identifier_str'])

        self._salesperson_filter = self.create_salesperson_filter(_("Sold by:"))
        self.add_filter(self._salesperson_filter, SearchFilterPosition.TOP,
                        callback=self._get_salesperson_query)

        # Adding a filter by date with custom interval
        self._date_filter = DateSearchFilter(_("Date:"))
        self._date_filter.select(data=DateSearchFilter.Type.USER_INTERVAL)
        if sysparam.get_bool('SALE_PAY_COMMISSION_WHEN_CONFIRMED'):
            self.add_filter(self._date_filter, SearchFilterPosition.BOTTOM,
                            columns=[self.search_spec.confirm_date])
        else:
            self.add_filter(self._date_filter, SearchFilterPosition.BOTTOM,
                            columns=[self.search_spec.paid_date])

    def get_columns(self):
        columns = [
            IdentifierColumn('identifier', title=_('Sale #'), sorted=True),
            SearchColumn('salesperson_name', title=_('Salesperson'),
                         data_type=str, expand=True),
            SearchColumn('method_description', title=_('Method'), data_type=str,
                         search_attribute='method_name',
                         valid_values=self._get_method_values()),
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

    def print_report(self):
        salesperson_id = self._salesperson_filter.combo.get_selected()
        salesperson = (salesperson_id and
                       self.store.get(SalesPerson, salesperson_id))

        print_report(self.report_class, list(self.results),
                     salesperson=salesperson,
                     filters=self.search.get_search_filters())

    #
    #  Callbacks
    #

    def on_search__search_completed(self, search, result_view, states):
        self._update_summary(result_view)

    def _get_salesperson_query(self, state):
        queries = []

        if api.sysparam.get_bool('SYNCHRONIZED_MODE'):
            current = api.get_current_branch(self.store)
            queries.append(Branch.id == current.id)

        salesperson = state.value
        if salesperson:
            queries.append(CommissionView.salesperson_id == salesperson)

        if queries:
            return And(*queries)
